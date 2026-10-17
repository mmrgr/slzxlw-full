# -*- coding: utf-8 -*-
"""Fig 3 | 城市级结果与符号结构: dS_pot 分布、q 分组、q>0 组有害=0。

科学问题: 城市净取水量 dS_pot 的符号结构是什么? 谁能预测这个符号?
结论: 839 个可靠情景严格符号为 626 负 / 177 正 / 36 零; q 分组 263/288/288;
      **q>0 组 263/263 全部有益 (有害 = 0)**, 即 q>0 是受益的充分条件。

数据: A13_可靠性机制/supply_state_regimes.csv (n_eff=839, 双门禁),
      A33_WP4_组成重构/wp4_results.csv (n_eff=47, 完整物种城市级),
      A13_可靠性机制/COLUMN_NAMES_CORRECTED.md (列名互换更正)。
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

import figstyle_a37 as F

F.apply_nw_style()

r = F.load_regimes()
w = F.load_wp4()
wrel = w[w["reliable"].astype(bool)]
sc = F.sign_counts(r["dS_pot_ml"])
qg = F.q_groups(r["q"])

fig = plt.figure(figsize=(7.2, 4.3))
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.0], hspace=0.62, wspace=0.30)

# ------------------------------------------------- (a) dS_pot 分布 (对称对数横轴)
ax = fig.add_subplot(gs[0, :])
d = r["dS_pot_ml"].to_numpy()
neg = d[d < 0]; pos = d[d > 0]; zero = d[d == 0]
bins = np.concatenate([-np.logspace(np.log10(max(1e-9, abs(neg).min())), np.log10(abs(neg).max()), 26)[::-1],
                       [0],
                       np.logspace(np.log10(max(1e-9, abs(pos).min())), np.log10(abs(pos).max()), 26)])
ax.hist(neg, bins=bins, color=F.C_BENEFIT, edgecolor="white", linewidth=0.25,
        label=f"beneficial  $\\Delta S_{{\\rm pot}}<0$  (n={sc['neg']})")
ax.hist(pos, bins=bins, color=F.C_HARMFUL, edgecolor="white", linewidth=0.25,
        label=f"harmful  $\\Delta S_{{\\rm pot}}>0$  (n={sc['pos']})")
ax.axvline(0, color="#2d3748", lw=0.9)
# 36 个解析零点: 单独画一根位于 0 处的柱, 避免被对数轴吞掉
ymax = ax.get_ylim()[1]
ax.bar([0], [sc["zero"]], width=180, color=F.C_ZERO, edgecolor="#2d3748",
       linewidth=0.6, label=f"exact zero  $\\Delta S_{{\\rm pot}}=0$  (n={sc['zero']})")
ax.set_ylim(0, ymax)
ax.annotate(f"{sc['zero']} exact analytic zeros ($q=0$ branch)\nkept in the partition, not dropped",
            xy=(120, sc["zero"]), xytext=(900, ymax * 0.55),
            fontsize=6.0, color="#4a5568", va="center",
            arrowprops=dict(arrowstyle="->", lw=0.6, color="#4a5568"))
ax.set_xscale("symlog", linthresh=100)
ax.set_xlabel(r"$\Delta S_{\rm pot}$ (ML per scenario)", fontsize=7)
ax.set_ylabel("scenarios", fontsize=7)
ax.set_title("a  Distribution of city-level net abstraction change", fontsize=7.4, loc="left")
ax.legend(fontsize=6.0, loc="upper left", handlelength=1.1, borderpad=0.25, labelspacing=0.35)
ax.set_xlim(-8e4, 1.1e5)
F.panel_label(ax, "", dx=0, dy=0)

# ------------------------------------------------- (b) 符号结构与 q 分组
ax = fig.add_subplot(gs[1, 0])
bars = [(f"$\\Delta S<0$\nbeneficial", sc["neg"], F.C_BENEFIT),
        (f"$\\Delta S>0$\nharmful", sc["pos"], F.C_HARMFUL),
        (f"$\\Delta S=0$\nzero", sc["zero"], F.C_ZERO)]
xs = np.arange(3)
ax.bar(xs, [b[1] for b in bars], color=[b[2] for b in bars],
       edgecolor="#2d3748", linewidth=0.6, width=0.6)
for i, b in enumerate(bars):
    ax.text(i, b[1] + 12, str(b[1]), ha="center", fontsize=6.8, fontweight="bold")
ax.set_xticks(xs); ax.set_xticklabels([b[0] for b in bars], fontsize=6.4)
ax.set_ylabel("scenarios", fontsize=7); ax.set_ylim(0, 760)
ax.set_title("b  Strict-sign partition ($n_{\\rm eff}$=839)", fontsize=7.4, loc="left")
F.panel_label(ax, "", dx=0, dy=0)

# ------------------------------------------------- (c) q 分组 + q>0 组有害=0
ax = fig.add_subplot(gs[1, 1])
sub = [("$q>0$", qg["pos"]), ("$q=0$", qg["zero"]), ("$q<0$", qg["neg"])]
xs = np.arange(3)
ax.bar(xs, [s[1] for s in sub], color=[F.C_PRIMARY, F.C_ZERO, "#718096"],
       edgecolor="#2d3748", linewidth=0.6, width=0.6)
for i, s in enumerate(sub):
    ax.text(i, s[1] + 8, str(s[1]), ha="center", fontsize=6.8, fontweight="bold")
ax.set_xticks(xs); ax.set_xticklabels([s[0] for s in sub], fontsize=6.8)
ax.set_ylabel("scenarios", fontsize=7); ax.set_ylim(0, 400)
ax.set_title(r"c  $q$ partition ($q=(M_0-M_1)/M_1$)", fontsize=7.4, loc="left")
qpos = r[r["q"] > 0]
nharm = int((qpos["dS_pot_ml"] > 0).sum())
ax.annotate(f"$q>0$: harmful = {nharm} / {len(qpos)}\n$\\Rightarrow$ benefit is a\nsufficient condition",
            xy=(0.20, qg["pos"] * 0.72), xytext=(0.72, 232), fontsize=6.1, color=F.C_BENEFIT,
            arrowprops=dict(arrowstyle="->", lw=0.6, color=F.C_BENEFIT))
F.panel_label(ax, "", dx=0, dy=0)

_N_ALL, _N_REL = 1052, 839  # 由 provenance 审计门禁核对

def compute():
    """从主网格实时计算图注所需的全部统计量。"""
    _d = pd.read_csv(Path(__file__).resolve().parent.parent / "A13_可靠性机制"
                     / "supply_state_regimes.csv")
    _rel = _d[(_d.status == "converged_unique") &
              (~_d.coc_floor_degenerate.astype(bool))].copy()
    _q = (_rel.M0_ml - _rel.M1_ml) / _rel.M1_ml
    _ds = _rel.dS_pot_ml
    return {
        "n_all": len(_d), "n_rel": len(_rel), "n_excl": len(_d) - len(_rel),
        "neg": int((_ds < 0).sum()), "pos": int((_ds > 0).sum()),
        "zero": int((_ds == 0).sum()),
        "q_pos": int((_q > 1e-9).sum()), "q_zero": int((_q.abs() <= 1e-9).sum()),
        "q_neg": int((_q < -1e-9).sum()),
        "q_pos_harm": int(((_q > 1e-9) & (_ds > 0)).sum()),
        "min_dS": float(_ds.min()), "max_dS": float(_ds.max()),
    }


F.provenance(
    fig,
    "Data: A13_Reliability/supply_state_regimes.csv (a-c); column-name swap corrected per "
    "COLUMN_NAMES_CORRECTED.md; q computed as (M0-M1)/M1.",
    f"n_eff = {_N_REL} of {_N_ALL} grid rows after the dual gate (status=converged_unique AND NOT "
    f"coc_floor_degenerate); {_N_ALL - _N_REL} excluded. ZERO CONVENTION: strict sign, dS_pot == 0.0 counted "
    "separately (a tolerance band of 1e-9 gives the older 631/102 split and must NOT be used).",
    "LIMITATION: the q>0 sufficiency check has no positive counterexample (0/263 harmful) because "
    "q>0 is algebraically tied to the same identity; it is an accounting consistency check, not an "
    "independent predictive test. City-level complete-species subset is only n_eff=47.",
)
F.save(fig, "Fig3_city_results_signs")
print("Fig3 done")


# ---------------------------------------------------------------
# 图注自动生成 (2026-10-17): 防止手工维护导致数字脱节
# ---------------------------------------------------------------
from caption_util import write_caption

_c = compute()
write_caption(
    3,
    title="City-level outcomes and the sign structure of $dS_{\\rm pot}$",
    sections={
        "Summary": (
            f"Across the {_c['n_rel']} solver-reliable grid scenarios, the strict-sign partition "
            f"of the primary estimand is **{_c['neg']} negative (beneficial) / {_c['pos']} positive "
            f"(harmful) / {_c['zero']} exactly zero** (panel **b**). Panel **c** partitions the same "
            f"scenarios by $q=(M_0-M_1)/M_1$ into **{_c['q_pos']} ($q>0$) / {_c['q_zero']} ($q=0$) / "
            f"{_c['q_neg']} ($q<0$)**; within $q>0$ the number of harmful outcomes is "
            f"**{_c['q_pos_harm']} of {_c['q_pos']}**."
        ),
        "Data and methods": (
            "All panels use `A13_可靠性机制/supply_state_regimes.csv`, the authoritative main grid. "
            "$q$ is computed as (M0_ml - M1_ml)/M1_ml; the file does not carry a $q$ column. "
            "Column names `x_ai_B1_ml` / `x_ai_B2_ml` are swapped relative to their meaning and "
            "must be read per `A13_可靠性机制/COLUMN_NAMES_CORRECTED.md`."
        ),
        "n": (
            f"$n_{{\\rm eff}}$ = **{_c['n_rel']}** of {_c['n_all']} grid rows after the dual gate "
            f"(`status == converged_unique` AND NOT `coc_floor_degenerate`); "
            f"**{_c['n_excl']} rows are excluded** ({_c['n_all']} - {_c['n_rel']}). "
            "Zero convention: strict sign, $dS_{\\rm pot}==0.0$ counted separately."
        ),
        "Zeros and range": (
            f"The {_c['zero']} zeros are not numerical noise: they are the exact analytic roots of "
            f"the identity on the $q=0$ branch (all satisfy $q=0$ with exactly zero identity "
            f"residual), and are kept as a separate class rather than discarded into a tolerance "
            f"band. Panel **a** uses a symmetric-log axis: beneficial cases extend to about "
            f"{_c['min_dS']:,.0f} ML and harmful cases to about +{_c['max_dS']:,.0f} ML."
        ),
        "Complete-species subset": (
            "City-level complete-species results are in `A33_WP4_组成重构/wp4_results.csv` "
            + r"($n_{\rm eff}=47$, all beneficial, $q$ split 23 / 24, 0 harmful)."
        ),
        "Limits": (
            "The $q>0$ sufficiency check has no positive counterexample because $q>0$ is "
            "algebraically tied to the same identity; it is an accounting consistency check, "
            "not an independent predictive test."
        ),
    },
)
