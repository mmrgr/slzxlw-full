# -*- coding: utf-8 -*-
"""E-B4 图件：三杠杆解耦矩阵。

三张图：
  FigB4a  CAWCC 的 (分流比 f × 替代率 r) 二维热图，两域并列
  FigB4b  沿两条轴的效应曲线：产量效应 vs 替代率效应
  FigB4c  首失效侧别的二维图：哪一格发生瓶颈身份改变

用法: python figs/make_fig_lever_decoupling.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from figstyle_b0 import (  # noqa: E402
    C_CO, C_GRID, C_HA, C_OTHER, C_POLICY, C_WATER, R2, apply_style, save,
)

apply_style()

DOMAIN_NAME = {"ha": "D-HA 缺水端", "co": "D-CO 凉爽端"}
SIDE_COLOR = {"水侧": C_WATER, "电网侧": C_GRID, "政策": C_POLICY,
              "社会供水": C_OTHER, "其他": C_OTHER, "未失效": "#cbd5e0"}


def load():
    df = pd.read_csv(R2 / "lever_decoupling_grid.csv", encoding="utf-8-sig")
    p = R2 / "lever_decoupling_summary.json"
    summary = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return df, summary


# ---------------------------------------------------------------- B4a
def fig_b4a(df: pd.DataFrame) -> list[Path]:
    """(f × r) 的 CAWCC 热图。"""
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.0))
    for ax, domain in zip(axes, ("ha", "co")):
        sub = df[df["域"] == domain]
        piv = sub.pivot_table(index="替代率r", columns="分流比f",
                              values="CAWCC_物理_MW")
        piv = piv.sort_index(ascending=False)  # r 从上到下递减更符合直觉
        data = piv.to_numpy(float)
        im = ax.imshow(data, cmap="YlGnBu", aspect="auto",
                       vmin=np.nanmin(data), vmax=np.nanmax(data))
        ax.set_xticks(np.arange(piv.shape[1]))
        ax.set_xticklabels([f"{c:.2f}" for c in piv.columns], fontsize=7)
        ax.set_yticks(np.arange(piv.shape[0]))
        ax.set_yticklabels([f"{i:.1f}" for i in piv.index], fontsize=7)
        ax.set_xlabel("污水分流比 $f$（决定再生水产量）")
        ax.set_ylabel("再生水替代率 $r$")
        ax.set_title(f"({'a' if domain == 'ha' else 'b'}) {DOMAIN_NAME[domain]}", loc="left")
        for i in range(piv.shape[0]):
            for j in range(piv.shape[1]):
                v = data[i, j]
                if np.isfinite(v):
                    ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=6.6,
                            color="white" if v > np.nanmin(data) + 0.62 * (
                                np.nanmax(data) - np.nanmin(data)) else "#1a202c")
        cb = fig.colorbar(im, ax=ax, fraction=0.042, pad=0.02)
        cb.set_label("CAWCC（MW）", fontsize=6.8)
        cb.ax.tick_params(labelsize=6)

    fig.suptitle("三杠杆的二维响应：提高产量沿纵列抬升，提高替代率沿竖行下压",
                 fontsize=9.2)
    fig.text(0.01, 0.02,
             "每格为一次完整 41 点容量扫描的纯物理 CAWCC；"
             "处理能力按 1.25 × 产量配套（沿用既有约定）。",
             fontsize=6.2, color="#4a5568")
    fig.subplots_adjust(wspace=0.30, left=0.075, right=0.945, top=0.80, bottom=0.215)
    return save(fig, "FigS18_lever_decoupling_heatmap")


# ---------------------------------------------------------------- B4b
def fig_b4b(df: pd.DataFrame, summary: dict) -> list[Path]:
    """两条轴的效应曲线。"""
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 2.9))

    # (a) 固定 r，横扫 f：产量效应
    ax = axes[0]
    for domain, color, marker in (("ha", C_HA, "o"), ("co", C_CO, "s")):
        sub = df[df["域"] == domain]
        for r_val, ls in ((0.0, "-"), (0.6, "--"), (0.9, ":")):
            blk = sub[np.isclose(sub["替代率r"], r_val)].sort_values("分流比f")
            if blk.empty:
                continue
            ax.plot(blk["分流比f"], blk["CAWCC_物理_MW"], marker=marker, ms=3.4,
                    lw=1.3, ls=ls, color=color,
                    label=f"{'D-HA' if domain=='ha' else 'D-CO'} r={r_val:.1f}")
    ax.set_xlabel("污水分流比 $f$")
    ax.set_ylabel("CAWCC（MW）")
    ax.set_title("(a) 产量杠杆：单调抬升", loc="left")
    ax.legend(loc="lower right", fontsize=5.7, ncol=2)
    ax.grid(color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)

    # (b) 固定 f，横扫 r：替代率效应
    ax = axes[1]
    for domain, color, marker in (("ha", C_HA, "o"), ("co", C_CO, "s")):
        sub = df[df["域"] == domain]
        for f_val, ls in ((0.16, "-"), (0.35, "--"), (0.60, ":")):
            blk = sub[np.isclose(sub["分流比f"], f_val)].sort_values("替代率r")
            if blk.empty:
                continue
            ax.plot(blk["替代率r"], blk["CAWCC_物理_MW"], marker=marker, ms=3.4,
                    lw=1.3, ls=ls, color=color,
                    label=f"{'D-HA' if domain=='ha' else 'D-CO'} f={f_val:.2f}")
    ax.axvline(0.5532, color="#9b2c2c", lw=1.0, ls="--", label="$r^*$ = 0.5532")
    ax.set_xlabel("再生水替代率 $r$")
    ax.set_ylabel("CAWCC（MW）")
    ax.set_title("(b) 替代率杠杆：非单调（越阈值后才损伤）", loc="left")
    # 图例放 (b) 内侧下方空白区（r>0.6 段曲线已降到 900 以下）
    ax.legend(loc="lower left", fontsize=5.6, ncol=2, framealpha=0.92,
              frameon=True, edgecolor="#e2e8f0")
    ax.grid(color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)
    ax.set_ylim(400, 1400)

    fig.suptitle("两个杠杆方向相反但可分离：产量单调增益，替代率在阈值后单调损失",
                 fontsize=9.0)
    fig.text(0.01, 0.02,
             "纯物理约束口径。两条轴的斜率符号相反，说明"
             "「扩大再生水利用」不是单一方向的政策变量。",
             fontsize=6.2, color="#4a5568")
    fig.subplots_adjust(wspace=0.26, left=0.070, right=0.985, top=0.79, bottom=0.215)
    return save(fig, "FigS19_lever_effects")


# ---------------------------------------------------------------- B4c
def fig_b4c(df: pd.DataFrame) -> list[Path]:
    """首失效约束的二维图（具体约束名 + 侧别）。"""
    CONSTR_ZH = {
        "max_source_abstraction_ratio": "水源取水比",
        "max_wtw_utilization": "给水厂利用率",
        "max_wwtw_utilization": "污水厂利用率",
        "peak_capacity_ratio": "峰值能力比",
        "max_local_connection_ratio": "本地配水接入比",
        "max_daily_average_grid_connection_ratio": "电网接网比",
        "reclaimed_water_substitution_ratio": "再生水替代率",
        "system_reliability_fraction": "系统可靠度",
        "domestic_unmet_ml": "居民未满足量",
        "unmet_cooling_water_ml": "冷却未满足量",
    }
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.0))
    for ax, domain in zip(axes, ("ha", "co")):
        sub = df[df["域"] == domain]
        piv = sub.pivot_table(index="替代率r", columns="分流比f",
                              values="首失效约束_物理", aggfunc="first")
        pside = sub.pivot_table(index="替代率r", columns="分流比f",
                                values="侧别_物理", aggfunc="first")
        piv = piv.sort_index(ascending=False)
        pside = pside.reindex(index=piv.index, columns=piv.columns)
        for i in range(piv.shape[0]):
            for j in range(piv.shape[1]):
                name = str(piv.iloc[i, j])
                side = str(pside.iloc[i, j])
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                                           facecolor=SIDE_COLOR.get(side, C_OTHER),
                                           alpha=0.70, edgecolor="white", lw=1.2))
                ax.text(j, i, CONSTR_ZH.get(name, name), ha="center", va="center",
                        fontsize=5.9, color="white")
        ax.set_xlim(-0.5, piv.shape[1] - 0.5)
        ax.set_ylim(piv.shape[0] - 0.5, -0.5)
        ax.set_xticks(np.arange(piv.shape[1]))
        ax.set_xticklabels([f"{c:.2f}" for c in piv.columns], fontsize=7)
        ax.set_yticks(np.arange(piv.shape[0]))
        ax.set_yticklabels([f"{i:.1f}" for i in piv.index], fontsize=7)
        ax.set_xlabel("污水分流比 $f$")
        ax.set_ylabel("再生水替代率 $r$")
        ax.set_title(f"({'a' if domain == 'ha' else 'b'}) {DOMAIN_NAME[domain]}", loc="left")
        ax.tick_params(length=0)

    # 如实陈述：本网格内未出现侧别翻转
    n_sides_ha = df[df["域"] == "ha"]["侧别_物理"].nunique()
    n_sides_co = df[df["域"] == "co"]["侧别_物理"].nunique()
    fig.suptitle("首失效约束在 (f, r) 网格上不改变：纯物理口径下两域各由单一约束贯穿",
                 fontsize=8.9)
    fig.text(0.01, 0.02,
             f"格内文字为首失效约束名，底色为侧别。HA 全程由水源取水比控制（{n_sides_ha} 种侧别），"
             f"CO 全程由给水厂利用率控制（{n_sides_co} 种侧别）：本网格内产量与替代率都只改变"
             "失效位置，不改变失效身份。",
             fontsize=6.1, color="#4a5568")
    fig.subplots_adjust(wspace=0.30, left=0.075, right=0.985, top=0.79, bottom=0.235)
    return save(fig, "FigS20_lever_identity_map")


def main() -> None:
    df, summary = load()
    out = []
    out += fig_b4a(df)
    out += fig_b4b(df, summary)
    out += fig_b4c(df)
    print(f"[OK] {len(out)} files")
    for p in out:
        print(" ", p.name)


if __name__ == "__main__":
    main()
