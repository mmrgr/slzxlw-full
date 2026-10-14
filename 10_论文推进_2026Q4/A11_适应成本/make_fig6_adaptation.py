"""Fig.6 —— 适应方案的成本-水量 Pareto (T13).

A: S_city vs 系统年能耗; 颜色=方案, 点大小=年化资本; 星标=4D-Pareto.
B: 各方案 S_city 条形 (相对 A0), 标注增量能耗.
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

COL = {"A0": "#4a5568", "A1": "#805ad5", "A2": "#2b6cb0", "A3": "#2f855a"}
NAME = {"A0": "A0  no adaptation", "A1": "A1  chemical / side-stream",
        "A2": "A2  membrane new capacity", "A3": "A3  dry / hybrid cooling"}


def main() -> int:
    df = pd.read_csv(HERE / "T13_pareto.csv", encoding="utf-8-sig")
    # 单位核对 (修复 F-1): energy_kwh_yr 是 kWh; ÷1e6 = GWh (与 §2.7 表格口径一致).
    # 旧版 ÷1e9 得到 TWh 却把轴标为 GWh -> 面板 A 的 x 轴错 1000 倍.
    # 验算: A0 的 7 763 225 748 kWh = 7 763 GWh = 7.763 TWh (§2.7 表首行).
    df["energy_gwh"] = df.energy_kwh_yr / 1e6

    fig = plt.figure(figsize=(12.6, 5.2))
    gs = fig.add_gridspec(1, 2, wspace=0.24, left=0.075, right=0.975,
                          top=0.9, bottom=0.13)

    # ---------------- A ----------------
    axA = fig.add_subplot(gs[0, 0])
    for pol, g in df.groupby("policy"):
        size = 26 + 150 * (g.capex_annual_cny / max(df.capex_annual_cny.max(), 1.0))
        axA.scatter(g.energy_gwh, g.S_city_ml, s=size, c=COL[pol], alpha=0.75,
                    edgecolors="white", linewidths=0.6, label=NAME[pol], zorder=3)
    par = df[df.pareto_4d]
    axA.scatter(par.energy_gwh, par.S_city_ml, s=260, facecolors="none",
                edgecolors="#d69e2e", linewidths=2.2, zorder=4, label="non-dominated")
    for _, r in par.iterrows():
        axA.annotate(r.variant, (r.energy_gwh, r.S_city_ml), fontsize=7.2,
                     xytext=(8, 6), textcoords="offset points", color="#744210")
    axA.axhline(0, color="#9b2c2c", lw=0.9, ls="--", alpha=0.6)
    axA.set_xlabel("system energy  (GWh yr$^{-1}$)")
    axA.set_ylabel(r"city saving  $S_{\rm city}$  (ML yr$^{-1}$)")
    # 标题核对 (修复 F-2): 旧标题 "only dry/hybrid escapes the loss" 是 M7 修正前
    # "A3 是唯一英雄" 的口径. 修正后 §2.7: A3 只能去害 (-418.6 -> 0), 而 A2 膜法扩容
    # 同样"逃出损失"且是唯一把 S_city 推正的杠杆 (图示蓝点 +610 ~ +6 101 ML/yr).
    axA.set_title("A  Water saving vs energy: dry/hybrid removes the loss; "
                  "only new capacity creates gain",
                  fontsize=10, loc="left")
    axA.legend(fontsize=7.2, frameon=False, loc="lower right")
    axA.text(0.02, 0.04, "marker size $\\propto$ annualised CAPEX", transform=axA.transAxes,
             fontsize=7.0, color="#4a5568")

    # ---------------- B ----------------
    axB = fig.add_subplot(gs[0, 1])
    plot = df.sort_values(["policy", "S_city_ml"]).reset_index(drop=True)
    ypos = np.arange(len(plot))
    cols = [COL[p] for p in plot.policy]
    axB.barh(ypos, plot.S_city_ml, color=cols, alpha=0.85, height=0.72)
    axB.set_yticks(ypos)
    axB.set_yticklabels(plot.variant, fontsize=6.6)
    axB.axvline(0, color="#4a5568", lw=0.8)
    axB.set_xlabel(r"$S_{\rm city}$  (ML yr$^{-1}$)")
    axB.set_title("B  Strategy ranking (relative to A0 baseline)", fontsize=10, loc="left")
    a0 = float(df[df.policy == "A0"].S_city_ml.iloc[0])
    axB.axvline(a0, color="#9b2c2c", lw=1.0, ls="--", alpha=0.7)
    axB.text(a0, len(plot) - 0.5, "  A0 baseline", color="#9b2c2c", fontsize=7.0)
    axB.set_xlim(min(plot.S_city_ml.min() * 1.15, -2100), plot.S_city_ml.max() * 1.12)

    out = HERE / "fig6_adaptation_pareto.png"
    fig.savefig(out, dpi=330)
    plt.close(fig)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
