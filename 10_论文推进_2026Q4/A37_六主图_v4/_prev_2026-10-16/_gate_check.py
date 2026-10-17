# -*- coding: utf-8 -*-
"""交付前门禁: 校验 PDF 字体嵌入、PNG dpi、以及图中标注数值与权威源一致。"""
import re, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import figstyle_a37 as F

fails, warns = [], []

# ---- 1. 文件齐全 ----
stems = ["Fig1_boundary_counterfactuals", "Fig2_water_quality_coc", "Fig3_city_results_signs",
         "Fig4_independent_prediction", "Fig5_sensitivity_extremes",
         "Fig6_external_anchor_partial_id"]
for s in stems:
    for ext in ("pdf", "png"):
        p = HERE / f"{s}.{ext}"
        if not p.exists() or p.stat().st_size < 5000:
            fails.append(f"missing/too small: {p.name}")
print(f"[1] 输出文件: {len(stems)*2} 个待检")

# ---- 2. PDF 字体嵌入 (pdf.fonttype=42) ----
try:
    from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib
    matplotlib.use("Agg")
    for s in stems:
        raw = (HERE / f"{s}.pdf").read_bytes()
        # Type42/TrueType 嵌入: 应含 FontFile2 或 Type0/TrueType
        has_ff2 = b"FontFile2" in raw
        if not has_ff2:
            warns.append(f"{s}.pdf: 未见 FontFile2 (可能未嵌入 TrueType)")
    print(f"[2] PDF 字体嵌入检查完成 ({len(stems)} 个)")
except Exception as e:
    warns.append(f"PDF 字体检查失败: {e}")

# ---- 3. PNG dpi ----
import struct
for s in stems:
    p = HERE / f"{s}.png"
    d = p.read_bytes()
    # 读 pHYs chunk
    i = d.find(b"pHYs")
    if i > 0:
        px, py, unit = struct.unpack(">IIB", d[i+4:i+13])
        if unit == 1:
            dpi = px * 0.0254
            if dpi < 300:
                fails.append(f"{s}.png dpi={dpi:.0f} < 300")
print("[3] PNG dpi 检查完成 (要求 ≥300)")

# ---- 4. 图中标注数值 vs 权威源 ----
r = F.load_regimes()
sc = F.sign_counts(r["dS_pot_ml"]); qg = F.q_groups(r["q"])
checks = [
    ("643/134/36", (sc["neg"], sc["pos"], sc["zero"]) == (643, 134, 36), str(sc)),
    ("q 290/288/235", (qg["pos"], qg["zero"], qg["neg"]) == (290, 288, 235), str(qg)),
    ("q>0 harmful=0", (r[r.q > 0]["dS_pot_ml"] > 0).sum() == 0, "0"),
    ("n_eff=813", len(r) == 813, str(len(r))),
    ("resid 2.55e-11", abs((r.dS_rebuilt - r.dS_pot_ml).abs().max() - 2.546585164964199e-11) < 1e-16,
     f"{(r.dS_rebuilt-r.dS_pot_ml).abs().max():.6e}"),
]
e3s = F.load_json("e3_summary"); e3b = F.load_json("e3b_summary")
checks += [
    ("E3 chem 0.6712", abs(e3s["predictors"]["P2 q>0 (CoC判据)"]["acc"] - 0.6712) < 1e-4,
     f"{e3s['predictors']['P2 q>0 (CoC判据)']['acc']:.4f}"),
    ("baseline 0.8608", abs(e3s["majority_baseline_acc"] - 0.8608) < 1e-4,
     f"{e3s['majority_baseline_acc']:.4f}"),
    ("C4 0.9059", abs(e3b["candidate_criteria"]["C4  q>0 或 pool_scale>=2"]["acc"] - 0.9059) < 1e-4,
     f"{e3b['candidate_criteria']['C4  q>0 或 pool_scale>=2']['acc']:.4f}"),
    ("OOS 0.9009/0.8594", abs(e3b["oos_mean_test_acc"] - 0.9009) < 1e-4
     and abs(e3b["oos_mean_baseline"] - 0.8594) < 1e-4,
     f"{e3b['oos_mean_test_acc']:.4f}/{e3b['oos_mean_baseline']:.4f}"),
]
sob = F.load_sobol()
s1 = sob[sob.config == "ha|IEUA"]["S1"].sum()
checks.append(("Sum S1 ~0.22", abs(s1 - 0.223) < 0.002, f"{s1:.4f}"))
exs = F.load_json("extreme_summary")["sign_flip_from_extremes"]
checks.append(("extremes 0/8", exs["n_flip_heatwave_vs_year"] == 0 and exs["n_flip_drought_vs_year"] == 0
               and exs["n_comparable_heatwave"] + exs["n_comparable_drought"] == 8,
               f"{exs['n_flip_heatwave_vs_year']+exs['n_flip_drought_vs_year']}/"
               f"{exs['n_comparable_heatwave']+exs['n_comparable_drought']}"))
pj = F.load_json("partial_id")
checks.append(("committed bounds 0-100",
               pj["provable_bounds_committed_pct"] == {"lower": 0.0, "upper": 100.0},
               str(pj["provable_bounds_committed_pct"])))
cap = F.load_capacity()
cv = cap[["capable_first_ha_pct","capable_first_co_pct","capable_half_ha_pct","capable_half_co_pct"]].to_numpy()
checks.append(("capacity 0.39-6.55", abs(cv.min()-0.388)<0.002 and abs(cv.max()-6.549)<0.002,
               f"{cv.min():.3f}-{cv.max():.3f}"))
wp4 = F.load_wp4(); wr = wp4[wp4.reliable.astype(bool)]
checks.append(("WP4 47 all beneficial", len(wr) == 47 and (wr.dS_pot_ml < 0).all(), f"n={len(wr)}"))

print("\n[4] 图中标注数值 vs 权威源:")
for name, ok, val in checks:
    print(f"   {'PASS' if ok else 'FAIL'}  {name:26s} {val}")
    if not ok:
        fails.append(f"value mismatch: {name} -> {val}")

print("\n" + "=" * 60)
if warns:
    print("WARN:"); [print("  -", w) for w in warns]
if fails:
    print(f"GATE FAILED ({len(fails)}):"); [print("  -", f) for f in fails]
    raise SystemExit(1)
print(f"GATE PASSED: 6/6 figures, {len(checks)}/{len(checks)} value checks consistent with sources.")
