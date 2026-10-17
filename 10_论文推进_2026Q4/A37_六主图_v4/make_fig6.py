# -*- coding: utf-8 -*-
"""Fig 6 | 外部锚定与**部分识别** (2026-10-16 修订: 加入 WP8 / WP9 / WP10 外部效度证据).

科学问题: 真实设施中 committed (已承诺) 分支占比是多少? 该用途、其规模与其成本有真实外部锚点吗?
结论 (修订后):
  (a) **不可识别** —— 需求侧无观测, 物理约束仅给 0 <= E_i <= D_i, 可证明界 = **[0%, 100%]**。
      ⚠ 本面板表述**不得被 WP8/WP9/WP10 削弱**: 这三个数据源都没有需求字段。
  (b) 处理量分布 (10,826 厂): 强右偏, 少数超大厂承载长尾。
  (c) 可识别量只有【产能可行性】: 处理量 x r 足以超过模型阈值的厂占比 0.39-6.55% (随 r)。
  (d) [新] WP8: 141 个真实再生水项目中工业冷却/一般工业回用 (B3) 是最大类别 40/141 = 28.4%;
      38 个报容量者中 68.4% (26/38) 落在本文模型域 1e3-1e5 m3/d; 容量中位 4,000 (p25 1,050/p75 17,500)。
      ⚠ 案例集非随机样本 ⇒ 28.4% **不是全国占比**; 无需求字段。
  (e) [新] WP9: 39 个行业冷却水占工业取水比 min 0.000 / 中位 0.184 / max 0.990 (>0.5 者 7 个);
      本文所用 0.258 = 39 行业均值, 独立重算 0.25799037378455597 与 A24 mean_of_means 逐位一致,
      位于约 62 分位 ⇒ 单一常数不代表全行业。
  (f) [新] WP10: 61 城市工业自来水价城市中位 1.550 CNY/m3 (0.590-6.650) vs B3 再生水总单位成本
      中位 2.413 CNY/m3 ⇒ 比 1.556 (再生水贵约 56%); 仅 17/61 (27.9%) 城市水价高于再生水成本。
      ⚠ 价格表无合同/分配字段 ⇒ 非因果证据, 不可做 NPV。

数据: A30_WP0取证/a24b_partial_id_summary.json, a24b_capacity_table.csv;
      A39_WP8_外部效度/wp8_real_reuse_cases_summary.json, wp9_cooling_share_summary.json,
      wp10_water_price_summary.json。
"""
from __future__ import annotations

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

import figstyle_a37 as F

F.apply_nw_style()

cap = F.load_capacity()
pj = F.load_json("partial_id")
wp8 = F.load_wp8()
wp9 = F.load_wp9()
wp10 = F.load_wp10()

fig = plt.figure(figsize=(7.2, 9.2))
gs = fig.add_gridspec(4, 2, height_ratios=[1.0, 1.0, 1.14, 1.0], hspace=0.86, wspace=0.36)

# =============================================== (a) committed 占比: 部分识别界 (不得削弱)
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
             fontsize=7.3, loc="left")

# =============================================== (b) 处理量分布 (右偏)
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
             fontsize=7.3, loc="left")
ax.set_ylim(0, max(vals) * 1.22)
ax.text(0.04, 0.70, "a few very large plants\ncarry the tail", transform=ax.transAxes,
        fontsize=5.9, color="#4a5568")

# =============================================== (c) 产能可行性 (可识别量)
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
             "(not prevalence of the committed regime)", fontsize=7.3, loc="left")
ax.legend(fontsize=6.0, loc="upper left", handlelength=1.3, ncol=2, borderpad=0.3,
          columnspacing=0.9)
ax.set_ylim(0, 8.6); ax.set_xlim(0.12, 1.06)

# =============================================== (d) [新] WP8: 真实项目用途分布
ax = fig.add_subplot(gs[2, 0])
dist = sorted(wp8["category_distribution"], key=lambda d: d["n"])
ypos = np.arange(len(dist))
nv = [d["n"] for d in dist]
cols = [F.C_ACCENT if d["code"] == "B3" else F.GREY for d in dist]
ax.barh(ypos, nv, color=cols, edgecolor="#2d3748", linewidth=0.5, height=0.66)
for i, d in enumerate(dist):
    ax.text(d["n"] + 0.7, i, f"{d['n']} ({d['share_pct']:.1f}%)", va="center", fontsize=4.9)
ax.set_yticks(ypos); ax.set_yticklabels([d["code"] for d in dist], fontsize=5.6)
ax.set_xlim(0, 62); ax.set_ylim(-0.6, len(dist) - 0.4)
ax.set_xlabel(f"real reclaimed-water projects (n = {wp8['n_cases']})", fontsize=6.4)
ax.set_title("d  WP8: cooling reuse is the largest documented use",
             fontsize=7.3, loc="left")
cap_b3 = wp8["b3_industrial_cooling"]["capacity"]
ax.text(0.985, 0.03, f"B3 median {cap_b3['median']:,.0f} m$^3$ d$^{{-1}}$ "
        f"(p25 {cap_b3['p25']:,.0f}, p75 {cap_b3['p75']:,.0f}; n={cap_b3['n']})\n"
        "68.4% (26/38) inside the modelled domain 10$^3$–10$^5$ m$^3$ d$^{-1}$\n"
        "case collection, NOT a random sample",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=5.0, color="#9b2c2c",
        linespacing=1.6)

# =============================================== (e) [新] WP9: 冷却水占工业取水比
ax = fig.add_subplot(gs[2, 1])
d9 = wp9["distribution"]
ax.barh([0.0], [d9["max"] - d9["min"]], left=d9["min"], height=0.26, color="#e2e8f0",
        edgecolor="#4a5568", linewidth=0.5)
for v in (d9["min"], d9["p25"], d9["median"], d9["p75"], d9["max"]):
    ax.plot([v, v], [-0.15, 0.15], color="#4a5568", lw=0.8)
ax.text(d9["min"], -0.20, f"{d9['min']:.3f}", ha="center", va="top", fontsize=4.9)
ax.text(d9["median"], -0.20, f"med {d9['median']:.3f}", ha="center", va="top", fontsize=4.9)
ax.text(d9["max"], -0.20, f"{d9['max']:.3f}", ha="center", va="top", fontsize=4.9)
mr = wp9["model_reference_value"]
ax.plot([mr, mr], [-0.36, 0.36], color=F.C_ACCENT, lw=1.6)
ax.annotate("", xy=(mr, 0.40), xytext=(mr + 0.30, 0.62),
            arrowprops=dict(arrowstyle="->", lw=0.6, color=F.C_ACCENT))
ax.text(0.62, 0.66, "model 0.258 = mean of the 39 sector means\n"
        f"(≈62nd pct; recomputed {d9['mean']:.17f},\nmatches A24 mean_of_means digit-for-digit)",
        ha="left", va="bottom", fontsize=4.8, color=F.C_ACCENT, linespacing=1.6)
ax.set_xlim(-0.03, 1.12); ax.set_ylim(-0.66, 1.62)
ax.set_yticks([])
ax.set_xlabel("cooling withdrawal / industrial withdrawal", fontsize=6.4)
ax.set_title(f"e  WP9: cooling share spans 0–1 ({d9['n_gt_0.5']} sectors > 0.5)",
             fontsize=7.3, loc="left")

# =============================================== (f) [新] WP10: 水价 vs 再生水成本
ax = fig.add_subplot(gs[3, 0])
p10 = wp10["per_city_median_stats"]
ratio = wp10["reuse_cost_over_tap_ratio"]
reuse = wp10["reuse_total_unit_cost_median"]
xs = np.arange(2); w = 0.44
vals = [p10["median"], reuse]
cols = [F.C_PRIMARY, F.C_ACCENT]
ax.bar(xs, vals, w, color=cols, edgecolor="#2d3748", linewidth=0.6)
for i, v in enumerate(vals):
    ax.text(i, v + 0.06, f"{v:.3f}", ha="center", fontsize=6.4, fontweight="bold")
ax.plot([0, 1], [vals[0], vals[0]], color="#4a5568", lw=0.7, ls=":")
ax.annotate("", xy=(1.30, reuse), xytext=(1.30, p10["median"]),
            arrowprops=dict(arrowstyle="<->", lw=0.8, color="#9b2c2c"))
ax.text(1.36, (reuse + p10["median"]) / 2, f"×{ratio:.2f}\n(+56%)", fontsize=5.8,
        color="#9b2c2c", va="center", ha="left", fontweight="bold")
ax.set_xlim(-0.55, 1.95)
ax.set_xticks(xs)
ax.set_xticklabels([f"industrial tap tariff\n(city median, n={p10['n_city']})",
                    "B3 reclaimed-water\ntotal unit cost (n=40)"], fontsize=5.8)
ax.set_ylabel("CNY m$^{-3}$", fontsize=6.8)
ax.set_ylim(0, 3.35)
ax.set_title("f  WP10: reclaimed water is not cheaper", fontsize=7.3, loc="left")
ax.text(0.03, 0.92, f"city tariffs span {p10['min']:.2f}–{p10['max']:.2f};\n"
        f"only 17/61 cities (27.9%) above\nreclaimed-water cost;\n"
        "order-of-magnitude only, NOT causal",
        transform=ax.transAxes, fontsize=5.0, color="#4a5568", va="top", linespacing=1.6)

# =============================================== (g) [新] 结论锚点小结 (文本面板)
ax = fig.add_subplot(gs[3, 1])
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
ax.set_title("g  External validity: what the new evidence does and does not change",
             fontsize=7.3, loc="left")
lines = [
    ("GAINED", F.C_BENEFIT, [
        "cooling reuse is a documented real use (40/141, 28.4%)",
        "68.4% of B3 projects sit inside the modelled scale",
        "the model's 0.258 is now fully traceable (62nd pct)",
        "reclaimed water is not cheaper than tap water (×1.56)",
    ]),
    ("NOT CHANGED", "#9b2c2c", [
        "committed share stays NOT IDENTIFIABLE, bound [0%, 100%]",
        "no demand-side field in any of the three new sources",
        "no causal link price -> pool occupancy (no contracts)",
    ]),
]
y = 0.93
for tag, col, items in lines:
    ax.text(0.0, y, tag, fontsize=6.0, fontweight="bold", color=col, va="top")
    y -= 0.115
    for it in items:
        ax.text(0.03, y, "– " + it, fontsize=5.1, color="#2d3748", va="top")
        y -= 0.100
    y -= 0.045

F.provenance(
    fig,
    "Data: A30_WP0/a24b_partial_id_summary.json (a,b), a24b_capacity_table.csv (c); "
    "A39_WP8_external-validity/wp8_real_reuse_cases_summary.json (d), wp9_cooling_share_summary.json "
    "(e), wp10_water_price_summary.json (f) - all three from the Shen et al. 2026 Nature Water "
    "source-data package (CC-BY). Superseded claim 'above 95% of real facilities are fully "
    "committed' = WITHDRAWN_AS_UNIDENTIFIED.",
    "n = 10,826 real treatment plants (b,c). WP8: n = 141 projects (38 with capacity, 40 with cost). "
    "WP9: n = 39 of 41 sectors with a mean (2 missing, counted explicitly, not zero-filled). WP10: "
    "62 city tariff series / 7,730 monthly observations / 61 summarisable cities. No point estimate "
    "and no CI is reported for the committed share, because the parameter is not identified.",
    "LIMITATION: panel c states CAPACITY FEASIBILITY only - a plant COULD exceed the modelled "
    "threshold; it says NOTHING about existing demand. The WP8 catalogue is a CASE COLLECTION, NOT A "
    "RANDOM SAMPLE, so 28.4% is not a national prevalence; it has NO demand-side field and therefore "
    "does NOT shrink or weaken the [0%, 100%] bound of panel a. WP10 is an order-of-magnitude "
    "comparison only: prices with no contracts or allocations, so no causal claim and no investment "
    "or net-present-value statement.",
)
F.save(fig, "Fig6_external_anchor_partial_id")
print("Fig6 done")
