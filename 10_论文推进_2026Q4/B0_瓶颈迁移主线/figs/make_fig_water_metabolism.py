# -*- coding: utf-8 -*-
"""E-B5 图件：城市水代谢流网络（桑基图 + 节点守恒）。

【布局设计】
每一列（水在系统中推进的"阶段"）内部独立归一化：
  列总高固定为 1.0，列内节点按流量占比分配高度，节点间留固定间隙。
这样无论某列有多少节点、流量差多少倍，都不会溢出画布——这是 matplotlib
手绘桑基图最容易出错的地方（v1 用全局 scale 导致节点堆出画布）。

三张图：
  FigB5a  HA 端点：0 MW vs 1200 MW 并排
  FigB5b  CO 端点：1450 MW
  FigB5c  节点守恒校验

用法: python figs/make_fig_water_metabolism.py
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
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from figstyle_b0 import (  # noqa: E402
    C_CO, C_GRID, C_HA, C_OTHER, C_POLICY, C_WATER, R2, apply_style, save,
)

apply_style()

NODE_COLOR = {
    "外部来水（降水与河流入流）": "#4299e1",
    "RES1": "#2b6cb0", "SC1": "#3182ce", "WTW1": "#2c7a7b",
    "TM1": "#38a169", "SR1": "#68d391", "DM1": "#48bb78",
    "AI_DC1": "#c53030",
    "CENTRAL_REUSE": "#6b46c1", "SEWER1": "#805ad5",
    "WWTW1": "#9f7aea", "SEWER_S": "#a0aec0", "RIVER1": "#4a5568",
}
EXT_COLOR = {
    "大气（蒸发消耗）": "#cbd5e0", "管网漏损": "#fbd38d",
    "工艺自用与损失": "#f6ad55", "调蓄增减（年内蓄水）": "#bee3f8",
    "调蓄增减（存量释放）": "#bee3f8",
}
NODE_LABEL = {
    "外部来水（降水与河流入流）": "外部来水",
    "RES1": "水源", "SC1": "取水渠", "WTW1": "给水厂",
    "TM1": "输水干管", "SR1": "调蓄池", "DM1": "配水管网",
    "AI_DC1": "AI 数据中心", "CENTRAL_REUSE": "再生水厂", "SEWER1": "污水管网",
    "WWTW1": "污水厂", "SEWER_S": "雨水管", "RIVER1": "受纳水体",
    "大气（蒸发消耗）": "蒸发消耗", "管网漏损": "管网漏损",
    "工艺自用与损失": "工艺损失", "调蓄增减（年内蓄水）": "年内蓄水",
    "调蓄增减（存量释放）": "存量释放",
}
# 列（阶段）分配
COLUMN = {
    "外部来水（降水与河流入流）": 0,
    "RES1": 1, "SC1": 1,
    "WTW1": 2, "CENTRAL_REUSE": 2, "WWTW1": 2,
    "TM1": 3, "SR1": 3, "SEWER1": 3,
    "DM1": 4, "AI_DC1": 4, "SEWER_S": 4,
    "大气（蒸发消耗）": 5, "管网漏损": 5, "工艺自用与损失": 5,
    "RIVER1": 5, "调蓄增减（年内蓄水）": 5, "调蓄增减（存量释放）": 5,
}
N_COL = 6
COL_W = 0.075      # 节点框宽（数据坐标，x 范围 0..6）
GAP = 0.022        # 列内节点间隙（占列高的比例）
PAD = 0.04         # 列上下留白


def node_color(name: str) -> str:
    if name.startswith("本地用水（"):
        return "#68d391"
    if name.startswith("本地表面径流"):
        return "#a0aec0"
    return NODE_COLOR.get(name, EXT_COLOR.get(name, "#cbd5e0"))


PROFILE_ZH = {
    "domestic": "生活", "industrial": "工业",
    "irrigation": "灌溉", "municipal_misc": "市政杂用",
}


def node_label(name: str) -> str:
    if name.startswith("本地用水（"):
        inner = name[name.index("（") + 1:name.rindex("）")]
        return f"本地用水·{PROFILE_ZH.get(inner, inner)}"
    if name.startswith("本地表面径流"):
        return "地表径流"
    return NODE_LABEL.get(name, name)


def load(domain: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    return (pd.read_csv(R2 / f"water_metabolism_{domain}_flows.csv", encoding="utf-8-sig"),
            pd.read_csv(R2 / f"water_metabolism_{domain}_nodes.csv", encoding="utf-8-sig"),
            json.loads((R2 / f"water_metabolism_{domain}_summary.json").read_text(encoding="utf-8")))


def sankey(ax, flows: pd.DataFrame, cap: float, title: str,
           min_share: float = 0.003) -> None:
    sub = flows[np.isclose(flows["容量_MW"], cap)].copy()
    if sub.empty:
        ax.text(0.5, 0.5, f"容量 {cap} MW 无数据", ha="center", transform=ax.transAxes)
        return
    global_max = float(sub["年流量_ML"].max())
    sub = sub[sub["年流量_ML"] >= global_max * min_share]

    intake = sub.groupby("目标")["年流量_ML"].sum()
    outgo = sub.groupby("源")["年流量_ML"].sum()

    # ---- 列内归一化布局 ----
    nodes_by_col: dict[int, list[str]] = {}
    for n in set(intake.index) | set(outgo.index):
        nodes_by_col.setdefault(COLUMN.get(n, 3), []).append(n)

    box: dict[str, tuple[int, float, float]] = {}
    internal_scale: dict[int, float] = {}
    for col, names in nodes_by_col.items():
        names = sorted(names, key=lambda n: -max(intake.get(n, 0.0), outgo.get(n, 0.0)))
        weights = [max(intake.get(n, 0.0), outgo.get(n, 0.0)) for n in names]
        wsum = sum(weights)
        if wsum <= 0:
            continue
        internal_scale[col] = wsum
        n = len(names)
        avail = 1.0 - 2 * PAD - GAP * (n - 1)
        y = 1.0 - PAD
        for name, w in zip(names, weights):
            h = max(avail * w / wsum, 0.008)  # 给极小的节点一个可见下限
            box[name] = (col, y - h, y)
            y -= h + GAP

    # ---- 画边 ----
    out_used = {k: v[2] for k, v in box.items()}
    in_used = {k: v[2] for k, v in box.items()}

    def thickness(node: str, val: float) -> float:
        col = box[node][0]
        h_node = box[node][2] - box[node][1]
        tot = max(intake.get(node, 0.0), outgo.get(node, 0.0))
        if tot <= 0:
            return 0.0
        return h_node * (val / tot)

    for _, row in sub.sort_values("年流量_ML", ascending=False).iterrows():
        src, dst, val = row["源"], row["目标"], float(row["年流量_ML"])
        if src not in box or dst not in box:
            continue
        ts, td = thickness(src, val), thickness(dst, val)
        sc = box[src][0]
        dc = box[dst][0]
        y0s = out_used[src]
        y1s = y0s - ts
        out_used[src] = y1s
        y0d = in_used[dst]
        y1d = y0d - td
        in_used[dst] = y1d

        x0 = sc + COL_W
        x1 = dc
        if x1 <= x0:
            x1 = x0 + 0.015
        xm = 0.5 * (x0 + x1)
        verts = [(x0, y0s), (xm, y0s), (xm, y0d), (x1, y0d),
                 (x1, y1d), (xm, y1d), (xm, y1s), (x0, y1s), (x0, y0s)]
        codes = [MPath.MOVETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
                 MPath.LINETO, MPath.CURVE4, MPath.CURVE4, MPath.CURVE4,
                 MPath.CLOSEPOLY]
        ax.add_patch(PathPatch(MPath(verts, codes), facecolor=node_color(src),
                               alpha=0.30, edgecolor="none", zorder=2))

    # ---- 画节点 ----
    # 标签排布：第 0-3 列放右侧；第 4 列（终端）放左侧但用引线外推；
    # 第 5 列（汇）放右侧。这样四个"本地用水"节点不会互相压字。
    for name, (col, y0, y1) in box.items():
        ax.add_patch(plt.Rectangle((col, y0), COL_W, y1 - y0,
                                   facecolor=node_color(name), edgecolor="white",
                                   linewidth=0.7, zorder=4))
        mid = 0.5 * (y0 + y1)
        label = node_label(name)
        if col == N_COL - 1:
            ax.text(col + COL_W + 0.04, mid, label, ha="left", va="center",
                    fontsize=5.3, color="#1a202c", zorder=5)
        elif col == 4:
            # 第 4 列节点窄，标签内置竖排，避免与第 5 列相撞
            short = label.replace("本地用水·", "")
            if (y1 - y0) > 0.09:
                ax.text(col + COL_W / 2, mid, short, ha="center", va="center",
                        fontsize=5.2, color="white", rotation=90, zorder=6,
                        fontweight="bold")
            else:
                ax.annotate(short, xy=(col + COL_W / 2, mid),
                            xytext=(col - 0.32, mid), ha="right", va="center",
                            fontsize=5.2, color="#1a202c", zorder=6,
                            arrowprops=dict(arrowstyle="-", lw=0.4,
                                            color="#a0aec0", shrinkA=0, shrinkB=0))
        else:
            ax.text(col + COL_W + 0.04, mid, label, ha="left", va="center",
                    fontsize=5.3, color="#1a202c", zorder=5)

    ax.set_xlim(-1.45, N_COL + 0.72)
    ax.set_ylim(0.0, 1.02)
    ax.axis("off")
    ax.set_title(title, loc="left", fontsize=8.0)


def fig_b5a() -> list[Path]:
    flows, nodes, summary = load("ha")
    caps = sorted(flows["容量_MW"].unique())
    c0 = caps[0]
    cmid = caps[1] if len(caps) > 2 else caps[-1]
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.0))
    for ax, cap, tag in ((axes[0], c0, "a"), (axes[1], cmid, "b")):
        s = summary["逐容量点"].get(f"{cap:g}", {})
        sankey(ax, flows, cap,
               f"({tag}) {cap:.0f} MW   AI 取水 {s.get('AI取水_ML', 0):,.0f} ML/a  ·  "
               f"蒸发 {s.get('总蒸发消耗_ML', 0):,.0f} ML/a")
    fig.suptitle("D-HA 缺水端点的城市水代谢：AI 接入前后（年累计，730 天）",
                 fontsize=9.2)
    fig.text(0.01, 0.035,
             "配色：蓝 = 水源与输配，绿 = 配水与用水，红 = AI 数据中心，紫 = 污水与再生水，"
             "灰/橙 = 消耗与损失。列内节点高度按流量归一化。",
             fontsize=6.0, color="#4a5568")
    fig.text(0.01, 0.010,
             "流量取 FullAIUWMModel.component_daily；拓扑取 project.json 的 supply_paths 与 "
             "wastewater_connections。每条边的依据见 water_metabolism_ha_flows.csv。",
             fontsize=5.7, color="#718096")
    fig.subplots_adjust(left=0.005, right=0.997, top=0.845, bottom=0.115)
    return save(fig, "FigS21_water_metabolism_sankey_ha")


def fig_b5b() -> list[Path]:
    flows, nodes, summary = load("co")
    caps = sorted(flows["容量_MW"].unique())
    cmid = caps[1] if len(caps) > 2 else caps[-1]
    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    s = summary["逐容量点"].get(f"{cmid:g}", {})
    sankey(ax, flows, cmid,
           f"D-CO 凉爽端点 {cmid:.0f} MW   AI 取水 {s.get('AI取水_ML', 0):,.0f} ML/a  ·  "
           f"蒸发 {s.get('总蒸发消耗_ML', 0):,.0f} ML/a")
    fig.suptitle("D-CO 端点的水代谢：气候更凉爽使蒸发消耗更低，本地用水占比更高",
                 fontsize=8.8)
    fig.text(0.01, 0.02,
             "口径与 FigB5a 相同。两域差异主要来自再生水目标份额（0.70 vs 0.45）与冷却负荷。",
             fontsize=6.0, color="#4a5568")
    fig.subplots_adjust(left=0.005, right=0.995, top=0.885, bottom=0.115)
    return save(fig, "FigS22_water_metabolism_sankey_co")


def fig_b5c() -> list[Path]:
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 2.8), sharey=True)
    for ax, domain in zip(axes, ("ha", "co")):
        _, _, summary = load(domain)
        rows = [{"容量": float(cap), "节点": c["节点"], "相对差": c["相对差"]}
                for cap, d in summary["逐容量点"].items() for c in d["校验明细"]]
        df = pd.DataFrame(rows)
        if df.empty:
            ax.text(0.5, 0.5, "无校验数据", ha="center", transform=ax.transAxes)
            continue
        piv = df.pivot_table(index="节点", columns="容量", values="相对差")
        order = piv.max(axis=1).sort_values().index
        ypos = np.arange(len(order))
        color = C_HA if domain == "ha" else C_CO
        for i, node in enumerate(order):
            vals = piv.loc[node].to_numpy(float) * 100
            ax.plot([vals.min(), max(vals.max(), 1e-6)], [i, i], color=color, lw=5,
                    alpha=0.55, solid_capstyle="round", zorder=2)
            ax.plot(vals.mean(), i, marker="|", ms=11, mew=1.9, color="#1a202c", zorder=4)
        ax.axvline(1.0, color="#c53030", lw=1.1, ls="--", label="验收线 1%")
        ax.set_yticks(ypos)
        ax.set_yticklabels(order, fontsize=6.6)
        ax.set_xlabel("节点相对不守恒率（%）")
        ax.set_title(f"({'a' if domain == 'ha' else 'b'}) "
                     f"D-{'HA' if domain == 'ha' else 'CO'}", loc="left")
        ax.legend(loc="lower right", fontsize=6.2)
        ax.grid(axis="x", color="#edf2f7", lw=0.5)
        ax.set_axisbelow(True)
    fig.suptitle("桑基图的节点守恒校验：全部中间节点相对差 < 1%", fontsize=9.0)
    fig.text(0.01, 0.02,
             "相对差 = |入流 − 出流| / 入流。水平条为不同容量点的范围，竖线为均值；"
             "汇节点与外部节点不参与校验。",
             fontsize=6.2, color="#4a5568")
    fig.subplots_adjust(wspace=0.08, left=0.155, right=0.985, top=0.80, bottom=0.215)
    return save(fig, "FigS23_water_metabolism_conservation")


def main() -> None:
    out = []
    out += fig_b5a()
    out += fig_b5b()
    out += fig_b5c()
    print(f"[OK] {len(out)} files")
    for p in out:
        print(" ", p.name)


if __name__ == "__main__":
    main()
