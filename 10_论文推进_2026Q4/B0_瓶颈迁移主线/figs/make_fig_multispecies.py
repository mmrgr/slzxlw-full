# -*- coding: utf-8 -*-
"""E-B3 图件：多物种水质控制切换。

三张图：
  FigB3a  三物种 r* 谱与"最紧物种决定系统阈值"
  FigB3b  r 全域控制物种区域图（哪一段由哪个组分决定 CoC）
  FigB3c  全因子网格下控制物种的占比（TDS 是否天然最紧）

用法: python figs/make_fig_multispecies.py
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

SP_ZH = {"TDS": "TDS", "chloride": "氯化物", "hardness_CaCO3": "钙硬度(CaCO3)"}
SP_COLOR = {"TDS": C_WATER, "chloride": C_GRID, "hardness_CaCO3": C_POLICY}
UNTRI = "未触发（设计值起控）"


def load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    rstar = pd.read_csv(R2 / "multispecies_rstar.csv", encoding="utf-8-sig")
    ctrl = pd.read_csv(R2 / "multispecies_control_map.csv", encoding="utf-8-sig")
    sens = pd.read_csv(R2 / "multispecies_sensitivity.csv", encoding="utf-8-sig")
    grid_path = R2 / "multispecies_grid.csv"
    summary = json.loads((R2 / "multispecies_summary.json").read_text(encoding="utf-8"))
    grid = pd.read_csv(grid_path, encoding="utf-8-sig") if grid_path.exists() else pd.DataFrame()
    return rstar, ctrl, sens, grid, summary


# ---------------------------------------------------------------- B3a
def fig_b3a(rstar: pd.DataFrame, ctrl: pd.DataFrame, summary: dict) -> list[Path]:
    """三物种 r* 谱 + 系统阈值由最紧者决定。"""
    fig, axes = plt.subplots(1, 2, figsize=(7.8, 2.9),
                            gridspec_kw={"width_ratios": [1.25, 1.0]})

    # (a) 各物种允许 CoC 曲线 + r* 竖线
    ax = axes[0]
    order = ["TDS", "chloride", "hardness_CaCO3"]
    r = ctrl["r"].to_numpy(float)
    for name in order:
        col = f"CoC上限_{name}"
        if col in ctrl:
            ax.plot(r, ctrl[col], lw=1.3, color=SP_COLOR[name],
                    label=f"{SP_ZH[name]}", zorder=3)
    ax.plot(r, ctrl["系统CoC"], lw=2.4, color="#1a202c", ls=":", alpha=0.75,
            label="系统实际 CoC（取 min）", zorder=2)
    ax.axhline(5.0, color="#4a5568", lw=0.9, ls="--", zorder=1)
    ax.text(0.015, 5.12, "设计浓缩倍数 CoC$_d$ = 5.0", fontsize=6.2, color="#4a5568")
    sys_r = summary.get("系统r星")
    for name in order:
        row = rstar[rstar["物种"] == name]
        if len(row):
            rs = float(row["r星"].iloc[0])
            if 0 < rs < 1:
                ax.axvline(rs, color=SP_COLOR[name], lw=0.9, ls=":", alpha=0.85)
                ax.plot(rs, 5.0, marker="v", ms=5.5, color=SP_COLOR[name], zorder=5)
    if sys_r and np.isfinite(sys_r):
        ax.axvline(sys_r, color="#9b2c2c", lw=1.6, zorder=4)
        ax.text(sys_r + 0.012, 7.15, f"系统 r* = {sys_r:.4f}", fontsize=6.8,
                color="#9b2c2c")
    ax.set_xlim(0, 1)
    ax.set_ylim(1.2, 11)
    ax.set_xlabel("再生水替代率 $r$")
    ax.set_ylabel("该物种允许的浓缩倍数 $L_s/C_{mix,s}(r)$")
    ax.set_title("(a) 三个限制组分的允许浓缩倍数", loc="left")
    ax.legend(loc="upper right", fontsize=6.1)
    ax.grid(color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)

    # (b) r* 谱条形图
    ax = axes[1]
    rows = rstar.sort_values("r星")
    ypos = np.arange(len(rows))
    for i, (_, row) in enumerate(rows.iterrows()):
        rs = float(row["r星"])
        color = SP_COLOR.get(row["物种"], C_OTHER)
        ax.barh(i, rs, height=0.5, color=color, alpha=0.9)
        ax.text(rs + 0.015, i, f"{rs:.4f}", va="center", fontsize=6.8)
        if not bool(row["是否主结果"]):
            ax.text(0.02, i - 0.33, "（压力测试，非项目配置）", fontsize=5.6,
                    color="#742a2a")
    if sys_r and np.isfinite(sys_r):
        ax.axvline(sys_r, color="#9b2c2c", lw=1.5, ls="--",
                   label=f"系统 r* = min = {sys_r:.4f}")
    ax.set_yticks(ypos)
    ax.set_yticklabels([SP_ZH.get(x, x) for x in rows["物种"]], fontsize=7)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("单物种临界替代率 $r^*_s$")
    ax.set_title("(b) 系统阈值取最紧者", loc="left")
    ax.legend(loc="lower right", fontsize=6.3)
    ax.grid(axis="x", color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)

    fig.suptitle("水质兼容阈值不是 TDS 专属：它是「各限制组分取最紧」的结构", fontsize=9.4)
    fig.text(0.01, 0.02,
             "CoC$_d$ = 5.0；物种参数见 multispecies_rstar.csv。钙硬度为工程常见区间的压力测试，"
             "不进入主结果。",
             fontsize=6.2, color="#4a5568")
    fig.subplots_adjust(wspace=0.30, left=0.095, right=0.985, top=0.79, bottom=0.205)
    return save(fig, "FigS15_multispecies_threshold_spectrum")


# ---------------------------------------------------------------- B3b
def fig_b3b(ctrl: pd.DataFrame, summary: dict) -> list[Path]:
    """r 全域控制物种区域图：哪一段由哪个水质组分决定浓缩倍数。"""
    fig, ax = plt.subplots(figsize=(7.2, 2.5))
    r = ctrl["r"].to_numpy(float)
    labels = ctrl["控制物种"].astype(str).tolist()

    # 构建连续区段（[lo, hi) 半开区间，最后一段闭合到 1.0）
    segs = []
    start = 0
    for i in range(1, len(labels) + 1):
        if i == len(labels) or labels[i] != labels[start]:
            lo = float(r[start])
            hi = float(r[i]) if i < len(labels) else float(r[-1])
            segs.append((lo, hi, labels[start]))
            start = i

    for lo, hi, name in segs:
        color = SP_COLOR.get(name, "#e2e8f0")
        ax.axvspan(lo, hi, color=color, alpha=0.28, lw=0, zorder=0)

    ax.plot(r, ctrl["系统CoC"], lw=1.9, color="#1a202c", zorder=3,
            label="系统实际 CoC（取 min）")
    ax.axhline(5.0, color="#4a5568", lw=0.8, ls="--", zorder=1,
               label="设计浓缩倍数 CoC$_d$ = 5.0")

    # 切换点与区段标签
    for sw in summary.get("控制权切换点", []):
        ax.axvline(sw["r"], color="#9b2c2c", lw=1.0, ls=":", zorder=4)
        ax.annotate(f"$r$={sw['r']:.2f}", (sw["r"], 5.03),
                    xytext=(3, 0), textcoords="offset points", fontsize=6.0,
                    color="#9b2c2c", ha="left", va="bottom")
    for lo, hi, name in segs:
        if hi - lo > 0.10:
            ax.text(0.5 * (lo + hi), 5.175, SP_ZH.get(name, "未触发"),
                    ha="center", fontsize=6.8, color="#2d3748")

    ax.set_xlim(0, 1)
    ax.set_ylim(4.30, 5.22)
    ax.set_xlabel("再生水替代率 $r$")
    ax.set_ylabel("系统实际浓缩倍数")
    ax.set_title("控制组分随替代率切换：同一城市在不同 $r$ 下受不同水质指标约束", loc="left")
    ax.legend(loc="lower left", fontsize=5.9, ncol=2)
    ax.grid(axis="y", color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)

    fig.text(0.01, 0.02,
             "背景色与顶部标签对应控制组分；黑线为系统实际 CoC（各组分允许值的最小）。"
             "r<0.53 时设计浓缩倍数起控，CoC 恒为 5.0。",
             fontsize=6.2, color="#4a5568")
    fig.subplots_adjust(left=0.085, right=0.985, top=0.88, bottom=0.215)
    return save(fig, "FigS16_multispecies_control_map")


# ---------------------------------------------------------------- B3c
def fig_b3c(grid: pd.DataFrame, summary: dict) -> list[Path]:
    """全因子网格下控制物种占比 + 系统 r* 分布。"""
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.8),
                            gridspec_kw={"width_ratios": [1.0, 1.35]})
    counts = grid["控制物种"].value_counts()
    ax = axes[0]
    order = counts.index.tolist()
    vals = counts.to_numpy(float)
    colors = [SP_COLOR.get(k, C_OTHER) for k in order]
    ypos = np.arange(len(order))
    ax.barh(ypos, vals / vals.sum() * 100, color=colors, height=0.55, alpha=0.9)
    for i, v in enumerate(vals):
        ax.text(v / vals.sum() * 100 + 1.0, i, f"{v/vals.sum()*100:.1f}%",
                va="center", fontsize=6.8)
    ax.set_yticks(ypos)
    ax.set_yticklabels([SP_ZH.get(k, k) for k in order], fontsize=7)
    ax.set_xlim(0, 60)
    ax.set_xlabel("占全部组合的百分比（%）")
    ax.set_title(f"(a) 谁是最紧组分（n={int(vals.sum())}）", loc="left")
    ax.grid(axis="x", color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)

    ax = axes[1]
    for k in order:
        sub = grid[grid["控制物种"] == k]["系统r星"].to_numpy(float)
        ax.hist(sub, bins=np.arange(0, 1.02, 0.02), alpha=0.55,
                color=SP_COLOR.get(k, C_OTHER), label=SP_ZH.get(k, k))
    ax.axvline(0.5532, color="#9b2c2c", lw=1.3, ls="--", label="标称 r*=0.5532")
    ax.set_xlabel("系统临界替代率 $r^*$")
    ax.set_ylabel("组合数")
    ax.set_title("(b) 系统阈值分布", loc="left")
    ax.legend(loc="upper right", fontsize=6.0)
    ax.grid(axis="y", color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)

    fig.suptitle("把三个组分参数在各自文献区间上网格化后，TDS 只在 27.7% 的组合里是最紧组分",
                 fontsize=8.9)
    axes_L = summary.get("全因子网格", {}).get("网格轴", {})
    fig.text(0.01, 0.02,
             "网格：L 与 $C_r$ 各 5 档（见 summary.json），$C_p$ 固定为项目值。"
             "结论：最紧组分取决于实际水质参数，判据须写成 min 形式。",
             fontsize=6.2, color="#4a5568")
    fig.subplots_adjust(wspace=0.30, left=0.115, right=0.985, top=0.78, bottom=0.215)
    return save(fig, "FigS17_multispecies_grid_share")


def main() -> None:
    rstar, ctrl, sens, grid, summary = load()
    out = []
    out += fig_b3a(rstar, ctrl, summary)
    out += fig_b3b(ctrl, summary)
    if len(grid):
        out += fig_b3c(grid, summary)
    print(f"[OK] {len(out)} files")
    for p in out:
        print(" ", p.name)


if __name__ == "__main__":
    main()
