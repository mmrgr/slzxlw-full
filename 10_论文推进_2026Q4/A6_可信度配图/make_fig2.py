"""Fig.2 — 模型可信度: 水化学参数域(T6) + 设施锚定(T7)
 A  真实再生水的 CoC_lim(phi) 曲线与质量临界掺混比 f*
 B  chi_eff = min(CoC_lim, CoC_design)/CoC_design: 全组分 vs 仅 TDS/Cl, 标注限值物种
 C  源报告水量账的算术自洽 (M/E = CoC/(CoC-1)) —— 非对冷却物理的独立验证
 D  Meta 有效披露 70 设施-年 WUE 分布 vs 模型园区等效值 (scope 声明)

列名口径（2026-10-14 图形修复轮）：本图曾按 **T6 v1** 的列名（`f_star` / `chi_full` /
`chi_2indicator` / `limiting_species_full` / `source`）读取 `T6_coc_limits.csv`，而该文件已在
审计修复轮被 **T6 v2** 覆写（列名 `f_star_2ind` / `chi_eff_all_ratio` / `chi_eff_conservative` /
`who_all` / `sample`），导致本脚本自 11:19 起 `AttributeError` 崩溃、成品图停留在 v2 之前。
现按 v2 列名重接；数值口径一律以 `T6_summary.json` / `T7_summary.json` 为准。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))          # 使 figstyle 可导入 (E-7 唯一实现)
from figstyle import apply_style_grid  # noqa: E402

apply_style_grid()                            # 样式: 变体 B (带网格), 与抽取前逐字等价

A4 = HERE.parent / "A4_水化学参数域"
A5 = HERE.parent / "A5_设施锚定"

smp = pd.read_csv(A4 / "T6_water_chemistry_samples.csv")
coc = pd.read_csv(A4 / "T6_coc_limits.csv")
gsa = pd.read_csv(A5 / "T7_gsa_anchoring.csv")
wue = pd.read_csv(A5 / "T7_meta_wue.csv")

LIM = {"TDS": 2200.0, "chloride": 500.0, "hardness": 700.0,
       "alkalinity": 500.0, "silica": 150.0}
POT = {"TDS": 180.0, "chloride": 35.0}
COC_D = 5.0

fig, ax = plt.subplots(2, 2, figsize=(11.2, 7.4))

# ---- A: CoC_lim(phi) ----
phi = np.linspace(0, 1, 400)
styles = {"IEUA RP-1 (2025, tertiary)": ("#2471a3", "-"),
          "Figshare RW (2025, paired study)": ("#c0392b", "-"),
          "AI-UWM model assumption": ("#148f77", "--")}
for _, r in smp.iterrows():
    if r.source not in styles:
        continue
    c, ls = styles[r.source]
    if not np.isfinite(r.TDS) or not np.isfinite(r.chloride):
        continue
    tds = POT["TDS"] + phi * (r.TDS - POT["TDS"])
    cl = POT["chloride"] + phi * (r.chloride - POT["chloride"])
    cl_lim = np.minimum(LIM["TDS"] / tds, LIM["chloride"] / cl)
    ax[0, 0].plot(phi, cl_lim, color=c, ls=ls, lw=2.1, label=r.source)
ax[0, 0].axhline(COC_D, color="k", lw=1.0, ls=":")
ax[0, 0].text(0.02, COC_D + .25, r"design $\mathrm{CoC}=5$", fontsize=7.5)
for _, r in coc.iterrows():
    if pd.notna(r.f_star_2ind) and r.f_star_2ind < 1:
        ax[0, 0].plot([r.f_star_2ind], [COC_D], "v",
                      color="#c0392b" if "Figshare" in r["sample"] else "#2471a3", ms=7)
ax[0, 0].set_xlabel(r"reclaimed blend fraction $\varphi$")
ax[0, 0].set_ylabel(r"attainable $\mathrm{CoC}_{\lim}$")
ax[0, 0].set_ylim(0, 16)
ax[0, 0].set_title("A  Real reclaimed water lowers attainable CoC", loc="left", fontsize=9.5)
ax[0, 0].legend(fontsize=6.8, loc="upper right")

# ---- B: chi_eff bar (v2 列: chi_eff_all_ratio = 全组分; chi_eff_conservative = 仅 TDS/Cl) ----
o = coc.sort_values("chi_eff_all_ratio")
y = np.arange(len(o))
ax[0, 1].barh(y - .2, o.chi_eff_all_ratio, height=.38, color="#2471a3",
              label="all species (composition ratios)")
ax[0, 1].barh(y + .2, o.chi_eff_conservative, height=.38, color="#e67e22",
              label="TDS/Cl only")
ax[0, 1].axvline(1.0, color="k", lw=1.0, ls=":")
for i, r in enumerate(o.itertuples()):
    ax[0, 1].text(max(r.chi_eff_all_ratio, r.chi_eff_conservative) * 1.15, i,
                  f"{r.who_all}", fontsize=6.6, va="center", color="#444")
ax[0, 1].set_yticks(y)
ax[0, 1].set_yticklabels([s.split(" (")[0] for s in o["sample"]], fontsize=7)
ax[0, 1].set_xscale("log")
ax[0, 1].set_xlabel(r"$\chi=\mathrm{CoC}_{\lim}/\mathrm{CoC}_{design}$  (log)")
ax[0, 1].set_title(r"B  Limiting species is often not TDS", loc="left", fontsize=9.5)
ax[0, 1].legend(fontsize=7, loc="lower right")

# ---- C: GSA 水量账算术自洽 (降级后口径; 数值取自 T7_summary.json) ----
t7 = json.loads((A5 / "T7_summary.json").read_text(encoding="utf-8"))
mae = t7["gsa_accounting_selfconsistent_MAE"]
coc_eff = t7["model_reference"]["CoC_effective_by_water_balance"]
cc = np.linspace(1.2, 6, 200)
ax[1, 0].plot(cc, cc / (cc - 1), color="k", lw=1.4, label=r"$M/E=\mathrm{CoC}/(\mathrm{CoC}-1)$")
for _, r in gsa.iterrows():
    ax[1, 0].plot(r.coc_water_balance, r.M_over_E, "o", ms=9, mfc="none",
                  mec="#c0392b", mew=1.8)
ax[1, 0].plot([], [], "o", ms=8, mfc="none", mec="#c0392b", mew=1.8,
              label="GSA courthouse tower, as reported")
# 设计点 (CoC=5) 必须落在恒等曲线上; 旧版标在 (5.0, 1.225) 而 1.225 实际对应有效 CoC=5.444 (口径差 8.16%)
ax[1, 0].plot([5.0], [5.0 / (5.0 - 1.0)], "s", color="#2471a3", ms=7,
              label="AI-UWM design (CoC = 5)")
ax[1, 0].plot([coc_eff], [coc_eff / (coc_eff - 1)], "^", color="#148f77", ms=7,
              label=f"AI-UWM effective CoC = {coc_eff:.2f}")
ax[1, 0].set_xlabel(r"reported $\mathrm{CoC}$ (water balance)")
ax[1, 0].set_ylabel(r"reported $M/E$")
ax[1, 0].set_title(f"C  Source-report water balance is arithmetically\n"
                   f"     self-consistent (MAE {mae:.4f}); not an independent test",
                   loc="left", fontsize=9.5)
ax[1, 0].legend(fontsize=7)

# ---- D: WUE (口径对齐后; 数值取自 T7_summary.json 的 meta_disclosure) ----
md = t7["meta_disclosure"]
med = md["disclosure_park_wue_q1_median_q3"][1]
m_park = md["model_park_equivalent_wue_l_per_kwh"]
ratio = md["ratio_of_park_equivalents"]
w = wue.loc[~wue.excluded, "wue_park_l_per_kwh"].clip(lower=1e-3)
ax[1, 1].hist(np.log10(w), bins=28, color="#7d3c98", alpha=.75)
ax[1, 1].axvline(np.log10(med), color="#c0392b", lw=2,
                 label=f"Meta fleet median (n={len(w)}) {med:.3f} L/kWh")
ax[1, 1].axvline(np.log10(m_park), color="#148f77", lw=2.4, ls="--",
                 label=f"AI-UWM park-equivalent {m_park:.3f} L/kWh  ({ratio:.1f}$\\times$)")
ax[1, 1].set_xlabel(r"$\log_{10}$ park WUE  (L/kWh)")
ax[1, 1].set_ylabel("facility-years")
ax[1, 1].set_title("D  Model represents a wet-cooling design (scope)", loc="left", fontsize=9.5)
ax[1, 1].legend(fontsize=7)

fig.suptitle("T6/T7 — Model credibility: water-chemistry parameter domain and independent facility anchoring",
             fontsize=11.5, y=1.0, x=.01, ha="left")
fig.tight_layout()
fig.savefig(HERE / "fig2_credibility.png", dpi=210, bbox_inches="tight")
print("[ok]", HERE / "fig2_credibility.png")
