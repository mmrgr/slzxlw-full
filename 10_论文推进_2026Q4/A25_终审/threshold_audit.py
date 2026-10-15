"""A25 审计: 核实 A17 的"理论临界 pool_scale"是否真的是 surplus 门槛.

【疑点】
A17 报告 critical_pool_scale = elig/P0 = (P0+gap)/P0 (ha 2.384 / co 2.567),
但实测 surplus 在 pool_scale=2.0 就已出现(早于 2.384), 50% 于 2.2/2.4。

【推导】
零挤占(surplus)的条件是: 既有用户在 B1(AI 进入后)仍能拿满其最大主张 gap
   ⇒ pool - x_ai_B1 >= gap
   ⇒ pool >= gap + x_ai_B1
   ⇒ pool_scale >= gap/P0 + x_ai_B1/P0          <-- 真正的门槛, 随 phi/chi 变!

而 A17 用的 elig/P0 = (P0+gap)/P0 = 1 + gap/P0, 只有当 x_ai_B1 = P0 时才相等。
x_ai_B1 随 phi、chi、水样变化 ⇒ 门槛不可能是常数 2.384。

【本脚本验证】
  对每个 (dom,pool_scale,phi,chi,sample) 检验"零挤占 <=> pool >= gap + x_ai_B1"。
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
for c in ("displaced_ml", "x_ai_B1_ml", "M0_ml", "M1_ml", "dS_pot_ml",
          "inc_B2_ml", "inc_B1_ml", "pool_ml", "inc_demand_ml"):
    ss[c] = pd.to_numeric(ss[c], errors="coerce")

rows = []
for dom in ("ha", "co"):
    bl = cm.BASELINES[dom]
    P0, gap = bl["P0"], bl["gap"]
    d = ss[ss.domain == dom]
    gap_over_P0 = gap / P0
    elig_over_P0 = (P0 + gap) / P0
    print(f"\n=== D-{dom.upper()} ===")
    print(f"  P0={P0:.2f}  gap={gap:.2f}")
    print(f"  gap/P0          = {gap_over_P0:.4f}   <-- 既有用户饱和所需(AI不取时)")
    print(f"  elig/P0=(P0+gap)/P0 = {elig_over_P0:.4f}   <-- A17 报告的'理论临界'")
    print(f"  真实门槛 = gap/P0 + x_ai_B1/P0 (随情景变)")
    # 真实门槛
    d = d.copy()
    d["thr_true"] = gap_over_P0 + d["x_ai_B1_ml"] / P0
    d["zero_disp"] = d["displaced_ml"].abs() < 1e-6
    # 检验判据: zero_disp <=> pool_scale >= thr_true (容差)
    d["ps"] = d["pool_ml"] / P0
    pred = d["ps"] >= d["thr_true"] - 1e-6
    agree = (pred == d["zero_disp"]).mean()
    print(f"  判据 'pool_scale >= gap/P0 + x_ai/P0' 与实测零挤占吻合率 = {agree:.4f}")
    # A17 判据
    pred2 = d["ps"] >= elig_over_P0 - 1e-6
    agree2 = (pred2 == d["zero_disp"]).mean()
    print(f"  判据 'pool_scale >= elig/P0'         与实测零挤占吻合率 = {agree2:.4f}")
    # 门槛范围
    print(f"  真实门槛范围: [{d.thr_true.min():.3f}, {d.thr_true.max():.3f}]")
    print(f"  零挤占情景的真实门槛: 中位={d[d.zero_disp].thr_true.median():.3f} "
          f"最大={d[d.zero_disp].thr_true.max():.3f}")
    print(f"  有挤占情景的真实门槛: 中位={d[~d.zero_disp].thr_true.median():.3f} "
          f"最小={d[~d.zero_disp].thr_true.min():.3f}")
    rows.append({"domain": dom, "P0": float(P0), "gap": float(gap),
                 "gap_over_P0": float(gap_over_P0),
                 "elig_over_P0_reported": float(elig_over_P0),
                 "agree_true_criterion": float(agree),
                 "agree_A17_criterion": float(agree2),
                 "thr_true_min": float(d.thr_true.min()),
                 "thr_true_max": float(d.thr_true.max())})

summary = {
    "finding": (
        "A17 的 critical_pool_scale = elig/P0 = (P0+gap)/P0 **不是** surplus(零挤占)门槛。"
        "真正的门槛是 pool_scale >= gap/P0 + x_ai_B1/P0, 随 phi/chi/水样变化, 而非常数。"),
    "correct_criterion": "零挤占 <=> pool >= gap + x_ai_B1",
    "by_domain": rows,
    "implication": (
        "A17 报告的 2.384/2.567 只在 x_ai_B1 = P0 这一特殊情形下等于真实门槛; "
        "故不能作为 surplus 的临界值使用。A24b 已改用经验测量阈值(2.0/2.2/2.4), "
        "该结果不受此问题影响。但 A17 文档与 summary 中的 critical_pool_scale 应更正。"),
    "discipline_note": "用现行 supply_state_regimes.csv 与 BASELINES 独立重算; 未改引擎。",
}
(HERE / "threshold_audit.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
pd.DataFrame(rows).to_csv(HERE / "threshold_audit.csv", index=False, encoding="utf-8-sig")
print("\n[write] threshold_audit.json / threshold_audit.csv")
