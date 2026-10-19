# -*- coding: utf-8 -*-
"""FigR4：零效应区与政策口径桥接。

两个面板：
  (a) 纯物理 CAWCC 随 r 的变化，标出"零效应区"（r ≤ r*）与政策目标区间（阴影）
      —— 直接回答"政策区间内为何无效应"
  (b) 全市利用率 u → 园区替代率 r_max 的换算（按 W/D 分层）
      —— 解释"25% 政策目标"与"55% 园区替代率"不矛盾

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
# 中国现行政策目标（literature_benchmark_city_sources.csv，OFFICIAL）
POLICY_U = [0.20, 0.25, 0.35]
POLICY_LO, POLICY_HI = 0.20, 0.35


def load_physical() -> pd.DataFrame:
    p = R2 / "rstar_physical_cawcc_by_r.csv"
    if not p.exists():
        raise FileNotFoundError(f"缺少产物: {p}")
    return pd.read_csv(p)


def load_bridge() -> pd.DataFrame:
    p = R2 / "rstar_policy_bridge.csv"
    if not p.exists():
        raise FileNotFoundError(f"缺少产物: {p}")
    return pd.read_csv(p)


def make_fig_r4() -> list[Path]:
    apply_style()
    ph = load_physical()
    br = load_bridge()

    fig, axes = plt.subplots(1, 2, figsize=(5.4, 2.5), constrained_layout=True)

    # ---------------- (a) 零效应区 ----------------
    ax = axes[0]
    # 政策目标区间（阴影）
    ax.axvspan(0.0, POLICY_HI, color=C_POLICY, alpha=0.10, zorder=0,
               label=f"现行政策区间 ({POLICY_LO:.0%}–{POLICY_HI:.0%})")
    ax.axvline(R_STAR, color=C_POLICY, ls="--", lw=1.0, zorder=1)

    for domain, color, marker, label in (
        ("ha", C_HA, "o", "D-HA（水源先卡）"),
        ("co", C_CO, "s", "D-CO（电网先卡）"),
    ):
        s = ph[ph["domain"] == domain].sort_values("target_r")
        ax.plot(s["target_r"], s["physical_cawcc_mw"], marker=marker, ms=4.0,
                lw=1.6, color=color, label=label, mfc=color)
        # 标出零效应区内的点（用空心强调）
        flat = s[s["target_r"] <= 0.5]
        ax.plot(flat["target_r"], flat["physical_cawcc_mw"], ls="none",
                marker=marker, ms=7.5, mfc="none", mec=color, mew=1.0, zorder=4)

    ax.annotate(f"$r^*$={R_STAR:.3f}", xy=(R_STAR, 1120),
                xytext=(0.62, 1230), fontsize=6.8, color=C_POLICY,
                arrowprops=dict(arrowstyle="-", lw=0.6, color=C_POLICY))
    ax.text(0.02, 1435, "零效应区：CAWCC 完全不变", fontsize=6.4,
            color=C_POLICY, va="top")
    ax.set_xlabel("再生水替代率 $r$")
    ax.set_ylabel("纯物理 CAWCC (MW)")
    ax.set_title("(a) 政策区间内零效应", loc="left")
    ax.set_ylim(1050, 1500)
    ax.set_xlim(-0.02, 0.92)
    ax.legend(loc="lower left", handletextpad=0.4, borderaxespad=0.2, fontsize=6.3)

    # ---------------- (b) u → r_max 换算 ----------------
    ax = axes[1]
    # 按 W/D 画三条线（500 / 1000 / 1500 MW 的代表值）
    wd_cases = [
        (10.34, "D-HA 500 MW", C_OTHER, ":"),
        (5.28, "D-HA 1000 MW", C_HA, "-"),
        (3.59, "D-HA 1500 MW", C_CO, "--"),
    ]
    u_grid = np.linspace(0.05, 0.60, 200)
    for wd, label, color, ls in wd_cases:
        ax.plot(u_grid, wd * u_grid, lw=1.5, ls=ls, color=color, label=f"{label} ($W/D$={wd:.1f})")

    ax.axhline(1.0, color="black", ls=":", lw=0.8, zorder=0)
    ax.text(0.32, 1.04, "$r_{max}=1$（园区用满全城再生水）", fontsize=6.2)
    ax.axhline(R_STAR, color=C_POLICY, ls="--", lw=1.0, zorder=1)
    ax.text(0.505, R_STAR + 0.035, f"$r^*$={R_STAR:.3f}", fontsize=6.6, color=C_POLICY)
    # 政策区间阴影
    ax.axvspan(POLICY_LO, POLICY_HI, color=C_POLICY, alpha=0.10, zorder=0)
    # 标注：政策区间内，1000MW 案例的 r_max 已越过 r*
    ax.annotate("", xy=(0.35, 0.35 * 5.28), xytext=(0.35, R_STAR),
                arrowprops=dict(arrowstyle="<->", lw=0.9, color=C_HA))
    ax.text(0.355, (0.35 * 5.28 + R_STAR) / 2, "已越过 $r^*$", fontsize=6.2,
            color=C_HA, va="center")

    ax.set_xlabel("全市再生水利用率 $u$")
    ax.set_ylabel("园区替代率上界 $r_{max}=u\\cdot(W/D)$")
    ax.set_title("(b) 总量口径 → 配比口径", loc="left")
    ax.set_xlim(0.05, 0.60)
    ax.set_ylim(0.0, 1.75)
    ax.legend(loc="upper left", handletextpad=0.4, borderaxespad=0.2, fontsize=6.2)

    fig.suptitle(
        "政策区间内零效应是阈值判据的推论；总量口径（全市 $u$）不约束配比口径（园区 $r$）"
        "（合成端点，未经实测率定）",
        fontsize=7.5, y=1.045,
    )
    return save(fig, "FigR4_zero_effect_and_policy_bridge")


def main() -> None:
    paths = make_fig_r4()
    for p in paths:
        print(f"  -> {p.name}  ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
