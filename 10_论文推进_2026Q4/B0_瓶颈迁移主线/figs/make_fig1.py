# -*- coding: utf-8 -*-
"""Fig 1：研究边界与三级论证结构（概念图）

科学问题：本文的研究对象、边界与论证层级是什么？
数据源：无（概念示意图）；元素取自 01_论证结构与主张登记表.md
estimand：不适用
n：不适用
结论限制：不承载任何新数值。

版式：竖向四层（研究问题 → 输入层 → 三级论证 → C 档禁令），
每层用固定高度，互不重叠。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from figstyle_b0 import C_CO, C_HA, apply_style, save

apply_style()

fig = plt.figure(figsize=(7.4, 5.6))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 10)
ax.set_ylim(0, 11)
ax.axis("off")


def box(x, y, w, h, *, fc="white", ec="0.6", lw=0.8):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.10",
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=2,
    ))


def arrow(x1, y1, x2, y2, color="0.45"):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=9,
        linewidth=0.9, color=color, zorder=1,
    ))


# ================= 层 1：研究问题 =================
box(0.30, 10.15, 9.40, 0.70, fc="#ebf4ff", ec=C_HA, lw=1.0)
ax.text(5.0, 10.50,
        "研究问题：AI 算力扩张时，城市水系统中哪个约束先失效、哪个干预有效？",
        ha="center", va="center", fontsize=8.2, fontweight="bold")

arrow(5.0, 10.15, 5.0, 9.55)

# ================= 层 2：输入层 =================
box(0.30, 7.55, 9.40, 1.95, fc="#fafafa", ec="0.55")

ax.text(0.50, 9.32, "三个反事实", fontsize=7.4, fontweight="bold", va="top")
for i, t in enumerate(["B0  无 AI 基线城市",
                       "B1  有 AI + 再生水 (phi>0)",
                       "B2  有 AI + 全自来水 (phi=0)"]):
    ax.text(0.52, 8.98 - i * 0.40, t, fontsize=6.6, va="top")

ax.text(3.62, 9.32, "六类 estimand（强制标签）", fontsize=7.4, fontweight="bold",
        va="top")
estimand_rows = [
    ("daily", "物理+政策 · 日尺度"),
    ("annual", "物理+政策 · 年尺度"),
    ("physical_daily", "仅物理 · 日尺度"),
    ("physical_annual", "仅物理 · 年尺度"),
    ("physical_hourly", "仅物理 · 小时代理"),
    ("reclaimed_target", "仅政策 · 日尺度"),
]
for i, (k, v) in enumerate(estimand_rows):
    y = 8.98 - i * 0.245
    ax.text(3.64, y, k, fontsize=5.9, va="top", family="monospace")
    ax.text(5.12, y, v, fontsize=5.8, va="top", color="0.35")

ax.text(7.05, 9.32, "两个合成参数域端点", fontsize=7.4, fontweight="bold", va="top")
box(7.05, 8.62, 2.45, 0.40, fc="white", ec=C_HA)
ax.text(8.28, 8.82, "D-HA 缺水—高冷负荷端", fontsize=6.4, ha="center", va="center")
box(7.05, 8.10, 2.45, 0.40, fc="white", ec=C_CO)
ax.text(8.28, 8.30, "D-CO 气候凉爽端", fontsize=6.4, ha="center", va="center")
ax.text(7.05, 7.92, "合成 730 日驱动 · 未经实测率定",
        fontsize=5.7, color="0.40", va="top")

arrow(5.0, 7.55, 5.0, 6.95)

# ================= 层 3：三级论证 =================
ax.text(0.30, 6.82, "三级论证结构", fontsize=8.2, fontweight="bold", va="top")

box(0.30, 5.35, 9.40, 1.30, fc="#ebf4ff", ec=C_HA, lw=1.0)
ax.text(0.48, 6.48, "A 档 · 主论点（可进摘要）", fontsize=7.4,
        fontweight="bold", va="top")
for i, t in enumerate([
    "P    瓶颈位置随容量迁移，迁移路径由水源侧余量结构决定",
    "P1  对症干预有效、非对症干预零增益，且 HA / CO 互斥",
    "P2  同一类措施作用于不同杠杆时分野相反（处理能力 vs 产水量）",
]):
    ax.text(0.50, 6.10 - i * 0.26, t, fontsize=6.5, va="top")

box(0.30, 3.55, 9.40, 1.65, fc="#fffaf0", ec="#b7791f", lw=1.0)
ax.text(0.48, 5.03, "A 档 · 方法学论断", fontsize=7.4, fontweight="bold", va="top")
for i, t in enumerate([
    "M1  毛替代率不能代表城市净量（0.700 vs 0.034）",
    "M2  库容可持续边界远低于设施吞吐边界——仅在 HA 端点成立（约 6 倍）",
    "M3  政策合规阈值与物理承载边界是不同 estimand",
    "M5  承载容量绝对值不可报、迁移结构可报（±2% 阈值扰动给出定量依据）",
]):
    ax.text(0.50, 4.72 - i * 0.27, t, fontsize=6.5, va="top")

box(0.30, 2.15, 9.40, 1.25, fc="#f7fafc", ec="0.55")
ax.text(0.48, 3.23, "B 档 · 条件性结果（条件句不可省略）", fontsize=7.4,
        fontweight="bold", va="top")
ax.text(0.50, 2.88,
        "R1–R21：端点边界、概率分布、成本效益、现实尺度、库容多序列、干预水能碳…",
        fontsize=6.4, va="top")
ax.text(0.50, 2.55,
        "每条必须携带 estimand 标签、适用范围与条件句；条件句缺失即降为 C 档。",
        fontsize=6.2, va="top", color="0.35")

arrow(5.0, 2.15, 5.0, 1.72)

# ================= 层 4：C 档禁令 =================
box(0.30, 0.30, 9.40, 1.32, fc="#fff5f5", ec="#c53030", lw=1.0)
ax.text(0.48, 1.48, "C 档 · 禁止进入结论", fontsize=7.4, fontweight="bold",
        color="#c53030", va="top")
for i, t in enumerate([
    "城市节点可用容量 / 备用率 / 电网余量的具体数值（grid 语义未定）",
    "多年、多城市实测可靠性；库容边界外推为年复现供水能力",
    "WUE 作为行业实测水平；2000 MW 当作真实承载值（实为网格上界右删失）",
]):
    ax.text(0.50, 1.18 - i * 0.26, "· " + t, fontsize=6.2,
            color="#742a2a", va="top")

fig.suptitle("图 1　研究边界与三级论证结构（概念图，不承载新数值）",
             x=0.012, y=0.995, ha="left", fontsize=9.5)
fig.text(0.012, 0.012,
         "元素取自 01_论证结构与主张登记表.md；本图不含任何容量数值；"
         "全文定位为机制研究，不声称任何真实城市的承载容量。",
         fontsize=5.8, color="0.4", ha="left")

for p in save(fig, "Fig1_framework"):
    print(p)
