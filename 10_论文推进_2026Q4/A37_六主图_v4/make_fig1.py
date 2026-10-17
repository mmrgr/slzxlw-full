# -*- coding: utf-8 -*-
"""Fig 1 | 研究边界、三反事实 (B0/B1/B2)、三分账与水量账本示意。

科学问题: 系统边界怎么划? 三种反事实分别是什么? 水量在"请求/交付/取用"三分账上如何守恒?
性质: **概念/记账图**。不承载新数值结论 —— 所有数字仅为定义性说明, 来自 A13 主网格的
      单情景示例 (B1 支路 x_ai ≡ 0 是定义结果)。
"""
from __future__ import annotations

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

import figstyle_a37 as F

F.apply_nw_style()

fig = plt.figure(figsize=(7.2, 5.0))
gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 1.0], hspace=0.42, wspace=0.26)

# ---------------------------------------------------------------- (a) 边界
ax = fig.add_subplot(gs[0, :])
ax.set_xlim(0, 10); ax.set_ylim(0, 3.2); ax.axis("off")

def box(x, y, w, h, text, fc, ec, fs=7, lw=0.8):
    ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                         facecolor=fc, edgecolor=ec, linewidth=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)

# 研究边界框
ax.add_patch(mpatches.FancyBboxPatch((0.15, 0.15), 9.7, 2.9,
                                     boxstyle="round,pad=0.05", facecolor="#f7fafc",
                                     edgecolor="#4a5568", linewidth=0.9, linestyle="--"))
ax.text(0.32, 2.86, "Study boundary (city water account)", fontsize=6.8,
        color="#4a5568", va="top")

box(0.55, 1.55, 1.85, 0.85, "Reclaimed\nwater source\n(pool)", "#bee3f8", F.BLUE)
box(3.05, 1.55, 1.85, 0.85, "Cooling system\n(AI data centre)", "#fefcbf", F.ORANGE)
box(5.55, 1.55, 1.85, 0.85, "Incumbent\nusers", "#c6f6d5", F.GREEN)
box(7.95, 1.55, 1.55, 0.85, "External\nmake-up", "#e2e8f0", "#4a5568")

for x0, x1 in [(2.40, 3.05), (4.90, 5.55)]:
    ax.annotate("", xy=(x1, 1.98), xytext=(x0, 1.98),
                arrowprops=dict(arrowstyle="-|>", lw=0.9, color="#2d3748"))
ax.annotate("", xy=(7.95, 1.98), xytext=(6.20, 1.98),
            arrowprops=dict(arrowstyle="-|>", lw=0.9, color="#9b2c2c", linestyle=":"))

ax.text(2.72, 2.20, r"$M_0$", fontsize=7, ha="center", color="#2d3748")
ax.text(5.22, 2.20, r"$M_1$", fontsize=7, ha="center", color="#2d3748")
ax.text(7.05, 1.30, r"$x_{\rm AI}$", fontsize=7, ha="center", color="#9b2c2c")

box(0.55, 0.45, 8.95, 0.72,
    r"$\Delta S_{\rm pot}=C-F=\max(0,\ \mathrm{inc}_{B2}-\mathrm{inc}_{B1})-\left[(M_0-M_1)+x_{\rm AI}\right]$"
    "\n" r"$>0$: city abstraction rises (harmful)   |   $<0$: falls (beneficial)",
    "#fffaf0", "#c05621", fs=7.4)
F.panel_label(ax, "a", dx=-0.005, dy=1.10)

# ------------------------------------------------------- (b) 三反事实 B0/B1/B2
ax = fig.add_subplot(gs[1, 0])
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
scen = [
    ("B0", "No data centre", "baseline water account", "#edf2f7", "#4a5568"),
    ("B1", "Data centre, no reuse", r"$x_{\rm AI}\equiv 0$ (by definition)", "#fff5f5", F.RED),
    ("B2", "Data centre, reuse", r"$x_{\rm AI}>0$; pool drawn", "#e6fffa", F.TEAL),
]
for i, (tag, t1, t2, fc, ec) in enumerate(scen):
    y = 0.60 - i * 0.30
    ax.add_patch(mpatches.FancyBboxPatch((0.04, y), 0.92, 0.25,
                                         boxstyle="round,pad=0.02", facecolor=fc,
                                         edgecolor=ec, linewidth=0.9))
    ax.text(0.11, y + 0.155, tag, fontsize=8.5, fontweight="bold", color=ec, va="center")
    ax.text(0.24, y + 0.165, t1, fontsize=7.2, va="center")
    ax.text(0.24, y + 0.070, t2, fontsize=6.3, va="center", color="#4a5568")
ax.text(0.04, 1.00, "Counterfactuals", fontsize=7.6, fontweight="bold", va="top")
F.panel_label(ax, "b", dx=-0.04, dy=1.06)

# ------------------------------------------------------------ (c) 三分账
ax = fig.add_subplot(gs[1, 1])
r = F.load_regimes()
ex = r[(r["phase"] if "phase" in r.columns else r["domain"]).notna()].iloc[0]
req = float(ex["inc_demand_ml"])
dlv = float(ex["inc_demand_ml"] - ex["unused_B2_ml"])
abs_ = float(ex["inc_B2_ml"])
labels = ["Requested\n(inc. demand)", "Delivered\n(allocated)", "Abstracted\n(from pool)"]
vals = [req, dlv, abs_]
colors = ["#bee3f8", "#90cdf4", F.BLUE]
bars = ax.bar(labels, vals, color=colors, edgecolor="#2d3748", linewidth=0.6, width=0.6)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + max(vals) * 0.03, f"{v:,.0f}",
            ha="center", fontsize=6.5)
ax.set_ylabel("Volume (ML)", fontsize=7)
ax.set_ylim(0, max(vals) * 1.22)
ax.set_title("Three-way water account (one example scenario)", fontsize=7.4, loc="left")
ax.tick_params(axis="x", labelsize=6.2)
F.panel_label(ax, "c", dx=-0.16, dy=1.10)

F.provenance(
    fig,
    "Data: A13_Reliability/supply_state_regimes.csv (panel c, example row 1); "
    "definitions per A26_Semantics/CHI_SEMANTICS.md.",
    "n = 1 illustrative scenario (panel c); conceptual panels a-b carry no statistical n.",
    "LIMITATION: panels a-b are schematic definitions, not evidence; the estimator is an accounting "
    "identity and its residual (2.55e-11 ML) is a consistency check, not a discovery.",
)
F.save(fig, "Fig1_boundary_counterfactuals")
print("Fig1 done")
