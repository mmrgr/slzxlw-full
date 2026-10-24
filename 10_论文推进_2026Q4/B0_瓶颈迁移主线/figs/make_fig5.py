# -*- coding: utf-8 -*-
"""Fig 5：城市梯度与政策情景

科学问题：结论沿城市参数轴是否连续？政策达标改善的是哪个 estimand？
数据源：r2/city_gradient_cawcc.csv（2026-10-18 已修复标签与年度列）
       r2/advanced_city_cawcc.csv
estimand：(a) 日尺度 + 年尺度（两个不同 estimand）；(b) 年尺度与日尺度并列
n：(a) 25 城 × 41 容量点 = 1025 行；(b) CO 域 4 变体
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import numpy as np

from figstyle_b0 import C_CO, C_HA, apply_style, load_advanced_city, \
    load_city_gradient_cawcc, save

apply_style()

grad = load_city_gradient_cawcc()
adv = load_advanced_city()

fig, axes = plt.subplots(1, 3, figsize=(8.8, 3.2),
                         gridspec_kw={"width_ratios": [1.0, 1.0, 1.20]})
fig.subplots_adjust(left=0.075, right=0.945, top=0.86, bottom=0.20, wspace=0.32)

# ---------------- (a)(b) 城市梯度热图 ----------------
for ax, col, title in (
    (axes[0], "CAWCC_日_MW", "(a) 日尺度"),
    (axes[1], "CAWCC_年_MW", "(b) 年尺度"),
):
    piv = grad.pivot(index="theta_climate", columns="theta_infra", values=col)
    im = ax.imshow(piv.to_numpy(dtype=float), origin="lower", aspect="auto",
                   cmap="YlGnBu", vmin=1000, vmax=1800)
    ax.set_xticks(range(len(piv.columns)))
    ax.set_xticklabels([f"{v:.2f}" for v in piv.columns], fontsize=6.2)
    ax.set_yticks(range(len(piv.index)))
    ax.set_yticklabels([f"{v:.2f}" for v in piv.index], fontsize=6.2)
    ax.set_xlabel("θ_infra（设施轴）", fontsize=7.2)
    if col == "CAWCC_日_MW":
        ax.set_ylabel("θ_climate（气候轴）", fontsize=7.2)
    ax.set_title(title, loc="left")
    # 数值标注
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.to_numpy()[i, j]
            if np.isfinite(v):
                ax.text(j, i, f"{v:.0f}", ha="center", va="center",
                        fontsize=5.4,
                        color="white" if v > 1450 else "0.2")
    # 端点标注（放在热图内部，避免被裁切）
    ax.text(0.10, 0.14, "D-HA", transform=ax.transAxes, fontsize=6.0,
            color="white", fontweight="bold", ha="left", va="bottom")
    ax.text(0.025, 0.955, "D-CO", transform=ax.transAxes, fontsize=6.0,
            color="white", fontweight="bold", ha="left", va="top",
            bbox=dict(boxstyle="round,pad=0.18", fc="black", alpha=0.32, lw=0))

# colorbar 放到整幅图最右侧独立轴，避免压住 (b)/(c)
cax = fig.add_axes([0.958, 0.22, 0.007, 0.50])
cbar = fig.colorbar(im, cax=cax)
cbar.set_label("CAWCC (MW)", fontsize=6.0, labelpad=1)
cbar.ax.tick_params(labelsize=5.2)

# ---------------- (c) 政策情景 ----------------
ax = axes[2]
sub = adv[adv["域"] == "co"].copy()
label_map = {
    "baseline": "baseline\n(漏损12%\n利用率~15%)",
    "leakage_09": "漏损达标\n(12%→9%)",
    "reuse_25": "再生水达标\n(→25%)",
    "both": "两项\n同时达标",
}
order = [v for v in ("baseline", "leakage_09", "reuse_25", "both")
         if v in set(sub["变体"])]
sub = sub.set_index("变体").loc[order].reset_index()

x = np.arange(len(order))
w = 0.38
yr = sub["CAWCC_年_MW"].astype(float).to_numpy()
dy = sub["CAWCC_日_MW"].astype(float).to_numpy()

b1 = ax.bar(x - w / 2, yr, w, color="#805ad5", alpha=0.85, label="年尺度",
            edgecolor="white", linewidth=0.4)
b2 = ax.bar(x + w / 2, dy, w, color=C_CO, alpha=0.85, label="日尺度",
            edgecolor="white", linewidth=0.4)
for b, v in zip(b1, yr):
    ax.text(b.get_x() + b.get_width() / 2, v + 25, f"{v:.0f}",
            ha="center", va="bottom", fontsize=5.8, color="#553c9a")
for b, v in zip(b2, dy):
    ax.text(b.get_x() + b.get_width() / 2, v + 25, f"{v:.0f}",
            ha="center", va="bottom", fontsize=5.8, color=C_CO)

ax.axhline(2000, color="0.4", lw=0.8, ls=":")
ax.text(-0.40, 2210, "网格上界 2000 MW（右删失，非真实承载值）", fontsize=5.3,
        va="bottom", ha="left", color="0.4")
ax.set_xticks(x)
ax.set_xticklabels([label_map[v] for v in order], fontsize=5.8)
ax.set_ylim(0, 2450)
ax.set_ylabel("CAWCC (MW)")
ax.set_title("(c) 政策情景（仅 CO 域）", loc="left")
ax.legend(fontsize=6.2, loc="lower right")
ax.grid(axis="y", color="0.92", lw=0.5)
ax.set_axisbelow(True)

fig.suptitle("图 5　城市梯度与政策情景：连续性 + 政策达标只改善年尺度 estimand",
             x=0.01, ha="left", fontsize=9.2)
fig.text(
    0.008, -0.06,
    "数据源：city_gradient_cawcc.csv（2026-10-18 修复标签并补齐年度 KPI 列）、advanced_city_cawcc.csv；"
    "(a)(b) n=25 合成城市 × 41 容量点 = 1025 行；(c) n=4 变体（仅 CO 域）。\n"
    "★ 中间城市是两端点的线性混合（合成谱），不是任何真实城市，仅用于检验参数轴连续性；"
    "未经实测率定。(c) 的 2000 MW 是网格上界（右删失），非真实承载值；"
    "政策达标使年尺度 1750→2000 MW，但日尺度 1450 MW 完全不动——政策改善的是政策 estimand，不是物理 estimand。",
    fontsize=5.5, color="0.35", ha="left", va="top",
)

for p in save(fig, "Fig5_city_gradient_policy"):
    print(p)
