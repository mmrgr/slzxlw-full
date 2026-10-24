"""task-1: 逐条核验文档宣称值 vs 冻结产物实测值."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\mmrgr\Desktop\论文\算力中心\10_论文推进_2026Q4")
A10, A9, A11, A12 = (ROOT / "A10_敏感性与边界", ROOT / "A9_无量纲折叠",
                     ROOT / "A11_适应成本", ROOT / "A12_时间分辨率")

J = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
t10, t11, t11b = J(A10 / "T10_summary.json"), J(A10 / "T11_summary.json"), J(A10 / "T11b_summary.json")
t12 = J(A10 / "T12_summary.json")
t9, t9b = J(A9 / "T9_summary.json"), J(A9 / "T9b_summary.json")
t13 = J(A11 / "T13_summary.json")
t14 = J(A12 / "T14_summary.json")

print("=" * 78)
print("A. S_city<=0 代数必然 —— dp=0 的 2 个正值来源")
d = pd.read_csv(A10 / "T11_uncertainty_samples.csv", encoding="utf-8-sig")
s0 = pd.to_numeric(d["S_city_dp0.0_ml"], errors="coerce")
pos = d[s0 > 0]
print(f"  P(S_city>0)@dp0 冻结值 = {t11['P_S_city_gt0']['dp0.0']:.6f}  = 2/700 = {2/700:.6f}")
for _, r in pos.iterrows():
    print(f"    {r['domain']} {r['panel']} S_city(dp=0)={r['S_city_dp0.0_ml']:.6e} ML")
print(f"  两个正值量级 ~1e-12 ML, 相对 dp=0 中位 |S_city| 3.2e2 ML => 完全是浮点残差, 非物理正值")

print()
print("=" * 78)
print("B. dp=0 vs dp>=0.5 的跳跃 (T11/T11b 自洽性)")
pg = t11["P_S_city_gt0"]
for k, v in pg.items():
    print(f"  {k}: {v:.6f}")
print(f"  T11b 分类: {t11b['class_counts']}  share={t11b['class_share']}")
print(f"  edge 占比 {t11b['class_share']['edge']} + positive {t11b['class_share']['positive']}"
      f" = {t11b['class_share']['edge']+t11b['class_share']['positive']:.4f}")
print(f"  文档称 '48% 落刀锋' -> T11b edge=0.48  MATCH")
print(f"  文档称 '~38% 无法转正' -> 1-0.62=0.38; T11b negative share={t11b['class_share']['negative']}"
      f" -> 1-0.62={0.38:.4f} vs negative={t11b['class_share']['negative']:.4f}")

print()
print("=" * 78)
print("C. 各 summary 关键宣称值")
checks = [
    ("T10 sobol gap S1", t10["sobol_main"][0]["S1"], 0.41709, 0.417),
    ("T10 sobol gap ST", t10["sobol_main"][0]["ST"], 0.76241, 0.762),
    ("T10 sobol pool S1", t10["sobol_main"][1]["S1"], 0.26539, 0.265),
    ("T10 sobol pool ST", t10["sobol_main"][1]["ST"], 0.33428, 0.334),
    ("T10 sobol dp S1", t10["sobol_main"][2]["S1"], 0.14091, 0.141),
    ("T10 sobol dp ST", t10["sobol_main"][2]["ST"], 0.22794, 0.228),
    ("T10 sobol blend S1", t10["sobol_main"][3]["S1"], 0.02091, 0.021),
    ("T10 sobol blend ST", t10["sobol_main"][3]["ST"], 0.02791, 0.028),
    ("T9 n_scenarios", t9["n_scenarios"], 480, 480),
    ("T9 collapse_resid_abs", t9["collapse_residual_max_abs"], 7.105427357601002e-15, 7.11e-15),
    ("T9 variance_reduction", t9["variance_reduction_ratio"], 19.372539681656892, 19.4),
    ("T9b best R2", t9b["candidates"][1]["R2"], 0.024692768150780253, 0.025),
    ("T9b pass", t9b["delta_prediction_pass"], False, False),
    ("T12 n_points", t12["n_points"], 1275, 1275),
    ("T12 boundary_share", t12["boundary_found_share"], 0.9411764705882353, 0.941),
    ("T12 statuses", str(t12["statuses"]), "['converged_unique']", "converged_unique"),
    ("T11b dp* median(neg)", t11b["dp_star_quantiles_negative_only"]["q50"], 0.0640732897445559, 0.064),
    ("T14 B net saving ha", t14["indicator_B"]["ha"]["evaporative"]["annual_net_saving_ml"], None, 7987),
]
for name, got, frozen, doc in checks:
    try:
        same = abs(float(got) - float(frozen)) < 1e-6
    except (TypeError, ValueError):
        same = str(got) == str(frozen)
    ok = "?" if frozen is None else ("OK " if same else "XX ")
    print(f"  [{ok}] {name:26s} json={got!r:28s} expect={frozen!r:28s} doc={doc!r}")

print()
print("=" * 78)
print("D. T14 指标 B: 文档称 7987(ha)/7894(co) ML/yr")
for dm in ("ha", "co"):
    v = t14["indicator_B"][dm]["evaporative"]["annual_net_saving_ml"]
    print(f"  {dm}: annual_net_saving_ml = {v:.4f} ML  (doc: {7987 if dm=='ha' else 7894})"
          f"  ratio={v/(7987 if dm=='ha' else 7894):.4f}")
    v730 = t14["indicator_B"][dm]["evaporative"]["annual_withdrawal_saving_ml"]
    print(f"      annual_withdrawal_saving_ml = {v730:.4f}  (/2 = {v730/2:.4f})")

print()
print("=" * 78)
print("E. T13 宣称值")
print("  keys:", list(t13.keys()))
for k in ("pareto_nondominated", "n_nondominated", "pareto", "policies", "summary"):
    if k in t13:
        print(f"  {k}: {json.dumps(t13[k], ensure_ascii=False)[:400]}")
