"""Fig.1 (v2, 修正版): 城市自来水收支 —— 排放-索取平衡.

⚠ 本图替代已撤回的 Fig1_two_channels.png (见 A13_可靠性机制/AUDIT_2026-10-14_撤回声明.md)

面板
  A: F (AI 释放的自来水) 与 C (既有用户索取的自来水), 展示 C >= F
  B: dS_pot = C - F 随 phi 上升, 且随水质 chi 分层 (核心结果)
  C: 恒等式验证 dS_pot = C - F = M1 - M0 (散点落在 y=x)
  D: 两口径对比 —— 固定池 (dS>=0) vs 新增产能 (dS<0), 符号反转
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
A13 = HERE.parent / "A13_可靠性机制"
A15 = HERE.parent / "A15_稳健性"
sys.path.insert(0, str(HERE.parent))
try:
    from figstyle import apply_style
    apply_style()
except Exception:  # noqa: BLE001
    pass

C_F = "#1e8449"      # discharge
C_C = "#c0392b"      # claim
C_NET = "#2c3e50"

d = pd.read_csv(A13 / "potable_flows.csv", encoding="utf-8-sig")
for c in ("phi", "F_released_ml", "C_claimed_ml", "dS_pot_ml", "M0_ml", "M1_ml", "chi"):
    d[c] = pd.to_numeric(d[c], errors="coerce")

fig = plt.figure(figsize=(13.6, 9.6))
gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.27)

# ---------- A: F 与 C ----------
ax = fig.add_subplot(gs[0, 0])
s = d[(d["domain"] == "ha") & (d["sample"] == "IEUA RP-1 (2025, tertiary)") &
      np.isclose(d["chi"], 0.5)].sort_values("phi")
ax.plot(s["phi"], s["C_claimed_ml"], "-", color=C_C, lw=2.3,
        label=r"$C$  potable claimed by displaced incumbents")
ax.plot(s["phi"], s["F_released_ml"], "-", color=C_F, lw=2.3,
        label=r"$F$  potable discharged by the data centre")
ax.fill_between(s["phi"], s["F_released_ml"], s["C_claimed_ml"],
                color=C_NET, alpha=0.16, label=r"gap $=dS_{pot}$")
ax.set_xlabel(r"reclaimed fraction of cooling makeup  $\varphi$")
ax.set_ylabel("potable flow  (ML per period)")
ax.set_title("A  Two opposing potable flows\n(D-HA, IEUA, fixed pool)", fontsize=10.5, loc="left")
ax.legend(fontsize=7.6, loc="upper left")

# ---------- B: dS_pot by chi ----------
ax = fig.add_subplot(gs[0, 1])
for chi, col in ((1.0, "#2e86c1"), (0.5, "#e67e22"), (0.25, "#c0392b")):
    m = d[np.isclose(d["chi"], chi)].groupby("phi")["dS_pot_ml"].mean()
    ax.plot(m.index, m.values, "o-", ms=3.6, lw=1.9, color=col,
            label=fr"$\chi={chi:.2f}$")
ax.set_xlabel(r"reclaimed fraction  $\varphi$")
ax.set_ylabel(r"$dS_{pot}$  (ML per period)")
ax.set_title("B  The city effect is set by water quality,\nand vanishes when quality does not bind",
             fontsize=10.5, loc="left")
ax.legend(fontsize=8.6, title=r"quality severity $\chi$", title_fontsize=8)
ax.axhline(0, color="k", lw=1.0, ls=":")

# ---------- C: identity check ----------
ax = fig.add_subplot(gs[1, 0])
ax.scatter(d["dS_pot_ml"], d["M1_ml"] - d["M0_ml"], s=11, alpha=0.5,
           color=C_NET, edgecolors="none")
lim = [min(d["dS_pot_ml"].min(), -1), d["dS_pot_ml"].max() * 1.05]
ax.plot(lim, lim, "r--", lw=1.5, label="y = x")
res = (d["dS_pot_ml"] - (d["M1_ml"] - d["M0_ml"])).abs().max()
ax.set_xlabel(r"$dS_{pot}=C-F$  (ML)")
ax.set_ylabel(r"$M_1-M_0$  (ML)")
ax.set_title(f"C  Identity holds exactly\nmax residual {res:.1e} ML, n={len(d):,}",
             fontsize=10.5, loc="left")
ax.legend(fontsize=8.6, loc="upper left")

# ---------- D: two regimes ----------
ax = fig.add_subplot(gs[1, 1])
ab = pd.read_csv(A15 / "ablation_matrix.csv", encoding="utf-8-sig")
for dp, col, lbl in ((0.0, "#1f77b4", "fixed pool  ($\\Delta P=0$)"),
                     (1.0, "#d35400", "added capacity  ($\\Delta P>0$)")):
    sub = ab[np.isclose(ab["dp_scale"], dp)]
    jit = (np.random.default_rng(0).random(len(sub)) - 0.5) * 0.06
    ax.scatter(np.full(len(sub), 0.35 if dp == 0 else 0.65) + jit,
               sub["dS_pot_ml"], s=42, alpha=0.75, color=col,
               edgecolors="white", lw=0.6, label=lbl)
ax.axhline(0, color="k", lw=1.2)
ax.set_xticks([0.35, 0.65])
ax.set_xticklabels(["fixed pool", "added capacity"])
ax.set_ylabel(r"$dS_{pot}$  (ML per period)")
ax.set_title("D  The identity has a regime boundary:\nadded capacity reverses the sign",
             fontsize=10.5, loc="left")
ax.legend(fontsize=8.2, loc="upper right")
ax.text(0.06, 0.90, "city potable withdrawal ↑", transform=ax.transAxes,
        ha="left", fontsize=8.4, color="#7b241c")
ax.text(0.06, 0.06, "city potable withdrawal ↓", transform=ax.transAxes,
        ha="left", fontsize=8.4, color="#186a3b")

fig.suptitle("A discharge–claim balance for reclaimed-water cooling in AI data centres",
             fontsize=13, y=0.972)
out = HERE / "Fig1_discharge_claim.png"
fig.savefig(out, dpi=340, bbox_inches="tight")
print("wrote", out)
