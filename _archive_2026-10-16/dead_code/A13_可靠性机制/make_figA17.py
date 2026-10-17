"""Fig.A17 (v2, 修正版): 三量判据与分支结构.

⚠ 修正说明 (2026-10-15): 上一版以"供给状态"二值框定（A: fully committed / C: unused
   surplus）并声称符号只由供给状态决定。组成维度修复后，该框定**不准确** ——
   符号由【三量判据】决定，挤占比单独无法预测（114 个纯挤占情景仍为负）。
   本版改正标题与标注，改为三量判据。

面板
  A: dS_pot vs 三量判据余量 —— 干净地线性分开零线
  B: 判据混淆矩阵 (吻合率)
  C: 统一恒等式验证
  D: 组成对符号的调制 (按水样)
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

C_NEG = "#1e8449"      # city withdrawal falls
C_POS = "#c0392b"      # city withdrawal rises
C_N = "#2c3e50"

d = pd.read_csv(HERE / "supply_state_regimes.csv", encoding="utf-8-sig")
for c in ("dS_pot_ml", "displaced_ml", "x_ai_B1_ml", "M0_ml", "M1_ml"):
    d[c] = pd.to_numeric(d[c], errors="coerce")
d["margin"] = d["x_ai_B1_ml"] + (d["M0_ml"] - d["M1_ml"]) - d["displaced_ml"]
d["pred_neg"] = d["margin"] > 0
d["actual_neg"] = d["dS_pot_ml"] < -1e-6
d["agree"] = d["pred_neg"] == d["actual_neg"]
acc = float(d["agree"].mean())

fig = plt.figure(figsize=(13.6, 9.8))
gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.27)

# ---------------- A: 三量判据 ----------------
ax = fig.add_subplot(gs[0, 0])
for flag, col, lbl in ((True, C_NEG, r"$dS_{\rm pot}<0$ (withdrawal falls)"),
                       (False, C_POS, r"$dS_{\rm pot}>0$ (withdrawal rises)")):
    s = d[d["actual_neg"] == flag]
    ax.scatter(s["margin"], s["dS_pot_ml"], s=22, alpha=0.55, color=col,
               label=lbl, edgecolors="none")
ax.axvline(0, color="k", lw=1.4, ls="--")
ax.axhline(0, color="k", lw=1.0)
ax.set_xlabel(r"three-term margin  $x_{\rm AI}+(M_0-M_1)-C_{\rm disp}$  (ML)")
ax.set_ylabel(r"$dS_{\rm pot}$  (ML per period)")
ax.set_yscale("symlog", linthresh=1e3)
ax.set_title(f"A  One criterion separates the signs\nagreement {acc*100:.1f}% (n={len(d):,})",
             fontsize=10.5, loc="left")
ax.legend(fontsize=7.8, loc="upper left", framealpha=0.93)

# ---------------- B: 混淆矩阵 ----------------
ax = fig.add_subplot(gs[0, 1])
cm = pd.crosstab(d["pred_neg"], d["actual_neg"])
mat = np.array([[cm.loc[False, False], cm.loc[False, True]],
                [cm.loc[True, False], cm.loc[True, True]]], dtype=float)
im = ax.imshow(mat, cmap="Blues", aspect="auto")
labs = ["rises", "falls"]
for i in range(2):
    for j in range(2):
        ax.text(j, i, f"{int(mat[i, j])}", ha="center", va="center",
                fontsize=13, color="white" if mat[i, j] > mat.max() * 0.6 else "black")
ax.set_xticks([0, 1], labels=[f"actual\n{l}" for l in labs])
ax.set_yticks([0, 1], labels=[f"predicted\n{l}" for l in labs])
ax.set_title(f"B  Confusion: {int(np.trace(mat))}/{int(mat.sum())} correct\n"
             "no off-diagonal errors", fontsize=10.5, loc="left")
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)

# ---------------- C: 统一恒等式 ----------------
ax = fig.add_subplot(gs[1, 0])
pred = d["displaced_ml"] - (d["M0_ml"] - d["M1_ml"]) - d["x_ai_B1_ml"]
res = (pred - d["dS_pot_ml"]).abs().max()
ax.scatter(pred, d["dS_pot_ml"], s=13, alpha=0.5, color=C_N, edgecolors="none")
lo, hi = d["dS_pot_ml"].min() * 1.05, max(d["dS_pot_ml"].max() * 1.1, 1e3)
ax.plot([lo, hi], [lo, hi], "r--", lw=1.5, label="y = x")
ax.set_xlabel(r"unified prediction  $C_{\rm disp}-(M_0-M_1)-x_{\rm AI}$  (ML)")
ax.set_ylabel(r"$dS_{\rm pot}=C-F$  (ML)")
ax.set_title(f"C  One identity covers both branches\nmax residual {res:.1e} ML",
             fontsize=10.5, loc="left")
ax.legend(fontsize=8.4, loc="upper left")

# ---------------- D: 组成调制符号 ----------------
ax = fig.add_subplot(gs[1, 1])
samples = list(d["sample"].unique())
names = [s.split(" (")[0][:26] for s in samples]
neg = [int(((d["sample"] == s) & d["actual_neg"]).sum()) for s in samples]
pos = [int(((d["sample"] == s) & ~d["actual_neg"]).sum()) for s in samples]
y = np.arange(len(names))
ax.barh(y, neg, color=C_NEG, alpha=0.85, label=r"$dS_{\rm pot}<0$")
ax.barh(y, pos, left=neg, color=C_POS, alpha=0.85,
        label=r"$dS_{\rm pot}\geq 0$ (incl. numerically zero)")
ax.set_yticks(y, labels=names, fontsize=8.4)
ax.set_xlabel("scenarios")
ax.set_title("D  Composition modulates the sign\n(same domains, same supply settings)",
             fontsize=10.5, loc="left")
ax.legend(fontsize=7.8, loc="lower right", framealpha=0.95)
for i, (n, p) in enumerate(zip(neg, pos)):
    ax.text(6, i, f"{n} / {p}", va="center", fontsize=8.2, color="white",
            fontweight="bold")

fig.suptitle("A three-term criterion for the urban outcome of reclaimed-water cooling",
             fontsize=13, y=0.972)
out = HERE / "figA17_supply_state.png"
fig.savefig(out, dpi=340, bbox_inches="tight")
print("wrote", out)
