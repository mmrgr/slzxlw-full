"""Fig.6 —— 无量纲折叠与可迁移性 (T9 核心图, Gate G-B).

A: 主折叠 —— y=S_city/M0 对 w=phi*delta. 478 个 LHS 情景 (池规模/缺口/扩容
   各跨 ~13x) 全部落在解析族 y=Phi*(w-u) 上; 颜色 = 无量纲水质因子 Phi.
B: 折叠残差 (对数直方图) —— 机器精度, R2=1.
C: 破坏阈值 delta*(phi): 城市由亏转盈所需的新增产能份额
   (精确等于 Delta P* = M(phi) - M0).
D: 维度缩减对照 —— 用 w 分箱 vs 用工程朴素坐标 dP/P0 分箱时 y 的组内方差.
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
sys.path.insert(0, str(HERE.parent))     # 使 figstyle 可导入 (E-7 唯一实现)
from figstyle import apply_style  # noqa: E402

apply_style()                            # 样式: 变体 A (无网格), 与抽取前逐字等价

SHORT = {
    "LADWP AWPF (2012, RO product)": "RO product (TDS 22)",
    "IEUA RP-1 (2025, tertiary)": "Tertiary reclaimed (TDS 443)",
    "AI-UWM model assumption": "Model assumption (TDS 650)",
    "Figshare RW (2025, paired study)": "High-salinity RW (TDS 1378)",
    "Figshare BW (5 g·L<sup>-1</sup>) (2025, paired study)": "Brackish (TDS 6131)",
}
ORDER = ["LADWP AWPF (2012, RO product)", "IEUA RP-1 (2025, tertiary)",
         "AI-UWM model assumption", "Figshare RW (2025, paired study)",
         "Figshare BW (5 g·L<sup>-1</sup>) (2025, paired study)"]
COLS = ["#2b6cb0", "#2f855a", "#c05621", "#9b2c2c", "#6b46c1"]
CMAP = dict(zip(ORDER, COLS))


def main() -> int:
    pts = pd.read_csv(HERE / "T9_collapse_points.csv", encoding="utf-8-sig")
    thr = pd.read_csv(HERE / "T9_thresholds.csv", encoding="utf-8-sig")
    summ = json.loads((HERE / "T9_summary.json").read_text(encoding="utf-8"))

    ok = pts[np.isfinite(pts.w) & np.isfinite(pts.y_num) & np.isfinite(pts.Phi)].copy()
    # 主图限定物理域 (质量惩罚 <= 2x). 极端苦咸水 (CoC->1, Phi 发散) 在 C 面板
    # 以"不可行域"呈现, 若混入本图会把 400+ 个常规情景压到不可见.
    n_all = len(ok)
    okp = ok[ok.Phi <= 2.0].copy()

    fig = plt.figure(figsize=(12.6, 8.4))
    gs = fig.add_gridspec(2, 2, hspace=0.34, wspace=0.27,
                          left=0.075, right=0.975, top=0.925, bottom=0.085)

    # ---------------- A: 主折叠 ----------------
    axA = fig.add_subplot(gs[0, 0])
    sc = axA.scatter(okp.w, okp.y_num, c=okp.Phi, cmap="viridis",
                     vmin=1.0, vmax=2.0,
                     s=15, alpha=0.85, linewidths=0)
    ww = np.linspace(0, 1.05, 200)
    for Phi, ls in [(1.0, "-"), (1.05, "--"), (1.2, "-."), (2.0, ":")]:
        u = 1.0 - 1.0 / Phi
        axA.plot(ww, Phi * (ww - u), color="k", lw=1.0, ls=ls, alpha=0.75,
                 label=f"$\\Phi$={Phi:g}")
    axA.axhline(0, color="#4a5568", lw=0.8, alpha=0.6)
    axA.set_xlabel(r"dimensionless new supply  $w=\varphi_{\rm eff}\,\delta$")
    axA.set_ylabel(r"normalized city benefit  $y=S_{\rm city}/M_0$")
    axA.set_title(rf"A  {len(okp)} LHS cities collapse onto  $y=\Phi\,(w-u)$",
                  fontsize=10, loc="left")
    axA.set_xlim(0, 1.05)
    axA.set_ylim(-2.4, 2.6)
    axA.legend(fontsize=7.2, frameon=False, loc="lower right", title="analytic",
               title_fontsize=7.2)
    axA.text(0.02, 0.03, rf"shown: $\Phi\leq2$ ({len(okp)}/{n_all}); "
                          rf"{n_all-len(okp)} extreme-salinity omitted",
             transform=axA.transAxes, fontsize=7.0, color="#4a5568")
    cb = fig.colorbar(sc, ax=axA, pad=0.02, fraction=0.045)
    cb.set_label(r"quality factor  $\Phi=M(\varphi)/M_0$", fontsize=8)
    cb.ax.tick_params(labelsize=7.5)

    # ---------------- B: 残差 ----------------
    axB = fig.add_subplot(gs[0, 1])
    res = np.abs(ok.y_num - ok.y_pred)
    res = res[res > 0]
    axB.hist(np.log10(res.clip(lower=1e-18)), bins=30, color="#4a5568", alpha=0.85)
    axB.set_xlabel(r"$\log_{10}\,|\,\hat y-y_{\rm pred}\,|$")
    axB.set_ylabel("count")
    axB.set_title("B  Collapse residual: machine precision", fontsize=10, loc="left")
    txt = (f"$R^2$ = {summ['collapse_R2']:.8f}\n"
           f"max $|\\Delta y|$ = {summ['collapse_residual_max_abs']:.2e}\n"
           f"n = {summ['n_valid']}/{summ['n_scenarios']} scenarios\n"
           f"volume closure = {summ['closure_residual_max_ml']:.1e} ML\n"
           r"$\Delta P^\ast = M(\varphi)-M_0$")
    axB.text(0.03, 0.96, txt, transform=axB.transAxes, va="top", fontsize=8,
             bbox=dict(fc="white", ec="#cbd5e0", lw=0.7, boxstyle="round,pad=0.4"))

    # ---------------- C: 破坏阈值 ----------------
    axC = fig.add_subplot(gs[1, 0])
    tb = thr[(thr.panel == "B_full") & (thr.phi >= 0.1)]
    for s in ORDER:
        d = tb[tb["sample"] == s].sort_values("phi")
        d = d[np.isfinite(d.delta_star)]
        if d.empty:
            continue
        feas = d[d.delta_star <= 1.0]
        infeas = d[d.delta_star > 1.0]
        axC.plot(feas.phi, feas.delta_star, color=CMAP[s], lw=1.8,
                 label=SHORT[s].split(" (")[0])
        if len(infeas):
            axC.plot(infeas.phi, np.clip(infeas.delta_star, 0, 1.0),
                     color=CMAP[s], lw=1.2, ls=":", alpha=0.6)
    axC.axhline(1.0, color="#9b2c2c", lw=0.9, ls="--", alpha=0.7)
    axC.text(0.03, 1.045, "infeasible above", color="#9b2c2c", fontsize=7.2)
    axC.set_xlabel(r"reclaimed blending fraction  $\varphi$")
    axC.set_ylabel(r"break-even new-capacity share  $\delta^\ast$")
    axC.set_title(r"C  Required new capacity $\Delta P^\ast=M(\varphi)-M_0$",
                  fontsize=10, loc="left")
    axC.legend(fontsize=6.9, frameon=False, loc="center", bbox_to_anchor=(0.47, 0.83), ncol=1, handlelength=1.6)
    axC.set_ylim(0, 1.12)

    # ---------------- D: 维度缩减 ----------------
    axD = fig.add_subplot(gs[1, 1])
    names = [r"$\varphi$" + "\n(blend only)",
             r"$\Delta P/P_0$" + "\n(engineering)",
             r"$w=\varphi_{\rm eff}\delta$" + "\n(collapsed)"]
    vals = [summ["dispersion_at_phi"], summ["dispersion_at_naive_dp"],
            summ["dispersion_at_w"]]
    bars = axD.bar(names, vals, color=["#a0aec0", "#a0aec0", "#2b6cb0"], width=0.55)
    for b, v in zip(bars, vals):
        axD.text(b.get_x() + b.get_width() / 2, v * 1.15, f"{v:.1e}",
                 ha="center", va="bottom", fontsize=8.2)
    axD.set_yscale("log")
    axD.set_ylim(min(vals) * 0.3, max(vals) * 4)
    axD.set_ylabel(r"within-bin variance of $y$")
    axD.set_title("D  Two groups suffice; raw coordinates do not",
                  fontsize=10, loc="left")
    axD.text(0.5, 0.90,
             f"variance reduction  {summ['variance_reduction_ratio']:.0f}$\\times$\n"
             f"($n$ = {summ['dispersion_n_physical']}, "
             f"$\\Phi\\leq2$)",
             transform=axD.transAxes, ha="center", fontsize=8.6,
             color="#2b6cb0", fontweight="bold")

    out = HERE / "fig6_dimensionless_collapse.png"
    fig.savefig(out, dpi=330)
    plt.close(fig)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
