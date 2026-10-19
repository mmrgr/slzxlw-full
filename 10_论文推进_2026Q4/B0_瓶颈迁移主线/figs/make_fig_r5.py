# -*- coding: utf-8 -*-
"""FigR5：网格收敛性检验。

三个面板：
  (a) CAWCC 绝对值随网格细化（50/25/10 MW）—— 显示单调趋近上界
  (b) 降幅随网格细化 —— 显示零效应区一致、端点稳健、中间区不稳定
  (c) 量化伪影示意 —— 说明为何降幅波动而绝对值趋近

⚠ 单一数据入口：全部数值经 load_* 从产物读取。
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from figstyle_b0 import (  # noqa: E402
    C_CO,
    C_HA,
    C_OTHER,
    C_POLICY,
    R2,
    apply_style,
    save,
)
import matplotlib.pyplot as plt  # noqa: E402

R_STAR = 0.5532
GRIDS = [("50mw", "50 MW", "o", "-"), ("25mw", "25 MW", "s", "--"), ("10mw", "10 MW", "^", ":")]


def load_convergence() -> pd.DataFrame:
    p = R2 / "rstar_grid_convergence_table.csv"
    if not p.exists():
        raise FileNotFoundError(f"缺少产物: {p}")
    return pd.read_csv(p)


def make_fig_r5() -> list[Path]:
    apply_style()
    d = load_convergence()

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5), constrained_layout=True)

    # ---------------- (a) 绝对值 ----------------
    ax = axes[0]
    ha = d[d["domain"] == "ha"].sort_values("target_r")
    for key, label, marker, ls in GRIDS:
        ax.plot(ha["target_r"], ha[f"cawcc_{key}"], marker=marker, ms=3.6,
                lw=1.3, ls=ls, color=C_HA, alpha=0.9 if key == "50mw" else 0.6,
                label=label, mfc=C_HA if key == "50mw" else "none")
    ax.axvline(R_STAR, color=C_POLICY, ls="--", lw=0.9, zorder=0)
    ax.set_xlabel("再生水替代率 $r$")
    ax.set_ylabel("纯物理 CAWCC (MW)")
    ax.set_title("(a) 绝对值随网格细化趋近上界", loc="left")
    ax.set_ylim(1075, 1215)
    ax.legend(loc="lower left", handletextpad=0.4, borderaxespad=0.2,
              title="容量网格", title_fontsize=6.3, fontsize=6.2)

    # ---------------- (b) 降幅 ----------------
    ax = axes[1]
    for key, label, marker, ls in GRIDS:
        ax.plot(ha["target_r"], ha[f"drop_{key}"], marker=marker, ms=3.6,
                lw=1.3, ls=ls, color=C_HA, alpha=0.9 if key == "50mw" else 0.6,
                label=label, mfc=C_HA if key == "50mw" else "none")
    ax.axvline(R_STAR, color=C_POLICY, ls="--", lw=0.9, zorder=0)
    ax.axhline(0, color=C_OTHER, lw=0.7, zorder=0)
    # 标注零效应区
    ax.axvspan(0.0, 0.5, color="#2c7a7b", alpha=0.10, zorder=0)
    ax.text(0.03, -112, "零效应区\n三网格一致", fontsize=6.0, color="#2c7a7b",
            va="bottom")
    # 标注不稳定区
    ax.annotate("中间区\n极差 30–40 MW", xy=(0.65, -55), xytext=(0.30, -30),
                fontsize=6.0, color=C_CO,
                arrowprops=dict(arrowstyle="->", lw=0.6, color=C_CO))
    ax.set_xlabel("再生水替代率 $r$")
    ax.set_ylabel("相对 r=0 的 CAWCC 降幅 (MW)")
    ax.set_title("(b) 降幅：端点稳健、中间不稳", loc="left")
    ax.set_ylim(-125, 12)
    # 用曲线末端直接标注替代图例，纵向错开避免重叠
    _offsets = {"50mw": -7.0, "25mw": 0.0, "10mw": 7.0}
    for key, label, marker, ls in GRIDS:
        yy = float(ha[f"drop_{key}"].iloc[-1]) + _offsets[key]
        ax.text(0.925, yy, label, fontsize=6.0, color=C_HA,
                va="center", ha="left", alpha=0.95)

    # ---------------- (c) 量化伪影示意 ----------------
    ax = axes[2]
    # 构造一个理想边界，展示不同网格的取整
    true_boundary = 1187.0
    base = 1200.0
    grid_pts = {
        "50 MW": np.arange(1100, 1251, 50),
        "25 MW": np.arange(1100, 1251, 25),
        "10 MW": np.arange(1100, 1251, 10),
    }
    colors = {"50 MW": C_HA, "25 MW": "#2c7a7b", "10 MW": C_CO}
    ypos = {"50 MW": 0.15, "25 MW": 0.5, "10 MW": 0.85}
    ax.axvline(true_boundary, color="black", lw=1.2, ls="-", zorder=3)
    ax.text(true_boundary + 3, 1.02, f"真实边界\n{true_boundary:.0f} MW",
            fontsize=6.0, va="top")
    for label, pts in grid_pts.items():
        # 找出 ≤ boundary 的最大点
        cand = pts[pts <= true_boundary]
        best = cand.max() if len(cand) else pts.min()
        y = ypos[label]
        ax.scatter(pts, [y] * len(pts), s=8, color=colors[label], alpha=0.35, zorder=2)
        ax.scatter([best], [y], s=55, color=colors[label], marker="v",
                   edgecolor="white", linewidth=0.5, zorder=4)
        drop = best - base
        ax.text(1102, y + 0.09, f"{label}: 报 {best:.0f}，降幅 {drop:+.0f}",
                fontsize=6.0, color=colors[label])
    ax.set_xlim(1095, 1215)
    ax.set_ylim(0.0, 1.12)
    ax.set_yticks([])
    ax.set_xlabel("容量 (MW)")
    ax.set_title("(c) 为何降幅波动：取整误差之差", loc="left")

    fig.suptitle(
        "网格收敛性：绝对值随细化单调趋近上界；零效应区降幅在三网格下一致；"
        "中间区降幅波动源于取整（合成端点，未经实测率定）",
        fontsize=7.4, y=1.045,
    )
    return save(fig, "FigR5_grid_convergence")


def main() -> None:
    paths = make_fig_r5()
    for p in paths:
        print(f"  -> {p.name}  ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
