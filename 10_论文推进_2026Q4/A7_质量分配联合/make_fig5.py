"""Fig.5 —— 水质-分配交互 (T2 + T8).

列名口径（2026-10-14 图形修复轮）：本脚本曾按审计 **B4 之前**的 `T2_cell_results.csv`
读取 L 维（`Ld` / `Ls` 两个字符串），而 B4 修正后 L 已拆为 **2×2 全因子**
（`Ld_claimP0_capP0` / `Ls_claim0_capGap` / `L_claim0_capP0` / `L_claimP0_capGap`），
导致自 11:20 起 `KeyError: ('Q0', 'Ld_claimP0_capP0')` 崩溃、成品图停留在 B4 之前。
现按 T2 docstring 声明的两个"选定端点"重接，面板 b 仍是 Q0/Q1 × $L_d$/$L_s$ 四线。
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
A4 = HERE.parent / "A4_水化学参数域"
A8 = HERE.parent / "A8_溶质闭合"

C_Q0 = "#4C78A8"
C_Q1 = "#E45756"
C_LD = "#54A24B"
C_LS = "#F58518"

SHORT = {
    "AI-UWM model assumption": "Model (650)",
    "IEUA RP-1 (2025, tertiary)": "Tertiary (443)",
    "LADWP AWPF (2012, RO product)": "RO product (22)",
    "Figshare RW (2025, paired study)": "High-salinity (1378)",
    "Figshare BW (5 g·L<sup>-1</sup>) (2025, paired study)": "Brackish (6131)",
}


def short(s: str) -> str:
    for k, v in SHORT.items():
        if s.startswith(k[:20]):
            return v
    return s[:22]


def main() -> int:
    curve = pd.read_csv(HERE / "T2_coc_curves.csv", encoding="utf-8-sig")
    cells = pd.read_csv(HERE / "T2_cell_results.csv", encoding="utf-8-sig")
    inter = pd.read_csv(HERE / "T2_interaction.csv", encoding="utf-8-sig")
    recirc = pd.read_csv(A8 / "T8_recirc_accumulation.csv", encoding="utf-8-sig")

    fig = plt.figure(figsize=(13.2, 9.0))
    gs = fig.add_gridspec(2, 2, hspace=0.34, wspace=0.24,
                          left=0.115, right=0.985, top=0.93, bottom=0.075)

    # ---------------- A: CoC(phi) by real water chemistry ----------------
    ax = fig.add_subplot(gs[0, 0])
    sub = curve[(curve.domain == "ha") & (curve.panel == "B_full")]
    for smp, g in sub.groupby("sample"):
        g = g.sort_values("phi_requested")
        ax.plot(g.phi_requested, g.CoC, marker="o", ms=3.4, lw=1.7, label=short(smp))
    ax.axhline(5.0, color="0.35", ls="--", lw=1.2)
    ax.annotate("design CoC = 5", (0.02, 5.05), fontsize=8, color="0.3")
    ax.set_xlabel(r"Reclaimed blending ratio $\varphi$ (requested)")
    ax.set_ylabel("Achievable CoC")
    ax.set_title("a  Water chemistry sets the cooling ceiling", loc="left", fontsize=11)
    ax.legend(fontsize=7.4, frameon=False, loc="lower left")
    ax.grid(alpha=0.22)

    # ---------------- B: four-cell S_city vs dP ----------------
    ax = fig.add_subplot(gs[0, 1])
    smp = "IEUA RP-1 (2025, tertiary)"
    sub = cells[(cells.domain == "ha") & (cells.panel == "B_full")
                & (cells["sample"] == smp)]
    # B4 后 L 维 = claim × capacity 的 2×2 全因子; 此处取 T2 docstring 声明的两个端点:
    #   L_d = (claim=P0, cap=P0)  L_s = (claim=0, cap=gap)
    L_ENDPOINTS = {"Ld_claimP0_capP0": r"$L_d$", "Ls_claim0_capGap": r"$L_s$"}
    sub = sub[sub.L.isin(L_ENDPOINTS)]
    style = {("Q0", "Ld_claimP0_capP0"): (C_Q0, "-", "o"),
             ("Q0", "Ls_claim0_capGap"): (C_LD, "--", "s"),
             ("Q1", "Ld_claimP0_capP0"): (C_Q1, "-", "^"),
             ("Q1", "Ls_claim0_capGap"): (C_LS, "--", "v")}
    for (q, l), g in sub.groupby(["Q", "L"]):
        g = g.sort_values("dP_frac")
        c, ls, mk = style[(q, l)]
        ax.plot(g.dP_frac, g.S_city_ml / 1000.0, ls, color=c, marker=mk, ms=4.6,
                lw=1.9, label=f"{q}-{L_ENDPOINTS[l]}")
    ax.axhline(0, color="0.3", lw=1.0)
    ax.set_xlabel(r"New reuse capacity $\Delta P / P_0$")
    ax.set_ylabel(r"Urban source-water saving $S_{city}$ ($\times10^3$ ML)")
    ax.set_title("b  Same physics, four allocation-quality regimes", loc="left", fontsize=11)
    ax.legend(fontsize=8.2, frameon=False)
    ax.grid(alpha=0.22)

    # ---------------- C: interaction term ----------------
    ax = fig.add_subplot(gs[1, 0])
    sub = inter[(inter.domain == "ha") & (inter.panel == "B_full") & (inter.dP_frac == 1.0)]
    sub = sub.assign(lab=sub["sample"].map(short)).sort_values("d_QL_ml")
    y = np.arange(len(sub))
    ax.barh(y - 0.2, sub.d_Q_given_Ld_ml / 1000, height=0.36, color=C_Q1, alpha=0.85,
            label=r"$\Delta$ water quality | $L_d$ (dedicated)")
    ax.barh(y + 0.2, sub.d_Q_given_Ls_ml / 1000, height=0.36, color=C_LS, alpha=0.85,
            label=r"$\Delta$ water quality | $L_s$ (shared)")
    ax.set_yticks(y)
    ax.set_yticklabels(sub.lab, fontsize=8.4)
    ax.axvline(0, color="0.3", lw=1.0)
    ax.set_xlabel(r"$\Delta S_{city}$ from switching Q0$\to$Q1 ($\times10^3$ ML)")
    ax.set_title(r"c  Quality penalty is allocation-dependent ($\Delta P=P_0$)",
                 loc="left", fontsize=11)
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    ax.grid(alpha=0.2, axis="x")

    # ---------------- D: recirculation accumulation ----------------
    ax = fig.add_subplot(gs[1, 1])
    sub = recirc[(recirc.domain == "ha") & (recirc.solute == "TDS")]
    for phi, g in sub.groupby("phi"):
        g = g.sort_values("r_removal")
        ax.plot(g.r_removal, g.CoC_effective, marker="o", ms=4.2, lw=1.8,
                label=rf"$\varphi$ = {phi}")
    ax.axhline(5.0, color="0.35", ls="--", lw=1.2)
    ax.annotate("design CoC", (0.30, 5.04), fontsize=8, color="0.3")
    ax.set_xlabel(r"Per-solute removal in internal recovery $r$")
    ax.set_ylabel(r"Effective CoC ($c_{loop}/c_{makeup}$)")
    ax.set_title("d  Recirculation erodes the ceiling further", loc="left", fontsize=11)
    ax.legend(fontsize=8.2, frameon=False)
    ax.grid(alpha=0.22)

    fig.suptitle("Water-quality and allocation constraints jointly govern urban benefit",
                 fontsize=12.5, y=0.975)
    out = HERE / "fig5_quality_allocation_interaction.png"
    fig.savefig(out, dpi=190, facecolor="white")
    print("saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
