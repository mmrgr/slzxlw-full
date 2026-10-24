# -*- coding: utf-8 -*-
"""Fig 4：干预反事实（对症 vs 非对症）

科学问题：哪些干预真正提升承载容量？零增益的干预花了多少钱？
数据源：r2/intervention_cost_benefit.csv（已用 50 MW 同网格重跑）
       r2/{ha,co}/intervention_marginal_50mw.csv
estimand：日尺度物理 CAWCC（50 MW 同网格，基线 HA 1150 / CO 1450 MW）
n：2 域 × 10 行（含 baseline）
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import numpy as np

from figstyle_b0 import C_CO, C_HA, apply_style, load_interventions, save

apply_style()

df = load_interventions()
# 排除 baseline（它不是干预）与投资缺失项（不参与成本排序）
inter = df[df["干预"] != "baseline"].copy()

INTERV_SHORT = {
    "wtw_plus_10pct": "给水+10%",
    "wtw_plus_20pct": "给水+20%",
    "reuse_plus_50pct": "再生水+50%",
    "reuse_plus_100pct": "再生水+100%",
    "wwtw_plus_20pct": "污水+20%",
    "local_connection_plus_50pct": "本地接网+50%",
    "grid_plus_50pct": "电网+50%",
    "leakage_minus_30pct": "降漏损30%",
    "combined_upgrade": "组合升级",
}

fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.7),
                         gridspec_kw={"width_ratios": [1.15, 1.0]})

# ---------------- (a) 增益条形图 ----------------
ax = axes[0]
names = list(dict.fromkeys(inter["干预"]))
ypos = np.arange(len(names))
width = 0.38

for offset, domain, color, label in (
    (-width / 2, "ha", C_HA, "D-HA"),
    (width / 2, "co", C_CO, "D-CO"),
):
    sub = inter[inter["域"] == domain].set_index("干预")
    vals = [float(sub.loc[n, "CAWCC增益_MW"]) if n in sub.index else np.nan for n in names]
    ax.barh(ypos + offset, vals, height=width, color=color, alpha=0.85,
            label=label, edgecolor="white", linewidth=0.5)

ax.set_yticks(ypos)
ax.set_yticklabels([INTERV_SHORT.get(n, n) for n in names], fontsize=7.0)
ax.invert_yaxis()
ax.axvline(0, color="black", lw=0.7)
ax.set_xlabel("承载容量增益 (MW)")
ax.set_title("(a) 对症 vs 非对症干预", loc="left")
ax.legend(loc="center right", fontsize=6.8)
ax.grid(axis="x", color="0.92", lw=0.5)
ax.set_axisbelow(True)
ax.text(0.98, 0.30, "零增益项画为 0 并加圆点标记（不省略）", transform=ax.transAxes,
        ha="right", va="bottom", fontsize=6.0, color="0.4")

# 2026-10-20 审稿修复：零增益干预的 barh 高度为 0，完全不可见，
# 与图注"画为零高度柱而非省略"承诺不符。为零增益项在 x=0 处加可见圆点。
for offset, domain, color in ((-width / 2, "ha", C_HA), (width / 2, "co", C_CO)):
    sub = inter[inter["域"] == domain].set_index("干预")
    for i, n in enumerate(names):
        v = float(sub.loc[n, "CAWCC增益_MW"]) if n in sub.index else np.nan
        if v == v and abs(v) < 1e-9:
            ax.plot(0, ypos[i] + offset, marker="o", ms=3.4,
                    color=color, zorder=5, markeredgecolor="white",
                    markeredgewidth=0.4)

# ---------------- (b) 投资 × 增益散点 ----------------
ax = axes[1]
for domain, color, marker in (("ha", C_HA, "o"), ("co", C_CO, "s")):
    sub = inter[inter["域"] == domain].copy()
    sub = sub[sub["投资中值_万元"].notna()]
    x = sub["投资中值_万元"].astype(float)
    y = sub["CAWCC增益_MW"].astype(float)
    ax.scatter(x, y, s=34, color=color, marker=marker, alpha=0.85,
               edgecolor="white", linewidth=0.5,
               label=f"D-{domain.upper()}")
    for _, r in sub.iterrows():
        if float(r["CAWCC增益_MW"]) > 0:
            ax.annotate(INTERV_SHORT.get(r["干预"], r["干预"]),
                        (float(r["投资中值_万元"]), float(r["CAWCC增益_MW"])),
                        textcoords="offset points", xytext=(5, 3),
                        fontsize=6.2, color=color)
    # 零增益但高投资的警示
    zero_hi = sub[(sub["CAWCC增益_MW"] == 0) & (sub["投资中值_万元"] > 40000)]
    for _, r in zero_hi.iterrows():
        ax.annotate(INTERV_SHORT.get(r["干预"], r["干预"]),
                    (float(r["投资中值_万元"]), 0.0),
                    textcoords="offset points", xytext=(-4, -9),
                    fontsize=6.2, color="0.35", ha="right")

ax.set_xscale("log")
ax.set_xlabel("投资中值 (万元, 对数轴)")
ax.set_ylabel("承载容量增益 (MW)")
ax.set_title("(b) 投资 × 增益：零增益但仍有投资", loc="left")
ax.axhline(0, color="black", lw=0.7)
ax.legend(loc="upper left", fontsize=6.8)
ax.grid(color="0.93", lw=0.5)
ax.set_axisbelow(True)

fig.suptitle(
    "图 4　干预反事实：对症干预有效、非对症零增益，且两端互斥",
    x=0.01, ha="left", fontsize=9.5,
)
fig.text(
    0.01, -0.10,
    "数据源：intervention_cost_benefit.csv（2026-10-18 用 50 MW 同网格重跑）；"
    "基线 HA 1150 / CO 1450 MW；9 项一对一干预，未检验交互；\n"
    "local_connection_plus_50pct 投资为 MISSING，不进入 (b)；造价参数部分 GREY，仅量级参考。",
    fontsize=5.9, color="0.35", ha="left", va="top",
)

for p in save(fig, "Fig4_interventions"):
    print(p)
