"""T15 —— 图定稿: 统一编号 + 补一张缺失的水质约束主图 (Fig.3)。

主图 (main text):
  Fig.1 传输恒等账本            A1_传输账本/fig1_transmission_identity.png
  Fig.2 分配规则与内生 γ        A3_三规则内生/fig4_rule_invariance.png
  Fig.3 水质约束 CoC 与判据差   ← 本脚本生成 A4_水化学参数域/fig3_water_quality.png
  Fig.4 水质×分配联合交互       A7_质量分配联合/fig5_quality_allocation_interaction.png
  Fig.5 条件边界曲面与敏感性    A10_敏感性与边界/fig5_conditional_boundary.png
  Fig.6 适应成本 Pareto         A11_适应成本/fig6_adaptation_pareto.png
  Fig.7 时间分辨率与关键时段失效 A12_时间分辨率/fig7_time_resolution.png

SI:
  Fig.S1 无量纲折叠 (代数化简)   A9_无量纲折叠/fig6_dimensionless_collapse.png
  Fig.S2 可信度与设施锚定        A6_可信度配图/fig2_credibility.png
  Fig.S3 分配规则响应            A2_规则实验/fig2_allocation_regime.png
  Fig.S4 内生 γ 曲线             A2_规则实验/fig3_endogenous_gamma.png

产出: 09_图定稿/ 下统一命名的副本 + figure_index.md
"""
from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
from figstyle import BLUE, GREEN, GREY, ORANGE, RED, apply_style  # noqa: E402

apply_style()                            # 样式+调色板: 统一实现, 与抽取前逐字等价

SHORT = {
    "IEUA RP-1 (2025, tertiary)": "Tertiary\nreclaimed\n(IEUA)",
    "LADWP AWPF (2012, RO product)": "RO product\n(LADWP)",
    "Figshare RW (2025, paired study)": "High-salinity\nreclaimed",
    "Figshare BW (5 g·L<sup>-1</sup>) (2025, paired study)": "Brackish\n(not RW)",
    "AI-UWM model assumption": "Engine\nplaceholder",
}


def make_fig3() -> Path:
    A4 = ROOT / "A4_水化学参数域"
    cl = pd.read_csv(A4 / "T6_coc_limits.csv", encoding="utf-8-sig")
    tiers = pd.read_csv(A4 / "T6_threshold_sensitivity.csv", encoding="utf-8-sig")

    fig = plt.figure(figsize=(12.6, 8.4))
    gs = fig.add_gridspec(2, 2, hspace=0.48, wspace=0.26,
                          left=0.085, right=0.965, top=0.925, bottom=0.09)

    # ---- A: CoC_lim by criterion ----
    axA = fig.add_subplot(gs[0, 0])
    order = ["IEUA RP-1 (2025, tertiary)", "Figshare RW (2025, paired study)",
             "AI-UWM model assumption", "LADWP AWPF (2012, RO product)"]
    sub = cl.set_index("sample").reindex(order)
    x = np.arange(len(order))
    w = 0.26
    axA.bar(x - w, sub["CoC_lim_all_ratio"], w, color=BLUE, label="composition ratios (all species)")
    axA.bar(x, sub["CoC_lim_precipitation_ratio"], w, color=ORANGE,
            label="precipitation-forming species")
    ph = sub["CoC_lim_phreeqc"].fillna(0).values
    mask = sub["CoC_lim_phreeqc"].isna().values
    axA.bar(x + w, np.where(mask, 0, ph), w, color=RED, label="PHREEQC saturation (Calcite etc.)")
    for xi, v, mk in zip(x + w, ph, mask):
        axA.text(xi, 0.4, "n/a" if mk else f"{v:.2f}", ha="center", fontsize=6.8,
                 color="#718096" if mk else RED, rotation=90)
    axA.set_xticks(x)
    axA.set_xticklabels([SHORT[o] for o in order], fontsize=6.8)
    axA.set_ylabel(r"allowable CoC  $\mathrm{CoC}_{\lim}$")
    axA.set_yscale("log")
    axA.legend(fontsize=6.8, frameon=False, loc="upper left")
    axA.set_title("A  Criterion choice dominates the water-quality penalty\n"
                  "     IEUA: ratios 3.57 vs saturation 2.52 (1.4x)",
                  fontsize=9.6, loc="left")

    # ---- B: tier sensitivity of chi_eff ----
    axB = fig.add_subplot(gs[0, 1])
    torder = ["conservative", "baseline", "permissive"]
    sel = ["IEUA RP-1 (2025, tertiary)", "Figshare RW (2025, paired study)",
           "AI-UWM model assumption"]
    cols = {"IEUA RP-1 (2025, tertiary)": BLUE,
            "Figshare RW (2025, paired study)": RED,
            "AI-UWM model assumption": ORANGE}
    for s in sel:
        d = tiers[tiers["sample"] == s].set_index("tier").reindex(torder)
        axB.plot(range(3), d.chi_eff.values, "o-", color=cols[s], lw=1.2, ms=5,
                 label=SHORT[s].replace("\n", " "))
    axB.axhline(1.0, color="#cbd5e0", lw=0.8, ls="--")
    axB.set_xticks(range(3))
    axB.set_xticklabels([t.capitalize() for t in torder], fontsize=7.6)
    axB.set_ylabel(r"effective severity  $\chi_{\rm eff}=\min(\mathrm{CoC}_{\lim},5)/5$")
    axB.legend(fontsize=6.8, frameon=False, loc="upper left")
    i = tiers[tiers["sample"] == "IEUA RP-1 (2025, tertiary)"]
    span = i.chi_eff.max() / i.chi_eff.min()
    axB.set_title(f"B  Threshold tier moves $\\chi$ by {span:.2f}x (not 200x)\n"
                  "     declared as placeholder limits, tiered as a hedge",
                  fontsize=9.6, loc="left")

    # ---- C: f* vs criteria ----
    axC = fig.add_subplot(gs[1, 0])
    axC.scatter(sub["chi_eff_all_ratio"], sub["f_star_2ind"], s=80, c=BLUE,
                label="composition ratios", zorder=3)
    axC.scatter(sub["chi_eff_phreeqc"], sub["f_star_2ind"], s=80, c=RED, marker="s",
                label="PHREEQC saturation", zorder=3)
    for o in order:
        if o in sub.index and pd.notna(sub.loc[o, "f_star_2ind"]):
            axC.annotate(SHORT[o].replace("\n", " "),
                         (sub.loc[o, "chi_eff_all_ratio"], sub.loc[o, "f_star_2ind"]),
                         fontsize=6.6, xytext=(5, -8), textcoords="offset points")
    axC.set_xlabel(r"severity  $\chi$")
    axC.set_ylabel(r"mass-critical blend  $f^\ast$")
    axC.set_xlim(0, 1.08)
    axC.legend(fontsize=6.8, frameon=False, loc="upper left")
    axC.set_title(r"C  $f^\ast$ collapses onto $\chi$ across sources and criteria",
                  fontsize=9.6, loc="left")

    # ---- D: completeness / charge balance ----
    axD = fig.add_subplot(gs[1, 1])
    d = cl.set_index("sample").reindex(order)
    yy = np.arange(len(order))
    axD.barh(yy, d["n_present"].fillna(0), height=0.42, color=GREEN)
    axD.set_yticks(yy)
    axD.set_yticklabels([SHORT[o].replace("\n", " ") for o in order], fontsize=7.0)
    axD.set_xlabel("ions present in the published profile (of 9 required)")
    axD.set_xlim(0, 10.5)
    for y, (n, ce) in enumerate(zip(d["n_present"], d["charge_error_pct"])):
        txt = f"n={int(n) if pd.notna(n) else 0}" + \
              (f",  charge bal. {ce:.2f}%" if pd.notna(ce) else ",  charge bal. n/a")
        axD.text((n if pd.notna(n) else 0) + 0.2, y, txt, va="center", fontsize=7.0,
                 color="#2d3748")
    axD.set_title("D  Only 1 of 5 sources has a verifiable full ion panel\n"
                  "     the rest are order-of-magnitude screens only",
                  fontsize=9.6, loc="left")

    for ax in (axA, axB, axC, axD):
        ax.tick_params(labelsize=7.6)

    fp = A4 / "fig3_water_quality.png"
    fig.savefig(fp, dpi=300)
    plt.close(fig)
    return fp


def main() -> int:
    dst = ROOT / "09_图定稿"
    dst.mkdir(exist_ok=True)

    f3 = make_fig3()
    mapping = [
        ("fig1_transmission_identity.png", "Fig.1", "A1_传输账本", "传输恒等账本"),
        ("fig4_rule_invariance.png", "Fig.2", "A3_三规则内生", "分配规则与内生 γ"),
        ("fig3_water_quality.png", "Fig.3", "A4_水化学参数域", "水质约束 CoC 与判据差"),
        ("fig5_quality_allocation_interaction.png", "Fig.4", "A7_质量分配联合", "水质×分配联合交互"),
        ("fig5_conditional_boundary.png", "Fig.5", "A10_敏感性与边界", "条件边界曲面与全局敏感性"),
        ("fig6_adaptation_pareto.png", "Fig.6", "A11_适应成本", "适应成本 Pareto"),
        ("fig7_time_resolution.png", "Fig.7", "A12_时间分辨率", "时间分辨率与关键时段失效"),
        ("fig6_dimensionless_collapse.png", "Fig.S1", "A9_无量纲折叠", "无量纲折叠（代数化简）"),
        ("fig2_credibility.png", "Fig.S2", "A6_可信度配图", "可信度与设施锚定"),
        ("fig2_allocation_regime.png", "Fig.S3", "A2_规则实验", "分配规则响应"),
        ("fig3_endogenous_gamma.png", "Fig.S4", "A2_规则实验", "内生 γ 曲线"),
    ]
    lines = ["# 图定稿索引 (T15)", "",
             "全部图由脚本确定性生成; `09_图定稿/` 为统一编号的副本。", "",
             "| 编号 | 文件 | 来源 | 内容 |", "|---|---|---|---|"]
    for fn, num, src, desc in mapping:
        s = ROOT / src / fn
        if not s.exists():
            lines.append(f"| {num} | _缺失: {fn}_ | {src} | {desc} |")
            continue
        out = dst / f"{num.replace('.', '_')}_{fn}"
        shutil.copy2(s, out)
        lines.append(f"| {num} | `{out.name}` | {src} | {desc} |")
    (dst / "figure_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print("\n生成:", f3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
