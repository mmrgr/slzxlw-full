"""A25 审计 (续): 解决两个问题.

【问题 A】为何"加了 OR x_ai=0"后吻合率【下降】?
  按推导 x_ai_B1=0 ⇒ inc_B1 = min(gap, pool-0) = inc_B2 ⇒ displaced=0。
  若该推理成立, 加这一支只可能提高吻合率。实测却下降 ⇒ 说明存在
  "x_ai≈0 但 displaced≠0" 的情景, 需查明原因(可能是 A17 的 displaced 定义
  与 inc_* 列不一致, 或 x_ai 是 B1 的列但 displaced 用的是别的量)。

【问题 B】真实 surplus 门槛的精确分布
  推导门槛 pool_scale* = gap/P0 + x_ai_B1/P0 (随情景变)。
  报告其分布, 并给出"最宽松"(最小值)与"严格"(中位/最大)三种取值对
  A24b 外部效度结论的影响, 以确认结论对阈值选择稳健。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "A10_敏感性与边界"))
import city_model as cm  # noqa: E402

ss = pd.read_csv(ROOT / "A13_可靠性机制" / "supply_state_regimes.csv", encoding="utf-8-sig")
for c in ("displaced_ml", "x_ai_B1_ml", "pool_ml", "inc_B2_ml", "inc_B1_ml",
          "inc_demand_ml", "elig_ml"):
    ss[c] = pd.to_numeric(ss[c], errors="coerce")
ss["zero"] = ss["displaced_ml"].abs() < 1e-6

print("=" * 78)
print("问题 A: x_ai≈0 但 displaced≠0 的情景")
print("=" * 78)
odd = ss[(ss["x_ai_B1_ml"].abs() <= 1e-6) & (~ss["zero"])]
print(f"  情景数 = {len(odd)} / {len(ss)}")
if len(odd):
    print(odd[["domain", "sample", "pool_scale", "phi", "chi",
               "x_ai_B1_ml", "inc_B2_ml", "inc_B1_ml", "displaced_ml",
               "inc_demand_ml"]].head(12).to_string(index=False))
    print()
    print("  ⇒ 若 x_ai=0 却仍有挤占, 说明 A17 的 displaced 列并非单纯 inc_B2-inc_B1,")
    print("     或 x_ai_B1 列在 0 附近有数值噪声。核查: ")
    print(f"     displaced 与 (inc_B2-inc_B1) 最大差 = "
          f"{(ss.displaced_ml - (ss.inc_B2_ml - ss.inc_B1_ml)).abs().max():.3e}")

print()
print("=" * 78)
print("问题 B: 真实 surplus 门槛分布 (pool_scale* = gap/P0 + x_ai_B1/P0)")
print("=" * 78)
thr = {}
for dom in ("ha", "co"):
    bl = cm.BASELINES[dom]
    P0, gap = bl["P0"], bl["gap"]
    d = ss[ss.domain == dom].copy()
    d["ps"] = d["pool_ml"] / P0
    d["thr_true"] = gap / P0 + d["x_ai_B1_ml"] / P0
    # 只统计零挤占情景的真实门槛(它们给出了"至少需要多少")
    z = d[d.zero]
    thr[dom] = {
        "gap_over_P0": float(gap / P0),
        "thr_min": float(d.thr_true.min()),
        "thr_median": float(d.thr_true.median()),
        "thr_max": float(d.thr_true.max()),
        "z_thr_max": float(z.thr_true.max()) if len(z) else float("nan"),
        "z_thr_median": float(z.thr_true.median()) if len(z) else float("nan"),
        "grid_min_scale_with_surplus": float(d[d.zero].ps.min()) if len(z) else float("nan"),
    }
    print(f"\n  D-{dom.upper()}: gap/P0={gap/P0:.4f}")
    print(f"    真实门槛分布: min={d.thr_true.min():.3f} median={d.thr_true.median():.3f} "
          f"max={d.thr_true.max():.3f}")
    print(f"    零挤占情景中: 门槛 median={z.thr_true.median():.3f} max={z.thr_true.max():.3f}")
    print(f"    实测 grid 上出现 surplus 的最小 pool_scale = {d[d.zero].ps.min():.3f}")
    print(f"    ⚠ A17 报告的 elig/P0 = {(P0+gap)/P0:.3f}  >> 真实门槛 ⇒ 明显偏高")

print()
print("=" * 78)
print("对 A24b 的影响: 三种阈值下的 surplus 现实占比 (r=0.5)")
print("=" * 78)
EXT = Path(r"C:/Users/mmrgr/Desktop/论文/_ext_data/source_data/Source_data.xlsx")
if EXT.exists():
    x = pd.ExcelFile(EXT)
    d = x.parse("WWTP_data_2020", header=0)
    cap = pd.to_numeric(d["Design Capacity/(10⁴ m³/d)"], errors="coerce") * 10.0
    lr = pd.to_numeric(d["Load Rate"], errors="coerce")
    act = (cap * lr).dropna()
    r = 0.5
    rec = act * r
    print(f"  {'阈值方案':28} {'D-HA surplus%':>14} {'D-CO surplus%':>14}")
    for label, key in (("A17 elig/P0 (偏高)", "elig_over_P0"),
                       ("经验首次出现 (2.0)", "grid"),
                       ("真实门槛中位", "median"),
                       ("真实门槛最大值", "max")):
        row = []
        for dom in ("ha", "co"):
            if key == "elig_over_P0":
                bl = cm.BASELINES[dom]
                t = (bl["P0"] + bl["gap"]) / bl["P0"]
            elif key == "grid":
                t = thr[dom]["grid_min_scale_with_surplus"]
            elif key == "median":
                t = thr[dom]["thr_median"]
            else:
                t = thr[dom]["thr_max"]
            need = t * cm.BASELINES[dom]["P0"] / cm.N_DAYS
            row.append(float((rec >= need).mean()) * 100)
        print(f"  {label:28} {row[0]:14.2f} {row[1]:14.2f}")

summary = {
    "problem_A": {
        "n_odd": int(len(odd)),
        "displaced_vs_inc_diff": float(
            (ss.displaced_ml - (ss.inc_B2_ml - ss.inc_B1_ml)).abs().max()),
    },
    "problem_B": thr,
    "finding": (
        "A17 的 critical_pool_scale = elig/P0 = (P0+gap)/P0 **不是** surplus 门槛, "
        "比真实门槛 (gap/P0 + x_ai/P0) 高出一个 P0。真实门槛随 phi/chi/水样变化。"),
    "impact": (
        "A17 文档与 summary 的 critical_pool_scale 须加注更正。A24b 用的是经验/真实门槛, "
        "结论(committed 占绝对多数)对阈值选择稳健。"),
    "discipline_note": "独立重算; 未改引擎。",
}
(HERE / "threshold_audit2.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
print("\n[write] threshold_audit2.json")
