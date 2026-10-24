# -*- coding: utf-8 -*-
"""批次 A：把仓库中已有、但从未上图的实验数据变成图（零边际成本）。

八张图，全部只读取权威产物，不重跑仿真：
  F-A1  CAWCC 概率分布与分位带         ha|co/probabilistic_corrected.csv
  F-A2  全局敏感性 Morris / Sobol       ha|co/city_morris.csv, city_sobol.csv
  F-A3  阈值扰动龙卷风图               threshold_perturbation_sensitivity.csv
  F-A4  文献基准对标森林图             literature_benchmark.csv
  F-A5  参数包络覆盖                   parameter_envelope_R7.csv
  F-A6  帕累托前沿（补 Fig4 缺失）      pareto_front.csv, intervention_cost_benefit.csv
  F-A7  冷却技术水—能权衡              technology_load_sensitivity_R7b.csv
  F-A8  水量/溶质闭合诊断              water_balance_closure.csv

用法: python figs/make_fig_supp_batch_a.py
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
    C_CO, C_GRID, C_HA, C_OTHER, C_POLICY, C_WATER, GREY, R2, apply_style, save, short_of,
)

apply_style()

DOMAINS = ("ha", "co")
DOMAIN_COLOR = {"ha": C_HA, "co": C_CO}
DOMAIN_NAME = {"ha": "D-HA 缺水端", "co": "D-CO 凉爽端"}
NOMINAL = {"ha": 1150.0, "co": 1450.0}


# ---------------------------------------------------------------- F-A1
def fig_a1() -> list[Path]:
    """CAWCC 概率分布：1024 样本蒙特卡洛 + 分位数带 + 标称值位置。"""
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 2.7))
    stats = {}
    for ax, domain in zip(axes, DOMAINS):
        df = pd.read_csv(R2 / domain / "probabilistic_corrected.csv",
                         encoding="utf-8-sig", low_memory=False)
        x = df["maximum_safe_ai_capacity_mw"].dropna().to_numpy(float)
        p05, p50, p95 = np.percentile(x, [5, 50, 95])
        nominal = NOMINAL[domain]
        pct = float((x < nominal).mean() * 100)
        stats[domain] = {"n": int(x.size), "p05": float(p05), "p50": float(p50),
                         "p95": float(p95), "nominal": nominal,
                         "nominal_percentile": pct,
                         "std": float(x.std(ddof=1))}
        bins = np.arange(x.min() - 25, x.max() + 50, 50)
        ax.hist(x, bins=bins, color=DOMAIN_COLOR[domain], alpha=0.55,
                edgecolor="white", linewidth=0.5)
        for val, style, lab in ((p05, ":", "P05"), (p50, "-", "P50"), (p95, ":", "P95")):
            ax.axvline(val, color="#4a5568", ls=style, lw=0.9,
                       label=f"{lab} = {val:.0f} MW" if lab == "P05" else None)
        ax.axvline(nominal, color="#9b2c2c", lw=1.6,
                   label=f"标称 = {nominal:.0f} MW（P{pct:.0f}）")
        ax.set_xlabel("条件化承载容量 CAWCC（MW）")
        ax.set_ylabel("样本数")
        ax.set_title(f"({'a' if domain == 'ha' else 'b'}) {DOMAIN_NAME[domain]} · "
                     f"{x.size} 样本", loc="left")
        ax.legend(loc="upper left", fontsize=6.6)
        ax.grid(axis="y", color="#e2e8f0", lw=0.5)
        ax.set_axisbelow(True)
    fig.suptitle("CAWCC 对 PUE / 设计浓缩倍数 / 温度系数的蒙特卡洛响应："
                 "标称值位于分布上四分位，不确定性带宽大于主结论效应量", fontsize=9.5)
    fig.text(0.01, 0.02,
             "样本：两端点各 1024 次拉丁超立方抽样，41 点容量扫描，联合口径约束集；"
             "红色实线为本文主结果引用的标称容量。",
             fontsize=6.4, color="#4a5568")
    fig.subplots_adjust(wspace=0.26, left=0.075, right=0.985, top=0.80, bottom=0.20)
    out = save(fig, "FigS1_cawcc_uncertainty")
    (HERE / "_fig_a1_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


# ---------------------------------------------------------------- F-A2
def fig_a2() -> list[Path]:
    """全局敏感性：Morris μ*–σ 平面 + Sobol 总效应排序。"""
    fig, axes = plt.subplots(1, 3, figsize=(8.6, 2.9),
                            gridspec_kw={"width_ratios": [1.05, 1.05, 1.5]})

    for ax, domain in zip(axes[:2], DOMAINS):
        df = pd.read_csv(R2 / domain / "city_morris.csv", encoding="utf-8-sig")
        df = df[df["metric"] == "max_source_abstraction_ratio"]
        mu = df["mu_star"].to_numpy(float)
        sig = df["sigma"].to_numpy(float)
        # 归一化到最大 μ*，便于跨端点比较
        scale = mu.max() if mu.max() > 0 else 1.0
        ax.scatter(mu / scale, sig / scale, s=22, color=DOMAIN_COLOR[domain],
                   alpha=0.8, edgecolor="white", linewidth=0.5, zorder=3)
        # 只标注影响最大的三个参数
        order = np.argsort(mu)[::-1][:3]
        for rank, idx in enumerate(order):
            label = df["parameter"].iloc[idx].split(".")[-1]
            ax.annotate(label, (mu[idx] / scale, sig[idx] / scale),
                        xytext=(4, 3 + rank * 6), textcoords="offset points",
                        fontsize=6.2, color="#2d3748")
        lim = max((mu / scale).max(), (sig / scale).max()) * 1.12
        ax.plot([0, lim], [0, lim], ls="--", lw=0.7, color=GREY,
                label="σ = μ*（线性/非线性分界）")
        ax.set_xlim(0, lim)
        ax.set_ylim(0, lim)
        ax.set_xlabel("归一化 Morris μ*")
        ax.set_ylabel("归一化 Morris σ")
        ax.set_title(f"({'a' if domain == 'ha' else 'b'}) {DOMAIN_NAME[domain]}", loc="left")
        ax.legend(loc="upper left", fontsize=6.2)
        ax.grid(color="#edf2f7", lw=0.5)
        ax.set_axisbelow(True)

    # (c) Sobol 总效应，两域并列
    ax = axes[2]
    rows = []
    for domain in DOMAINS:
        df = pd.read_csv(R2 / domain / "city_sobol.csv", encoding="utf-8-sig")
        df = df[df["metric"] == "max_source_abstraction_ratio"]
        df = df.assign(domain=domain, short=df["parameter"].str.split(".").str[-1])
        rows.append(df)
    sobol = pd.concat(rows)
    piv = sobol.pivot_table(index="short", columns="domain", values="ST", aggfunc="first")
    piv = piv.reindex(piv.max(axis=1).sort_values(ascending=True).index)
    ypos = np.arange(len(piv))
    h = 0.36
    ax.barh(ypos - h / 2, piv["ha"], height=h, color=C_HA, alpha=0.85, label="D-HA")
    ax.barh(ypos + h / 2, piv["co"], height=h, color=C_CO, alpha=0.85, label="D-CO")
    ax.set_yticks(ypos)
    ax.set_yticklabels(piv.index, fontsize=6.4)
    ax.set_xlabel("Sobol 总效应 $S_T$（对水源取水比）")
    ax.set_title("(c) 参数总效应排序", loc="left")
    ax.legend(loc="lower right", fontsize=6.4)
    ax.grid(axis="x", color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)
    ax.axvline(0, color="#4a5568", lw=0.6)

    fig.suptitle("全局敏感性：漏损率主导水量侧指标，替代率并非一阶驱动",
                 fontsize=9.5)
    fig.text(0.01, 0.02,
             "Morris 取 μ*–σ 平面（σ>μ* 提示强非线性或交互），Sobol 取总效应 $S_T$；"
             "指标为年度水源取水占用比，14 个参数，两端点各一套。",
             fontsize=6.4, color="#4a5568")
    fig.subplots_adjust(wspace=0.36, left=0.075, right=0.985, top=0.80, bottom=0.20)
    return save(fig, "FigS2_global_sensitivity")


# ---------------------------------------------------------------- F-A3
def fig_a3() -> list[Path]:
    """阈值扰动图。

    ⚠ 口径说明（读产物时必读）：`audit_threshold_perturbation.py` 的
    `build_perturbed` 是把**全部非零容忍约束同时**乘以 factor，不是逐约束单独
    扰动。因此 `CAWCC位移_MW` 列是"全约束同时 ±2%"下的总容量位移（同一 factor
    下各行相同），**不能**当作单约束贡献。按约束分解的正确列是 `位移_MW`
    （该约束首失效容量自身的移动），面板 (a) 用它。
    """
    df = pd.read_csv(R2 / "threshold_perturbation_sensitivity.csv", encoding="utf-8-sig")
    df = df[~df["是否跳过扰动"].astype(bool)]
    base_cawcc = float(df.loc[df["域"] == "ha", "域基准CAWCC_MW"].iloc[0])
    base_co = float(df.loc[df["域"] == "co", "域基准CAWCC_MW"].iloc[0])

    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.0),
                            gridspec_kw={"width_ratios": [1.30, 1.0]})

    # (a) 逐约束首失效位移（真正的按约束分解）
    ax = axes[0]
    ha = df[df["域"] == "ha"]
    piv = ha.pivot_table(index="约束", columns="扰动系数", values="位移_MW", aggfunc="first")
    piv = piv.reindex(piv.abs().max(axis=1).sort_values().index)
    ypos = np.arange(len(piv))
    lo = pd.to_numeric(piv[0.98], errors="coerce").fillna(0).to_numpy(float)
    hi = pd.to_numeric(piv[1.02], errors="coerce").fillna(0).to_numpy(float)
    ax.barh(ypos, lo, height=0.62, color=C_WATER, alpha=0.85,
            label="阈值 ×0.98（收紧）")
    ax.barh(ypos, hi, height=0.62, color="#c53030", alpha=0.85,
            label="阈值 ×1.02（放松）")
    ax.axvline(0, color="#2d3748", lw=0.8)
    ax.set_yticks(ypos)
    ax.set_yticklabels([short_of(str(x)) for x in piv.index], fontsize=6.6)
    ax.set_xlabel("该约束首失效容量的位移（MW）")
    ax.set_title("(a) D-HA：各约束首失效位置的阈值弹性", loc="left")
    ax.legend(loc="lower right", fontsize=6.4)
    ax.grid(axis="x", color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)

    # (b) 全约束同时扰动的 CAWCC 区间（这才是 CAWCC位移_MW 的正确用法）
    ax = axes[1]
    for k, (domain, color, nominal) in enumerate(
            (("ha", C_HA, base_cawcc), ("co", C_CO, base_co))):
        sub = df[df["域"] == domain]
        vals = pd.to_numeric(sub["扰动后CAWCC_MW"], errors="coerce").dropna().to_numpy(float)
        if vals.size == 0:
            continue
        ax.barh(k, vals.max() - vals.min(), left=vals.min(), height=0.40,
                color=color, alpha=0.40)
        ax.plot([vals.min(), vals.max()], [k, k], color=color, lw=1.6)
        ax.plot(nominal, k, marker="D", ms=5, color="#9b2c2c", zorder=5)
        ax.text(vals.max() + 30, k + 0.26,
                f"{vals.min():.0f}–{vals.max():.0f} MW（跨度 {vals.max()-vals.min():.0f}）",
                va="center", fontsize=6.5, color="#2d3748")
    ax.set_yticks([0, 1])
    ax.set_yticklabels([DOMAIN_NAME["ha"], DOMAIN_NAME["co"]], fontsize=7.2)
    ax.set_xlabel("扰动后 CAWCC（MW）")
    ax.set_xlim(900, 1780)
    ax.set_title("(b) 全约束同时扰动 ±2% 的容量区间", loc="left")
    ax.plot([], [], marker="D", ls="none", color="#9b2c2c", label="未扰动标称值")
    ax.legend(loc="lower right", fontsize=6.4)
    ax.grid(axis="x", color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)

    fig.suptitle("阈值不确定性：±2% 的阈值误差可使 D-HA 容量移动 250 MW，"
                 "远大于本文主张的 100 MW 效应", fontsize=9.2)
    fig.text(0.01, 0.02,
             "(a) 逐约束扰动下该约束首失效位置的位移；(b) 全部非零容忍约束同时 ×0.98–×1.02 "
             "时的 CAWCC 区间（零容忍约束及向上越界的约束不扰动）。",
             fontsize=6.3, color="#4a5568")
    fig.subplots_adjust(wspace=0.32, left=0.155, right=0.985, top=0.79, bottom=0.21)
    return save(fig, "FigS3_threshold_perturbation")


# ---------------------------------------------------------------- F-A4
def fig_a4() -> list[Path]:
    """文献基准对标：各冷却技术的 WUE 与已披露/行业基准区间对照。

    数据是 7 种冷却技术 × 14 个对标主体，只含 WUE 一个指标，因此按
    "每个对标主体一个面板行、技术用颜色区分"来画，而不是按指标分面。
    """
    df = pd.read_csv(R2 / "literature_benchmark.csv", encoding="utf-8-sig")
    df = df[df["对标区间低"].notna() & df["模型值"].notna()].copy()
    if df.empty:
        fig, ax = plt.subplots(figsize=(5, 2))
        ax.text(0.5, 0.5, "literature_benchmark.csv 无可用对标行", ha="center")
        return save(fig, "FigS4_literature_benchmark")

    # 只看技术对象（排除"容量 xxx MW"这类重复切片）
    techs = [t for t in df["模型对象"].unique() if not str(t).startswith("容量")]
    df = df[df["模型对象"].isin(techs)]
    subjects = df.drop_duplicates("对标主体")[["对标主体", "对标区间低", "对标区间高"]]
    subjects = subjects.sort_values("对标区间低").reset_index(drop=True)
    order = subjects["对标主体"].tolist()

    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    cmap = plt.get_cmap("tab10")
    ypos = np.arange(len(order))
    # 文献/行业区间：横向灰条
    for i, (_, row) in enumerate(subjects.iterrows()):
        lo, hi = float(row["对标区间低"]), float(row["对标区间高"])
        if lo == hi:
            lo, hi = lo * 0.94, hi * 1.06 if hi > 0 else 0.06
        ax.plot([lo, hi], [i, i], color="#cbd5e0", lw=5,
                solid_capstyle="round", zorder=1)
    # 模型值：每个技术一个颜色
    for k, tech in enumerate(techs):
        sub = df[df["模型对象"] == tech]
        xs, ys = [], []
        for _, row in sub.iterrows():
            if row["对标主体"] in order:
                xs.append(float(row["模型值"]))
                ys.append(order.index(row["对标主体"]))
        ax.scatter(xs, ys, s=22, color=cmap(k % 10), zorder=4,
                   edgecolor="white", linewidth=0.4, label=str(tech))

    ax.set_yticks(ypos)
    ax.set_yticklabels(order, fontsize=6.8)
    ax.set_xlabel("站点 WUE（L/kWh$_{IT}$）")
    ax.set_xlim(-0.08, max(subjects["对标区间高"].astype(float).max() * 1.05, 1.0))
    ax.set_title("模型各冷却技术的 WUE 相对已披露值与行业基准区间的位置", loc="left")
    ax.legend(loc="lower right", fontsize=5.9, ncol=2, title="模型冷却技术",
              title_fontsize=6.2)
    ax.grid(axis="x", color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)
    n_in = int(df["判定"].eq("在区间内").sum())
    fig.text(0.01, 0.015,
             f"灰条为对标区间（同一主体有多个披露值时显示为跨年包络）；"
             f"{len(techs)} 种技术 × {len(order)} 个主体 = {len(df)} 个对标组合，"
             f"其中判定「在区间内」{n_in} 个。",
             fontsize=6.2, color="#4a5568")
    fig.subplots_adjust(left=0.175, right=0.985, top=0.94, bottom=0.145)
    return save(fig, "FigS4_literature_benchmark")


# ---------------------------------------------------------------- F-A5
def fig_a5() -> list[Path]:
    """参数包络：模型取值相对文献观测区间的覆盖情况。

    参数跨 5 个数量级（0.03 → 165），单一数值轴无论线性或对数都会挤成一团。
    做法：每行把该参数自己的观测区间画成灰条（横跨固定视觉宽度），模型值按
    "在区间内的相对位置"落点；越界者落在条外，并用颜色区分。横轴因此是
    无量纲的相对位置，不是参数值本身；右侧附上真实数值与原区间。
    """
    df = pd.read_csv(R2 / "parameter_envelope_R7.csv", encoding="utf-8-sig")
    df = df[df["观测下界"].notna() & df["观测上界"].notna()].copy()
    df = df.drop_duplicates(subset=["参数路径", "锚点编号"])
    df["lo"] = pd.to_numeric(df["观测下界"], errors="coerce")
    df["hi"] = pd.to_numeric(df["观测上界"], errors="coerce")
    df["val"] = pd.to_numeric(df["模型取值"], errors="coerce")
    df = df[df["lo"].notna() & df["hi"].notna() & df["val"].notna()].copy()

    span = (df["hi"] - df["lo"]).replace(0, np.nan)
    pos = (df["val"] - df["lo"]) / span
    degenerate = span.isna()
    pos[degenerate] = 1.0  # 退化区间：命中即视为位于上界
    df["pos"] = pos.fillna(0.5).clip(-0.55, 1.55)
    df["越界方向"] = np.select(
        [df["pos"] < 0, df["pos"] > 1], ["低于下界", "高于上界"], default="区间内")
    df = df.sort_values(["pos", "val"]).reset_index(drop=True)

    status_color = {"区间内": "#2c7a7b", "低于下界": "#2b6cb0", "高于上界": "#c53030"}
    fig, ax = plt.subplots(figsize=(7.8, max(2.5, 0.34 * len(df))))
    ypos = np.arange(len(df))
    for i, row in df.iterrows():
        ax.plot([0, 1], [i, i], color="#cbd5e0", lw=7, solid_capstyle="round", zorder=1)
        color = status_color[row["越界方向"]]
        ax.plot(row["pos"], i, marker="o", ms=5.2, color=color,
                markeredgecolor="white", markeredgewidth=0.5, zorder=4)
        ax.text(1.62, i,
                f"{row['val']:.4g}  [ {row['lo']:.4g} , {row['hi']:.4g} ]",
                va="center", ha="left", fontsize=5.9, color="#4a5568",
                family="DejaVu Sans")
    ax.axvline(0, color="#2d3748", lw=1.0)
    ax.axvline(1, color="#2d3748", lw=1.0)
    ax.set_yticks(ypos)
    ax.set_yticklabels([str(x)[:28] for x in df["锚点名"]], fontsize=6.2)
    ax.set_xlim(-0.62, 2.35)
    ax.set_ylim(-0.7, len(df) - 0.3)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["下界", "0.25", "0.5", "0.75", "上界"])
    ax.set_xlabel("模型取值在各自文献观测区间内的相对位置（灰条 = [下界, 上界]）")
    ax.set_title("关键参数相对文献观测包络的位置", loc="left")
    for key, color in status_color.items():
        ax.plot([], [], marker="o", ls="none", ms=5.2, color=color,
                markeredgecolor="white", markeredgewidth=0.5, label=key)
    ax.legend(loc="lower right", fontsize=6.2, ncol=1)
    ax.grid(axis="x", color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)
    n_out = int((df["越界方向"] != "区间内").sum())
    fig.text(0.008, 0.012,
             f"{len(df)} 个有文献锚点的参数；右侧文字为「模型取值 [观测下界, 观测上界]」。"
             f"越界 {n_out} 个。注意各参数量纲不同，横轴只表示相对位置，不可横向比较大小。",
             fontsize=6.1, color="#4a5568")
    fig.subplots_adjust(left=0.255, right=0.985, top=0.935, bottom=0.135)
    return save(fig, "FigS5_parameter_envelope")


# ---------------------------------------------------------------- F-A6
def fig_a6() -> list[Path]:
    """帕累托前沿：投资—增益平面，显式标出有效集（补 Fig4 图注承诺）。

    要点：
    - `pareto_front.csv` 的 Pareto 有效集为 {baseline, 对症干预}：
      HA 为 baseline + leakage_minus_30pct(+150)，CO 为 baseline + grid_plus_50pct(+100)。
    - baseline 投资为 0，对数轴无法容纳，因此用 symlog 横轴，零投资点落在左缘。
    - combined_upgrade 与 leakage 增益相同但投资更高，故非有效——这正是
      "冗余不是额外增益" 的图形证据。
    """
    df = pd.read_csv(R2 / "pareto_front.csv", encoding="utf-8-sig")
    df["gain"] = pd.to_numeric(df["CAWCC增益_MW"], errors="coerce")
    df["cost"] = pd.to_numeric(df["投资中值_万元"], errors="coerce").fillna(0.0)
    df["有效"] = df["Pareto有效"].astype(str).str.lower().isin(("true", "是", "1"))
    # 中文/可读标签
    label_map = {
        "baseline": "基线（零投资）",
        "leakage_minus_30pct": "降漏损 30%",
        "grid_plus_50pct": "电网接入 +50%",
        "combined_upgrade": "组合升级",
        "wtw_plus_10pct": "给水 +10%",
        "wtw_plus_20pct": "给水 +20%",
        "reuse_plus_50pct": "再生水处理 +50%",
        "reuse_plus_100pct": "再生水处理 +100%",
        "wwtw_plus_20pct": "污水厂 +20%",
    }
    df["label"] = df["干预"].map(label_map).fillna(df["干预"])

    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.1))
    for ax, domain in zip(axes, DOMAINS):
        sub = df[df["域"] == domain].sort_values("gain")
        # 非有效：先画，避免压住有效点
        ne = sub[~sub["有效"]]
        ax.scatter(ne["cost"].clip(lower=1.0), ne["gain"], s=26, color=C_OTHER,
                   alpha=0.8, edgecolor="white", linewidth=0.5, label="非有效", zorder=3)
        ok = sub[sub["有效"]]
        ax.scatter(ok["cost"].clip(lower=1.0), ok["gain"], s=62,
                   color=DOMAIN_COLOR[domain], edgecolor="#1a202c", linewidth=0.8,
                   zorder=5, label="帕累托有效")
        # 标出有效点与零增益高投资点
        for _, row in ok.iterrows():
            ax.annotate(row["label"], (max(row["cost"], 1.0), row["gain"]),
                        xytext=(6, 6), textcoords="offset points",
                        fontsize=6.2, color="#1a202c", zorder=6)
        for _, row in ne[(ne["gain"] == 0) & (ne["cost"] > 30000)].iterrows():
            ax.annotate(f"{row['label']}\n（+0 MW，投资 {row['cost']:.0f} 万元）",
                        (row["cost"], row["gain"]), xytext=(-6, 22),
                        textcoords="offset points", fontsize=5.9,
                        color="#742a2a", ha="right",
                        arrowprops=dict(arrowstyle="-", lw=0.6, color="#a0aec0"))
        ax.set_xscale("symlog", linthresh=1000.0)
        ax.set_xlim(-200, 1.2e5)
        ax.set_xticks([0, 1e3, 1e4, 1e5])
        ax.set_xticklabels(["0", r"$10^3$", r"$10^4$", r"$10^5$"], fontsize=7)
        ax.set_ylim(-14, 180)
        ax.set_xlabel("投资中值（万元，symlog 轴）")
        ax.set_ylabel("容量增益（MW）")
        ax.set_title(f"({'a' if domain == 'ha' else 'b'}) {DOMAIN_NAME[domain]}", loc="left")
        ax.legend(loc="upper left", fontsize=6.4)
        ax.grid(color="#edf2f7", lw=0.5, which="both")
        ax.set_axisbelow(True)

    fig.suptitle("干预的帕累托有效集：每个端点只有一项干预进入前沿，"
                 "与它是否对症一一对应", fontsize=9.2)
    fig.text(0.01, 0.02,
             "投资为下限–上限的中点；`local_connection_plus_50pct` 因投资数据缺失未纳入。"
             "baseline 投资为零，落在 symlog 左缘。",
             fontsize=6.3, color="#4a5568")
    fig.subplots_adjust(wspace=0.26, left=0.085, right=0.985, top=0.80, bottom=0.205)
    return save(fig, "FigS6_pareto_front")


# ---------------------------------------------------------------- F-A7
def fig_a7() -> list[Path]:
    """冷却技术的水—能权衡与"电网水强度反转"。

    这张表的核心不是"干冷省水"，而是：干冷省水的**方向**本身依赖于厂外电力
    水强度（EWIF）。现场水降到 0，但能耗惩罚 +11~15%，若电网间接水耗高到
    反转阈值（15.5–36.3 L/kWh）以上，全口径节水转负。三个 EWIF 档
    （项目现值 / GreenGrid 1.8 / LBNL 4.52）下节水幅度从 90% 掉到 20%。
    """
    df = pd.read_csv(R2 / "technology_load_sensitivity_R7b.csv", encoding="utf-8-sig")
    tech_col = "冷却技术"
    cap = 750.0
    sub = df[np.isclose(df["IT容量_MW"], cap)].copy()
    if sub.empty:
        sub = df[df["IT容量_MW"] == df["IT容量_MW"].max()].copy()
    order = ["evaporative", "efficient_evaporative", "liquid_to_water",
             "hybrid", "dry_first", "dry", "liquid_to_air"]
    zh = {"evaporative": "蒸发冷却", "efficient_evaporative": "高效蒸发",
          "liquid_to_water": "液冷转水冷", "hybrid": "混合冷却",
          "dry_first": "干冷优先", "dry": "全干冷", "liquid_to_air": "液冷转风冷"}

    fig, axes = plt.subplots(1, 3, figsize=(9.0, 3.0),
                            gridspec_kw={"width_ratios": [1.15, 1.0, 1.05]})

    # (a) 水 vs 能：每项技术的（耗水强度, 能耗惩罚）
    ax = axes[0]
    for domain, marker in (("D-HA", "o"), ("D-CO", "s")):
        s = sub[sub["域签"] == domain]
        ax.scatter(s["站点耗水强度_L_per_kWhIT"], s["设施能耗惩罚_相对evaporative百分比"],
                   s=42, marker=marker, alpha=0.85,
                   color=C_HA if domain == "D-HA" else C_CO,
                   edgecolor="white", linewidth=0.5,
                   label="D-HA" if domain == "D-HA" else "D-CO", zorder=3)
    ax.axhline(0, color="#2d3748", lw=0.9, ls="--")
    # 不逐点标注（会与相邻面板压字）：用技术编号 + 图例映射，避免拥挤
    for _, row in sub[sub["域签"] == "D-HA"].iterrows():
        idx = order.index(str(row[tech_col])) + 1 if str(row[tech_col]) in order else 0
        ax.annotate(f"T{idx}",
                    (float(row["站点耗水强度_L_per_kWhIT"]),
                     float(row["设施能耗惩罚_相对evaporative百分比"])),
                    xytext=(5, 4), textcoords="offset points", fontsize=6.0,
                    color="#1a202c", fontweight="bold")
    ax.set_xlabel("站点耗水强度（L/kWh$_{IT}$）")
    ax.set_ylabel("能耗惩罚（相对蒸发冷却，%）")
    ax.set_title("(a) 水—能权衡前沿（T1–T7 见 b 轴）", loc="left")
    ax.set_xlim(-0.12, 2.25)
    ax.set_ylim(-4.5, 19)
    ax.legend(loc="center right", fontsize=6.2)
    ax.grid(color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)

    # (b) 三个 EWIF 档下的全口径节水
    ax = axes[1]
    cols = [("全口径节水百分比_项目现值", "本文现值", C_WATER),
            ("全口径节水百分比_GreenGrid_1.8", "GreenGrid 1.8", C_OTHER),
            ("全口径节水百分比_LBNL_4.52", "LBNL 4.52", C_GRID)]
    s = sub[sub["域签"] == "D-HA"].set_index(tech_col).reindex(order)
    x = np.arange(len(order))
    w = 0.26
    for k, (col, lab, color) in enumerate(cols):
        vals = pd.to_numeric(s[col], errors="coerce").to_numpy(float)
        ax.bar(x + (k - 1) * w, vals, width=w, color=color, alpha=0.88, label=lab)
    ax.set_xticks(x)
    ax.set_xticklabels([f"T{k+1} {zh.get(t, t)}" for k, t in enumerate(order)],
                       rotation=38, ha="right", fontsize=6.1)
    ax.axhline(0, color="#2d3748", lw=0.8)
    ax.set_ylabel("全口径节水（%）")
    ax.set_title("(b) 节水幅度取决于 EWIF", loc="left")
    ax.set_ylim(0, 118)
    ax.legend(loc="upper center", fontsize=5.9, ncol=3,
              title="厂外电力水强度 L/kWh", title_fontsize=5.9)
    ax.grid(axis="y", color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)

    # (c) 反转阈值：干冷类技术的 EWIF 临界点 vs 文献范围
    ax = axes[2]
    dry_rows = sub[(sub["域签"] == "D-HA") &
                   pd.to_numeric(sub["反转阈值EWIF_L_per_kWh"], errors="coerce").notna()]
    dry_rows = dry_rows.set_index(tech_col).reindex(
        [t for t in order if t in dry_rows[tech_col].values])
    ypos = np.arange(len(dry_rows))
    vals = pd.to_numeric(dry_rows["反转阈值EWIF_L_per_kWh"], errors="coerce")
    ax.barh(ypos, vals, color=C_WATER, alpha=0.85, height=0.55)
    for i, v in enumerate(vals):
        if pd.notna(v):
            ax.text(v + 0.8, i, f"{v:.1f}", va="center", fontsize=6.4)
    # 文献 EWIF 区间
    ax.axvspan(1.8, 4.52, color="#f6ad55", alpha=0.30, zorder=0,
               label="已披露 EWIF 区间 1.8–4.52")
    ax.set_yticks(ypos)
    ax.set_yticklabels([zh.get(str(t), str(t)) for t in dry_rows.index], fontsize=6.3)
    ax.set_xlabel("EWIF 反转阈值（L/kWh）")
    ax.set_title("(c) 节水转负的临界 EWIF", loc="left")
    ax.set_xlim(0, max(40, float(vals.max()) * 1.15))
    ax.set_ylim(-0.75, len(dry_rows) - 0.1)
    ax.legend(loc="upper right", fontsize=5.9)
    ax.grid(axis="x", color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)

    fig.suptitle("冷却技术的水—能权衡：干冷把现场水降到零，但能耗惩罚使节水方向依赖电网间接水强度",
                 fontsize=8.9)
    fig.text(0.01, 0.02,
             f"取 IT 容量 {cap:.0f} MW 切片（两种容量下结论同向）。(c) 为 D-HA；"
             "反转阈值指全口径节水由正转负所需的厂外电力水强度，均高于已披露区间上限 4.52。",
             fontsize=6.2, color="#4a5568")
    fig.subplots_adjust(wspace=0.34, left=0.065, right=0.985, top=0.79, bottom=0.235)
    return save(fig, "FigS7_technology_tradeoff")


# ---------------------------------------------------------------- F-A8
def fig_a8() -> list[Path]:
    """水量闭合诊断。

    ⚠ 必须读 `相对闭合误差_科学计数` 列：`相对闭合误差_pct` 列因
    round(...,9) 已被压平成全 0（这正是 B0 第 53 轮加的修复），用它画图会
    得到空图。故本图横轴为 log10(相对误差)，量级 1e-16 ~ 1e-13 %。
    """
    df = pd.read_csv(R2 / "water_balance_closure.csv", encoding="utf-8-sig")
    rel = "相对闭合误差_科学计数"
    absmax = "最大绝对残差_科学计数"
    for col in (rel, absmax):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df[df[rel] > 0].copy()
    if df.empty:
        raise ValueError("闭合诊断无正值残差，无法作图")

    IDENT_ZH = {
        "dStorage == inflow - outflow - loss": "储量平衡",
        "delivered == potable + reuse + other": "交付平衡",
    }
    df["恒等式简称"] = df["恒等式"].map(IDENT_ZH).fillna(df["恒等式"])

    fig, axes = plt.subplots(1, 2, figsize=(8.2, 2.8))

    # (a) 两种恒等式 × 两域 的误差量级条带（钉线图）
    ax = axes[0]
    groups = []
    for ident in df["恒等式简称"].drop_duplicates():
        for domain in DOMAINS:
            s = df[(df["恒等式简称"] == ident) & (df["域"] == domain)][rel]
            if len(s):
                groups.append((ident, domain, float(s.min()), float(s.median()),
                               float(s.max()), len(s)))
    ypos = np.arange(len(groups))
    for i, (ident, domain, lo, med, hi, n) in enumerate(groups):
        color = C_HA if domain == "ha" else C_CO
        ax.plot([np.log10(lo), np.log10(hi)], [i, i], color=color, lw=5,
                solid_capstyle="round", alpha=0.55, zorder=2)
        ax.plot(np.log10(med), i, marker="|", ms=11, mew=2.0, color=color, zorder=4)
        ax.text(np.log10(hi) + 0.18, i, f"max {hi:.2e}%（n={n}）",
                va="center", fontsize=6.1, color="#4a5568")
    ax.set_yticks(ypos)
    ax.set_yticklabels([f"{g[0]}\n{'D-HA' if g[1] == 'ha' else 'D-CO'}" for g in groups],
                       fontsize=6.5)
    ax.axvline(np.log10(5.0), color="#c53030", lw=1.2, ls="--", zorder=1)
    ax.text(np.log10(5.0), len(groups) - 0.35, " 验收线 5%", fontsize=6.2,
            color="#c53030", va="top")
    ax.set_xlabel("log$_{10}$(相对闭合误差 %)")
    ax.set_title("(a) 两类恒等式的误差量级", loc="left")
    ax.grid(axis="x", color="#edf2f7", lw=0.5)
    ax.set_axisbelow(True)
    ax.set_ylim(-0.7, len(groups) - 0.1)

    # (b) 误差异质性：按容量点的分布（说明不是个别点侥幸）
    ax = axes[1]
    for domain, color in (("ha", C_HA), ("co", C_CO)):
        s = df[(df["域"] == domain) & (df["恒等式简称"] == "储量平衡")].copy()
        s["cap"] = pd.to_numeric(s["容量点"].str.replace("cap_", "", regex=False),
                                 errors="coerce")
        s = s.sort_values("cap")
        ax.plot(s["cap"], s[rel], marker="o", ms=3.0, lw=0.9, color=color,
                label=f"D-{'HA' if domain=='ha' else 'CO'} 储量平衡")
    ax.set_yscale("log")
    ax.axhline(5.0, color="#c53030", lw=1.0, ls="--", label="验收线 5%")
    ax.set_xlabel("容量点（MW）")
    ax.set_ylabel("相对闭合误差（%）")
    ax.set_title("(b) 沿容量轴的稳定性", loc="left")
    ax.legend(loc="center right", fontsize=5.9)
    ax.grid(color="#edf2f7", lw=0.5, which="both")
    ax.set_axisbelow(True)

    fig.suptitle("数值自洽性：水量闭合残差在 $10^{-13}$% 量级，比 5% 验收线低 14 个数量级",
                 fontsize=9.0)
    fig.text(0.01, 0.02,
             "注意：溶质闭合残差为记账恒等式，其为零不构成盐分守恒的物理验证，"
             "详见主稿关于该约定的声明。",
             fontsize=6.3, color="#4a5568")
    fig.subplots_adjust(wspace=0.38, left=0.115, right=0.985, top=0.79, bottom=0.215)
    return save(fig, "FigS8_closure_diagnostics")


def main() -> None:
    builders = [("F-A1", fig_a1), ("F-A2", fig_a2), ("F-A3", fig_a3),
                ("F-A4", fig_a4), ("F-A5", fig_a5), ("F-A6", fig_a6),
                ("F-A7", fig_a7), ("F-A8", fig_a8)]
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
            fail.append((tag, str(exc)))
    print(f"\n完成 {len(ok)}/{len(builders)}；失败 {fail}")


if __name__ == "__main__":
    main()
