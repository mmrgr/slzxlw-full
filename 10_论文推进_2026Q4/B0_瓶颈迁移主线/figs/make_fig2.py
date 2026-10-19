# -*- coding: utf-8 -*-
"""Fig 2：瓶颈迁移阶梯图（核心图）

科学问题：两域各自哪条约束先失效、迁移序列如何？
数据源：r2/{ha,co}/constraint_boundaries_corrected.csv
estimand：日尺度（daily 约束集）
n：2 域 × 10 约束 × 41 容量点（50–2000 MW，50 MW 步长）
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import numpy as np

from figstyle_b0 import (
    C_CO, C_HA, CONSTRAINT_SIDE, SIDE_COLOR, apply_style, load_capacity_thresholds,
    load_constraint_boundaries, save, short_of, side_of,
)

apply_style()

boundaries = load_constraint_boundaries()
thresholds = load_capacity_thresholds()

fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.9), sharey=False)

for ax, domain, color in zip(axes, ("ha", "co"), (C_HA, C_CO)):
    sub = boundaries[boundaries["domain"] == domain].copy()

    # 未失效约束排在最后；按首失效容量升序
    sub["first_failed_capacity_mw"] = sub["first_failed_capacity_mw"].astype(float)
    failed = sub[sub["first_failed_capacity_mw"].notna()].sort_values(
        "first_failed_capacity_mw"
    )
    never = sub[sub["first_failed_capacity_mw"].isna()]

    order = list(failed["constraint"]) + list(never["constraint"])
    ypos = {name: i for i, name in enumerate(order)}

    for _, row in sub.iterrows():
        name = row["constraint"]
        y = ypos[name]
        side = side_of(name)
        c = SIDE_COLOR[side]

        if row["first_failed_capacity_mw"] == row["first_failed_capacity_mw"]:  # not NaN
            x0 = float(row["first_failed_capacity_mw"])
            # 已失效区间：从首失效到网格上界
            ax.barh(y, 2000 - x0, left=x0, height=0.62, color=c, alpha=0.30,
                    edgecolor=c, linewidth=0.6)
            ax.plot([x0], [y], marker="o", ms=4.2, color=c, zorder=5)
            # 数值标签放在圆点右侧（已失效区间内），避免与 CAWCC 竖线重叠
            ax.text(x0 + 35, y, f"{x0:.0f}", va="center", ha="left",
                    fontsize=6.6, color=c, zorder=6)
        else:
            # 未失效：画一条浅色虚线贯穿全区间
            ax.plot([50, 2000], [y, y], color=c, alpha=0.22, lw=1.0, ls=":")
            ax.text(1960, y, "未失效", va="center", ha="right",
                    fontsize=6.2, color=c, alpha=0.75)

    # CAWCC 竖线（physical_daily）
    cawcc = float(thresholds[domain]["physical_daily"]["maximum_safe_ai_capacity_mw"])
    ax.axvline(cawcc, color="black", lw=1.0, ls="--", zorder=1)
    ax.text(cawcc + 25, -0.55, f"物理日尺度 CAWCC {cawcc:.0f}",
            ha="left", va="bottom", fontsize=6.4)

    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([short_of(n) for n in order], fontsize=7.0)
    ax.set_xlim(50, 2100)
    ax.set_ylim(-0.7, len(order) - 0.3)
    ax.set_xlabel("AI 装机容量 (MW)")
    ax.set_title(f"{'D-HA 缺水—高冷负荷端' if domain == 'ha' else 'D-CO 气候凉爽端'}",
                 loc="left")
    ax.grid(axis="x", color="0.92", lw=0.5)
    ax.set_axisbelow(True)

# 侧别图例（放在图外底部，避免遮挡标签）
handles = [
    plt.Line2D([], [], marker="s", ls="", ms=7, color=SIDE_COLOR["water"], label="水源侧"),
    plt.Line2D([], [], marker="s", ls="", ms=7, color=SIDE_COLOR["grid"], label="电网侧"),
    plt.Line2D([], [], marker="s", ls="", ms=7, color=SIDE_COLOR["policy"], label="政策"),
    plt.Line2D([], [], marker="s", ls="", ms=7, color=SIDE_COLOR["social"], label="社会/供水"),
]
fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=6.8,
           bbox_to_anchor=(0.5, -0.10))

fig.suptitle(
    "图 2 | 约束首次失效容量（日尺度，50–2000 MW 扫描）：D-HA 水先卡、D-CO 电先卡",
    x=0.01, ha="left", fontsize=9.5,
)
fig.text(
    0.01, -0.155,
    "数据源：constraint_boundaries_corrected.csv（2 域 × 10 约束 × 41 容量点）；estimand = 日尺度；"
    "合成参数域端点，未经实测率定；未失效约束显式标注。",
    fontsize=6.0, color="0.35", ha="left",
)

for p in save(fig, "Fig2_bottleneck_migration"):
    print(p)
