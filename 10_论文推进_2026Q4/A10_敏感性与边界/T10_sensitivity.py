"""T10: 全局敏感性 (Morris 筛选 + Sobol 方差分解).

目标估计量
----------
y = S_city / M0   (无量纲城市净水源取水变化; >0 表示城市净获益)

控制量 (归一化物理域, 见 city_model.CONTROL_BOUNDS)
    pool_scale  城市再生水池规模 / P0        [0.3, 4.0]
    gap_scale   既有用户缺口 / gap           [0.3, 4.0]
    dp_scale    新增回用产能 / P0            [0.0, 3.0]
    ai_target   AI 目标再生水掺混比          [0.10, 0.95]

为什么用全局方法 (规划 §2.5)
    单因素扫描会被审稿人驳回; Morris 先筛 (便宜, 给 mu/mu_star/sigma),
    Sobol 对关键参数做方差分解 (S1/ST).

纪律 (审计教训)
    1. y 是**估计量**, 不是可迁移规律; 本表只回答"哪些控制量主导 y 的方差".
    2. 如实报告: 若某控制量不显著, 就报不显著, 不事后挑显著项.
    3. 冻结口径: pool/gap 为分配池与缺口, dp 为专用增量, 规则 = Ls(既有主张0).

调用引擎现成实现: aiuwm.sensitivity.morris_sensitivity / sobol_sensitivity.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import city_model as cm  # noqa: E402

from aiuwm.sensitivity import morris_sensitivity, sobol_sensitivity  # noqa: E402

SAMPLE_RECLAIMED = "IEUA RP-1 (2025, tertiary)"
SAMPLE_MODEL = "AI-UWM model assumption"

CONFIGS = [
    ("ha|B_full|IEUA", "ha", "B_full", SAMPLE_RECLAIMED),
    ("co|B_full|IEUA", "co", "B_full", SAMPLE_RECLAIMED),
    ("ha|B_full|model", "ha", "B_full", SAMPLE_MODEL),
    ("ha|A_engine2|IEUA", "ha", "A_engine2", SAMPLE_RECLAIMED),
]


def make_evaluator(dom, panel, sample, samples, counter):
    cache: dict = {}

    def evaluator(p: dict) -> float:
        out = cm.city_outcome(dom, panel, sample,
                              pool_scale=p["pool_scale"], gap_scale=p["gap_scale"],
                              dp_scale=p["dp_scale"], ai_target=p["ai_target"],
                              cache=cache, samples=samples)
        y = out["y"]
        counter["n"] += 1
        if not np.isfinite(y):
            counter["nan"] += 1
            return 0.0
        return float(y)

    return evaluator


def main() -> int:
    samples = cm.load_samples()
    bounds = cm.CONTROL_BOUNDS

    morris_rows, sobol_rows = [], []
    for tag, dom, panel, sample in CONFIGS:
        counter = {"n": 0, "nan": 0}
        ev = make_evaluator(dom, panel, sample, samples, counter)
        m = morris_sensitivity(ev, bounds, trajectories=24, seed=20261014)
        m.insert(0, "config", tag)
        morris_rows.append(m)
        print(f"[Morris] {tag}: n_eval={counter['n']} nan={counter['nan']}")
        print(m.to_string(index=False))

    # Sobol 只在主配置上跑 (贵)
    tag, dom, panel, sample = CONFIGS[0]
    counter = {"n": 0, "nan": 0}
    ev = make_evaluator(dom, panel, sample, samples, counter)
    s = sobol_sensitivity(ev, bounds, samples=512, seed=20261014)
    s.insert(0, "config", tag)
    sobol_rows.append(s)
    print(f"\n[Sobol] {tag}: n_eval={counter['n']} nan={counter['nan']}")
    print(s.to_string(index=False))

    mo = pd.concat(morris_rows, ignore_index=True)
    so = pd.concat(sobol_rows, ignore_index=True)
    mo.to_csv(HERE / "T10_morris.csv", index=False, encoding="utf-8-sig")
    so.to_csv(HERE / "T10_sobol.csv", index=False, encoding="utf-8-sig")

    # 主配置排名摘要
    m_main = mo[mo.config == "ha|B_full|IEUA"].sort_values("mu_star", ascending=False)
    s_main = so.sort_values("ST", ascending=False)
    summary = {
        "estimand": "y = S_city / M0 (Ls rule: incumbent claim = 0)",
        "control_bounds": {k: list(v) for k, v in bounds.items()},
        "configs": [c[0] for c in CONFIGS],
        "morris_main_ranking": m_main[["parameter", "mu", "mu_star", "sigma"]]
            .round(5).to_dict(orient="records"),
        "sobol_main": s_main[["parameter", "S1", "ST"]].round(5).to_dict(orient="records"),
        "morris_by_config": {
            c: mo[mo.config == c].sort_values("mu_star", ascending=False)
                [["parameter", "mu_star", "sigma"]].round(5).to_dict(orient="records")
            for c in mo.config.unique()},
        "interpretation": "global sensitivity of the city-level estimand to the four "
                          "allocation knobs; ranking is model-based and conditional on "
                          "the Ls rule and the frozen water samples",
    }
    (HERE / "T10_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("\n[T10] 已写出 T10_morris.csv / T10_sobol.csv / T10_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
