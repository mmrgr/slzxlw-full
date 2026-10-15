"""A25 审计: 零挤占(displaced=0)的【精确】充要条件.

【推导】
  displaced = inc_B2 - inc_B1
  B2 (phi=0, 无 AI):  inc_B2 = min(gap, pool)
  B1 (AI 在场):       inc_B1 = min(gap, pool - x_ai_B1)     (既有用户优先)

  零挤占 ⟺ inc_B1 = inc_B2

  情形 1: pool >= gap
      inc_B2 = gap
      需 min(gap, pool - x_ai) = gap  ⟺  pool - x_ai >= gap  ⟺  pool >= gap + x_ai
  情形 2: pool < gap
      inc_B2 = pool
      需 min(gap, pool - x_ai) = pool
      但 pool - x_ai <= pool, 故 min(gap, pool-x_ai) <= pool - x_ai <= pool
      等号成立 ⟺ x_ai = 0

  ⇒ **零挤占 ⟺ (pool >= gap + x_ai_B1)  OR  (x_ai_B1 = 0)**

【本脚本】
  检验该完整判据 vs 只有第一支的判据, 与实测零挤占的吻合率。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "A10_敏感性与边界"))
import city_model as cm  # noqa: E402

ss = pd.read_csv(ROOT / "A13_可靠性机制" / "supply_state_regimes.csv", encoding="utf-8-sig")
for c in ("displaced_ml", "x_ai_B1_ml", "pool_ml", "inc_B2_ml", "inc_B1_ml",
          "inc_demand_ml"):
    ss[c] = pd.to_numeric(ss[c], errors="coerce")

ss["zero"] = ss["displaced_ml"].abs() < 1e-6
res = {}
for dom in ("ha", "co"):
    bl = cm.BASELINES[dom]
    P0, gap = bl["P0"], bl["gap"]
    d = ss[ss.domain == dom].copy()
    # 判据 A: 仅第一支
    predA = d["pool_ml"] >= gap + d["x_ai_B1_ml"] - 1e-6
    # 判据 B: 完整 (OR x_ai=0)
    predB = predA | (d["x_ai_B1_ml"].abs() <= 1e-6)
    # 判据 C: A17 的 elig/P0
    predC = (d["pool_ml"] / P0) >= ((P0 + gap) / P0) - 1e-6
    res[dom] = {
        "n": int(len(d)),
        "agree_A_first_branch_only": float((predA == d["zero"]).mean()),
        "agree_B_full_criterion": float((predB == d["zero"]).mean()),
        "agree_C_A17_elig_over_P0": float((predC == d["zero"]).mean()),
        "n_zero_disp": int(d["zero"].sum()),
        "n_xai_zero": int((d["x_ai_B1_ml"].abs() <= 1e-6).sum()),
    }
    print(f"\n=== D-{dom.upper()} (n={len(d)}) ===")
    print(f"  判据A 仅 pool>=gap+x_ai        : {res[dom]['agree_A_first_branch_only']:.4f}")
    print(f"  判据B 完整 (OR x_ai=0)         : {res[dom]['agree_B_full_criterion']:.4f}")
    print(f"  判据C A17 的 pool/P0>=elig/P0  : {res[dom]['agree_C_A17_elig_over_P0']:.4f}")
    print(f"  零挤占情景数={res[dom]['n_zero_disp']}  x_ai=0 情景数={res[dom]['n_xai_zero']}")

summary = {
    "exact_condition": "零挤占 ⟺ (pool >= gap + x_ai_B1) OR (x_ai_B1 = 0)",
    "derivation": (
        "inc_B2 = min(gap, pool); inc_B1 = min(gap, pool - x_ai_B1). "
        "分 pool>=gap 与 pool<gap 两支求解等式 inc_B1 = inc_B2 即得。"),
    "findings": res,
    "verdict": (
        "判据B(完整) 应达 ~1.0; 判据C(A17 的 elig/P0) 明显更低。"
        "⇒ A17 的 critical_pool_scale = (P0+gap)/P0 **不是** surplus 门槛, 应更正。"),
    "impact": (
        "A24b 外部效度检验使用【经验测量阈值】(2.0 / 2.2 / 2.4), 非该闭式值 "
        "⇒ 结果不受影响。但 A17 文档、summary 中的 critical_pool_scale 须加注更正。"),
    "discipline_note": "用现行 supply_state_regimes.csv 与 BASELINES 独立重算; 未改引擎。",
}
(HERE / "zero_disp_criterion.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
print("\n[write] zero_disp_criterion.json")
