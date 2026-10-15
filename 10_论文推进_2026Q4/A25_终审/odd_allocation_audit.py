"""A25 审计 (续2): 查明 38 个"x_ai=0 且 inc_B1=0 但 inc_B2>0"情景的成因.

【现象】
  pool_scale=0.5, ha, AI-UWM 样本: inc_B2=12202, inc_B1=0, x_ai_B1=0
  ⇒ B1 中 AI 取 0、既有用户也取 0, 但池有 12202 未被使用?
  这不物理 —— 除非联合求解器返回了异常解(状态非 converged)。

【本脚本】
  逐情景重跑, 打印 solver status / roots / closure_residual,
  判断是"模型特性"还是"求解器故障"。
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
for c in ("displaced_ml", "x_ai_B1_ml", "pool_ml", "inc_B2_ml", "inc_B1_ml"):
    ss[c] = pd.to_numeric(ss[c], errors="coerce")

odd = ss[(ss["x_ai_B1_ml"].abs() <= 1e-6) & (ss["displaced_ml"].abs() > 1e-6)]
print(f"异常情景数 = {len(odd)}")
print()

# 检查可用列
print("CSV 可用列:", list(ss.columns))
print()

# 逐情景重跑, 查看求解器状态
rows = []
for i, r in odd.head(12).iterrows():
    dom, smp, ps, phi, chi = r.domain, r["sample"], r.pool_scale, r.phi, r.chi
    bl = cm.BASELINES[dom]
    out = {}
    for tag, tgt in (("B2", 0.0), ("B1", float(phi))):
        o = cm.city_outcome(dom, "B_full", smp, pool_scale=float(ps),
                            gap_scale=1.0, dp_scale=0.0, ai_target=tgt,
                            limit_scale=float(chi))
        out[tag] = o
    b2, b1 = out["B2"], out["B1"]
    rows.append({
        "domain": dom, "sample": smp[:22], "ps": ps, "phi": phi, "chi": chi,
        "B2_status": b2["status"], "B1_status": b1["status"],
        "B2_roots": b2["roots"], "B1_roots": b1["roots"],
        "B2_inc": float(b2["inc_reclaimed_ml"]), "B1_inc": float(b1["inc_reclaimed_ml"]),
        "B2_xai": float(b2["x_ai_ml"]), "B1_xai": float(b1["x_ai_ml"]),
        "B2_M": float(b2["M_ml"]), "B1_M": float(b1["M_ml"]),
        "B1_closure": float(b1["closure_residual_ml"]),
    })
d = pd.DataFrame(rows)
pd.set_option("display.width", 220)
print(d.to_string(index=False))

print()
print("=== 判定 ===")
bad = d[(d.B1_status != "converged") | (d.B2_status != "converged")]
print(f"  非 converged 的情景数 = {len(bad)} / {len(d)}")
if len(bad):
    print("  ⇒ 求解器未收敛, 属【求解器故障】而非物理特性")
else:
    print("  ⇒ 全部 converged; 需进一步判断是否为物理特性")

print()
print("=== 关键检验: B1 中 AI 取 0 时, 既有用户能否拿到 pool ===")
r0 = odd.iloc[0]
bl = cm.BASELINES[r0.domain]
print(f"  pool = {r0.pool_ml:.1f}, gap = {bl['gap']:.1f}")
print(f"  B2: inc={r0.inc_B2_ml:.1f}  (=min(gap,pool)? {min(bl['gap'], r0.pool_ml):.1f})")
print(f"  B1: inc={r0.inc_B1_ml:.1f}  x_ai={r0.x_ai_B1_ml:.1f}")
print(f"  ⇒ 若 B1 的 AI 取 0, 则既有用户理应仍得 {min(bl['gap'], r0.pool_ml):.1f}")
print("     实测 0 ⇒ 分配器在 B1 把池分给了谁? 需查 allocation 明细")

# 查分配明细
o1 = cm.city_outcome(r0.domain, "B_full", r0["sample"], pool_scale=float(r0.pool_scale),
                     gap_scale=1.0, dp_scale=0.0, ai_target=float(r0.phi),
                     limit_scale=float(r0.chi))
print()
print("  重跑 B1 的完整返回:")
for k in ("M_ml", "x_ai_ml", "inc_reclaimed_ml", "pool_ml", "S_AI_ml",
          "S_city_ml", "CoC_ai", "status", "roots", "closure_residual_ml",
          "phi_eff", "inc_saturated", "unused_B2_ml", "state_by_alloc"):
    if k in o1:
        print(f"    {k} = {o1[k]}")

summary = {
    "n_odd": int(len(odd)),
    "detail": rows,
    "n_not_converged": int(len(bad)),
    "verdict": ("求解器故障" if len(bad) else "需进一步判断"),
    "discipline_note": "独立重跑 city_outcome; 未改引擎。",
}
(HERE / "odd_allocation_audit.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print("\n[write] odd_allocation_audit.json")
