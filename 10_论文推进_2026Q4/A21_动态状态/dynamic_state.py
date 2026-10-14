"""A21 / WP1.3: 动态储冷与溶质状态实验（GPT 意见2 §WP1.1/§WP1.3）.

【为什么做】
GPT 指出：项目的全部中心结果都在"零储冷 + 稳态水质"下取得；
储冷、溶质累积、处理延迟**从未在研究中启用过**。
引擎其实已有 opt-in 的 R10a 水质状态路径（`quality_state_enabled=True`，
含 `QualityState` / `mix_quality_states` / `withdraw_quality_state` /
`partition_blowdown_solutes`），但**只在单日诊断脚本里跑过**
（`scripts/audit_r10a_quality_invariants.py`），从未进入多情景研究。

【本实验要回答】
  Q1 启用逐日储冷 + 溶质状态后，稳态结论（A17 的三量判据）是否仍成立？
  Q2 储冷容量是否引入**超出静态恒等式**的新机制（时滞、迟滞、累积）？
  Q3 若存在新机制，它能否用一个**可外部预测的量**刻画？

【纪律】
  全部量取自引擎执行的逐日输出；不引入自造公式。
  与"零储冷"基线配对比较（同输入、仅切换 quality_state_enabled / 储冷容量）。
"""
from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ENGINE = Path(r"C:/Users/mmrgr/Desktop/论文/算力中心/07_代码_AI-UWM引擎/aiuwm_src")
if str(ENGINE / "src") not in sys.path:
    sys.path.insert(0, str(ENGINE / "src"))

from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ENGINE / "examples" / "cawcc_r2"
DOMS = ("ha", "co")
# 储冷容量档 (ML): 0 = 与既有研究一致的零储冷基线
STORAGE_GRID = (0.0, 50.0, 200.0, 800.0)


def load(dom: str):
    proj = json.loads((R2 / dom / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / dom / "timeseries.csv")
    return proj, ts


def run_case(dom: str, storage_ml: float, *, quality_state: bool,
             reuse_fraction: float = 0.6, treatment_capacity_ml_day: float = 200.0,
             tds_limits: float = 1100.0, reclaimed_tds: float = 900.0,
             potable_tds: float = 200.0) -> dict:
    """单情景：设定储冷容量与水质状态开关，跑完整日尺度引擎。"""
    proj, ts = load(dom)
    proj = copy.deepcopy(proj)
    dc = proj["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = 1000.0
    dc["cooling_storage_capacity_ml"] = float(storage_ml)
    dc["cooling_storage_ml"] = float(storage_ml) / 2.0      # 半满初值, 避免端点偏差
    dc["initial_cooling_storage_ml"] = float(storage_ml) / 2.0
    dc["quality_state_enabled"] = bool(quality_state)
    dc["cooling"]["coc_mode"] = "quality_limited"
    dc["cooling"]["cycles_of_concentration"] = 8.0
    dc["cooling"]["water_quality_limits"] = {"TDS": float(tds_limits)}
    dc["water_sources"]["reclaimed"]["target_fraction"] = float(reuse_fraction)
    dc["water_sources"]["potable"]["target_fraction"] = 1.0 - float(reuse_fraction)
    dc["water_sources"]["reclaimed"]["quality_mg_l"] = {"TDS": float(reclaimed_tds)}
    dc["water_sources"]["potable"]["quality_mg_l"] = {"TDS": float(potable_tds)}

    reuse = proj["components"].get("CENTRAL_REUSE")
    if reuse is not None:
        reuse["treatment_capacity_ml_day"] = float(treatment_capacity_ml_day)
        reuse["quality_mg_l"] = {"TDS": float(reclaimed_tds)}
        reuse["quality_provenance"] = "treated_output"

    sim = proj.setdefault("simulation", {})
    sim["start"] = str(pd.Timestamp(ts["date"].iloc[0]).date())
    sim["end"] = str(pd.Timestamp(ts["date"].iloc[-1]).date())

    res = FullAIUWMModel(proj, ts).run()
    d = res.data_center_daily
    area = getattr(res, "area_daily", None)

    def s(df, col):
        if df is None or col not in df.columns:
            return float("nan")
        return float(pd.to_numeric(df[col], errors="coerce").sum())

    out = {
        "domain": dom, "storage_ml": float(storage_ml),
        "quality_state": bool(quality_state),
        "reuse_fraction": float(reuse_fraction),
        "n_days": int(len(d)),
        # 逐日求和的主要量
        "evaporation_ml": s(d, "evaporation_ml"),
        "makeup_ml": s(d, "external_makeup_ml"),
        "blowdown_ml": s(d, "blowdown_ml"),
        "reclaimed_used_ml": s(d, "reclaimed_used_ml"),
        "potable_used_ml": s(d, "potable_used_ml"),
        "storage_end_ml": float(pd.to_numeric(d["cooling_storage_ml"], errors="coerce").iloc[-1])
        if "cooling_storage_ml" in d.columns else float("nan"),
        "coc_mean": float(pd.to_numeric(d["cycles_of_concentration"], errors="coerce").mean())
        if "cycles_of_concentration" in d.columns else float("nan"),
        "coc_min": float(pd.to_numeric(d["cycles_of_concentration"], errors="coerce").min())
        if "cycles_of_concentration" in d.columns else float("nan"),
    }
    # 场级量（若有）
    if area is not None:
        for c in ("reuse_delivered_ml", "potable_delivered_ml", "demand_industrial_ml",
                  "demand_municipal_misc_ml"):
            out[f"area_{c}"] = s(area, c)
    # 水质状态量（R10a 路径）
    for c in ("loop_tds_mg_l", "storage_tds_mg_l", "makeup_tds_mg_l",
              "blowdown_tds_mg_l"):
        if c in d.columns:
            out[f"{c}_mean"] = float(pd.to_numeric(d[c], errors="coerce").mean())
    # 水/溶质闭合残差
    for c in ("water_balance_residual_ml", "solute_balance_residual_kg"):
        if c in d.columns:
            v = pd.to_numeric(d[c], errors="coerce").abs()
            out[f"{c}_max_abs"] = float(v.max())
    return out


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 80)
    rec("A21 / WP1.3  动态储冷与溶质状态实验")
    rec("=" * 80)

    rows = []
    for dom in DOMS:
        for st in STORAGE_GRID:
            for qs in (False, True):     # False = 既有研究口径(零水质状态)
                try:
                    r = run_case(dom, st, quality_state=qs)
                    rows.append(r)
                    rec(f"  {dom} storage={st:6.1f} ML quality_state={str(qs):5} "
                        f"| makeup={r['makeup_ml']:12.0f} coc_mean={r['coc_mean']:.3f}")
                except Exception as e:  # noqa: BLE001
                    rec(f"  ERROR {dom} st={st} qs={qs}: {type(e).__name__}: {e}")
    d = pd.DataFrame(rows)
    d.to_csv(HERE / "dynamic_state_grid.csv", index=False, encoding="utf-8-sig")
    rec(f"\n完成 {len(d)} 情景")

    if len(d) == 0:
        raise SystemExit("全部失败 —— 见日志")

    # ---------- Q1: 闭合性 ----------
    rec("\n[Q1] 物理闭合 (必须有界且小)")
    for c in ("water_balance_residual_ml_max_abs", "solute_balance_residual_kg_max_abs"):
        if c in d.columns:
            rec(f"  {c}: max = {d[c].max():.3e}  (非零行数 = {int((d[c] > 1e-9).sum())})")

    # ---------- Q2: 储冷是否改变稳态结果 ----------
    rec("\n[Q2] 储冷容量对补水的影响 (与 0 储冷配对)")
    base = d[(d.storage_ml == 0.0)].set_index(["domain", "quality_state"])
    for (dom, qs), g in d.groupby(["domain", "quality_state"]):
        b = base.loc[(dom, qs), "makeup_ml"]
        for _, r in g.sort_values("storage_ml").iterrows():
            rec(f"  {dom} qs={qs} storage={r['storage_ml']:6.1f}: "
                f"makeup={r['makeup_ml']:12.0f}  Δ vs 0={r['makeup_ml']-b:+10.0f} ML "
                f"({100*(r['makeup_ml']-b)/max(b,1e-9):+6.2f}%)")

    # ---------- Q3: 水质状态是否引入新机制 ----------
    rec("\n[Q3] 水质状态 (R10a) 是否改变结果")
    for dom in DOMS:
        a = d[(d.domain == dom) & (~d.quality_state)].set_index("storage_ml")["makeup_ml"]
        b = d[(d.domain == dom) & (d.quality_state)].set_index("storage_ml")["makeup_ml"]
        common = a.index.intersection(b.index)
        for st in common:
            rec(f"  {dom} storage={st:6.1f}: qs_off={a[st]:12.0f} qs_on={b[st]:12.0f} "
                f"Δ={b[st]-a[st]:+10.0f} ML")

    summary = {
        "n_scenarios": int(len(d)),
        "storage_grid_ml": list(STORAGE_GRID),
        "n_days": int(d["n_days"].iloc[0]),
        "water_closure_max_abs_ml": float(d.get("water_balance_residual_ml_max_abs",
                                                pd.Series([np.nan])).max()),
        "solute_closure_max_abs_kg": float(d.get("solute_balance_residual_kg_max_abs",
                                                 pd.Series([np.nan])).max()),
        "makeup_by_storage": {
            f"{dom}|qs={qs}": {
                str(int(r.storage_ml)): float(r.makeup_ml)
                for _, r in g.sort_values("storage_ml").iterrows()}
            for (dom, qs), g in d.groupby(["domain", "quality_state"])},
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": (
            "启用引擎原生 opt-in 的 R10a 逐日水质状态路径 (quality_state_enabled)。"
            "全部量取自逐日输出求和; 与同输入零储冷基线配对。首次把该路径用于多情景研究。"),
    }
    (HERE / "dynamic_state_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    rec(f"\n完成 {summary['runtime_s']}s")
    (HERE / "a21_repro_log.txt").write_text("\n".join(log), encoding="utf-8")


if __name__ == "__main__":
    main()
