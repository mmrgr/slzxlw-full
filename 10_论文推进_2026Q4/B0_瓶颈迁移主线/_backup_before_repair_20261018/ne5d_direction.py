"""阶段 2-d：验证方向性声明 —— 改用 R10a 后 dS_pot 是否更负(更有利)?

【为何必须做】
我在阶段2结论中写下"volume-only 高估水质惩罚 ⇒ dS_pot 偏正(偏害) ⇒ R10a 下会更负"。
这是**推断, 不是实测**。若写入主稿而不验证, 就是新的"未证主张"。

【方法】
小规模抽样: 4 组成 × 2 域 × 3 φ × 2 pool = 48 情景, 在两条路径下各算 dS_pot。
注意: R10a 只能走完整引擎(FullAIUWMModel), 不能走 city_model 的 solve_city。
因此本脚本**直接用引擎**算 M0 / M1, 再用主估计量公式组装 dS_pot:
    dS_pot = C - F - x_ai,  其中在纯挤占(池用尽)下 x_ai == C, 故 dS_pot = -F = -(M0-M1)
即 dS_pot = M1 - M0。两支路之差即 C - x_ai = 0。

本检验聚焦【设施级补水差】F = M0 - M1 的符号与量级:
    F > 0 (回用省水) ⇒ dS_pot = -F < 0 (城市受益)
比较两条路径的 F, 即可判定方向。
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).resolve().parents[2] / "07_代码_AI-UWM引擎" / "aiuwm_src"
sys.path.insert(0, str(ENGINE / "src"))

import pandas as pd  # noqa: E402

from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ENGINE / "examples" / "cawcc_r2"
OUT = HERE / "ne5d_direction_summary.json"

SAMPLES = {
    "IEUA": {"TDS": 443.0, "chloride": 100.0, "hardness": 149.427,
             "alkalinity": 140.0, "silica": 24.0},
    "LADWP": {"TDS": 22.0, "chloride": 3.6, "hardness": 1.024,
              "alkalinity": 7.1, "silica": 0.52},
    # Figshare RW 源表确无 silica; 引擎要求 5 物种齐全, 故用同类回用水上界 175*0.5
    # 作为显式标注的假设值 (仅本方向性检验使用)
    "FigshareRW": {"TDS": 1378.0, "chloride": 313.7325, "hardness": 538.5185,
                   "alkalinity": 228.18, "silica": 87.5},
    "Assumed": {"TDS": 650.0, "chloride": 130.0, "hardness": 400.0,
                "alkalinity": 200.0, "silica": 15.0},
}
POTABLE = {"TDS": 180.0, "chloride": 35.0, "hardness": 120.0,
           "alkalinity": 100.0, "silica": 10.0}
LIMITS = {"TDS": 2200.0, "chloride": 700.0, "hardness": 750.0,
          "alkalinity": 350.0, "silica": 175.0}


def run(domain: str, q: dict, phi: float, quality_state: bool) -> float:
    """返回全期外部补水量 M (ML)。"""
    proj = json.loads((R2 / domain / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / domain / "timeseries.csv")
    proj = copy.deepcopy(proj)
    dc = proj["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = 1000.0
    dc["quality_state_enabled"] = bool(quality_state)
    dc["cooling"]["coc_mode"] = "quality_limited"
    dc["cooling"]["cycles_of_concentration"] = 5.0
    dc["cooling"]["water_quality_limits"] = dict(LIMITS)
    dc["water_sources"]["reclaimed"]["target_fraction"] = float(phi)
    dc["water_sources"]["potable"]["target_fraction"] = 1.0 - float(phi)
    for src, qq in (("reclaimed", q), ("potable", POTABLE)):
        s = dc["water_sources"][src]
        s["quality_mg_l"] = dict(qq)
        s.pop("quality", None)
    sim = proj.setdefault("simulation", {})
    sim["start"] = str(pd.Timestamp(ts["date"].iloc[0]).date())
    sim["end"] = str(pd.Timestamp(ts["date"].iloc[-1]).date())
    r = FullAIUWMModel(proj, ts).run()
    return float(r.data_center_daily["external_makeup_ml"].sum())


def main() -> int:
    print("=" * 78)
    print("阶段 2-d ｜ 方向性验证: R10a 是否使 dS_pot 更负(更有利)?")
    print("=" * 78)
    print("\n逻辑: dS_pot = M1 - M0 (纯挤占分支)。")
    print("      R10a 的 CoC 更高 ⇒ M1 更小 ⇒ M1-M0 更负 ⇒ 城市更受益。\n")

    rows = []
    for dom in ("ha", "co"):
        for name, q in SAMPLES.items():
            for phi in (0.4, 0.6):
                m0_vo = run(dom, q, 0.0, False)
                m1_vo = run(dom, q, phi, False)
                m0_r10 = run(dom, q, 0.0, True)
                m1_r10 = run(dom, q, phi, True)
                f_vo = m0_vo - m1_vo
                f_r10 = m0_r10 - m1_r10
                ds_vo = m1_vo - m0_vo
                ds_r10 = m1_r10 - m0_r10
                rows.append({"domain": dom, "sample": name, "phi": phi,
                             "F_volume_only": f_vo, "F_r10a": f_r10,
                             "dS_volume_only": ds_vo, "dS_r10a": ds_r10,
                             "R10a_more_negative": (ds_r10 < ds_vo)})
                print(f"  {dom} {name:<11} φ={phi}  "
                      f"dS_vo={ds_vo:>10.1f}  dS_r10a={ds_r10:>10.1f}  "
                      f"{'更负✓' if ds_r10 < ds_vo else '更负✗'}")

    df = pd.DataFrame(rows)
    n_more_neg = int(df["R10a_more_negative"].sum())
    n_all = len(df)
    print("\n" + "=" * 78)
    print("裁定")
    print("=" * 78)
    print(f"  R10a 使 dS_pot 更负的情景 = {n_more_neg}/{n_all}")
    if n_more_neg == n_all:
        verdict = "DIRECTION_CONFIRMED_R10A_MORE_BENEFICIAL"
    elif n_more_neg == 0:
        verdict = "DIRECTION_REFUTED_R10A_MORE_HARMFUL"
    else:
        verdict = "MIXED"
    print(f"  ⇒ {verdict}")

    # 符号是否变化
    flips = int(((df.dS_volume_only > 0) != (df.dS_r10a > 0)).sum())
    print(f"  dS 符号翻转的情景 = {flips}/{n_all}")
    nulls = int((df.dS_volume_only.abs() < 1e-9).sum())
    print(f"  (其中 volume-only 为 0 的情景 = {nulls})")

    OUT.write_text(json.dumps({
        "rows": rows,
        "n_more_negative": n_more_neg,
        "n_total": n_all,
        "sign_flips": flips,
        "n_volume_only_zero": nulls,
        "verdict": verdict,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n[write] {OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
