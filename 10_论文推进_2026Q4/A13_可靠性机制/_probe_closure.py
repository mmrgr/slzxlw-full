"""探针: 确认 S_city<=0 的代数来源, 并标定可靠性闭合需要的外生量级.

只读调用 A10/city_model.py 与引擎, 不写任何冻结产物.
"""
import sys, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A10 = HERE.parent / "A10_敏感性与边界"
sys.path.insert(0, str(A10))
import city_model as cm  # noqa: E402

out = {}
# 1) 复算 T11b 的一个冻结情景, 确认口径
d = cm.city_outcome("ha", "B_full", "IEUA RP-1 (2025, tertiary)",
                    pool_scale=1.0, gap_scale=1.0, dp_scale=1.0, ai_target=0.7)
out["ha_B_full_IEUA_dp1"] = {k: d[k] for k in
    ("M_ml", "x_ai_ml", "inc_reclaimed_ml", "pool_ml", "dp_ml",
     "S_AI_ml", "S_city_ml", "y", "eta_transfer", "phi_eff", "CoC_ai", "status")}

# 2) 基线量级: 既有用户可回用需求 / 池 / AI 补水
bl = cm.BASELINES["ha"]
out["baseline_ha"] = {"P0_ml": bl["P0"], "gap_ml": bl["gap"], "E_total_ml": bl["E_total"]}
blc = cm.BASELINES["co"]
out["baseline_co"] = {"P0_ml": blc["P0"], "gap_ml": blc["gap"], "E_total_ml": blc["E_total"]}

# 3) 扫 phi, 看 inc_recl 与 pool 的关系 (确认挤占)
rows = []
for phi in (0.0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8):
    r = cm.city_outcome("ha", "B_full", "IEUA RP-1 (2025, tertiary)",
                        pool_scale=1.0, gap_scale=1.0, dp_scale=0.0, ai_target=phi)
    rows.append({"phi": phi, "M": r["M_ml"], "x_ai": r["x_ai_ml"],
                 "inc_recl": r["inc_reclaimed_ml"], "pool": r["pool_ml"],
                 "S_AI": r["S_AI_ml"], "S_city": r["S_city_ml"],
                 "m0": r["m0_ml"], "CoC": r["CoC_ai"]})
out["phi_scan_dp0"] = rows

print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
