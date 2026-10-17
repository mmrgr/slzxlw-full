"""Fig.A23: q 的解析理论 (A22/A23 核心结果).

面板
  A: q 的闭式曲面 q=(CoC1-CoC0)/(CoC1(CoC0-1)) —— 零等值线恰为 CoC1=CoC0
  B: 充分条件的实测检验 (各水样的 c_rec vs c_pot, 逐物种)
  C: CoC_design 截断的作用 (LADWP 在两档 limit_scale 下的 CoC0/CoC1)
  D: q>0 与城市结果的关系 (349/349 有益)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
try:
    from figstyle import apply_style
    apply_style()
except Exception:  # noqa: BLE001
    pass

C_POS = "#c0392b"
C_NEG = "#1e8449"
C_N = "#2c3e50"

fig = plt.figure(figsize=(13.6, 9.6))
gs = fig.add_gridspec(2, 2, hspace=0.36, wspace=0.27)

# ---------------- A: 闭式曲面 ----------------
ax = fig.add_subplot(gs[0, 0])
c0 = np.linspace(1.05, 6.0, 240)
c1 = np.linspace(1.05, 6.0, 240)
C0, C1 = np.meshgrid(c0, c1)
Q = (C1 - C0) / (C1 * (C0 - 1.0))
lim = np.abs(Q).max()
im = ax.pcolormesh(C0, C1, Q, cmap="RdYlGn_r", vmin=-lim, vmax=lim, shading="auto")
ax.plot([1.05, 6.0], [1.05, 6.0], "k--", lw=1.8, label=r"$q=0$  ($\mathrm{CoC}_1=\mathrm{CoC}_0$)")
ax.set_xlabel(r"$\mathrm{CoC}_0$  (all-potable)")
ax.set_ylabel(r"$\mathrm{CoC}_1$  (with reclaimed)")
ax.set_title(r"A  Closed form: $q=\frac{\mathrm{CoC}_1-\mathrm{CoC}_0}"
             r"{\mathrm{CoC}_1(\mathrm{CoC}_0-1)}$", fontsize=10.5, loc="left")
ax.legend(fontsize=8.4, loc="upper left")
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
cb.set_label(r"$q$", fontsize=9)

# ---------------- B: 充分条件检验 ----------------
ax = fig.add_subplot(gs[0, 1])
th = json.loads((HERE / "q_theory_summary.json").read_text(encoding="utf-8"))
pot = th["potable_concentrations"]
samples = th["per_sample"]
labels, ratios = [], []
for s in samples:
    if s["n_species"] < 3:
        continue
    labels.append(s["sample"].split(" (")[0][:18])
    ratios.append(1.0 if s["all_cleaner_than_potable"] else 0.0)
# 用 CoC1/CoC0 比值展示
coc_ratio = [s["CoC1"] / s["CoC0"] for s in samples if s["n_species"] >= 3]
lab2 = [s["sample"].split(" (")[0][:18] for s in samples if s["n_species"] >= 3]
cols = [C_NEG if r > 1.0 else C_POS for r in coc_ratio]
y = np.arange(len(lab2))
ax.barh(y, coc_ratio, color=cols, alpha=0.85)
ax.axvline(1.0, color="k", lw=1.5, ls="--")
ax.set_yticks(y, labels=lab2, fontsize=8.4)
ax.set_xlabel(r"$\mathrm{CoC}_1/\mathrm{CoC}_0$   (>1 ⇒ $q>0$ ⇒ beneficial)")
ax.set_title("B  Sufficient condition: all species cleaner\n⇒ CoC rises ⇒ q>0 (0 violations)",
             fontsize=10.5, loc="left")
for i, (r, s) in enumerate(zip(coc_ratio, [x for x in samples if x["n_species"] >= 3])):
    ax.text(r + 0.03, i, f"{r:.2f}  ({s['n_species']}sp)", va="center", fontsize=7.8)

# ---------------- C: 设计截断 ----------------
ax = fig.add_subplot(gs[1, 0])
vals = {"tight limit\n(limit_scale=0.5)": (2.500, 5.000),
        "loose limit\n(limit_scale=5.0)": (5.000, 5.000)}
x = np.arange(len(vals))
w = 0.35
c0v = [v[0] for v in vals.values()]
c1v = [v[1] for v in vals.values()]
ax.bar(x - w / 2, c0v, w, label=r"$\mathrm{CoC}_0$ (all-potable)", color=C_N, alpha=0.85)
ax.bar(x + w / 2, c1v, w, label=r"$\mathrm{CoC}_1$ (reclaimed)", color=C_NEG, alpha=0.85)
ax.axhline(5.0, color="r", lw=1.4, ls=":", label="design ceiling")
ax.set_xticks(x, labels=list(vals.keys()), fontsize=8.6)
ax.set_ylabel("cycles of concentration")
ax.set_title("C  The design ceiling blocks the benefit:\nif $\\mathrm{CoC}_0$ is already capped, $q\\leq0$",
             fontsize=10.5, loc="left")
ax.legend(fontsize=7.8, loc="lower right")
for i, (a, b) in enumerate(zip(c0v, c1v)):
    ax.text(i - w / 2, a + 0.08, f"{a:.3f}", ha="center", fontsize=7.6)
    ax.text(i + w / 2, b + 0.08, f"{b:.3f}", ha="center", fontsize=7.6)

# ---------------- D: q>0 与城市结果 ----------------
ax = fig.add_subplot(gs[1, 1])
groups = th_missing = json.loads(
    (HERE.parent / "A22_判据分解" / "derived_criterion_summary.json").read_text(encoding="utf-8"))
g = groups["q_sign_groups"]
names = [r["group"].split("  ")[0] for r in g]
ben = [r["n_beneficial"] for r in g]
harm = [r["n_harmful"] for r in g]
y = np.arange(len(names))
ax.barh(y, ben, color=C_NEG, alpha=0.85, label="city withdrawal falls (beneficial)")
ax.barh(y, harm, left=ben, color=C_POS, alpha=0.85, label="city withdrawal rises (harmful)")
ax.set_yticks(y, labels=names, fontsize=8.6)
ax.set_xlabel("scenarios")
ax.set_title(r"D  $q>0$ ⇒ beneficial in 349/349 (no exception)", fontsize=10.5, loc="left")
ax.legend(fontsize=7.8, loc="lower right")
for i, (b, h) in enumerate(zip(ben, harm)):
    ax.text(b + h + 5, i, f"{b} / {h}", va="center", fontsize=8.2)

fig.suptitle("A closed-form theory for when reclaimed-water cooling reduces urban withdrawal",
             fontsize=12.8, y=0.972)
out = HERE / "figA23_q_theory.png"
fig.savefig(out, dpi=340, bbox_inches="tight")
print("wrote", out)
