# -*- coding: utf-8 -*-
"""Fig 4 | 独立预测检验 (本文最硬贡献)。

科学问题: 仅用**干预前可观测量**能否预测 dS_pot 的符号?
结论: 仅化学 (q>0) 失败 (0.671 < 基线 0.861); 化学+分配联合判据 C4 成功
      (全样本 0.906, 留一水样折外 0.901 vs 基线 0.859)。

数据: A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json,
      wp2_e3b_combined_prediction_summary.json, wp2_e3_predictions.csv,
      wp2_e3b_features.csv。
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np

import figstyle_a37 as F

F.apply_nw_style()

e3s = F.load_json("e3_summary")
e3b = F.load_json("e3b_summary")
pred = __import__("pandas").read_csv(F._p("e3"))
feat = __import__("pandas").read_csv(F._p("e3b"))

base = e3s["majority_baseline_acc"]

fig = plt.figure(figsize=(7.2, 4.6))
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.0], hspace=0.66, wspace=0.34)

# ---------------------------------------- (a) 仅化学 vs 基线 vs 联合 (全样本)
ax = fig.add_subplot(gs[0, 0])
cands = e3b["candidate_criteria"]
items = [("chem only\n($q>0$)", cands["C1  仅化学 q>0"]["acc"], F.RED),
         ("allocation\nonly", cands["C2  仅分配 pool_scale>=2"]["acc"], F.GREY),
         ("C4 combined\n(OR)", cands["C4  q>0 或 pool_scale>=2"]["acc"], F.C_BENEFIT)]
xs = np.arange(len(items))
ax.bar(xs, [i[1] for i in items], color=[i[2] for i in items],
       edgecolor="#2d3748", linewidth=0.6, width=0.58)
ax.axhline(base, color="#2d3748", lw=0.9, ls="--")
ax.text(-0.42, base + 0.022, f"majority baseline {base:.3f}", fontsize=6.0, ha="left",
        color="#2d3748")
for i, it in enumerate(items):
    ax.text(i, it[1] + 0.014, f"{it[1]:.3f}", ha="center", fontsize=6.6, fontweight="bold")
ax.set_xticks(xs); ax.set_xticklabels([i[0] for i in items], fontsize=6.3)
ax.set_ylabel("accuracy (full sample)", fontsize=7)
ax.set_ylim(0, 1.16)
ax.set_title("a  Pre-intervention prediction", fontsize=7.4, loc="left")

# ---------------------------------------- (b) 留一水样折外
ax = fig.add_subplot(gs[0, 1])
loo = e3b["leave_one_sample_out"]
short = {"AI-UWM model assumption": "AI-UWM\nassumption",
         "Figshare RW (2025, paired study)": "Figshare RW",
         "IEUA RP-1 (2025, tertiary)": "IEUA RP-1",
         "LADWP AWPF (2012, RO product)": "LADWP AWPF"}
xs = np.arange(len(loo)); w = 0.36
ax.bar(xs - w / 2, [l["test_acc"] for l in loo], w, color=F.C_PRIMARY,
       edgecolor="#2d3748", linewidth=0.55, label="C4 (out-of-sample)")
ax.bar(xs + w / 2, [l["test_baseline"] for l in loo], w, color=F.GREY,
       edgecolor="#2d3748", linewidth=0.55, label="majority baseline")
for i, l in enumerate(loo):
    ax.text(i - w / 2, l["test_acc"] + 0.02, f"{l['test_acc']:.2f}", ha="center", fontsize=5.6)
    ax.text(i + w / 2, l["test_baseline"] + 0.02, f"{l['test_baseline']:.2f}", ha="center", fontsize=5.6)
ax.axhline(e3b["oos_mean_test_acc"], color=F.C_BENEFIT, lw=0.8, ls=":")
ax.text(-0.42, e3b["oos_mean_test_acc"] - 0.075, f"mean OOS {e3b['oos_mean_test_acc']:.3f}",
        fontsize=5.6, color=F.C_BENEFIT)
ax.set_xticks(xs); ax.set_xticklabels([short[l["held_out"]] for l in loo], fontsize=6.0)
ax.set_ylabel("held-out accuracy", fontsize=7); ax.set_ylim(0, 1.18)
ax.legend(fontsize=5.8, loc="upper center", ncol=2, handlelength=1.0,
          columnspacing=0.8, borderpad=0.2)
ax.set_title("b  Leave-one-sample-out", fontsize=7.4, loc="left")

# ---------------------------------------- (c) per-sample accuracy, chem-only
ax = fig.add_subplot(gs[1, 0])
ps = e3s["by_sample"]
names = [p["sample"].split(" (")[0] for p in ps]
vals = [p["acc"] for p in ps]
cols = [F.RED if v < base else F.C_BENEFIT for v in vals]
xs = np.arange(len(ps))
ax.bar(xs, vals, color=cols, edgecolor="#2d3748", linewidth=0.55, width=0.58)
ax.axhline(base, color="#2d3748", lw=0.9, ls="--")
ax.text(len(ps) - 0.45, base + 0.03, f"baseline {base:.3f}", fontsize=5.6, ha="right")
for i, p in enumerate(ps):
    ax.text(i, p["acc"] + 0.03, f"{p['acc']:.2f}", ha="center", fontsize=5.8)
    ax.text(i, 0.04, f"n={p['n']}", ha="center", fontsize=5.2, color="white")
ax.set_xticks(xs); ax.set_xticklabels(names, fontsize=5.8, rotation=18, ha="right")
ax.set_ylabel("chem-only accuracy", fontsize=7); ax.set_ylim(0, 1.22)
ax.set_title("c  Chemistry alone fails on real samples", fontsize=7.4, loc="left")

# ---------------------------------------- (d) 判据判定空间: q vs pool_scale (C4 规则)
# 只用 n_eff=733 子集 (剔除 80 个近零行), 使图上的 tp/fp/tn/fn 与 summary 完全一致。
ax = fig.add_subplot(gs[1, 1])
f2 = feat.dropna(subset=["q", "pool_scale"]).copy()
f2 = f2[~f2["zero"].astype(bool)]
c4 = e3b["candidate_criteria"]["C4  q>0 或 pool_scale>=2"]
p_pos = (f2["q"] > 0) | (f2["pool_scale"] >= 2)   # C4 预测"有害"
for lab, col, mk, name in [(0, F.C_BENEFIT, "o", "beneficial (true)"),
                           (1, F.C_HARMFUL, "s", "harmful (true)")]:
    s = f2[f2["y"] == lab]
    ax.scatter(s["q"], s["pool_scale"], s=3.0, color=col, marker=mk, alpha=0.5,
               linewidths=0, label=name)
ax.axvline(0, color="#2d3748", lw=0.9, ls="--")
ax.axhline(2, color="#2d3748", lw=0.9, ls="--")
ax.set_xlim(f2["q"].min() - 0.03, f2["q"].max() + 0.09)
ax.set_ylim(f2["pool_scale"].min() - 0.25, f2["pool_scale"].max() + 0.85)
for (tx, ty, txt, col) in [(0.22, 0.13, f"TN={c4['tn']}", F.C_BENEFIT),
                           (0.97, 0.13, f"FP={c4['fp']}", F.C_HARMFUL),
                           (0.22, 0.95, f"FN={c4['fn']}", F.C_BENEFIT),
                           (0.97, 0.95, f"TP={c4['tp']}", F.C_HARMFUL)]:
    ax.text(tx, ty, txt, fontsize=6.2, color=col, transform=ax.transAxes,
            ha="left" if tx < 0.6 else "right", va="center", fontweight="bold",
            bbox=dict(fc="white", ec="none", alpha=0.9, pad=1.0))
ax.text(0.50, 0.60, r"C4: $q>0$ OR pool$\geq$2" "\n" f"accuracy {c4['acc']:.3f}",
        fontsize=6.0, color="#2d3748", transform=ax.transAxes, ha="center", va="center",
        bbox=dict(fc="#f7fafc", ec="#cbd5e0", lw=0.5, pad=1.8))
ax.set_xlabel(r"$q>0$ criterion (chemistry)", fontsize=7)
ax.set_ylabel("reclaimed pool scale (allocation)", fontsize=7)
ax.set_title("d  C4 decision space", fontsize=7.4, loc="left")
ax.legend(fontsize=5.7, loc="upper center", markerscale=2.2, handletextpad=0.3,
          borderpad=0.25, ncol=2, columnspacing=0.9, bbox_to_anchor=(0.5, 0.42))

F.provenance(
    fig,
    "Data: A31_WP2/wp2_e3_independent_prediction_summary.json, wp2_e3b_combined_prediction_summary.json, "
    "wp2_e3_predictions.csv, wp2_e3b_features.csv.",
    "n_all = 813 reliable scenarios; n_eff = 733 after excluding 80 near-zero rows "
    "(|dS_pot| < 1e-9). Leave-one-sample-out groups: n=184/170/196/183.",
    "LIMITATION: the predictor is causal only for the MECHANISM it encodes (pre-intervention chemistry and "
    "pool availability); it requires allocation-side data and gives no city-level calibration. AI-UWM and "
    "Figshare RW are incomplete-species samples (2-3 of 5 species), so their per-sample accuracies are SI-only.",
)
F.save(fig, "Fig4_independent_prediction")
print("Fig4 done")
