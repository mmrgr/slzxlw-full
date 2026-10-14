"""Fig.7 —— 时间分辨率与关键时段失效 (T5 + T14, 指标 C).

A: 730 天逐日冷却蒸发 —— 蒸发式(近乎恒定) vs 混合式(强季节性 + 冬季零湿)
B: 混合式湿分 vs 湿球温度 —— 引擎 24 °C 全湿阈值, 说明峰值为何与热浪同步
C: 逐日替代覆盖率(混合式, ha) —— 年均值掩盖夏季塌陷
D: 失效概率 热浪窗 vs 非热浪窗 + 峰值失效临界规模 s*(σ)
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
sys.path.insert(0, str(HERE))
plt.rcParams.update({
    "font.size": 9, "axes.linewidth": 0.8, "font.family": "DejaVu Sans",
    "axes.spines.top": False, "axes.spines.right": False,
})

BLUE, ORANGE, RED, GREY, GREEN = "#2b6cb0", "#c05621", "#9b2c2c", "#a0aec0", "#2f855a"


def main() -> int:
    s5 = json.loads((HERE / "T5_summary.json").read_text(encoding="utf-8"))
    s14 = json.loads((HERE / "T14_summary.json").read_text(encoding="utf-8"))
    dom = "ha"

    ev = pd.read_csv(HERE / f"T5_daily_series_{dom}_evaporative.csv", parse_dates=["date"])
    hy = pd.read_csv(HERE / f"T5_daily_series_{dom}_hybrid.csv", parse_dates=["date"])
    ts = pd.read_csv(HERE.parent.parent / "07_代码_AI-UWM引擎" / "aiuwm_src" /
                     "examples" / "cawcc_r2" / dom / "timeseries.csv", parse_dates=["date"])
    wb_thr = s5["domains"][dom]["wet_bulb_threshold_p95_c"]
    heat = (ev.wet_bulb_c >= wb_thr).to_numpy()
    x = np.arange(len(ev))

    fig = plt.figure(figsize=(13.0, 8.8))
    gs = fig.add_gridspec(2, 2, hspace=0.42, wspace=0.26,
                          left=0.075, right=0.97, top=0.92, bottom=0.09)

    # ---------------- A ----------------
    axA = fig.add_subplot(gs[0, 0])
    for i in np.where(heat)[0]:
        axA.axvspan(i - 0.5, i + 0.5, color="#fed7d7", lw=0, zorder=0)
    axA.plot(x, ev.evaporation_ml, color=BLUE, lw=1.0,
             label="Evaporative (wet year-round)")
    axA.plot(x, hy.evaporation_ml, color=ORANGE, lw=1.0,
             label="Hybrid (dry below 12 $^\\circ$C wet-bulb)")
    axA.set_xlabel("day of simulation (2029-01-01 → 2030-12-31)")
    axA.set_ylabel("daily evaporation  (ML d$^{-1}$)")
    axA.set_xlim(0, len(ev) - 1)
    axA.set_ylim(bottom=0)
    axA.legend(fontsize=7.4, frameon=False, loc="lower center", ncol=2)
    axA.text(0.985, 0.95, "pink bands: heat-wave days (wet-bulb ≥ p95)",
             transform=axA.transAxes, fontsize=7.0, color=RED, ha="right")
    pe = s5["domains"][dom]["tech"]
    axA.set_title("A  Flat vs peaked water demand\n"
                  f"     peak / mean = {pe['evaporative']['evaporation']['peak_over_mean']:.2f} "
                  f"(evaporative)  vs  {pe['hybrid']['evaporation']['peak_over_mean']:.2f} (hybrid)",
                  fontsize=9.6, loc="left")

    # ---------------- B ----------------
    axB = fig.add_subplot(gs[0, 1])
    axB.scatter(hy.wet_bulb_c, hy.wet_fraction, s=9, c=ORANGE, alpha=0.55,
                edgecolors="none", label="hybrid, day-by-day")
    axB.axvline(24.0, color=RED, ls="--", lw=0.9)
    axB.text(24.4, 0.60, "engine full-wet\nthreshold\n24 $^\\circ$C", fontsize=7.0, color=RED)
    axB.axvline(12.0, color=GREY, ls=":", lw=0.9)
    axB.text(12.4, 0.10, "wet-mode onset 12 $^\\circ$C", fontsize=7.0, color="#718096")
    axB.set_xlabel("wet-bulb temperature  ($^\\circ$C)")
    axB.set_ylabel("wet cooling fraction")
    axB.set_ylim(-0.04, 1.06)
    axB.set_title("B  Peak coincides with heat waves by construction\n"
                  "     (heat rejection stays dry until the tower is forced wet)",
                  fontsize=9.6, loc="left")

    # ---------------- C ----------------
    axC = fig.add_subplot(gs[1, 0])
    import daily_model as dm
    R = dm.daily_reuse_supply(dom).reuse_delivered_ml.to_numpy()
    ent = s14["params"]["phi"] * hy.external_makeup_ml.to_numpy()
    for sig, c, lab in ((1.00, GREY, r"$\sigma=1.0$ (full pool)"),
                        (0.70, BLUE, r"$\sigma=0.7$"),
                        (0.50, RED, r"$\sigma=0.5$")):
        cov = np.where(ent > 1e-12, np.minimum(sig * R, ent) / np.maximum(ent, 1e-12), 1.0)
        axC.plot(x, cov, color=c, lw=0.9, label=lab)
    axC.axhline(1.0, color="#cbd5e0", lw=0.7)
    axC.set_xlabel("day of simulation")
    axC.set_ylabel("reclaimed substitution coverage")
    axC.set_xlim(0, len(ent) - 1)
    axC.set_ylim(0, 1.08)
    axC.legend(fontsize=7.2, frameon=False, loc="lower left", ncol=3)
    ch = s14["indicator_C"][dom]["hybrid"]["coverage_by_share"]
    axC.set_title("C  Annual averages hide the critical-period collapse\n"
                  f"     hybrid $\\sigma$=0.5: coverage {ch['sigma_0.50']['coverage_mean']:.2f} "
                  f"annual vs {ch['sigma_0.50']['coverage_heatwave']:.2f} heat-wave",
                  fontsize=9.6, loc="left")

    # ---------------- D ----------------
    axD = fig.add_subplot(gs[1, 1])
    techs = ("evaporative", "hybrid")
    sigs = ("sigma_0.50", "sigma_0.70")
    width = 0.19
    labels, hw_v, nh_v = [], [], []
    for ti, t in enumerate(techs):
        for si, sk in enumerate(sigs):
            cb = s14["indicator_C"][dom][t]["coverage_by_share"][sk]
            labels.append(f"{'Evap.' if ti==0 else 'Hybrid'}\n" + r"$\sigma$=" + sk.split("_")[1])
            hw_v.append(cb["failure_prob_heatwave"])
            nh_v.append(cb["failure_prob_non_heatwave"])
    pos = np.arange(len(labels))
    axD.bar(pos - width / 2, hw_v, width, color=RED, label="heat-wave days")
    axD.bar(pos + width / 2, nh_v, width, color=BLUE, label="non-heat-wave days")
    axD.set_xticks(pos)
    axD.set_xticklabels(labels, fontsize=7.4)
    axD.set_ylabel("probability of reclaimed-supply failure")
    axD.set_ylim(0, 1.12)
    axD.legend(fontsize=7.2, frameon=False, loc="upper left")
    for p, v in zip(pos - width / 2, hw_v):
        axD.text(p, v + 0.02, f"{v:.2f}", ha="center", fontsize=6.8, color=RED)
    for p, v in zip(pos + width / 2, nh_v):
        axD.text(p, v + 0.02, f"{v:.2f}", ha="center", fontsize=6.8, color=BLUE)
    ss = s14["indicator_C"][dom]["hybrid"]["failure_scale_s_star"]
    txt = ",  ".join(f"{k.replace('sigma_','')}'={('-' if v is None or v!=v else f'{v:.2f}')}"
                     for k, v in ss.items())
    axD.set_title("D  Failure is a critical-period, not an annual-average, property\n"
                  "     hybrid failure-onset scale  " + txt,
                  fontsize=9.6, loc="left")

    for ax in (axA, axB, axC, axD):
        ax.tick_params(labelsize=7.6)

    fp = HERE / "fig7_time_resolution.png"
    fig.savefig(fp, dpi=300)
    plt.close(fig)
    print("wrote", fp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
