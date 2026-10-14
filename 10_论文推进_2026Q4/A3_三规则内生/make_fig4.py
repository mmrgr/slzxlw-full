"""T1/T1b 配图 (Fig.4 核心)
 A  固定池: 所有分配规则给出 S_city <= 0 (规则不变性)
 B  新增能力下: 城市获益 vs 数据中心份额 — 归属由"权利认定"决定
 C  数据中心取得再生水所需门槛 ΔP* 随权利认定的变化 (跨 34 倍)
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
sys.path.insert(0, str(HERE.parent))          # 使 figstyle 可导入 (E-7 唯一实现)
from figstyle import apply_style_grid  # noqa: E402

apply_style_grid()                            # 样式: 变体 B (带网格), 与抽取前逐字等价

t1 = pd.read_csv(HERE / "T1_rule_identity.csv")
t1b = pd.read_csv(HERE / "T1b_claim_convention.csv")

COL = {"engine_native": "#c0392b", "pro_rata": "#e67e22",
       "incumbent_first": "#2471a3", "dedicated": "#148f77"}
LAB = {"engine_native": "engine native (AI-priority, status quo)",
       "pro_rata": "pro-rata (no priority)",
       "incumbent_first": "incumbent-first (shared pool)",
       "dedicated": "dedicated new supply"}

fig, ax = plt.subplots(1, 3, figsize=(13.4, 4.0))

# ---- A ----
for rule, mk in zip(COL, ["o", "s", "^", "v"]):
    d = t1[(t1.domain == "ha") & np.isclose(t1.theta, 0.0) & (t1.rule == rule)]
    if d.empty:
        continue
    d = d.sort_values("phi_requested")
    ax[0].plot(d.phi_requested, d.S_city_ml / 1e3, color=COL[rule], lw=2.3,
               marker=mk, ms=3.2, label=LAB[rule])
d = t1[(t1.domain == "co") & np.isclose(t1.theta, 0.0) & (t1.rule == "engine_native")]
ax[0].plot(d.sort_values("phi_requested").phi_requested,
           d.sort_values("phi_requested").S_city_ml / 1e3, color="k", lw=1, ls=":", alpha=.55,
           label="D-CO (all rules collapse here)")
ax[0].axhline(0, color="k", lw=.8)
ax[0].set_xlabel(r"requested reclaimed fraction $\varphi_{req}$")
ax[0].set_ylabel(r"urban saving $S_{city}$ (1000 ML)")
ax[0].set_title("A  Fixed pool: every rule gives $S_{city}\\leq 0$", loc="left", fontsize=9.5)
ax[0].legend(fontsize=6.3, loc="lower left", framealpha=.92)

# ---- B ----
h = t1b[(t1b.domain == "ha") & np.isclose(t1b.phi_requested, 0.7)]
for om, c in zip([0.0, 0.25, 0.5, 0.75, 1.0],
                 ["#148f77", "#5dade2", "#7d3c98", "#d68910", "#c0392b"]):
    s = h[np.isclose(h.omega, om)].sort_values("dP_ml")
    ax[1].plot(s.dP_ml / 1e3, s.S_city_ml / 1e3, color=c, lw=2.0,
               label=rf"$\omega={om}$")
ax[1].axhline(0, color="k", lw=.8)
ax[1].set_xlabel(r"new reuse capacity $\Delta P$ (1000 ML)")
ax[1].set_ylabel(r"urban saving $S_{city}$ (1000 ML)")
ax[1].set_title(r"B  New supply: city gains regardless of $\omega$", loc="left", fontsize=9.5)
ax[1].legend(fontsize=7, loc="upper left", ncol=2)

# ---- C ----
for dom, ls, mk in (("ha", "-", "o"), ("co", "--", "s")):
    s = t1b[(t1b.domain == dom) & np.isclose(t1b.phi_requested, 0.7)]
    thr = []
    for om in sorted(s.omega.unique()):
        g = s[np.isclose(s.omega, om)].sort_values("dP_ml")
        pos = g[g.AI_reclaimed_ml > 1e-6]
        thr.append((om, pos.dP_ml.min() / 1e3 if len(pos) else np.nan))
    thr = np.array(thr)
    ax[2].plot(thr[:, 0], thr[:, 1], ls, color="#2471a3" if dom == "ha" else "#e67e22",
               lw=2.3, marker=mk, ms=5, label=f"D-{dom.upper()}")
g = t1b[(t1b.domain == "ha") & np.isclose(t1b.phi_requested, 0.7)]
g0 = g[np.isclose(g.omega, 0.0)].sort_values("dP_ml")
ax[2].plot(g0.dP_ml / 1e3, np.zeros(len(g0)), color="#148f77", lw=0, alpha=0)
ax[2].axhline(0, color="k", lw=.8)
ax[2].set_xlabel(r"recognised incumbent right  $\omega$")
ax[2].set_ylabel(r"$\Delta P$ for data centre to receive water (1000 ML)")
ax[2].set_title("C  Data-centre access needs up to 34$\\times$ more capacity", loc="left", fontsize=9.5)
ax[2].legend(fontsize=8)

fig.suptitle("Allocation rules cannot create urban water benefit from a fixed pool; "
             "new capacity benefits the incumbent backlog first",
             fontsize=11.5, y=1.02, x=.01, ha="left")
fig.tight_layout()
fig.savefig(HERE / "fig4_rule_invariance.png", dpi=210, bbox_inches="tight")
print("[ok]", HERE / "fig4_rule_invariance.png")
