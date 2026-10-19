# -*- coding: utf-8 -*-
"""Fig 6：时间尺度与库容边界

科学问题：不同时间尺度给出的边界差多少？库容可持续边界与设施吞吐边界的关系是否端点依赖？
数据源：r2/{ha,co}/capacity_threshold_corrected.json
       r2/reservoir_multiyear_ensemble.json（20 序列 × 10 年，hydrology_validation = NONE）
estimand：(a) physical_daily / physical_annual / physical_hourly 三个独立 estimand
         (b) E4（10 年合成联合门槛）
n：(a) 2 域 × 3 尺度 = 6 值；(b) 2 域 × 20 序列
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import numpy as np

from figstyle_b0 import (
    C_CO, C_HA, C_OTHER, apply_style, load_capacity_thresholds,
    load_reservoir_ensemble, save,
)

apply_style()

thresholds = load_capacity_thresholds()
ensemble = load_reservoir_ensemble()

fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.5),
                         gridspec_kw={"width_ratios": [1.0, 1.15]})

# ---------------- (a) 三尺度边界 ----------------
ax = axes[0]
scales = [
    ("physical_daily", "日尺度"),
    ("physical_annual", "年尺度"),
    ("physical_hourly", "小时代理"),
]
x = np.arange(len(scales))
width = 0.36

for offset, domain, color, label in (
    (-width / 2, "ha", C_HA, "D-HA"),
    (width / 2, "co", C_CO, "D-CO"),
):
    vals = [
        float(thresholds[domain][key]["maximum_safe_ai_capacity_mw"])
        for key, _ in scales
    ]
    bars = ax.bar(x + offset, vals, width=width, color=color, alpha=0.85,
                  label=label, edgecolor="white", linewidth=0.5)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 25, f"{v:.0f}",
                ha="center", va="bottom", fontsize=6.4, color=color)

ax.set_xticks(x)
ax.set_xticklabels([label for _, label in scales], fontsize=7.5)
ax.set_ylabel("物理承载容量 (MW)")
ax.set_title("(a) 三个时间尺度的 estimand", loc="left")
ax.legend(loc="upper center", fontsize=6.6, ncol=2)
ax.set_ylim(0, 2350)
ax.grid(axis="y", color="0.92", lw=0.5)
ax.set_axisbelow(True)
# 小时代理的口径说明放在脚注（避免与柱体重叠）
ax.set_xticklabels([label for _, label in scales], fontsize=7.5)

# ---------------- (b) 库容多序列分布 ----------------
ax = axes[1]
for i, (domain, color) in enumerate((("ha", C_HA), ("co", C_CO))):
    block = ensemble[domain]
    values = [float(v) for v in block["joint_gate_mw_values"]]
    median = float(block["joint_gate_mw_median"])
    # 抖动散点
    rng = np.random.default_rng(20261018)
    jitter = rng.uniform(-0.09, 0.09, size=len(values))
    ax.scatter(np.full(len(values), i) + jitter, values, s=26, color=color,
               alpha=0.72, edgecolor="white", linewidth=0.4, zorder=3)
    # 中位线
    ax.hlines(median, i - 0.26, i + 0.26, color="black", lw=1.3, zorder=4)
    ax.text(i + 0.29, median, f"中位 {median:.0f}", va="center", ha="left",
            fontsize=6.6)

    # 日尺度物理 CAWCC 参考线 + 比值
    phys = float(thresholds[domain]["physical_daily"]["maximum_safe_ai_capacity_mw"])
    ax.hlines(phys, i - 0.34, i + 0.34, color=color, lw=1.0, ls="--", zorder=2)
    ax.text(i - 0.30, phys + 45, f"日尺度 {phys:.0f}", fontsize=6.2, color=color,
            ha="left", va="bottom")
    ratio = phys / median if median else float("nan")
    ax.text(i, 2150, f"比值 {ratio:.2f}", ha="center", va="top",
            fontsize=7.0, fontweight="bold",
            color=color)

ax.set_xticks([0, 1])
ax.set_xticklabels(["D-HA", "D-CO"], fontsize=7.5)
ax.set_xlim(-0.55, 1.55)
ax.set_ylim(0, 2250)
ax.set_ylabel("10 年联合门控容量 (MW)")
ax.set_title("(b) 库容可持续边界 vs 设施吞吐边界", loc="left")
ax.grid(axis="y", color="0.92", lw=0.5)
ax.set_axisbelow(True)
ax.text(0.02, 0.98, "20 条序列 · hydrology_validation = NONE",
        transform=ax.transAxes, ha="left", va="top",
        fontsize=6.0, color="0.4")

fig.suptitle(
    "图 5 | 时间尺度与库容边界：HA 端差约 6 倍，CO 端同量级",
    x=0.01, ha="left", fontsize=9.5,
)
fig.text(
    0.01, -0.09,
    "数据源：capacity_threshold_corrected.json、reservoir_multiyear_ensemble.json；"
    "(a) 三个独立 estimand；(b) E4，20 序列 × 10 年，n=20/域；"
    "★ hydrology_validation = NONE：序列为同一合成驱动规则的不同种子抽样，非观测水文；"
    "条数增加只提高采样精度，不提高证据等级。\n"
    "(a) 小时代理基于合成日内曲线（peak factor 1.058），不是实测小时负荷，极端小时结论不可外推。"
    "D-CO 的 20 条序列给出完全相同值（stdev=0），该端点结论几乎不携带不确定性信息。",
    fontsize=5.7, color="0.35", ha="left", va="top",
)

for p in save(fig, "Fig6_timescale_reservoir"):
    print(p)
