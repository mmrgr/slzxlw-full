"""WP3 阶段 3 配图: 分配规则决定城市级水效益."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

OUT = Path(__file__).resolve().parent
CURVE = pd.read_csv(OUT / "stage1_cooling_curve.csv")
GS = pd.read_csv(OUT / "stage1b_gamma_star.csv")
RULES = pd.read_csv(OUT / "stage2_allocation_rules.csv")
COL = {"ha": "#c0392b", "co": "#2471a3"}
LBL = {"ha": "D-HA", "co": "D-CO"}

fig, axes = plt.subplots(2, 2, figsize=(12.6, 8.6))

# A. 冷却物理曲线
ax = axes[0, 0]
for d in ("ha", "co"):
    c = CURVE[CURVE.domain == d].sort_values("phi_actual")
    ax.plot(c["phi_actual"], c["M_ml"] / 1e3, "-", color=COL[d], label=f"{LBL[d]}  $M(\\varphi)$")
    ax.plot(c["phi_actual"], c["CoC_mean"] * 5, "--", color=COL[d], alpha=0.5, label=f"{LBL[d]}  CoC x5")
ax.axhline(27973.5 / 1e3, color="grey", lw=0.8, ls=":")
ax.set_xlabel("Reclaimed fraction of cooling makeup $\\varphi$")
ax.set_ylabel("Total makeup $M$ (10$^3$ ML)  /  CoC (x5)")
ax.set_title("A. Quality-limited CoC raises gross makeup", fontsize=11)
ax.legend(fontsize=7.5)

# B. gamma*
ax = axes[0, 1]
for d in ("ha", "co"):
    g = GS[(GS.domain == d) & GS["gamma_star"].notna()].sort_values("phi")
    ax.plot(g["phi"], g["gamma_star"], "-", color=COL[d], lw=2, label=LBL[d])
ax.set_ylim(0.88, 1.005)
ax.axhspan(0.90, 0.95, color="#f1c40f", alpha=0.12)
ax.set_xlabel("Reclaimed fraction of cooling makeup $\\varphi$")
ax.set_ylabel("Critical displacement share $\\gamma^*$")
ax.set_title("B. Benefit holds iff $\\gamma<\\gamma^*$ (≈0.92–1.00)", fontsize=11)
ax.legend(fontsize=8)

# C. S_city vs phi per rule
ax = axes[1, 0]
STYLE = {"ai_priority": ("o-", "AI-priority ($\\gamma$=1)"), "proportional": ("s--", "Pro-rata ($\\gamma$=0.5)"), "incumbent_first": ("^:", "Incumbent-first ($\\gamma$=0)")}
for d in ("ha",):
    for r, (st, lab) in STYLE.items():
        s = RULES[(RULES.domain == d) & (RULES.rule == r)].sort_values("phi_effective")
        ax.plot(s["phi_effective"], s["S_city_ml"] / 1e3, st, color=COL[d], ms=4, label=lab)
ax.axhline(0, color="k", lw=1)
ax.set_xlabel("Reclaimed fraction of cooling makeup $\\varphi$")
ax.set_ylabel("$S_{city}$ (10$^3$ ML)")
ax.set_title("C. D-HA: same physics, three allocation rules", fontsize=11)
ax.legend(fontsize=8)

# D. 三规则的城市效益对比 (两域)
ax = axes[1, 1]
rules = ["ai_priority", "proportional", "incumbent_first"]
x = np.arange(len(rules))
w = 0.36
for i, d in enumerate(("ha", "co")):
    vals = [float(RULES[(RULES.domain == d) & (RULES.rule == r)]["S_city_ml"].max()) / 1e3 for r in rules]
    ax.bar(x + (i - 0.5) * w, vals, w, color=COL[d], label=LBL[d])
    for xi, v in zip(x + (i - 0.5) * w, vals):
        ax.text(xi, v + 0.5, f"{v:.1f}", ha="center", fontsize=8)
ax.set_xticks(x)
ax.set_xticklabels(["AI-priority\n$\\gamma$=1", "Pro-rata\n$\\gamma$=0.5", "Incumbent-first\n$\\gamma$=0"])
ax.set_ylabel("Max $S_{city}$ (10$^3$ ML)")
ax.set_title("D. Allocation regime spans 0 to full transmission", fontsize=11)
ax.legend(fontsize=8)

for a in axes.ravel():
    a.grid(alpha=0.25, lw=0.6)
    a.set_facecolor("#fbfbfb")
fig.suptitle("Urban water benefit of data-centre reclaimed-water reuse is set by the allocation regime, not the technology",
             fontsize=12.5, y=1.0)
fig.tight_layout()
fig.savefig(OUT / "fig2_allocation_regime.png", dpi=190, bbox_inches="tight", facecolor="white")
print("saved", OUT / "fig2_allocation_regime.png")
