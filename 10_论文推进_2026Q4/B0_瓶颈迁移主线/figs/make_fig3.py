# -*- coding: utf-8 -*-
"""Fig 3：容量扫描轨迹与约束信息量

科学问题：逐容量点各约束的实际值如何逼近阈值？哪些约束真正 informative？
数据源：r2/constraint_binding_diagnosis.csv（2026-10-18 已扩展至 50–2000 MW）
       r2/{ha,co}/constraint_informativeness.csv
estimand：日尺度 + 年尺度（diagnosis 的「尺度」列）
n：2 域 × 2 尺度 × 40 容量点 = 160 行
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import numpy as np

from figstyle_b0 import (
    C_HA, C_CO, SIDE_COLOR, apply_style, load_binding_diagnosis,
    load_constraint_informativeness, save, short_of, side_of,
)

apply_style()

diag = load_binding_diagnosis()
info = load_constraint_informativeness()

CONSTRAINTS = [
    "max_source_abstraction_ratio",
    "max_wtw_utilization",
    "max_daily_average_grid_connection_ratio",
    "max_local_connection_ratio",
    "peak_capacity_ratio",
    "reclaimed_water_substitution_ratio",
    "domestic_unmet_ml",
]
TARGET = {
    "max_source_abstraction_ratio": 0.95,
    "max_wtw_utilization": 0.95,
    "max_daily_average_grid_connection_ratio": 1.0,
    "max_local_connection_ratio": 1.0,
    "peak_capacity_ratio": 1.0,
    "reclaimed_water_substitution_ratio": 0.65,
    "domestic_unmet_ml": None,   # 阈值 0，无法归一化
}
GE = {"reclaimed_water_substitution_ratio"}  # >= 型

# 注意：不能用 sharex=True——右栏 informative 图的 x 轴是 0–1.55（无单位），
# 左栏是 0–2050 MW。共享 x 轴会让右栏的 set_xlim 覆盖左栏，
# 使轨迹被压缩到 0–1.55 MW 的极窄区间（曾导致曲线"消失"）。
fig, axes = plt.subplots(2, 2, figsize=(7.6, 5.4), sharex=False,
                         gridspec_kw={"width_ratios": [2.1, 1.0]})

for row, domain in enumerate(("ha", "co")):
    sub = diag[(diag["域"] == domain) & (diag["尺度"] == "日尺度")].sort_values("容量_MW")
    cap = sub["容量_MW"].astype(float).to_numpy()

    # ---- 左：归一化轨迹 ----
    ax = axes[row][0]
    plotted = 0
    for name in CONSTRAINTS:
        if name not in sub.columns:
            continue
        thr = TARGET[name]
        if thr is None:
            continue
        vals = sub[name].astype(float).to_numpy()
        # 归一化：<= 型为 v/thr；>= 型为 thr/v（越小越安全）
        if name in GE:
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio = thr / np.where(vals <= 0, np.nan, vals)
        else:
            ratio = vals / thr
        ratio = np.asarray(ratio, dtype=float)
        if np.all(~np.isfinite(ratio)):
            continue
        ax.plot(cap, ratio, lw=1.4, color=SIDE_COLOR[side_of(name)],
                label=short_of(name), alpha=0.92)
        plotted += 1
    ax.axhline(1.0, color="black", lw=1.0, ls="--")
    ax.text(0.985, 1.005, "失效线", transform=ax.transAxes,
            fontsize=6.0, va="bottom", ha="right", color="0.3")
    ax.set_ylim(0.60, 1.60)
    ax.set_xlim(0, 2050)
    ax.set_ylabel("归一化约束值")
    ax.set_title(f"{'D-HA' if domain == 'ha' else 'D-CO'} · 日尺度轨迹"
                 f"（{plotted} 条可归一化约束）", loc="left")
    ax.grid(color="0.93", lw=0.5)
    ax.set_axisbelow(True)
    if row == 0:
        ax.legend(fontsize=5.6, ncol=2, loc="upper left")

    # ---- 右：informative 标记 ----
    ax2 = axes[row][1]
    sub_info = info[info["domain"] == domain].copy()
    names = list(sub_info["constraint"])
    flags = [str(v).strip().lower() == "true" for v in sub_info["informative"]]
    y = np.arange(len(names))
    colors = [SIDE_COLOR[side_of(n)] if f else "#e2e8f0"
              for n, f in zip(names, flags)]
    ax2.barh(y, [1.0 if f else 0.42 for f in flags], color=colors,
             edgecolor="white", linewidth=0.4)
    ax2.set_yticks(y)
    ax2.set_yticklabels([short_of(n) for n in names], fontsize=6.2)
    ax2.invert_yaxis()
    ax2.set_xlim(0, 1.55)
    ax2.set_xticks([])
    for i, f in enumerate(flags):
        ax2.text(1.06, i, "是" if f else "否", fontsize=6.0, va="center",
                 ha="left", color="black" if f else "0.5",
                 fontweight="bold" if f else "normal")
    ax2.set_title("informative?", loc="left")
    ax2.spines["bottom"].set_visible(False)

axes[1][0].set_xlabel("AI 装机容量 (MW)")

fig.suptitle(
    "图 3　容量扫描轨迹与约束信息量（日尺度，50–2000 MW）",
    x=0.01, ha="left", fontsize=9.5,
)
# 用 fig.text 而非负 y 坐标的 fig.text + bbox_inches='tight'，
# 避免 tight bbox 把画布外推成超大图像。
fig.text(
    0.01, 0.075,
    "数据源：constraint_binding_diagnosis.csv（160 行，2026-10-18 扩展至 50–2000 MW）；"
    "estimand = 日尺度；n = 2 域 × 2 尺度 × 40 容量点；"
    "归一化：≤ 型取 v/thr，≥ 型取 thr/v，故 >1 即失效。",
    fontsize=5.9, color="0.35", ha="left", va="bottom",
)
fig.text(
    0.01, 0.025,
    "非 informative 约束在整个扫描区间从未越界，不构成「系统安全」的证据，仅说明未触及；"
    "0 MW 基线已排除（无 AI 时政策约束不适用）。",
    fontsize=5.9, color="0.35", ha="left", va="bottom",
)
# 2026-10-20 审稿修复：wspace=0.10 过小，右面板的 y 轴中文标签压到左面板轨迹上，
# 且 bottom=0.14 容纳不下两行长说明。分别加大到 0.42 / 0.22。
fig.subplots_adjust(left=0.13, right=0.985, top=0.90, bottom=0.22, hspace=0.34,
                    wspace=0.42)

for p in save(fig, "Fig3_constraint_trajectories"):
    print(p)
