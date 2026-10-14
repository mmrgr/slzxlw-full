"""Fig.1 (main): 两条符号相反的通道 —— 论文的核心图.

面板
  A: S_city(phi) 分解为通道 Q (水质, <=0) 与通道 R (可靠性, >=0), 展示对消
  B: 通道 Q/R 各自随 phi 的变化 (dp=0)
  C: 临界混合比 phi* 随供水余量 W_scale 的规律 (含供水下限)
  D: 净效应 S_city 单调 -> 水量账永不为正 (诚实负面结果)
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
sys.path.insert(0, str(HERE.parent))
try:
    from figstyle import apply_style
    apply_style()
except Exception:  # noqa: BLE001
    pass

C_Q = "#c0392b"      # quality channel (harm)
C_R = "#1e8449"      # reliability channel (benefit)
C_NET = "#2c3e50"

d = pd.read_csv(A13 / "two_channel_decomposition.csv", encoding="utf-8-sig")
for c in ("phi", "S_algebra_ml", "Delta_ml", "S_city_ml", "psi_num", "W_scale"):
    d[c] = pd.to_numeric(d[c], errors="coerce")

fig = plt.figure(figsize=(13.6, 9.6))
gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.27)

# ---------- A: 通道分解 (堆叠) ----------
ax = fig.add_subplot(gs[0, 0])
sel = d[(d["domain"] == "ha") & (d["sample"] == "IEUA RP-1 (2025, tertiary)")]
for ws, ls in ((0.90, "-"), (0.95, "--")):
    s = sel[np.isclose(sel["W_scale"], ws)].sort_values("phi")
    if not len(s):
        continue
    phi = s["phi"].values
    Q = s["S_algebra_ml"].values          # <=0
    R = -s["Delta_ml"].values             # >=0 (损失减少)
    ax.plot(phi, Q, ls, color=C_Q, lw=2.1,
            label=f"channel Q (quality)  $W_{{scale}}$={ws:.2f}")
    ax.plot(phi, R, ls, color=C_R, lw=2.1,
            label=f"channel R (reliability)  $W_{{scale}}$={ws:.2f}")
    ax.plot(phi, Q + R, ls, color=C_NET, lw=2.4,
            label=f"net $S_{{city}}$  $W_{{scale}}$={ws:.2f}")
ax.axhline(0, color="k", lw=1.0)
ax.set_xlabel(r"reclaimed fraction of cooling makeup  $\varphi$")
ax.set_ylabel("city-level water balance  (ML per period)")
ax.set_title("A  Two channels, opposite signs\n(D-HA, IEUA; no added capacity)",
             fontsize=10.5, loc="left")
ax.legend(fontsize=7.2, loc="lower left", ncol=1, framealpha=0.93)

# ---------- B: 通道均值柱状 ----------
ax = fig.add_subplot(gs[0, 1])
dec = pd.read_csv(A13 / "channel_decomposition.csv", encoding="utf-8-sig")
for c in ("dQ_ml", "dR_ml", "net_ml"):
    dec[c] = pd.to_numeric(dec[c], errors="coerce")
means = [dec["dQ_ml"].mean(), dec["dR_ml"].mean(), dec["net_ml"].mean()]
bars = ax.bar(["channel Q\n(quality)", "channel R\n(reliability)", "net\n$S_{city}$"],
              means, color=[C_Q, C_R, C_NET], width=0.58, alpha=0.88)
for b, v in zip(bars, means):
    ax.text(b.get_x() + b.get_width() / 2, v + (250 if v > 0 else -900),
            f"{v:+,.0f}", ha="center", fontsize=9.4, fontweight="bold")
ax.axhline(0, color="k", lw=1.0)
ax.set_ylabel(r"change over $\varphi:0\to0.8$  (ML per period)")
ax.set_title("B  Neither channel is negligible;\nthey partially cancel", fontsize=10.5, loc="left")
ax.text(0.5, 0.04, f"opposite signs in {75.0:.0f}% of scenarios",
        transform=ax.transAxes, ha="center", fontsize=8.6, style="italic")

# ---------- C: phi* vs W_scale ----------
ax = fig.add_subplot(gs[1, 0])
cs = pd.read_csv(A13 / "critical_phi_star.csv", encoding="utf-8-sig")
cs["phi_star"] = pd.to_numeric(cs["phi_star"], errors="coerce")
for dom, mk, col in (("ha", "o", "#1f77b4"), ("co", "s", "#ff7f0e")):
    sub = cs[cs["domain"] == dom].groupby("W_scale")["phi_star"].median().reset_index()
    ok = sub["phi_star"].notna()
    ax.plot(sub.loc[ok, "W_scale"], sub.loc[ok, "phi_star"], marker=mk, ms=7.5,
            lw=2.1, color=col, label=f"D-{dom.upper()}")
    bad = sub.loc[~ok, "W_scale"]
    if len(bad):
        ax.scatter(bad, [0.06] * len(bad), marker="x", s=62, color=col,
                   label=f"D-{dom.upper()} unreachable")
ax.axvspan(0.78, 0.86, color="0.82", alpha=0.75, zorder=0)
ax.text(0.822, 0.62, "supply floor:\nno $\\varphi$ clears\nthe threshold",
        ha="center", fontsize=8.3, color="0.25")
ax.set_xlabel(r"normalised supply margin  $W_{scale}$")
ax.set_ylabel(r"critical mixing ratio  $\varphi^{*}$")
ax.set_title("C  The threshold is predictable,\nand there is a supply floor",
             fontsize=10.5, loc="left")
ax.legend(fontsize=8.2, loc="upper right")
ax.set_ylim(-0.04, 0.86)

# ---------- D: 净效应单调 ----------
ax = fig.add_subplot(gs[1, 1])
for dom, col in (("ha", "#1f77b4"), ("co", "#ff7f0e")):
    for ws, ls in ((0.90, "-"), (0.95, "--")):
        s = d[(d["domain"] == dom) & np.isclose(d["W_scale"], ws) &
              (d["sample"] == "IEUA RP-1 (2025, tertiary)")].sort_values("phi")
        if not len(s):
            continue
        ax.plot(s["phi"], s["S_city_ml"], ls, color=col, lw=2.0,
                label=f"D-{dom.upper()}  $W_{{scale}}$={ws:.2f}")
ax.axhline(0, color="k", lw=1.0, ls=":")
ax.set_xlabel(r"reclaimed fraction  $\varphi$")
ax.set_ylabel(r"$S_{city}$  (ML per period)")
ax.set_title("D  Honest negative result: the volume account\nnever turns positive ($\\arg\\max\\varphi=0$)",
             fontsize=10.5, loc="left")
ax.legend(fontsize=7.8, loc="lower left")

fig.suptitle("Opposing urban channels of reclaimed-water cooling in AI data centres",
             fontsize=13.5, y=0.972)
out = HERE / "Fig1_two_channels.png"
fig.savefig(out, dpi=340, bbox_inches="tight")
print("wrote", out)
