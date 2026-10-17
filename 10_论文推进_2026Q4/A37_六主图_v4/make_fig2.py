# -*- coding: utf-8 -*-
"""Fig 2 | 水质与冷却过程: CoC 随掺混比变化 + 碱度是唯一绑定物种 (限 cited/permissive 档)。

科学问题: 再生水掺混如何改变循环冷却水的浓缩倍数 (CoC)? 哪个物种卡住 CoC?
结论: 两条水样的 CoC(phi) 曲线方向相反 —— IEUA 下降 (碱度受限)、LADWP 上升至设计上限 5.000
      (截断); 在**引用档 (baseline)** 下碱度是唯一绑定物种 (限值/浓度比 2.500 最小; LADWP 49.3)。
      ⚠ NE-2 边界注: 该"唯一绑定"结论**只在 alkalinity 限值同为 350 的 cited/permissive 两档成立**;
      strict 档 (1000/250/450/350/30) 下绑定物种变为 silica (IEUA) / TDS (LADWP)。

数据: A33_WP4_组成重构/wp4_results.csv (n_eff=47), A4_水化学参数域/T6_coc_limits.csv,
      A4_水化学参数域/T6_water_chemistry_samples.csv, A27_引用限值报告 (限值/浓度比),
      A38_模拟审稿/ne2_panel_robustness_summary.json (限值档边界)。
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

import figstyle_a37 as F

F.apply_nw_style()

wp4 = F.load_wp4()
coc = F.load_coc_limits()
smp = F.load_samples()
rel = wp4[wp4["reliable"].astype(bool)]

fig = plt.figure(figsize=(7.2, 3.5))
gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1.0, 1.15], wspace=0.42)

IEUA = "IEUA RP-1 (2025, tertiary)"
LADWP = "LADWP AWPF (2012, RO product)"

# ------------------------------------- (a) CoC vs phi: 两条相反曲线 (pool_scale=1 切片)
ax = fig.add_subplot(gs[0, 0])
xoff = {"IEUA": 0.0, "LADWP": 0.0}
for samp, col, mk, lab in [(IEUA, F.RED, "o", "IEUA (tertiary)"),
                           (LADWP, F.BLUE, "s", "LADWP (RO product)")]:
    s = rel[(rel["sample"] == samp) & (rel["domain"] == "ha")
            & (rel["pool_scale"] == 1.0)].sort_values("phi")
    s = s[s["phi"] > 0]
    ax.plot(s["phi"], s["CoC1"], marker=mk, ms=3.6, lw=1.2, color=col, label=lab)
    # CoC0 = 3.5 参考 (phi=0 定义, 被门禁剔除故单独画)
ax.axhline(3.5, color="#4a5568", lw=0.7, ls=":", zorder=1)
ax.text(0.21, 3.55, r"$\mathrm{CoC}_0=3.5$ (no reuse)", fontsize=5.8, color="#4a5568")
ax.axhline(5.0, color=F.BLUE, lw=0.6, ls="--", alpha=0.6, zorder=1)
ax.text(0.21, 5.06, "design cap 5.000", fontsize=5.8, color=F.BLUE)
ax.annotate("alkalinity-limited\n(CoC falls)", xy=(0.78, 3.10), xytext=(0.40, 3.72),
            fontsize=5.8, color=F.RED,
            arrowprops=dict(arrowstyle="->", lw=0.6, color=F.RED))
ax.annotate("cap-truncated\n(CoC rises)", xy=(0.62, 4.65), xytext=(0.44, 3.72),
            fontsize=5.8, color=F.BLUE,
            arrowprops=dict(arrowstyle="->", lw=0.6, color=F.BLUE))
ax.set_xlabel(r"blending ratio $\varphi$", fontsize=7)
ax.set_ylabel(r"$\mathrm{CoC}_1$ (with reuse)", fontsize=7)
ax.set_title("a  Opposite-signed CoC responses", fontsize=7.4, loc="left")
ax.set_ylim(2.4, 5.45); ax.set_xlim(0.15, 0.90)
ax.legend(fontsize=6.0, loc="lower left", handlelength=1.2, borderpad=0.2)

# ------------------------------------- (b) 碱度唯一绑定: 限值/浓度比 (baseline 限值)
ax = fig.add_subplot(gs[0, 1])
ie = smp[smp["source"] == IEUA].iloc[0]
limits = {"TDS": 2200.0, "chloride": 700.0, "hardness": 750.0,
          "alkalinity": 350.0, "silica": 175.0}
conc = {"TDS": ie["TDS"], "chloride": ie["chloride"], "hardness": ie["hardness"],
        "alkalinity": ie["alkalinity"], "silica": ie["silica"]}
names = list(limits.keys())
ratio = [limits[k] / conc[k] for k in names]
order = np.argsort(ratio)
cols = [F.RED if names[i] == "alkalinity" else F.GREY for i in order]
ypos = np.arange(len(order))
ax.barh(ypos, [ratio[i] for i in order], color=cols,
        edgecolor="#2d3748", linewidth=0.6, height=0.62)
for i, idx in enumerate(order):
    ax.text(ratio[idx] + 0.14, i, f"{ratio[idx]:.3f}", va="center", fontsize=6.1)
ax.set_yticks(ypos); ax.set_yticklabels([names[i] for i in order], fontsize=6.6)
ax.axvline(1.0, color="#2d3748", lw=0.8, ls="--")
ax.text(1.10, len(order) - 0.42, "binding\nthreshold", fontsize=5.5, color="#2d3748")
ax.set_xlabel("limit / concentration ratio", fontsize=7)
ax.set_xlim(0, 9.2)
ax.set_title("b  Alkalinity is the only binding\n     species (IEUA)", fontsize=7.4, loc="left")
# NE-2 边界注: 该结论的适用域 (置于坐标区下方, 避免与标题重叠)
ax.text(0.0, -0.30,
        "cited / permissive tier only —\nstrict tier (1000/250/450/350/30) $\\Rightarrow$ silica",
        transform=ax.transAxes, fontsize=5.0, color="#9b2c2c", va="top", ha="left",
        linespacing=1.6)

# ------------------------------------ (c) CoC_lim under three criteria, IEUA vs LADWP
ax = fig.add_subplot(gs[0, 2])
sub = coc[coc["sample"].isin([IEUA, LADWP])]
judgs = ["CoC_lim_engine_conservative", "CoC_lim_all_ratio", "CoC_lim_phreeqc"]
jlabs = ["engine\n(TDS)", "all species\n(ratio)", "PHREEQC\n(calcite)"]
whos = ["who_engine", "who_all", "who_precipitation"]
x = np.arange(len(judgs)); w = 0.36
CAP = 8.0   # 展示上限, 超出者截断并标注真实值
for k, (samp, col, sname) in enumerate([(IEUA, F.RED, "IEUA"), (LADWP, F.BLUE, "LADWP")]):
    row = sub[sub["sample"] == samp].iloc[0]
    vals = [float(row[j]) for j in judgs]
    shown = [min(v, CAP) for v in vals]
    ax.bar(x + (k - 0.5) * w, shown, w, color=col, edgecolor="#2d3748",
           linewidth=0.6, label=sname)
    for xi, v, sv, j in zip(x + (k - 0.5) * w, vals, shown, whos):
        txt = f"{v:.2f}" if v <= CAP else f"{v:.0f}*"
        ax.text(xi, sv + 0.18, txt, ha="center", fontsize=5.9)
        ax.text(xi, 0.16, str(row[j]).replace("none_below_upper", "none")[:8],
                ha="center", fontsize=4.7, rotation=90, color="white", va="bottom")
ax.set_xticks(x); ax.set_xticklabels(jlabs, fontsize=6.1)
ax.set_ylabel(r"$\mathrm{CoC}_{\lim}$", fontsize=7)
ax.set_ylim(0, 9.4)
ax.legend(fontsize=6.0, loc="upper left", handlelength=1.2)
ax.set_title("c  Binding species depends on\n     the criterion", fontsize=7.4, loc="left")
ax.text(0.02, 0.80, "*truncated at 8.0", transform=ax.transAxes, fontsize=5.2,
        color="#4a5568")

F.provenance(
    fig,
    "Data: A33_WP4/wp4_results.csv (a; pool_scale=1 slice, n_eff=47), "
    "A4/T6_coc_limits.csv (c), A4/T6_water_chemistry_samples.csv + A27 cited-limit tier (b); "
    "NE-2 boundary from A38_simulated-review/ne2_panel_robustness_summary.json.",
    "n_eff = 47 city-level scenarios after the dual gate (converged_unique & not coc-floor-degenerate); "
    "IEUA n=24, LADWP n=23. phi=0 rows excluded by the gate (CoC-floor degenerate).",
    "LIMITATION: panel b is a static headroom ratio at the cited tier, NOT a dynamic threshold (the "
    "dynamic flip point for alkalinity is ~2.615x, Fig 5). Its 'only binding species' reading holds "
    "ONLY for the cited and permissive tiers, which share an alkalinity limit of 350; under the "
    "strict make-up tier (1000/250/450/350/30) the binding species becomes silica (IEUA) and TDS "
    "(LADWP) - see Fig 5c / NE-2. Only 2 complete-species samples exist, so the opposite-signed "
    "curves in (a) are a 2-sample contrast, not a population result.",
)
F.save(fig, "Fig2_water_quality_coc")
print("Fig2 done")
