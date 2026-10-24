"""task-1 关键独立验证: S_city <= 0 是否为代数必然.

三条独立证据线:
 (A) 对全部 700 个冻结情景, 校验恒等式 S_city == S_AI + inc_recl - pool 且 inc_recl <= pool.
 (B) 在 dp=0 (无新增产能) 时, 检验 S_city <= 0 是否恒成立.
 (C) 解析: 由 _pro_rata 的 no-overdraw 不变量推出 inc_recl + x_ai <= pool + dp.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

A10 = Path(r"C:\Users\mmrgr\Desktop\论文\算力中心\10_论文推进_2026Q4\A10_敏感性与边界")
sys.path.insert(0, str(A10))
import city_model as cm  # noqa: E402

d = pd.read_csv(A10 / "T11_uncertainty_samples.csv", encoding="utf-8-sig")

# ---------- (A) 全库恒等式 + inc_recl <= pool 校验 (dp=1.0 列无法拆分, 故重算 40 例) ----------
print("=== (A) 恒等式与 pro-rata 上界校验 (重算 40 情景) ===")
rng = np.random.default_rng(7)
pick = rng.choice(len(d), size=40, replace=False)
worst_id, worst_ub, worst_inc, worst_neg = 0.0, 0.0, 0.0, 0.0
rows = []
for i in sorted(pick):
    r = d.iloc[int(i)]
    for dpv in (0.0, 1.0):
        rec = cm.solve_city(
            cm.BASELINES[str(r["domain"])], str(r["panel"]), str(r["sample"]),
            cm.quality_dict(r, cm.PANELS[str(r["panel"])]),
            cm.m0_of(cm.BASELINES[str(r["domain"])], str(r["panel"]),
                     cm.quality_dict(r, cm.PANELS[str(r["panel"])])),
            cm.BASELINES[str(r["domain"])]["P0"] * float(r["pool_scale"]),
            cm.BASELINES[str(r["domain"])]["gap"] * float(r["gap_scale"]),
            cm.BASELINES[str(r["domain"])]["P0"] * float(dpv),
            float(r["ai_target"]),
        )
        M = rec["M_ml"]; x = rec["x_ai_ml"]; inc = rec["inc_reclaimed_ml"]
        pool = rec["pool_ml"]; s_ai = rec["S_AI_ml"]; s_city = rec["S_city_ml"]
        # 恒等式残差
        ident = abs(s_city - (s_ai + inc - pool))
        # pro-rata 上界: x_ai + inc <= pool + dp
        ub = (x + inc) - (pool + cm.BASELINES[str(r["domain"])]["P0"] * dpv)
        m0 = cm.m0_of(cm.BASELINES[str(r["domain"])], str(r["panel"]),
                      cm.quality_dict(r, cm.PANELS[str(r["panel"])]))
        # 解析恒等式: S_city = (m0 - M) + (x+inc) - pool
        analytic = (m0 - M) + (x + inc) - pool
        worst_id = max(worst_id, ident)
        worst_ub = max(worst_ub, ub)
        worst_neg = max(worst_neg, analytic - s_city)
        rows.append({"i": int(i), "dp": dpv, "S_city": s_city, "inc": inc,
                     "pool": pool, "x_ai": x, "M": M, "s_ai": s_ai,
                     "ub_excess": ub, "ident_resid": ident})
        if dpv == 0.0:
            worst_inc = max(worst_inc, inc - pool)

print(f"  max |S_city - (S_AI + inc - pool)|      = {worst_id:.3e} ML")
print(f"  max (x_ai + inc) - (pool + dp)          = {worst_ub:.3e} ML   [<=0 => S_city <= S_AI]")
print(f"  max (inc - pool)  @dp=0                 = {worst_inc:.3e} ML   [<=0 => S_city <= S_AI]")
print(f"  max |analytic - reported|               = {worst_neg:.3e} ML")

nA = len(rows)
viol_ub = sum(1 for x in rows if x["ub_excess"] > 1e-6)
viol_id = sum(1 for x in rows if x["ident_resid"] > 1e-6)
print(f"  违反上界的情景: {viol_ub}/{nA} ; 违反恒等式: {viol_id}/{nA}")

# ---------- (B) dp=0 时 S_city <= 0 是否恒成立 (用冻结 CSV 的 S_city_dp0.0_ml 列) ----------
print("\n=== (B) dp=0 列的符号统计 (冻结 CSV, n=%d) ===" % len(d))
s0 = pd.to_numeric(d["S_city_dp0.0_ml"], errors="coerce")
print(f"  S_city(dp=0) > 0 的条数 : {int((s0 > 0).sum())}")
print(f"  S_city(dp=0) <= 0 的条数: {int((s0 <= 0).sum())}")
print(f"  >0 的取值             : {sorted(s0[s0 > 0].tolist())[:10]}")
print(f"  max(S_city(dp=0))     : {s0.max():.6e} ML")
print(f"  |S_city(dp=0)| 中位数 : {s0.abs().median():.6e} ML")

# 与 dp=1 尺度对比: dp=0 的负值是否是机器精度级
s1 = pd.to_numeric(d["S_city_dp1.0_ml"], errors="coerce")
scale = s1.abs().clip(lower=1e-12)
print(f"  |S_city(dp=0)|/|S_city(dp=1)| 中位数: {(s0.abs()/scale).median():.3e}")
print(f"  该比值 <= 1e-9 的占比         : {float(((s0.abs()/scale) <= 1e-9).mean()):.4f}")

# ---------- (C) 解析结论 ----------
print("\n=== (C) 解析 ===")
print("  S_city = (m0 - M) + (x_ai + inc_recl) - pool")
print("  _pro_rata 不变量: x_ai + inc_recl <= pool + dp")
print("  => S_city <= (m0 - M) + dp = S_AI + dp")
print("  dp = 0 时: S_city <= S_AI; 且池满吸走全部再生水时 S_city <= 0")

JSON = {
    "max_identity_residual_ml": worst_id,
    "max_upper_bound_excess_ml": worst_ub,
    "max_inc_minus_pool_at_dp0_ml": worst_inc,
    "n_scenarios_checked": nA,
    "n_upper_bound_violations": viol_ub,
    "n_identity_violations": viol_id,
    "dp0_positive_count": int((s0 > 0).sum()),
    "dp0_nonpositive_count": int((s0 <= 0).sum()),
    "dp0_max_ml": float(s0.max()),
    "dp0_abs_over_dp1_abs_median": float((s0.abs() / scale).median()),
    "dp0_knife_edge_share_1e-9": float(((s0.abs() / scale) <= 1e-9).mean()),
}
(Path(__file__).resolve().parent / "algebra_check.json").write_text(
    json.dumps(JSON, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwrote algebra_check.json")
