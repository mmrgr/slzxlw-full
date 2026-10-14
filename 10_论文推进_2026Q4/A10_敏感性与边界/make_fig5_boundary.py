"""Fig.5 —— 条件边界与全局敏感性 (T10 + T12).

A: Morris 筛选 (mu* vs sigma) —— 主配置 ha|B_full|IEUA.
B: Sobol 一阶/总效应 (S1/ST) —— 主配置.
C: 条件响应曲面 S_city(rho=DeltaP/P0, chi=CoC_lim/CoC_design) + 零界面 (IEUA).
D: 零界面 dp*(chi) —— 三组水样对照.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))     # 使 figstyle 可导入 (E-7 唯一实现)
from figstyle import apply_style  # noqa: E402

apply_style()                            # 样式: 变体 A (无网格), 与抽取前逐字等价

LBL = {"pool_scale": r"pool scale  $P/P_0$", "gap_scale": r"incumbent gap  $G/G_0$",
       "dp_scale": r"new capacity  $\Delta P/P_0$", "ai_target": r"AI blend target  $\varphi$"}
SHORT = {"IEUA RP-1 (2025, tertiary)": "Tertiary reclaimed (IEUA)",
         "AI-UWM model assumption": "Model assumption",
         "Figshare RW (2025, paired study)": "High-salinity RW"}
COLS = {"IEUA RP-1 (2025, tertiary)": "#2b6cb0",
        "AI-UWM model assumption": "#c05621",
        "Figshare RW (2025, paired study)": "#9b2c2c"}


def main() -> int:
    mo = pd.read_csv(HERE / "T10_morris.csv", encoding="utf-8-sig")
    so = pd.read_csv(HERE / "T10_sobol.csv", encoding="utf-8-sig")
    surf = pd.read_csv(HERE / "T12_surface.csv", encoding="utf-8-sig")
    cv = pd.read_csv(HERE / "T12_boundary_curves.csv", encoding="utf-8-sig")

    mo = mo[mo.config == "ha|B_full|IEUA"]
    so = so[so.config == "ha|B_full|IEUA"]

    fig = plt.figure(figsize=(12.6, 8.4))
    gs = fig.add_gridspec(2, 2, hspace=0.36, wspace=0.28,
                          left=0.085, right=0.965, top=0.925, bottom=0.09)

    # ---------------- A: Morris ----------------
    axA = fig.add_subplot(gs[0, 0])
    axA.scatter(mo.mu_star, mo.sigma, s=70, c="#2b6cb0", zorder=3)
    for _, r in mo.iterrows():
        axA.annotate(LBL[r.parameter], (r.mu_star, r.sigma), fontsize=7.4,
                     xytext=(5, 4), textcoords="offset points")
    lim = max(mo.mu_star.max(), mo.sigma.max()) * 1.25
    axA.plot([0, lim], [0, lim], ls="--", color="#a0aec0", lw=0.8)
    axA.text(lim * 0.62, lim * 0.58, r"$\sigma=\mu^\ast$", fontsize=7.4, color="#718096")
    axA.set_xlim(0, lim)
    axA.set_ylim(0, lim)
    axA.set_xlabel(r"Morris  $\mu^\ast$  (normalized effect)")
    axA.set_ylabel(r"Morris  $\sigma$  (interaction)")
    axA.set_title("A  Screening: incumbent gap dominates the city-level benefit",
                  fontsize=10, loc="left")

    # ---------------- B: Sobol ----------------
    axB = fig.add_subplot(gs[0, 1])
    order = so.sort_values("ST", ascending=True)
    ypos = np.arange(len(order))
    axB.barh(ypos + 0.19, order.ST, height=0.36, color="#2b6cb0", label=r"$S_T$ (total)")
    axB.barh(ypos - 0.19, order.S1, height=0.36, color="#90cdf4", label=r"$S_1$ (first)")
    axB.set_yticks(ypos)
    axB.set_yticklabels([LBL[p] for p in order.parameter], fontsize=8)
    for y, s1, st in zip(ypos, order.S1, order.ST):
        axB.text(st + 0.012, y + 0.19, f"{st:.2f}", va="center", fontsize=7.2)
        axB.text(s1 + 0.012, y - 0.19, f"{s1:.2f}", va="center", fontsize=7.2)
    axB.set_xlim(0, max(order.ST) * 1.22)
    axB.set_xlabel("Sobol index")
    axB.legend(fontsize=7.6, frameon=False, loc="lower right")
    axB.set_title("B  Variance decomposition: gap > pool > capacity >> blend",
                  fontsize=10, loc="left")

    # ---------------- C: 条件响应曲面 ----------------
    axC = fig.add_subplot(gs[1, 0])
    s_ieua = surf[surf["sample"] == "IEUA RP-1 (2025, tertiary)"]
    piv = s_ieua.pivot_table(index="chi", columns="dp_scale", values="S_city_ml")
    xs = piv.columns.to_numpy()
    ys = piv.index.to_numpy()
    Z = piv.to_numpy()
    vmax = np.nanpercentile(np.abs(Z), 98)
    cf = axC.contourf(xs, ys, Z, levels=np.linspace(-vmax, vmax, 41),
                      cmap="RdBu_r", extend="both")
    cs = axC.contour(xs, ys, Z, levels=[0.0], colors="k", linewidths=1.8)
    axC.clabel(cs, fmt=r"$S_{\rm city}=0$", fontsize=7.6)
    axC.set_xlabel(r"new reuse capacity  $\rho=\Delta P/P_0$")
    axC.set_ylabel(r"water-quality severity  $\chi={\rm CoC}_{\lim}/{\rm CoC}_{\rm design}$")
    axC.set_title("C  Conditional response surface (IEUA tertiary reclaimed)",
                  fontsize=10, loc="left")
    cb = fig.colorbar(cf, ax=axC, pad=0.02, fraction=0.046)
    cb.set_label(r"$S_{\rm city}$  (ML yr$^{-1}$)", fontsize=8)
    cb.ax.tick_params(labelsize=7.5)

    # ---------------- D: 零界面 ----------------
    axD = fig.add_subplot(gs[1, 1])
    for s in SHORT:
        d = cv[(cv["sample"] == s) & cv.found].sort_values("chi")
        if d.empty:
            continue
        axD.plot(d.chi, d.dp_star_dimensionless, "-o", ms=3.2, lw=1.7,
                 color=COLS[s], label=SHORT[s])
    axD.set_xlabel(r"water-quality severity  $\chi={\rm CoC}_{\lim}/{\rm CoC}_{\rm design}$")
    axD.set_ylabel(r"break-even capacity  $\rho^\ast$")
    axD.set_title("D  Zero contour: stricter water requires larger new capacity",
                  fontsize=10, loc="left")
    axD.legend(fontsize=7.4, frameon=False, loc="upper right")
    axD.set_ylim(0, max(0.4, axD.get_ylim()[1]))
    axD.text(0.03, 0.05, r"below/left of curve: $S_{\rm city}<0$",
             transform=axD.transAxes, fontsize=7.2, color="#4a5568")

    out = HERE / "fig5_conditional_boundary.png"
    fig.savefig(out, dpi=330)
    plt.close(fig)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
