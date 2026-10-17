# -*- coding: utf-8 -*-
"""Fig 5 | 全局敏感性与极端事件: Morris mu* 排名 + Sobol ST (Sum S1 ~ 0.22) + 极端事件 0/8。

科学问题: 哪个参数主导 dS_pot? 参数间的交互有多强? 观测极端事件会翻转结论吗?
结论: limit_scale 与 x_alkalinity 主导 (ST 0.944 / 0.682); 主效应仅解释 ~22% 方差 (强交互);
      碱度是**唯一**能翻转符号的单参数 (临界 ~2.615x); 观测驱动的热浪/干旱 0/8 翻转符号。

数据: A34_WP5_敏感性与极端事件/wp5_morris.csv, wp5_sobol.csv, wp5_extreme_cases.csv,
      wp5_extreme_summary.json。
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

import figstyle_a37 as F

F.apply_nw_style()

mor = F.load_morris()
sob = F.load_sobol()
exs = F.load_json("extreme_summary")
exc = __import__("pandas").read_csv(F._p("extreme_cases"))

cfg = "ha|IEUA"
m = mor[mor["config"] == cfg].sort_values("mu_star", ascending=True)
s = sob[sob["config"] == cfg].set_index("parameter")

fig = plt.figure(figsize=(7.2, 4.8))
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.0], hspace=0.62, wspace=0.40)

# ---------------------------------------------- (a) Morris mu* 排名
ax = fig.add_subplot(gs[0, 0])
names = [F.PARAM_LABEL.get(p, p) for p in m["parameter"]]
ypos = np.arange(len(m))
cols = [F.C_ACCENT if p == "x_alkalinity" else (F.C_PRIMARY if p == "limit_scale" else F.GREY)
        for p in m["parameter"]]
ax.barh(ypos, m["mu_star"], color=cols, edgecolor="#2d3748", linewidth=0.5, height=0.66)
ax.errorbar(m["mu_star"], ypos, xerr=m["sigma"] / 2, fmt="none", ecolor="#4a5568",
            elinewidth=0.6, capsize=1.2)
ax.set_yticks(ypos); ax.set_yticklabels(names, fontsize=5.9)
ax.set_xlabel(r"Morris $\mu^{*}$ (ML), bar $\pm\sigma/2$", fontsize=6.8)
ax.set_title("a  Morris ranking (ha | IEUA)", fontsize=7.4, loc="left")
ax.tick_params(axis="x", labelsize=6.2)
ax.annotate("only sign-changing\nparameter", xy=(m[m.parameter == "x_alkalinity"]["mu_star"].iloc[0],
                                                 list(m["parameter"]).index("x_alkalinity")),
            xytext=(2.1e4, 1.1), fontsize=5.7, color=F.C_ACCENT,
            arrowprops=dict(arrowstyle="->", lw=0.6, color=F.C_ACCENT))

# ---------------------------------------------- (b) Sobol ST 与 S1
ax = fig.add_subplot(gs[0, 1])
order = ["limit_scale", "x_alkalinity", "pool_scale", "phi", "e_scale", "gap_scale", "dp_scale"]
order = [p for p in order if p in s.index]
xs = np.arange(len(order)); w = 0.36
ST = [float(s.loc[p, "ST"]) for p in order]
S1 = [float(s.loc[p, "S1"]) for p in order]
ax.bar(xs - w / 2, ST, w, color=F.C_PRIMARY, edgecolor="#2d3748", linewidth=0.5,
       label=r"$S_T$ (total)")
ax.bar(xs + w / 2, S1, w, color="#90cdf4", edgecolor="#2d3748", linewidth=0.5,
       label=r"$S_1$ (main)")
for i, (t, m1) in enumerate(zip(ST, S1)):
    ax.text(i - w / 2, t + 0.02, f"{t:.2f}", ha="center", fontsize=5.4)
    ax.text(i + w / 2, max(m1, 0) + 0.02, f"{m1:.2f}", ha="center", fontsize=5.4)
ax.axhline(sum(S1), color=F.C_BENEFIT, lw=0.9, ls=":")
ax.text(len(order) - 0.45, sum(S1) + 0.035, rf"$\sum S_1\approx{sum(S1):.2f}$",
        fontsize=6.0, color=F.C_BENEFIT, ha="right")
ax.set_xticks(xs)
ax.set_xticklabels(["limit\nscale", "alkalinity\nmult.", "pool\nscale", r"blending $\varphi$",
                    "compute\nenergy", "gap\nscale", "price\ndiff."], fontsize=5.4)
ax.set_ylabel("Sobol index", fontsize=6.8); ax.set_ylim(-0.06, 1.08)
ax.legend(fontsize=5.7, loc="upper right", handlelength=1.0, borderpad=0.25)
ax.set_title("b  Variance decomposition (ha | IEUA)", fontsize=7.4, loc="left")

# ---------------------------------------------- (c) 唯一符号杠杆: 单参数扫描
ax = fig.add_subplot(gs[1, 0])
sc = exs["forced_perturbation_thresholds"]
lev = [t for t in sc if t.get("parameter") == "x_alkalinity"]
# 若无逐点扫描数据, 用表中记录的范围与临界值作图
thr = lev[0] if lev else None
params_signflip = [("x_alkalinity", True), ("phi", False), ("pool_scale", False),
                   ("gap_scale", False), ("dp_scale", False), ("e_scale", False),
                   ("coc_design", False), ("limit_scale", False)]
yy = np.arange(len(params_signflip))
signflip_range = []
for p, flips in params_signflip:
    signflip_range.append(1.0 if flips else 0.0)
ax.barh(yy, signflip_range, color=[F.C_ACCENT if fl else "#e2e8f0" for _, fl in params_signflip],
        edgecolor="#2d3748", linewidth=0.55, height=0.62)
ax.set_yticks(yy)
ax.set_yticklabels([F.PARAM_LABEL.get(p, p) for p, _ in params_signflip], fontsize=5.9)
ax.set_xticks([0, 1]); ax.set_xticklabels(["no", "YES"], fontsize=6.2)
ax.set_xlim(0, 1.9); ax.set_ylim(-1.45, len(params_signflip) - 0.35)
crit = 2.615
ax.text(1.06, 0, f"critical ≈ {crit:.3f}×", va="center", fontsize=5.9, color=F.C_ACCENT)
ax.text(0.03, -0.72, "boundary scan over 41 points × 2 domains × 2 samples\n"
        "(other parameters held at frozen values)",
        fontsize=5.2, color="#4a5568", va="top")
ax.set_title("c  Only alkalinity can change the sign", fontsize=7.4, loc="left")
ax.set_xlabel("sign of $\\Delta S_{\\rm pot}$ flips within scan range?", fontsize=6.6)

# ---------------------------------------------- (d) 极端事件: 0/8 翻转
ax = fig.add_subplot(gs[1, 1])
sf = exs["sign_flip_from_extremes"]
cats = ["heatwave\nvs full year", "drought\nvs full year"]
n_comp = [sf["n_comparable_heatwave"], sf["n_comparable_drought"]]
n_flip = [sf["n_flip_heatwave_vs_year"], sf["n_flip_drought_vs_year"]]
xs = np.arange(2); w = 0.34
ax.bar(xs - w / 2, n_comp, w, color=F.GREY, edgecolor="#2d3748", linewidth=0.55,
       label="comparable windows")
ax.bar(xs + w / 2, n_flip, w, color=F.C_BENEFIT, edgecolor="#2d3748", linewidth=0.55,
       label="sign flips")
for i in range(2):
    ax.text(i - w / 2, n_comp[i] + 0.08, str(n_comp[i]), ha="center", fontsize=6.4)
    ax.text(i + w / 2, n_flip[i] + 0.08, str(n_flip[i]), ha="center", fontsize=6.4,
            fontweight="bold", color=F.C_BENEFIT)
ax.set_xticks(xs); ax.set_xticklabels(cats, fontsize=6.1)
ax.set_ylabel("count", fontsize=6.8); ax.set_ylim(0, 6.4)
ax.legend(fontsize=5.8, loc="upper center", handlelength=1.0, borderpad=0.25, ncol=2,
          columnspacing=0.8)
ax.set_title("d  Observed extremes: no sign flip", fontsize=7.4, loc="left")
ax.text(0.50, 0.42, "total 0 / 8\nmagnitude only (max 1.139×)", transform=ax.transAxes,
        fontsize=6.1, color=F.C_BENEFIT, fontweight="bold", ha="center", va="center")

F.provenance(
    fig,
    "Data: A34_WP5/wp5_morris.csv, wp5_sobol.csv, wp5_extreme_cases.csv, wp5_extreme_summary.json.",
    "Morris/Sobol: Saltelli design on config ha|IEUA; LADWP configs report NOT_IDENTIFIABLE "
    "(6-7 of 512 points fail the gate; NaN silently propagated) and are NOT plotted. "
    "Extremes: n_eff = 64 of 64 windowed scenarios after the dual gate. ZERO CONVENTION: "
    "|dS_pot| < 1e-6 ML counted as 0.",
    "LIMITATION: LADWP Sobol indices are not identifiable and are omitted rather than imputed. "
    "The alkalinity critical value ~2.615x has NO observational support (measured samples: IEUA "
    "140 mg/L, LADWP 7.1 mg/L), so it is a sensitivity boundary, not a predicted regime. Extreme-event "
    "windows use driver-only forcing and a single-city domain.",
)
F.save(fig, "Fig5_sensitivity_extremes")
print("Fig5 done")
