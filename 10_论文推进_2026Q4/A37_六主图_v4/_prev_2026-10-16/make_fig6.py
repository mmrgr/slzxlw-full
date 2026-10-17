# -*- coding: utf-8 -*-
"""Fig 6 | 外部锚定与**部分识别** (不作点估计)。

科学问题: 真实污水厂中处于 committed (已承诺) 分支的比例是多少?
结论: **不可识别** —— 需求侧无观测, 物理约束仅给 0 <= E_i <= D_i, 可证明界 = [0%, 100%]。
      可识别量只有【产能可行性】: 处理量 x r 足以支撑模型阈值处理的厂占比 0.39-6.55% (随 r)。

⚠ 本图**必须**体现部分识别而非点估计; 原 "95% 已承诺" 主张为 WITHDRAWN_AS_UNIDENTIFIED。

数据: A30_WP0取证/a24b_capacity_table.csv, a24b_partial_id_summary.json。
"""
from __future__ import annotations

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

import figstyle_a37 as F

F.apply_nw_style()

cap = F.load_capacity()
pj = F.load_json("partial_id")

fig = plt.figure(figsize=(7.2, 4.4))
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.0], hspace=0.72, wspace=0.34)

# ------------------------------------------------ (a) committed 占比: 部分识别界
ax = fig.add_subplot(gs[0, 0])
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
ax.add_patch(mpatches.Rectangle((0.10, 0.34), 0.80, 0.44, facecolor="#fef3c7",
                                edgecolor=F.C_ACCENT, linewidth=1.3))
ax.text(0.50, 0.56, "NOT\nIDENTIFIABLE", ha="center", va="center", fontsize=8.5,
        fontweight="bold", color=F.C_ACCENT)
ax.annotate("", xy=(0.10, 0.22), xytext=(0.90, 0.22),
            arrowprops=dict(arrowstyle="<|-|>", lw=1.0, color=F.C_ACCENT))
ax.text(0.50, 0.24, "provable bound  [0%, 100%]", ha="center", va="bottom",
        fontsize=6.8, color=F.C_ACCENT, fontweight="bold")
ax.text(0.50, 0.88, "share of real facilities in the\ncommitted branch",
        ha="center", va="center", fontsize=6.8, color="#2d3748")
ax.text(0.50, 0.06, "demand side unobserved:  $0 \\leq E_i \\leq D_i$ admits\n"
        "both branches for every plant, so no point\nestimate and no CI exist",
        ha="center", va="center", fontsize=5.6, color="#4a5568", linespacing=1.5)
ax.set_title("a  Committed share is a partial-identification problem",
             fontsize=7.4, loc="left")

# ------------------------------------------------ (b) 处理量分布 (右偏)
ax = fig.add_subplot(gs[0, 1])
rv = pj["real_treated_volume"]
qs = ["p50", "p75", "p90", "p95", "p99"]
vals = [rv[q] for q in qs]
xs = np.arange(len(qs))
ax.bar(xs, vals, color=["#90cdf4"] * 2 + [F.C_PRIMARY] * 3,
       edgecolor="#2d3748", linewidth=0.6, width=0.6)
for i, v in enumerate(vals):
    ax.text(i, v + 4, f"{v:.1f}", ha="center", fontsize=6.0)
ax.set_xticks(xs)
ax.set_xticklabels(["p50", "p75", "p90", "p95", "p99"], fontsize=6.4)
ax.set_ylabel("treated volume (ML d$^{-1}$)", fontsize=6.8)
ax.set_title(f"b  Throughput is strongly right-skewed (n={rv['n']:,})",
             fontsize=7.4, loc="left")
ax.set_ylim(0, max(vals) * 1.22)
ax.text(0.04, 0.70, "a few very large plants\ncarry the tail", transform=ax.transAxes,
        fontsize=5.9, color="#4a5568")

# ------------------------------------------------ (c) 产能可行性 (可识别量)
ax = fig.add_subplot(gs[1, :])
rs = cap["r"].to_numpy()
series = [("capable_first_co_pct", "first-year threshold, coastal", F.C_ACCENT, "o"),
          ("capable_first_ha_pct", "first-year threshold, humid", F.C_PRIMARY, "s"),
          ("capable_half_ha_pct", "half threshold, humid", "#90cdf4", "^"),
          ("capable_half_co_pct", "half threshold, coastal", F.GREY, "v")]
allv = []
for col, lab, c, mk in series:
    ax.plot(rs, cap[col], marker=mk, ms=3.4, lw=1.1, color=c, label=lab)
    allv.extend(cap[col].tolist())
ax.axhspan(min(allv), max(allv), color="#e6fffa", zorder=0)
ax.text(0.86, (min(allv) + max(allv)) / 2, f"identifiable range {min(allv):.2f}–{max(allv):.2f}%",
        fontsize=6.2, color=F.C_BENEFIT, ha="right", va="center", fontweight="bold",
        bbox=dict(fc="white", ec="none", alpha=0.8, pad=1.0))
ax.set_xlabel("recovery fraction $r$", fontsize=6.9)
ax.set_ylabel("plants with sufficient\ncapacity (%)", fontsize=6.9)
ax.set_title("c  What IS identifiable: capacity feasibility only "
             "(not prevalence of the committed regime)", fontsize=7.4, loc="left")
ax.legend(fontsize=6.0, loc="upper left", handlelength=1.3, ncol=2, borderpad=0.3,
          columnspacing=0.9)
ax.set_ylim(0, 8.6); ax.set_xlim(0.12, 1.06)

F.provenance(
    fig,
    "Data: A30_WP0/a24b_partial_id_summary.json (a,b) and a24b_capacity_table.csv (c). The superseded "
    "claim 'above 95% of real facilities are fully committed' is WITHDRAWN "
    "(status_of_original_claim = WITHDRAWN_AS_UNIDENTIFIED).",
    "n = 10,826 real treatment plants (panels a,b). No point estimate and no confidence interval is "
    "reported for the committed share, because the parameter is not identified.",
    "LIMITATION: panel c states CAPACITY FEASIBILITY only - that a plant COULD produce enough reclaimed "
    "water to exceed the modelled threshold. It says NOTHING about existing demand. Exactly two claims "
    "are permitted: (a) real plant throughput is strongly right-skewed; (b) only ~0.4-7% of plants have "
    "capacity for a surplus-type scheme at the modelled threshold.",
)
F.save(fig, "Fig6_external_anchor_partial_id")
print("Fig6 done")
