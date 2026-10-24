# -*- coding: utf-8 -*-
"""E-B6 多类型统计图：把已有产物用此前未用过的图型重新表达。

【为什么需要这一批】
前几轮的图集中在"指标对指标"（曲线、热图、相图、桑基）。但项目里还有大量
**分布型/排序型**的数据，适合用箱线、CDF、雷达、小提琴等图型表达，
而这些正是参考论文（Nature Water 2026、Applied Energy 2025）常用的手法：

  · 参考论文 Fig 6/7 用箱线 + 误差棒表达情景不确定性
  · Facility-level 用 CDF 表达省际异质性
  · China's CWTS 用雷达/多维归一化表达区域画像

四张图：
  FigB6a  箱线图：多情景 × 两域的 CAWCC 分布（用蒙特卡洛样本）
  FigB6b  累积分布（CDF）：169 个加州供水系统的 k 值分布与阈值位置
  FigB6c  雷达图：两域相对"约束压力画像"（十约束归一化后）
  FigB6d  小提琴 + 散点：干预增益的分组分布（含零增益项）

用法: python figs/make_fig_distribution_types.py
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
    C_CO, C_GRID, C_HA, C_OTHER, C_POLICY, C_WATER, R2, apply_style,
    CONSTRAINT_SHORT, load_binding_diagnosis, save, short_of,
)

apply_style()

DOMAIN_NAME = {"ha": "D-HA 缺水端", "co": "D-CO 凉爽端"}
SCEN_ZH = {"G0": "G0 基准", "G1": "G1 高温", "G2": "G2 干旱"}


# ---------------------------------------------------------------- B6a
def fig_b6a() -> list[Path]:
    """箱线图：四情景 × 两域的 CAWCC 分布（来自压力情景扫描，逐 r 展开）。"""
    df = pd.read_csv(R2 / "pressure_regime_scan.csv", encoding="utf-8-sig")
    df = df[df["CAWCC_物理_MW"].notna()]
    fig, ax = plt.subplots(figsize=(7.6, 3.0))
    scenarios = ["G0", "G1", "G2"]
    width = 0.34
    xticks, xlabels = [], []
    for i, domain in enumerate(("ha", "co")):
        for j, scen in enumerate(scenarios):
            sub = df[(df["域"] == domain) & (df["情景"] == scen)]["CAWCC_物理_MW"]
            if sub.empty:
                continue
            pos = i * (len(scenarios) + 1) + j
            bp = ax.boxplot([sub.to_numpy(float)], positions=[pos], widths=width,
                            patch_artist=True, showfliers=False,
                            medianprops=dict(color="#1a202c", lw=1.2),
                            whiskerprops=dict(color="#4a5568", lw=0.7),
                            capprops=dict(color="#4a5568", lw=0.7))
            color = C_HA if domain == "ha" else C_CO
            for patch in bp["boxes"]:
                patch.set_facecolor(color)
                patch.set_alpha(0.35 + 0.18 * j)
                patch.set_edgecolor("#4a5568")
            # 叠加所有样本点（jitter）
            rng = np.random.default_rng(42 + j)
            ax.scatter(pos + rng.uniform(-0.09, 0.09, len(sub)), sub,
                       s=8, color=color, alpha=0.55, edgecolor="none", zorder=3)
            xticks.append(pos)
            xlabels.append(scen)
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels, fontsize=6.8)
    # 域分组标注
    n_s = len(scenarios) + 1
    for i, domain in enumerate(("ha", "co")):
        ax.text(i * n_s + 1, -0.16, DOMAIN_NAME[domain], transform=ax.get_xaxis_transform(),
                ha="center", fontsize=7.2, color="#1a202c")
    ax.axhline(0, color="#cbd5e0", lw=0.6)
    ax.set_ylabel("CAWCC（MW）")
    ax.set_title("各外部压力情景下 CAWCC 的分布（每情景 6 个替代率点）", loc="left")
    ax.grid(axis="y", color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)

    fig.suptitle("箱线 + 散点：干旱情景把分布整体压到低位，且域内离散度收窄",
                 fontsize=9.0)
    fig.text(0.01, 0.02,
             "箱体为四分位距，中线为中位数，须为 1.5×IQR 内极值；散点为全部样本（每个 r 一个点）。"
             "G3 复合情景在两域均不可行，故未绘出。",
             fontsize=6.2, color="#4a5568")
    fig.subplots_adjust(left=0.085, right=0.985, top=0.79, bottom=0.225)
    return save(fig, "FigS24_cawcc_boxplot_by_scenario")


# ---------------------------------------------------------------- B6b
def fig_b6b() -> list[Path]:
    """CDF：加州供水系统的 k 值分布与阈值位置。

    数据源 `_ca_k_clean.json` / `_ca_k_distribution.json` 的结构是
    {k_star, n_clean, records:[{k, potable_af, recycled_af, ...}]}，
    k 值在 records 内，不是顶层数组。
    """
    b0 = HERE.parent
    ks, source, n_raw = None, None, None
    for p in (b0 / "_ca_k_clean.json", b0 / "_ca_k_distribution.json"):
        if not p.exists():
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        recs = d.get("records") if isinstance(d, dict) else None
        if not isinstance(recs, list) or not recs:
            continue
        vals = []
        for item in recs:
            if not isinstance(item, dict):
                continue
            for kk in ("k", "k_value", "ratio"):
                if kk in item and item[kk] is not None:
                    try:
                        vals.append(float(item[kk]))
                    except (TypeError, ValueError):
                        pass
                    break
        if len(vals) >= 10:
            ks = np.array(vals)
            source = p.name
            n_raw = d.get("n_raw")
            break

    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    if ks is None:
        ax.text(0.5, 0.5, "未找到可解析的加州 k 值列表", ha="center", va="center",
                transform=ax.transAxes, fontsize=7.5)
        ax.axis("off")
        fig.suptitle("加州供水系统判据筛查的累积分布", fontsize=9.0)
        return save(fig, "FigS25_california_k_cdf")

    ks = np.sort(ks[ks > 0])
    cdf = np.arange(1, len(ks) + 1) / len(ks) * 100
    ax.step(ks, cdf, where="post", color=C_WATER, lw=1.7)
    ax.fill_between(ks, 0, cdf, step="post", color=C_WATER, alpha=0.13)

    marks = [(3.4999, "$k^*$=3.50（份额 6%/26%）", "#c53030", 30),
             (0.8077, "$k^*$=0.81（份额相等）", "#c05621", 55)]
    for k_star, label, color, ypos in marks:
        ax.axvline(k_star, color=color, lw=1.2, ls="--")
        n = int((ks < k_star).sum())
        pct = n / len(ks) * 100
        ax.annotate(f"{label}\n{n}/{len(ks)} = {pct:.1f}%", xy=(k_star, ypos),
                    xytext=(6, 0), textcoords="offset points",
                    fontsize=6.3, color=color, ha="left", va="center")

    ax.set_xscale("log")
    ax.set_xlabel("自来水 / 再生水用量比 $k$（对数轴）")
    ax.set_ylabel("累积占比（%）")
    ax.set_ylim(0, 103)
    ax.set_title("加州供水系统在判据筛查中的累积分布", loc="left")
    ax.grid(color="#edf2f7", lw=0.5, which="both")
    ax.set_axisbelow(True)

    fig.suptitle(f"{len(ks)} 个加州供水系统：k 跨越三个数量级，低于 3.50 的仅约七分之一",
                 fontsize=9.0)
    fig.text(0.01, 0.02,
             f"数据源：{source}" + (f"（清洗前 {n_raw} 条，清洗后 {len(ks)} 条）" if n_raw else "")
             + "。k 由公开年报的供水量与再生水用量构造，非实测设施水质。",
             fontsize=6.2, color="#4a5568")
    fig.subplots_adjust(left=0.105, right=0.985, top=0.80, bottom=0.215)
    return save(fig, "FigS25_california_k_cdf")


# ---------------------------------------------------------------- B6c
def fig_b6c() -> list[Path]:
    """雷达图：两域十约束的归一化压力画像。"""
    diag = load_binding_diagnosis()
    fig, axes = plt.subplots(1, 2, figsize=(7.8, 3.4),
                            subplot_kw={"projection": "polar"})
    # 取接近各自 CAWCC 的容量点做画像
    targets = {"ha": 1150.0, "co": 1450.0}
    cons_cols = ["max_source_abstraction_ratio", "max_wtw_utilization",
                 "max_wwtw_utilization", "reclaimed_water_substitution_ratio",
                 "peak_capacity_ratio", "max_local_connection_ratio",
                 "max_daily_average_grid_connection_ratio",
                 "system_reliability_fraction"]
    for ax, domain in zip(axes, ("ha", "co")):
        sub = diag[(diag["域"] == domain) & (diag["尺度"] == "日尺度")]
        if sub.empty:
            continue
        target = targets[domain]
        sub = sub.assign(d=lambda x: (x["容量_MW"].astype(float) - target).abs())
        row = sub.sort_values("d").iloc[0]
        vals, labels = [], []
        for c in cons_cols:
            if c not in row:
                continue
            try:
                v = float(row[c])
            except (TypeError, ValueError):
                continue
            vals.append(min(max(v, 0.0), 1.35))
            labels.append(short_of(c))
        if not vals:
            continue
        ang = np.linspace(0, 2 * np.pi, len(vals), endpoint=False).tolist()
        vals_c = vals + vals[:1]
        ang_c = ang + ang[:1]
        color = C_HA if domain == "ha" else C_CO
        ax.plot(ang_c, vals_c, lw=1.5, color=color)
        ax.fill(ang_c, vals_c, color=color, alpha=0.22)
        ax.set_xticks(ang)
        ax.set_xticklabels(labels, fontsize=5.6)
        ax.set_ylim(0, 1.35)
        ax.set_yticks([0.5, 1.0])
        ax.set_yticklabels(["0.5", "1.0"], fontsize=5.4, color="#718096")
        # 1.0 阈值参考环
        ax.plot(np.linspace(0, 2 * np.pi, 100), [1.0] * 100, ls="--", lw=0.8,
                color="#c53030", alpha=0.7)
        ax.set_title(f"{DOMAIN_NAME[domain]}\n（{float(row['容量_MW']):.0f} MW）",
                     fontsize=7.6, pad=20)

    fig.suptitle("约束压力画像（雷达图）：两域的形状不同，说明瓶颈结构而非规模差异",
                 fontsize=9.0, y=0.985)
    fig.text(0.01, 0.02,
             "各轴为约束的实际取值（比率型，无量纲），红色虚线圈为 1.0 失效线。"
             "越靠近外圈越接近失效。",
             fontsize=6.2, color="#4a5568")
    fig.subplots_adjust(left=0.06, right=0.94, top=0.74, bottom=0.16, wspace=0.42)
    return save(fig, "FigS26_constraint_pressure_radar")


# ---------------------------------------------------------------- B6d
def fig_b6d() -> list[Path]:
    """干预增益的分布（含零增益项）。

    ⚠ 这批数据不适合小提琴图：每域 9 项干预里 8 项增益恰为 0、1 项非零，
    是**高度退化**的离散分布。KDE 会把 0 处的质量抹成宽包，并把单个非零点
    画成假峰（v1 果然出现了错误双峰）。
    改用：零增益项画成 0 线上的抖动点，非零项画成独立的水平条 + 标注。
    """
    import csv
    path = R2 / "intervention_cost_benefit.csv"
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    if not rows:
        raise ValueError("intervention_cost_benefit.csv 为空")
    df = pd.DataFrame(rows)
    gain_col = [c for c in df.columns if "增益" in c and "MW" in c][0]
    dom_col = df.columns[0]
    int_col = [c for c in df.columns if "干预" in c][0]
    df = df.rename(columns={gain_col: "gain", dom_col: "domain", int_col: "intervention"})
    df["gain"] = pd.to_numeric(df["gain"], errors="coerce")
    df = df[df["intervention"] != "baseline"]

    fig, ax = plt.subplots(figsize=(7.8, 3.1))
    for i, domain in enumerate(("ha", "co")):
        sub = df[df["domain"] == domain]
        color = C_HA if domain == "ha" else C_CO
        pos = i + 1
        rng = np.random.default_rng(7 + i)
        zero = sub[sub["gain"].abs() < 1e-9]
        nz = sub[sub["gain"].abs() >= 1e-9]
        # 零增益：在 0 线上抖动
        ax.scatter(pos + rng.uniform(-0.22, 0.22, len(zero)),
                   np.zeros(len(zero)), s=34, color=color, alpha=0.55,
                   edgecolor="white", linewidth=0.5, zorder=4,
                   label="零增益" if i == 0 else None)
        # 非零：水平条，标出是哪一项（同增益值的多项纵向错开）
        seen: dict[float, int] = {}
        for _, row in nz.sort_values("gain").iterrows():
            g = float(row["gain"])
            k = seen.get(g, 0)
            seen[g] = k + 1
            dy = 0.0 if k == 0 else (-7.5 * k)
            ax.hlines(g, pos - 0.30, pos + 0.30, color=color, lw=3.2,
                      alpha=0.9 - 0.2 * k, zorder=5)
            ax.annotate(f"{str(row['intervention']).replace('_', ' ')}"
                        f"  +{g:.0f} MW",
                        xy=(pos + 0.32, g), xytext=(0, dy),
                        textcoords="offset points", fontsize=6.2,
                        color="#1a202c", va="center", ha="left", zorder=6)
        ax.text(pos, -18, DOMAIN_NAME[domain], ha="center", fontsize=7.0)
        ax.text(pos, 175, f"零增益 {len(zero)}/{len(zero)+len(nz)} 项",
                ha="center", fontsize=6.4, color="#4a5568")

    ax.axhline(0, color="#4a5568", lw=0.8)
    ax.set_xticks([])
    ax.set_xlim(0.45, 2.90)
    ax.set_ylim(-28, 195)
    ax.set_ylabel("容量增益（MW）")
    ax.set_title("九项一对一干预的容量增益（已排除基线）", loc="left")
    ax.legend(loc="upper left", fontsize=6.4)
    ax.grid(axis="y", color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)

    fig.suptitle("干预增益是高度退化的离散分布：每域 9 项中仅 1 项非零，其余严格为 0",
                 fontsize=9.0)
    fig.text(0.01, 0.02,
             "因数据退化（8 个 0 + 1 个正值），小提琴/KDE 会画出假峰，故改用抖动点 + 水平条。"
             "零增益项不是缺失值，而是真实的 0。",
             fontsize=6.2, color="#4a5568")
    fig.subplots_adjust(left=0.085, right=0.985, top=0.79, bottom=0.185)
    return save(fig, "FigS27_intervention_gain_strip")


def main() -> None:
    builders = [("B6a", fig_b6a), ("B6b", fig_b6b), ("B6c", fig_b6c), ("B6d", fig_b6d)]
    ok, fail = [], []
    for tag, fn in builders:
        try:
            paths = fn()
            print(f"[OK] {tag} -> {paths[0].name}")
            ok.append(tag)
        except Exception as exc:  # noqa: BLE001
            import traceback
            print(f"[FAIL] {tag}: {exc}")
            traceback.print_exc()
            fail.append(tag)
    print(f"\n完成 {len(ok)}/{len(builders)}；失败 {fail}")


if __name__ == "__main__":
    main()
