# -*- coding: utf-8 -*-
"""Fig 5 | 全局敏感性与极端事件 (2026-10-16 修订: 加入 NE-4 bootstrap 区间与 NE-2 限值档).

科学问题: 哪个参数主导 dS_pot? 参数间的交互有多强? 结论跨限值档稳健吗? 观测极端事件会翻转吗?
结论 (修订后, 措辞按 NE-2 / NE-4 收窄):
  1. Morris/Sobol 点估计: limit_scale 与 alkalinity 排名居前; 但**主效应仅解释一小部分方差**;
  2. NE-4 bootstrap(400) 95% 区间: 单点值不得单独引用 (phi 的 ST 区间 [0.051, 2.568] 极宽);
     Sum S1 = 0.19 (IEUA, n_eff=117) / 0.58 (LADWP, n_eff=128), 均远小于 1;
  3. NE-2 限值档: "碱度是唯一符号杠杆"**只在 cited/permissive 档成立**, strict 档绑定物种
     变为 silica (IEUA) / TDS (LADWP), 且不存在任何单物种符号杠杆 ⇒ 不跨档稳健;
  4. 观测驱动的热浪/干旱 0/8 翻转符号 (幅度 ≤1.139x)。

数据: A34_WP5/wp5_morris.csv, wp5_sobol.csv, wp5_extreme_cases.csv, wp5_extreme_summary.json;
      A38_模拟审稿/ne4_sobol_bootstrap_summary.json (95% 区间), ne2_panel_robustness_summary.json。
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import figstyle_a37 as F

F.apply_nw_style()

mor = F.load_morris()
sob = F.load_sobol()
exs = F.load_json("extreme_summary")
exc = pd.read_csv(F._p("extreme_cases"))
ne4 = F.load_ne4()
ne2 = F.load_ne2()

cfg = "ha|IEUA"
m = mor[mor["config"] == cfg].sort_values("mu_star", ascending=True)
s = sob[sob["config"] == cfg].set_index("parameter")

fig = plt.figure(figsize=(7.2, 4.8))
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.0], hspace=0.66, wspace=0.42)

# ===================================================== (a) Morris mu* 排名 (原样保留)
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
ax.annotate("sign lever only in\ncited/permissive tier\n(see panel c)",
            xy=(m[m.parameter == "x_alkalinity"]["mu_star"].iloc[0],
                list(m["parameter"]).index("x_alkalinity")),
            xytext=(2.1e4, 1.1), fontsize=5.4, color=F.C_ACCENT,
            arrowprops=dict(arrowstyle="->", lw=0.6, color=F.C_ACCENT))

# ===================================================== (b) Sobol ST 与 S1 + NE-4 95% bootstrap 区间
ax = fig.add_subplot(gs[0, 1])
order = [p for p in ["limit_scale", "x_alkalinity", "pool_scale", "phi", "e_scale",
                     "gap_scale", "dp_scale"] if p in s.index]
xs = np.arange(len(order)); w = 0.36
ST = [float(s.loc[p, "ST"]) for p in order]
S1 = [float(s.loc[p, "S1"]) for p in order]
ax.bar(xs - w / 2, ST, w, color=F.C_PRIMARY, edgecolor="#2d3748", linewidth=0.5,
       label=r"$S_T$ (total)")
ax.bar(xs + w / 2, S1, w, color="#90cdf4", edgecolor="#2d3748", linewidth=0.5,
       label=r"$S_1$ (main)")

# --- NE-4: 对四个有定义的参数叠加 95% bootstrap 区间 (水平误差条, 与柱同色系) ---
ci_params = ["limit_scale", "phi", "x_alkalinity"]
for p in ci_params:
    if p not in order:
        continue
    row = F.ne4_index(ne4, F.NE4_IEUA, p)
    i = order.index(p)
    lo, hi = row["ST_lo"], row["ST_hi"]
    ax.plot([lo, hi], [ST[i] + 0.055] * 2, color="#1a365d", lw=0.9, solid_capstyle="butt",
            zorder=5)
    for e in (lo, hi):
        ax.plot([e, e], [ST[i] + 0.010, ST[i] + 0.100], color="#1a365d", lw=0.7, zorder=5)
ax.plot([], [], color="#1a365d", lw=0.9, label=r"$S_T$ 95% CI (NE-4)")

sum_s1 = F.ne4_config(ne4, F.NE4_IEUA)["sum_S1"]
sum_s1_ladwp = F.ne4_config(ne4, F.NE4_LADWP)["sum_S1"]
ax.axhline(sum_s1, color=F.C_BENEFIT, lw=0.9, ls=":")
ax.text(0.02, sum_s1 + 0.055, rf"NE-4 $\sum S_1$ = {sum_s1:.2f} (IEUA) / {sum_s1_ladwp:.2f} (LADWP) "
        rf"$\ll 1$", fontsize=5.6, color=F.C_BENEFIT, ha="left")
ax.set_xticks(xs)
ax.set_xticklabels(["limit\nscale", "alkalinity\nmult.", "pool\nscale", r"blending $\varphi$",
                    "compute\nenergy", "gap\nscale", "price\ndiff."], fontsize=5.2)
ax.set_ylabel("Sobol index", fontsize=6.8); ax.set_ylim(-0.09, 1.62)
ax.legend(fontsize=5.4, loc="upper left", handlelength=1.0, borderpad=0.25, labelspacing=0.3)
ax.set_title("b  Variance decomposition with 95% bootstrap CI (ha | IEUA)",
             fontsize=7.4, loc="left")
ax.annotate(r"$\varphi$ CI [0.05, 2.57]: direction only," "\nno point value quoted",
            xy=(3 - w / 2, 1.05), xytext=(3.30, 1.34), fontsize=5.0, color="#1a365d",
            ha="left", arrowprops=dict(arrowstyle="->", lw=0.5, color="#1a365d"))

# ===================================================== (c) NE-2: 三限值档的绑定物种与符号杠杆
ax = fig.add_subplot(gs[1, 0])
tiers = F.NE2_TIER_ORDER
bs = ne2["binding_species_by_panel"]
sets = ne2["binding_sets_by_panel"]
# 符号杠杆: baseline/permissive = alkalinity (IEUA); strict = none  (NE2 报告 §3 表)
lever = {"baseline": "alkalinity", "permissive": "alkalinity", "strict": None}
IEUA_S = "IEUA RP-1 (2025, tertiary)"
LADWP_S = "LADWP AWPF (2012, RO product)"
xs = np.arange(len(tiers)); w = 0.30
for k, (samp, lab, col, hatch) in enumerate(
        [(IEUA_S, "IEUA binding", F.RED, ""),
         (LADWP_S, "LADWP binding", F.BLUE, "///")]):
    vals = [1.0] * len(tiers)   # 每个水样每档只有一个绑定物种
    ax.bar(xs + (k - 0.5) * w, vals, w, color=col, edgecolor="#2d3748", linewidth=0.55,
           hatch=hatch, label=lab)
    for i, t in enumerate(tiers):
        ax.text(i + (k - 0.5) * w, 0.50, bs[t][samp], ha="center", va="center",
                fontsize=5.9, color="white", fontweight="bold", rotation=90)
# 符号杠杆标记
for i, t in enumerate(tiers):
    has = lever[t] is not None
    ax.text(i, 1.11, ("sign lever:\n" + lever[t]) if has else "NO single-species\nsign lever",
            ha="center", va="bottom", fontsize=5.4, fontweight="bold",
            color=F.C_ACCENT if has else "#9b2c2c")
ax.set_xticks(xs); ax.set_xticklabels([F.NE2_TIER_LABEL[t] for t in tiers], fontsize=4.6)
ax.set_yticks([]); ax.set_ylim(0, 1.62)
ax.set_ylabel("binding species\n(limit / concentration)", fontsize=6.6)
ax.set_title("c  The sign lever is NOT panel-invariant (NE-2)", fontsize=7.4, loc="left")
ax.legend(fontsize=5.5, loc="upper right", handlelength=1.0, borderpad=0.25)
ax.text(0.5, -0.40, "strict tier tightens TDS and silica while alkalinity stays 350,\n"
        "so the binding set becomes {silica, TDS} and the lever disappears",
        transform=ax.transAxes, ha="center", va="top", fontsize=5.0, color="#4a5568",
        linespacing=1.4)
ax.set_xlabel("limit tier (TDS/Cl/hardness/alkalinity/silica)", fontsize=6.0, labelpad=1.5)

# ===================================================== (d) 极端事件: 0/8 翻转 (原样保留)
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
    "Data: A34_WP5/wp5_morris.csv, wp5_sobol.csv, wp5_extreme_cases.csv, wp5_extreme_summary.json "
    "(panels a,b,d); A38_simulated-review/ne4_sobol_bootstrap_summary.json (b, 95% CI) and "
    "ne2_panel_robustness_summary.json (c).",
    "Morris/Sobol panels a,b: Saltelli design on config ha|IEUA; LADWP configs report "
    "NOT_IDENTIFIABLE and are NOT plotted. NE-4 CI: 400 bootstrap replicates, N_base=128, d=7; "
    "n_eff = 117 (IEUA) / 128 (LADWP) after dropping degenerate points. NE-2: 2 complete-species "
    "samples x 3 limit tiers x 2 domains, phi=0.6. Extremes: n_eff = 64 of 64 windowed scenarios "
    "after the dual gate. ZERO CONVENTION: |dS_pot| < 1e-6 ML counted as 0.",
    "LIMITATION: (i) Sum S1 = 0.19 (IEUA) / 0.58 (LADWP) is far below 1, so point rankings "
    "describe only part of the variance; (ii) phi's CI [0.051, 2.568] is so wide that only its "
    "direction, never a point value, may be quoted; (iii) the alkalinity sign lever is a "
    "sensitivity boundary WITHOUT observational support (IEUA 140 mg/L, LADWP 7.1 mg/L) and it "
    "does NOT survive the strict make-up tier of NE-2 - it is a lever identified within an "
    "explicitly bounded limit domain, not a universal mechanism; (iv) extreme-event windows use "
    "driver-only forcing and a single-city domain.",
)
F.save(fig, "Fig5_sensitivity_extremes")
print("Fig5 done")
