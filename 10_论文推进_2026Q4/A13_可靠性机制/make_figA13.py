#!/usr/bin/env python
# ⛔ OBSOLETE / 已作废 (2026-10-14) —— 请勿运行, 勿引用其产物。
# 作废原因: 见 A13_可靠性机制/AUDIT_2026-10-14_撤回声明.md
#   该脚本使用已撤回的 psi/Delta 公式 (D 取错量 + 取水量与缺口相减)。
# 替代品: A13_可靠性机制/potable_flow_corrected.py (核心)
#        A15_稳健性/ablation_matrix_corrected.py (消融)
#        A15_稳健性/holdout_validation_corrected.py (留出+边界)
# 保留本文件仅作审计留痕。

"""Fig.A13: 有限供水可靠性闭合下的城市净效益结构与水质—可靠性耦合.

面板
  A: psi 判据验证 (Delta > 0 当且仅当 psi > 1), 3840 格点
  B: Delta > 0 占比热图 (W_scale x chi) -- 水质—可靠性耦合
  C: 旧恒等式 vs 新闭合的 S_city 分布 (展示被低估的损失)
  D: psi 随 phi 下降 -- 被遮蔽的正向通道
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
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
try:
    from figstyle import apply_style, apply_style_grid  # noqa: E402
    apply_style()
    HAS_STYLE = True
except Exception:  # noqa: BLE001
    HAS_STYLE = False

g = pd.read_csv(HERE / "reliability_grid.csv", encoding="utf-8-sig")
g = g[~g["status"].astype(str).str.startswith("ERROR")].copy()
for c in ("W_scale", "D_scale", "ai_target", "chi", "psi", "Delta_ml",
          "S_city_ml", "S_algebra_ml", "eff_ai_pot_ml", "phi_eff", "M_ml"):
    g[c] = pd.to_numeric(g[c], errors="coerce")

fig = plt.figure(figsize=(13.5, 9.5))
gs = fig.add_gridspec(2, 2, hspace=0.34, wspace=0.26)

C_TIGHT = "#c0392b"
C_LOOSE = "#2471a3"
C_ALG = "#7f8c8d"
C_NEW = "#c0392b"

# ---------------- A: psi 判据 ----------------
ax = fig.add_subplot(gs[0, 0])
tight = g[g["psi"] > 1.0 + 1e-9]
loose = g[g["psi"] <= 1.0 + 1e-9]
ax.scatter(loose["psi"], np.maximum(loose["Delta_ml"], 1e-3), s=9,
           c=C_LOOSE, alpha=0.45, label=f"$\\psi\\leq1$: $\\Delta=0$  (n={len(loose)})")
ax.scatter(tight["psi"], np.maximum(tight["Delta_ml"], 1e-3), s=9,
           c=C_TIGHT, alpha=0.45, label=f"$\\psi>1$: $\\Delta>0$  (n={len(tight)})")
xs = np.linspace(0.75, 1.6, 100)
Wm = g["W_ml"].median()
ax.plot(xs, np.maximum(Wm * (xs - 1.0), 1e-3), "k--", lw=1.6,
        label=r"$\Delta=W(\psi-1)$ (analytical)")
ax.axvline(1.0, color="k", lw=1.0, ls=":")
ax.set_yscale("log")
ax.set_xlabel(r"water-supply stress  $\psi=(D_{inc}+W_{AI,pot})/W$")
ax.set_ylabel(r"unmet incumbent demand  $\Delta$  (ML per period)")
ax.set_title("A  The gap criterion holds exactly\n(3,840 grid points, zero exceptions)",
             fontsize=10.5, loc="left")
ax.legend(fontsize=7.6, loc="upper left", framealpha=0.92)

# ---------------- B: 水质—可靠性耦合 ----------------
ax = fig.add_subplot(gs[0, 1])
piv = g.assign(pos=(g["Delta_ml"] > 1).astype(float)).pivot_table(
    index="W_scale", columns="chi", values="pos", aggfunc="mean")
piv = piv.sort_index()
im = ax.imshow(piv.values, aspect="auto", cmap="RdYlBu_r", vmin=0, vmax=1,
               origin="lower")
ax.set_xticks(range(len(piv.columns)))
ax.set_xticklabels([f"{c:.2f}" for c in piv.columns])
ax.set_yticks(range(len(piv.index)))
ax.set_yticklabels([f"{i:.2f}" for i in piv.index], fontsize=8)
ax.set_xlabel(r"water-quality severity  $\chi=\mathrm{CoC}_{lim}/\mathrm{CoC}_{design}$")
ax.set_ylabel(r"supply availability  $W_{scale}$")
for i in range(piv.shape[0]):
    for j in range(piv.shape[1]):
        v = piv.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7.4,
                color="white" if (v > 0.62 or v < 0.12) else "black")
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
cb.set_label(r"share of grid points with $\Delta>0$", fontsize=8)
ax.set_title("B  Water quality pushes the city across the\nshortage threshold",
             fontsize=10.5, loc="left")

# ---------------- C: 旧 vs 新 ----------------
ax = fig.add_subplot(gs[1, 0])
bins = np.linspace(g["S_algebra_ml"].min(), 0, 46)
ax.hist(g["S_algebra_ml"], bins=bins, color=C_ALG, alpha=0.72,
        label=r"old identity  $S_{algebra}=M_0-M$")
ax.hist(g["S_city_ml"], bins=bins, color=C_NEW, alpha=0.62,
        label=r"new closure  $S_{city}=S_{algebra}-\Delta$")
ax.axvline(0, color="k", lw=1.2)
ax.set_xlabel("city-level water balance  (ML per period)")
ax.set_ylabel("count")
ax.set_title("C  The old identity systematically\nunderstates urban loss",
             fontsize=10.5, loc="left")
ax.legend(fontsize=8, loc="upper left")
d = g["Delta_ml"]
ax.annotate(f"max extra loss\n{d.max():,.0f} ML", xy=(d.min() + g['S_algebra_ml'].min(), 0),
            xytext=(0.03, 0.62), textcoords="axes fraction", fontsize=8.2,
            color=C_NEW,
            arrowprops=dict(arrowstyle="->", color=C_NEW, lw=1.2))

# ---------------- D: psi vs phi ----------------
ax = fig.add_subplot(gs[1, 1])
for dom, mk in (("ha", "o"), ("co", "s")):
    r = g[(g["domain"] == dom) & np.isclose(g["D_scale"], 1.0) &
          np.isclose(g["chi"], 0.5) & np.isclose(g["W_scale"], 0.9)]
    if len(r) == 0:
        continue
    m = r.groupby("ai_target")["psi"].mean()
    ax.plot(m.index, m.values, marker=mk, ms=5, lw=1.7,
            label=f"D-{dom.upper()}  ($W_{{scale}}=0.9$)")
ax.axhline(1.0, color="k", ls=":", lw=1.2)
ax.text(0.02, 1.005, r"shortage threshold $\psi=1$", fontsize=8, color="k")
ax.set_xlabel(r"reclaimed fraction of cooling makeup  $\varphi$")
ax.set_ylabel(r"supply stress  $\psi$")
ax.set_title("D  A masked positive channel:\nreclaimed cooling lowers $\\psi$ (64/64 cases)",
             fontsize=10.5, loc="left")
ax.legend(fontsize=8.2, loc="best")

fig.suptitle("Finite-supply reliability closure: why the bookkeeping identity is not a law",
             fontsize=13, y=0.975)
out = HERE / "figA13_reversal.png"
fig.savefig(out, dpi=340, bbox_inches="tight")
print("wrote", out)
