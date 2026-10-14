"""WP3 第二步: 把 gamma 内生 —— 用引擎实测的池/挤占口径解出三规则的净效应.

引擎实测事实 (D-HA, 1000 MW, 730 天)
------------------------------------
* 中央回用池 (CENTRAL_REUSE) 产水 P(phi): 24 404 ML (phi=0) -> 24 686 ML (phi=0.8)
  由 WWTW1 的 central_reuse_fraction=0.16 决定; 处理能力 40 ML/day。
* 既有用户在 phi=0 时拿走全部 P -> 池子是"满负荷、被占满"的。
* 既有用户的可回用需求 = 58 183 ML >> P -> 持续供不应求。
* DC 目标比例优先: R_AI = phi*M(phi), 既有用户被挤占 = R_AI - dP。
  => 引擎原生规则 gamma_native ~= 0.99 (纯挤占)。

内生结论
--------
池固定且被占满时, 任何"重新分配"规则都只挪动同一块饼 -> S_city ~= 0。
唯一产生正 S_city 的路径是**新增回用处理能力**。设新增能力覆盖 DC 再生水需求的
份额为 delta (delta = 1 - gamma), 则

    S_city(phi, delta) = delta * phi*M(phi) - [M(phi) - M(0)]

    S_city > 0  <=>  delta > delta*(phi) = [M(phi) - M(0)] / [phi*M(phi)]

    delta=0  : 纯挤占 (引擎原生行为)      -> S_city = M(0)-M(phi) <= 0
    delta=1  : 既有用户被完整保护+扩容     -> S_city = S_AI, eta = 1
    delta*   : 城市刚好不亏所需的扩容份额

输出
----
stage4_endogenous.csv          逐 phi 的净效应、delta*、扩容需求
fig3_endogenous_gamma.png      内生 gamma 结果图
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
CURVE = pd.read_csv(OUT / "stage1_cooling_curve.csv")

# 引擎实测的中央回用单元参数 (D-HA); 池规模 M(0) 不在此硬编码,
# 一律从 stage1_cooling_curve.csv 的 M_ml[phi=0] 读取 (见 analyse())。
REUSE_PLANT_ML_DAY = 40.0     # CENTRAL_REUSE.treatment_capacity_ml_day
WWTW_REUSE_FRACTION = 0.16
REUSE_ELEC_KWH_M3 = 0.25      # CENTRAL_REUSE.electricity_kwh_m3
GRID_KG_PER_KWH = 0.35        # 电网因子 (需在 WP5 用真实值替换)


def analyse(domain: str) -> pd.DataFrame:
    c = CURVE[CURVE.domain == domain].sort_values("phi_actual")
    m0 = float(c["M_ml"].iloc[0])
    days = 730.0
    rows = []
    for _, r in c.iterrows():
        phi, m, p = float(r["phi_actual"]), float(r["M_ml"]), float(r["wwtw_treated_ml"])
        pool = p * WWTW_REUSE_FRACTION
        r_ai_full = phi * m                       # DC 想用的再生水量
        quality_penalty = m - m0
        s_ai = r_ai_full - quality_penalty        # = M0 - (M - R_AI)
        s_city_divert = m0 - m                     # delta = 0 (纯挤占)
        s_city_protect = s_ai                      # delta = 1
        delta_star = quality_penalty / r_ai_full if r_ai_full > 1e-9 else np.nan
        # 扩容需求: 需要新增的处理能力 (ML/day), 相对现有 40 ML/day
        extra_cap_ml_day = max(0.0, r_ai_full / days)
        extra_energy_kwh = r_ai_full * 1000.0 * REUSE_ELEC_KWH_M3 / 1000.0
        rows.append({
            "domain": domain, "phi": phi, "M_ml": m, "pool_ml": pool,
            "AI_reclaimed_full_ml": r_ai_full,
            "quality_penalty_ml": quality_penalty,
            "S_AI_ml": s_ai,
            "S_city_delta0_divert_ml": s_city_divert,
            "S_city_delta1_protect_ml": s_city_protect,
            "delta_star": delta_star,
            "eta_at_delta1": 1.0,
            "eta_at_delta0": (s_city_divert / s_ai) if s_ai > 1e-9 else np.nan,
            "extra_capacity_ml_day": extra_cap_ml_day,
            "capacity_expansion_ratio": extra_cap_ml_day / REUSE_PLANT_ML_DAY,
            "extra_energy_kwh": extra_energy_kwh,
            "extra_ghg_kg_co2e": extra_energy_kwh * GRID_KG_PER_KWH,
        })
    return pd.DataFrame(rows)


def main() -> int:
    frames = [analyse(d) for d in ("ha", "co")]
    df = pd.concat(frames, ignore_index=True)
    df.to_csv(OUT / "stage4_endogenous.csv", index=False, encoding="utf-8-sig")

    print("== 内生结果 (D-HA, 抽点) ==")
    sel = df[(df.domain == "ha") & (df.phi.round(3).isin([0.0, 0.3, 0.5, 0.6, 0.7, 0.8, 0.82]))]
    print(sel[["phi", "M_ml", "AI_reclaimed_full_ml", "quality_penalty_ml", "S_AI_ml",
               "S_city_delta0_divert_ml", "S_city_delta1_protect_ml", "delta_star",
               "capacity_expansion_ratio"]].round(3).to_string(index=False))

    # 图
    fig, axes = plt.subplots(1, 3, figsize=(15.2, 4.5))
    for d, col, lab in (("ha", "#c0392b", "D-HA"), ("co", "#2471a3", "D-CO")):
        g = df[df.domain == d].sort_values("phi")
        axes[0].plot(g["phi"], g["S_city_delta0_divert_ml"] / 1e3, "o-", color=col, ms=3.5,
                     label=f"{lab}  $\\delta$=0 (diversion)")
        axes[0].plot(g["phi"], g["S_city_delta1_protect_ml"] / 1e3, "^-", color=col, ms=3.5, alpha=0.75,
                     label=f"{lab}  $\\delta$=1 (new supply)")
        axes[1].plot(g["phi"], 100 * g["delta_star"], "-", color=col, lw=2, label=lab)
        axes[2].plot(g["phi"], g["capacity_expansion_ratio"], "-", color=col, lw=2, label=lab)
    axes[0].axhline(0, color="k", lw=1)
    axes[0].set_xlabel("Reclaimed fraction $\\varphi$")
    axes[0].set_ylabel("$S_{city}$ (10$^3$ ML)")
    axes[0].set_title("A. No reallocation rule creates water", fontsize=11)
    axes[0].legend(fontsize=7)

    axes[1].set_xlabel("Reclaimed fraction $\\varphi$")
    axes[1].set_ylabel("$\\delta^*$ (% of DC demand from new supply)")
    axes[1].set_title("B. Minimum new supply to break even", fontsize=11)
    axes[1].legend(fontsize=8)

    axes[2].set_xlabel("Reclaimed fraction $\\varphi$")
    axes[2].set_ylabel("Required capacity / existing reuse plant")
    axes[2].set_title("C. Infrastructure cost of a real saving", fontsize=11)
    axes[2].legend(fontsize=8)

    for a in axes:
        a.grid(alpha=0.25, lw=0.6)
        a.set_facecolor("#fbfbfb")
    fig.suptitle("Endogenous allocation: positive city water benefit requires new reuse capacity, not reallocation", fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_endogenous_gamma.png", dpi=190, bbox_inches="tight", facecolor="white")
    print("\nsaved fig3_endogenous_gamma.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
