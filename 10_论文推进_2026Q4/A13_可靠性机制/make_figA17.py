"""Fig.A17: 三供给状态与统一恒等式 (A17 核心结果).

面板
  A: dS_pot 随归一化供给余量的变化 —— 符号翻转 (核心)
  B: 挤占比 displacement/x_ai 从 1.00 (充分占用) 降到 0.00 (有余量)
  C: 统一恒等式验证 (散点落在 y=x), 含两分支
  D: 同负荷下 A 态 vs C 态的直接对照
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
sys.path.insert(0, str(HERE))
try:
    from figstyle import apply_style
    apply_style()
except Exception:  # noqa: BLE001
    pass

C_A = "#c0392b"      # fully committed (harm)
C_C = "#1e8449"      # surplus (benefit)
C_N = "#2c3e50"

d = pd.read_csv(HERE / "supply_state_regimes.csv", encoding="utf-8-sig")
for c in ("pool_scale", "phi", "pool_ml", "elig_ml", "displaced_ml", "x_ai_B1_ml",
          "M0_ml", "M1_ml", "dS_pot_ml", "unused_B2_ml"):
    d[c] = pd.to_numeric(d[c], errors="coerce")
d["slack_ratio"] = (d["pool_ml"] - d["elig_ml"]) / d["elig_ml"]
d = d[d["chi_label"].astype(str) == "free"].copy() if "chi_label" in d.columns else d
d["disp_ratio"] = d["displaced_ml"] / d["x_ai_B1_ml"].replace(0, np.nan)
d["pred"] = d["displaced_ml"] - (d["M0_ml"] - d["M1_ml"]) - d["x_ai_B1_ml"]

fig = plt.figure(figsize=(13.6, 9.8))
gs = fig.add_gridspec(2, 2, hspace=0.34, wspace=0.27)

# ---------------- A: dS vs slack ----------------
ax = fig.add_subplot(gs[0, 0])
for dom, mk in (("ha", "o"), ("co", "s")):
    s = d[d["domain"] == dom]
    ax.scatter(s["slack_ratio"], s["dS_pot_ml"], s=26, marker=mk, alpha=0.6,
               label=f"D-{dom.upper()}", edgecolors="none")
ax.axhline(0, color="k", lw=1.3)
ax.axvline(0, color="k", lw=1.0, ls=":")
ax.axvspan(-0.65, 0, color=C_A, alpha=0.07)
ax.axvspan(0, 0.75, color=C_C, alpha=0.07)
ax.text(0.03, 0.97, "A: fully committed\n(city withdrawal ↑)", fontsize=8.4,
        color=C_A, transform=ax.transAxes, va="top")
ax.text(0.97, 0.03, "C: unused surplus\n(city withdrawal ↓)", fontsize=8.4,
        color=C_C, transform=ax.transAxes, ha="right", va="bottom")
ax.set_xlabel(r"normalised supply slack  $(P-\mathrm{elig})/\mathrm{elig}$")
ax.set_ylabel(r"$dS_{\rm pot}$  (ML per period)")
ax.set_title("A  The sign is set by the supply state,\nnot by the cooling technology",
             fontsize=10.5, loc="left")
ax.legend(fontsize=8.4, loc="lower left", framealpha=0.92)
ax.set_xlim(-0.9, 0.8)

# ---------------- B: displacement ratio ----------------
ax = fig.add_subplot(gs[0, 1])
agg = d.groupby(d["slack_ratio"].round(2))["disp_ratio"].median()
ax.plot(agg.index, agg.values, "o-", color=C_N, ms=5, lw=1.9)
ax.axhline(1.0, color=C_A, lw=1.3, ls="--",
           label="1.0 = pure displacement (no saving)")
ax.axhline(0.0, color=C_C, lw=1.3, ls="--",
           label="0.0 = no displacement (full saving)")
ax.axvline(0, color="k", lw=0.9, ls=":")
ax.set_xlabel(r"normalised supply slack  $(P-\mathrm{elig})/\mathrm{elig}$")
ax.set_ylabel(r"displacement ratio  $C/x_{\rm AI}$")
ax.set_title("B  Competition declines continuously\nfrom full to zero displacement",
             fontsize=10.5, loc="left")
ax.legend(fontsize=7.8, loc="upper right", framealpha=0.92)

# ---------------- C: unified identity ----------------
ax = fig.add_subplot(gs[1, 0])
A = d["displaced_ml"] - d["x_ai_B1_ml"].abs() * 0 - d["x_ai_B1_ml"]
ax.scatter(d["pred"], d["dS_pot_ml"], s=13, alpha=0.55, color=C_N, edgecolors="none")
lim = [d["dS_pot_ml"].min() * 1.05, max(d["dS_pot_ml"].max() * 1.1, 1000)]
ax.plot(lim, lim, "r--", lw=1.5, label="y = x")
res = (d["pred"] - d["dS_pot_ml"]).abs().max()
ax.set_xlabel(r"unified prediction  $C_{\rm disp}-(M_0-M_1)-x_{\rm AI}$  (ML)")
ax.set_ylabel(r"$dS_{\rm pot}=C-F$  (ML)")
ax.set_title(f"C  One identity covers both branches\nmax residual {res:.1e} ML, n={len(d)}",
             fontsize=10.5, loc="left")
ax.legend(fontsize=8.4, loc="upper left")

# ---------------- D: A vs C at matched load ----------------
ax = fig.add_subplot(gs[1, 1])
for dom, mk in (("ha", "o"), ("co", "s")):
    s = d[(d["domain"] == dom) & np.isclose(d["phi"], 0.8)]
    a = s[s["displaced_ml"] > 1e-6]["dS_pot_ml"]
    c = s[s["displaced_ml"] <= 1e-6]["dS_pot_ml"]
    if len(a):
        ax.scatter(np.full(len(a), 0.34) + (np.random.default_rng(1).random(len(a)) - .5) * .05,
                   a, s=42, marker=mk, color=C_A, alpha=0.75, edgecolors="white", lw=0.6)
    if len(c):
        ax.scatter(np.full(len(c), 0.66) + (np.random.default_rng(2).random(len(c)) - .5) * .05,
                   c, s=42, marker=mk, color=C_C, alpha=0.75, edgecolors="white", lw=0.6)
ax.axhline(0, color="k", lw=1.3)
ax.set_xticks([0.34, 0.66])
ax.set_xticklabels(["A: pool committed", "C: surplus present"])
ax.set_ylabel(r"$dS_{\rm pot}$  (ML per period)")
ax.set_title(r"D  Same load, same $\varphi=0.8$, same chemistry:"
             "\nopposite signs", fontsize=10.5, loc="left")
ax.text(0.5, 0.55, "city withdrawal ↑", transform=ax.transAxes, ha="center",
        fontsize=8.4, color=C_A)
ax.text(0.5, 0.10, "city withdrawal ↓", transform=ax.transAxes, ha="center",
        fontsize=8.4, color=C_C)

fig.suptitle("Supply state, not cooling technology, sets the urban outcome of reclaimed-water cooling",
             fontsize=12.8, y=0.972)
out = HERE / "figA17_supply_state.png"
fig.savefig(out, dpi=340, bbox_inches="tight")
print("wrote", out)
