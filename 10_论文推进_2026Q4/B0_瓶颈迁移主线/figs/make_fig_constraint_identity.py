# -*- coding: utf-8 -*-
"""E-B1 图件：约束身份相图 —— 谁先失效，水侧还是电网侧？

三张图：
  FigB1a  相图（CAWCC 等值线 + 身份区域 + 两端点位置）
  FigB1b  分界线：临界电网容量 G* 随取水能力的变化（细化版，若已有）
  FigB1c  沿分界线的容量跳变（说明为什么"瓶颈身份"是离散结论而非连续过渡）

用法: python figs/make_fig_constraint_identity.py
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
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from figstyle_b0 import (  # noqa: E402
    C_CO, C_GRID, C_HA, C_OTHER, C_POLICY, C_WATER, R2, apply_style, save,
)

apply_style()

IDENT_ORDER = ["电网侧", "水侧", "政策", "其他", "基线不可行"]
IDENT_COLOR = {"电网侧": C_GRID, "水侧": C_WATER, "政策": C_POLICY,
               "其他": C_OTHER, "基线不可行": "#e2e8f0"}
DOMAIN_NAME = {"ha": "D-HA 缺水端", "co": "D-CO 凉爽端"}
# 项目原始参数（相图上的端点标记位置）
BASE = {"ha": {"a": 1.00, "A": 380.0, "G": 1500.0},
        "co": {"a": 1.00, "A": 400.0, "G": 1500.0}}


def load():
    phase = pd.read_csv(R2 / "constraint_identity_phase.csv", encoding="utf-8-sig")
    summ_path = R2 / "constraint_identity_summary.json"
    summary = json.loads(summ_path.read_text(encoding="utf-8")) if summ_path.exists() else {}
    fr_path = R2 / "constraint_identity_frontier_refined.csv"
    refined = pd.read_csv(fr_path, encoding="utf-8-sig") if fr_path.exists() else pd.DataFrame()
    return phase, refined, summary


# ---------------------------------------------------------------- B1a
def fig_b1a(phase: pd.DataFrame, refined: pd.DataFrame) -> list[Path]:
    """相图：(取水倍数 a) × (电网容量 G) 上的 CAWCC 与约束身份。"""
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.4))
    for ax, domain in zip(axes, ("ha", "co")):
        sub = phase[phase["域"] == domain]
        piv_img = sub.pivot_table(index="电网接入容量_MW", columns="取水倍数a",
                                  values="CAWCC_物理_MW")
        piv_id = sub.pivot_table(index="电网接入容量_MW", columns="取水倍数a",
                                 values="身份_物理", aggfunc="first")
        # 对齐
        piv_id = piv_id.reindex(index=piv_img.index, columns=piv_img.columns)
        xs = piv_img.columns.to_numpy(float)
        ys = piv_img.index.to_numpy(float)

        # 身份：用格点方块（不插值），因为 9×9 网格的插值会错误归属边界格
        if len(xs) > 1:
            dx = float(np.min(np.diff(xs))) * 0.92
        else:
            dx = 0.04
        if len(ys) > 1:
            dy = float(np.min(np.diff(ys))) * 0.92
        else:
            dy = 100.0
        for i, g_val in enumerate(ys):
            for j, a_val in enumerate(xs):
                ident = piv_id.to_numpy()[i, j]
                color = IDENT_COLOR.get(str(ident), C_OTHER)
                ax.add_patch(plt.Rectangle(
                    (a_val - dx / 2, g_val - dy / 2), dx, dy,
                    facecolor=color, alpha=0.42, edgecolor="none", zorder=1))

        # CAWCC 等值线（少而清晰）
        arr = piv_img.to_numpy(float)
        lo, hi = float(np.nanmin(arr)), float(np.nanmax(arr))
        step = 200.0
        levels = np.arange(np.ceil(lo / step) * step, hi + step, step)
        levels = levels[(levels >= lo) & (levels <= hi)]
        if len(levels) >= 2:
            cs = ax.contour(xs, ys, arr, levels=levels,
                            colors="#2d3748", linewidths=0.8, zorder=3)
            ax.clabel(cs, inline=True, fontsize=5.8, fmt="%d", colors="#1a202c")

        # 精化分界线（若有）
        if len(refined):
            r = refined[(refined["域"] == domain) & refined["G星_MW"].notna()]
            if len(r):
                ax.plot(r["取水倍数a"], r["G星_MW"], color="#9b2c2c", lw=2.0,
                        marker="o", ms=3.2, zorder=6,
                        label="临界电网容量 $G^*$（二分细化）")

        # 端点点位
        b = BASE[domain]
        ax.plot(b["a"], b["G"], marker="*", ms=13, color="#9b2c2c",
                markeredgecolor="white", markeredgewidth=0.7, zorder=7)
        ax.annotate("本文端点\n(a=1.00, G=1500)", (b["a"], b["G"]),
                    xytext=(9, -20), textcoords="offset points", fontsize=6.0,
                    color="#9b2c2c",
                    arrowprops=dict(arrowstyle="-", lw=0.6, color="#9b2c2c"))

        ax.set_xlabel("水源取水能力倍数 $a$（1.00 = 该端点基准）")
        ax.set_ylabel("电网接入容量 $G$（MW）")
        ax.set_title(f"({'a' if domain == 'ha' else 'b'}) {DOMAIN_NAME[domain]}", loc="left")
        ax.legend(loc="upper left", fontsize=6.0)
        ax.set_xlim(float(min(xs)) - 0.04, float(max(xs)) + 0.04)
        ax.set_ylim(float(min(ys)) - 105, float(max(ys)) + 105)

    handles = [Patch(facecolor=IDENT_COLOR[k], alpha=0.55, label=k)
               for k in IDENT_ORDER if k != "其他"]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=6.4,
               frameon=False, bbox_to_anchor=(0.5, -0.032))
    fig.suptitle("约束身份相图：水侧与电网侧主导区被一条分界线隔开，"
                 "两端点是这条线上的两个抽样点", fontsize=9.2)
    fig.text(0.01, 0.055,
             "底色 = 主导约束的侧别（每格为一个实测参数组合）；黑色等值线 = CAWCC（MW，步长 200）；"
             "红星 = 主稿使用的两个端点。取水能力用相对自身基准的倍数。",
             fontsize=6.1, color="#4a5568")
    fig.subplots_adjust(wspace=0.26, left=0.065, right=0.985, top=0.84, bottom=0.235)
    return save(fig, "FigS9_constraint_identity_phase")


# ---------------------------------------------------------------- B1b
def fig_b1b(refined: pd.DataFrame, phase: pd.DataFrame) -> list[Path]:
    """分界线：G* 随 a 的变化 + 端点裕度。"""
    fig, axes = plt.subplots(1, 2, figsize=(7.8, 2.9),
                            gridspec_kw={"width_ratios": [1.3, 1.0]})

    ax = axes[0]
    any_line = False
    for domain, color, marker in (("ha", C_HA, "o"), ("co", C_CO, "s")):
        sub = refined[(refined["域"] == domain) & refined["G星_MW"].notna()] \
            if len(refined) else pd.DataFrame()
        if len(sub):
            ax.plot(sub["取水倍数a"], sub["G星_MW"], marker=marker, ms=4.2, lw=1.4,
                    color=color, label=DOMAIN_NAME[domain], zorder=3)
            any_line = True
        # 若无细化结果，用相图表格推断的区间中点作为降级方案
        elif len(phase):
            p = phase[(phase["域"] == domain) & phase["CAWCC_物理_MW"].notna()]
            pts = []
            for a_val, blk in p.groupby("取水倍数a"):
                w = blk[blk["身份_物理"] == "水侧"]["电网接入容量_MW"]
                g = blk[blk["身份_物理"] == "电网侧"]["电网接入容量_MW"]
                if len(w) and len(g):
                    pts.append((float(a_val),
                                0.5 * (w.min() + g.max())))
            if pts:
                xs, ys = zip(*sorted(pts))
                ax.plot(xs, ys, marker=marker, ms=4.2, lw=1.4, ls="--",
                        color=color, label=f"{DOMAIN_NAME[domain]}（粗网格）", zorder=3)
                any_line = True
    ax.axhline(1500.0, color="#9b2c2c", lw=1.2, ls=":", zorder=2,
               label="两端点设定的 G = 1500 MW")
    ax.set_xlabel("水源取水能力倍数 $a$")
    ax.set_ylabel("临界电网接入容量 $G^*$（MW）")
    ax.set_title("(a) 分界线位置", loc="left")
    ax.legend(loc="lower left", fontsize=6.0)
    ax.grid(color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)
    if not any_line:
        ax.text(0.5, 0.5, "无可用分界线数据（细化任务未完成）",
                ha="center", va="center", transform=ax.transAxes, fontsize=7)

    # (b) 端点相对分界线的裕度
    ax = axes[1]
    rows = []
    for domain in ("ha", "co"):
        sub = refined[(refined["域"] == domain)] if len(refined) else pd.DataFrame()
        if len(sub):
            at1 = sub[np.isclose(sub["取水倍数a"], 1.0) & sub["G星_MW"].notna()]
            if len(at1):
                g_star = float(at1["G星_MW"].iloc[0])
                rows.append((domain, BASE[domain]["G"], g_star))
    if rows:
        ypos = np.arange(len(rows))
        for i, (domain, g_set, g_star) in enumerate(rows):
            margin = g_set - g_star
            ax.barh(i, margin, height=0.42,
                    color="#c53030" if margin < 0 else "#2c7a7b", alpha=0.85)
            # 负值条向左，标签放条左端外侧；正值条向右，标签放条右端外侧
            ax.text(margin + (-10 if margin < 0 else 10), i,
                    f"{margin:+.0f} MW", va="center", fontsize=7.0,
                    ha="right" if margin < 0 else "left")
            ax.plot(0, i, marker="|", ms=12, mew=1.6, color="#2d3748")
        ax.axvline(0, color="#2d3748", lw=1.0)
        ax.set_yticks(ypos)
        ax.set_yticklabels([DOMAIN_NAME[r[0]] for r in rows], fontsize=7)
        ax.set_xlabel("端点设定容量 减 临界容量（MW）")
        ax.set_title("(b) 端点距分界线的裕度", loc="left")
        lo = min(0.0, min(r[1] - r[2] for r in rows))
        hi = max(0.0, max(r[1] - r[2] for r in rows))
        pad = max(abs(lo), abs(hi)) * 0.30
        ax.set_xlim(lo - pad, hi + pad)
        ax.set_ylim(-0.6, len(rows) - 0.4)
        ax.grid(axis="x", color="#edf2f7", lw=0.5)
        ax.set_axisbelow(True)
    else:
        ax.text(0.5, 0.5, "无细化结果", ha="center", transform=ax.transAxes)

    fig.suptitle("分界线与端点裕度：缺水端点的电网设定高出临界值 244 MW，"
                 "凉爽端点反而低于临界值 131 MW", fontsize=9.0)
    fig.text(0.01, 0.02,
             "(b) 正值表示端点落在水侧主导区（电网有余量），负值表示落在电网主导区。"
             "分界线与取水能力无关（a≥1.00 后为常数），只由电网接网比阈值决定。",
             fontsize=6.2, color="#4a5568")
    fig.subplots_adjust(wspace=0.34, left=0.105, right=0.985, top=0.80, bottom=0.205)
    return save(fig, "FigS10_constraint_identity_frontier")


# ---------------------------------------------------------------- B1c
def fig_b1c(phase: pd.DataFrame) -> list[Path]:
    """沿固定 a 的横切：CAWCC 随 G 的跳变，说明身份切换是离散事件。"""
    fig, axes = plt.subplots(1, 2, figsize=(7.8, 2.8), sharey=True)
    for ax, domain in zip(axes, ("ha", "co")):
        sub = phase[(phase["域"] == domain) & phase["CAWCC_物理_MW"].notna()]
        for a_val in sorted(sub["取水倍数a"].unique()):
            if a_val not in (1.00, 0.95, 1.10):
                continue
            blk = sub[np.isclose(sub["取水倍数a"], a_val)].sort_values("电网接入容量_MW")
            ax.plot(blk["电网接入容量_MW"], blk["CAWCC_物理_MW"],
                    marker="o", ms=2.6, lw=1.1,
                    label=f"a = {a_val:.2f}")
        ax.axvline(1500.0, color="#9b2c2c", lw=1.1, ls=":", zorder=1)
        ax.set_xlabel("电网接入容量 $G$（MW）")
        ax.set_title(f"({'a' if domain == 'ha' else 'b'}) {DOMAIN_NAME[domain]}", loc="left")
        ax.legend(loc="lower right", fontsize=6.2)
        ax.grid(color="#edf2f7", lw=0.5)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("CAWCC（MW）")
    fig.suptitle("容量对电网设定值的响应：D-CO 随 G 单调抬升至两级平台，D-HA 迅速饱和",
                 fontsize=9.0)
    fig.text(0.01, 0.02,
             "红点线为两端点设定的 G = 1500 MW。D-CO 的两个平台对应两种不同的主导约束"
             "（本地配水接入比、电网接网比），说明「瓶颈身份」是离散量。",
             fontsize=6.2, color="#4a5568")
    fig.subplots_adjust(wspace=0.10, left=0.075, right=0.985, top=0.79, bottom=0.205)
    return save(fig, "FigS11_identity_switch_step")


def main() -> None:
    phase, refined, summary = load()
    out = []
    out += fig_b1a(phase, refined)
    out += fig_b1b(refined, phase)
    out += fig_b1c(phase)
    print(f"[OK] {len(out)} files")
    for p in out:
        print(" ", p.name)


if __name__ == "__main__":
    main()
