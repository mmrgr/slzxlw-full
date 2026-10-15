"""A25 审计: 核实 incumbent 的需求上界到底是 gap 还是 P0+gap.

【关键疑点】
A17 用 elig = P0 + gap 作为"既有用户可回用需求", 并据此给 critical_pool_scale = (P0+gap)/P0。
但 city_model.solve_city 里:
    JointQualityRequest("INC", ..., incumbent_reclaimed_ml=inc_claim,
                        max_reclaimed_ml=max(inc_claim, gap, 1e-9), ...)
且 A17 自身:
    inc_demand = bl["gap"]        # 既有用户最大可主张量
⇒ incumbent 的上界是 **gap**, 不是 P0+gap。

【本脚本】
  直接调用 solve_city 检验: 当 pool 在 [gap, P0+gap) 区间时, incumbent 是否已拿满 gap?
  若拿满 ⇒ 上界是 gap ⇒ A17 的 elig 用错。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "A10_敏感性与边界"))
import city_model as cm  # noqa: E402

out = {}
for dom in ("ha", "co"):
    bl = cm.BASELINES[dom]
    P0, gap = bl["P0"], bl["gap"]
    print(f"\n=== D-{dom.upper()}  P0={P0:.2f}  gap={gap:.2f}  P0+gap={P0+gap:.2f} ===")
    print(f"  {'pool':>12} {'pool/P0':>8} {'inc_recl':>11} {'拿满gap?':>9} {'x_ai':>10}")
    rows = []
    samples = cm.load_samples()
    row = samples[samples["source"] == "IEUA RP-1 (2025, tertiary)"].iloc[0]
    q = cm.quality_dict(row, cm.PANELS["B_full"])
    m0 = cm.m0_of(bl, "B_full", q)
    for target_ps in (0.9, 1.2, 1.3841, 1.6, 2.0, 2.3841, 2.6, 3.0):
        pool = P0 * target_ps
        # solve_city(bl, panel_name, sample, q, m0, pool, gap, dp, ai_target)
        r = cm.solve_city(bl, "B_full", "IEUA RP-1 (2025, tertiary)",
                          q, m0, pool, gap, 0.0, 0.7)
        inc = float(r["inc_reclaimed_ml"])
        x_ai = float(r["x_ai_ml"])
        sat = bool(inc >= gap - 1e-6)
        rows.append({"pool": float(pool), "pool_over_P0": float(target_ps),
                     "inc_reclaimed": inc, "saturated": sat, "x_ai": x_ai})
        print(f"  {pool:12.1f} {target_ps:8.4f} {inc:11.2f} {str(sat):>9} {x_ai:10.2f}")
    out[dom] = {"P0": float(P0), "gap": float(gap), "P0_plus_gap": float(P0 + gap),
                "gap_over_P0": float(gap / P0), "rows": rows}

summary = {
    "question": "incumbent 的可主张上界是 gap 还是 P0+gap?",
    "evidence": (
        "city_model.solve_city 传 max_reclaimed_ml=max(inc_claim, gap, 1e-9) 且 inc_claim=0 "
        "⇒ 上界是 gap; A17 自身也写 inc_demand = bl['gap']。"),
    "conclusion": (
        "A17 的 elig = P0 + gap 把 incumbent 上界**高估了一个 P0**, "
        "导致 critical_pool_scale = (P0+gap)/P0 比真实 surplus 门槛高约 1.0。"
        "真实门槛为 pool >= gap + x_ai_B1, 即 pool_scale >= gap/P0 + x_ai_B1/P0。"),
    "by_domain": out,
    "impact": (
        "A24b 的外部效度检验**不受影响**(它用经验测量阈值 2.0/2.2/2.4, 非该闭式值)。"
        "但 A17 文档与 summary 中的 critical_pool_scale 必须更正/加注。"),
    "discipline_note": "直接调用 city_model.solve_city 独立验证; 未改引擎。",
}
(HERE / "incumbent_bound_audit.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
print("\n[write] incumbent_bound_audit.json")
