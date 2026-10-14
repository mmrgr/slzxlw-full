"""T13: delta 成本曲线 + A0-A3 Pareto 前沿 (把方案反馈回主模型重解).

关键纪律 (规划 §4 T13)
    引擎 adaptation.evaluate_adaptation 是**只读账本**, 不能直接据此给方案优劣.
    本脚本把每个适应方案**反馈回主模型重新求解** S_city, 再单独做工程/能耗/碳核算.

四个方案 (在主模型上的实现)
    A0  no adaptation      : evaporative, chi 用原限值, dp=0
    A1  化学/旁流软化提标   : limit_scale -> 1 (chi->1, 消除水质惩罚), dp=0
                             能耗/药耗按处理水量计
    A2  膜法新增产能        : limit_scale -> 1, dp_scale = kappa (新增产能/P0)
                             能耗/资本按膜产水量计, 浓水按回收率计
    A3  混合/干式冷却       : cooling_tech in {hybrid,dry} + heat_rejection_wet_fraction=w
                             蒸发下降用**逐日求和的年蒸发**表达, 年度基座见
                             daily_model.tech_annual_basis

审计修复 (本轮)
    M4/M6/M7  A3 原来在"域内湿球中位日"上求值, 而 hybrid/dry 的湿球中位日恰好**零蒸发**
              → E=0 → M/E 退化 → A3 整块水量归零 (M7)。现改为**技术年度基座**:
              E_total = Σ_t E(t), 代表日 = 该技术湿日的中位湿球日, period_days = 730。
              同时 m0_of / solve_city 透传 cooling_tech 与 period_days (M4/M6)。
    能量口径   原实现 A0/A3 用"单日设施能耗 × 365", A1/A2 用增量 —— 口径不统一。
              现**全部**改为逐日求和的年设施能耗 (Σ_t facility_energy_mwh / 2)。

参数来源 (不造数)
    * 新增回用单位投资 5000-7000 元/(m3/d)  <- validation_artifacts/r2/cost_parameters.csv
    * 碳强度 0.35 kgCO2e/kWh                <- 引擎自身 intervention_water_energy_carbon.csv
    * 膜能耗 1.0-2.5 kWh/m3, A1 能耗 0.10-0.20 kWh/m3, A1 药耗 0.3-0.6 元/m3  <- DECLARED
    * 折现 6% / 20 年 -> CRF=0.0872 (声明值)

产出: Pareto 前沿 (最大化 S_city, 最小化 能耗/碳/资本) + 不可行域标注.
纪律: A2/A3 的额外能耗/碳/浓水全部入账; 不给"零代价适应"结论.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "A10_敏感性与边界"))
sys.path.insert(0, str(HERE.parent / "A12_时间分辨率"))
import city_model as cm       # noqa: E402
import daily_model as dm      # noqa: E402

from aiuwm.adaptation import (  # noqa: E402
    AdaptationConfig, CoolingDayLedger, evaluate_adaptation,
)

DOM, PANEL = "ha", "B_full"
SAMPLE = "IEUA RP-1 (2025, tertiary)"
POOL, GAP, AIT = 1.0, 1.0, 0.70
# 量纲约定 (已核对引擎): 主模型的水量 (M/pool/E_total) 是 **730 天合计 ML**;
# calculate_data_center_plan 的 energy/evaporation 是 **单日** 值.
MODEL_DAYS = 730.0
DAYS_PER_YEAR = 365.0
ML_PER_YEAR_TO_M3_DAY = 1.0e6 / MODEL_DAYS
LS_FULL = 6.0
CARBON_KG_PER_KWH = 0.35
CRF = 0.06 * (1.06 ** 20) / ((1.06 ** 20) - 1.0)

# DECLARED 参数带 (定稿前须补引用)
MEMBRANE_KWH_PER_M3 = (1.0, 2.5)
A1_KWH_PER_M3 = (0.10, 0.20)
A1_CHEM_CNY_PER_M3 = (0.30, 0.60)
REUSE_CAPEX_CNY_PER_M3D = (5000.0, 7000.0)

SAMPLE_Q = None


def quality() -> dict:
    global SAMPLE_Q
    if SAMPLE_Q is None:
        row = cm.load_samples()
        SAMPLE_Q = cm.quality_dict(row[row["source"] == SAMPLE].iloc[0], cm.PANELS[PANEL])
    return SAMPLE_Q


def annual_facility_energy_kwh(dom: str, tech: str, *, wet_fraction=None,
                               limit_scale: float = 1.0, phi: float = AIT) -> dict:
    """逐日求和的年设施能耗 (kWh/yr) —— 全方案统一口径。"""
    ser = dm.daily_plan_series(dom, SAMPLE, tech=tech, panel=PANEL, phi=phi,
                               limit_scale=limit_scale, wet_fraction=wet_fraction,
                               load_col="ai_load_factor_a30")
    return {"energy_kwh_yr": float(ser.facility_energy_mwh.sum() / 2.0 * 1000.0),
            "pue_mean": float(ser.pue.mean()),
            "E_annual_ml": float(ser.evaporation_ml.sum() / 2.0),
            "wet_frac_mean": float(ser.wet_fraction.mean()),
            "n_zero_wet_days": int((ser.evaporation_ml <= 1e-9).sum())}


def main() -> int:
    rows = []
    cache: dict = {}
    q = quality()
    gap = float(cm.BASELINES[DOM]["gap"])
    P0 = float(cm.BASELINES[DOM]["P0"])

    # ---------- A0 ----------
    a0 = cm.city_outcome(DOM, PANEL, SAMPLE, pool_scale=POOL, gap_scale=GAP,
                         dp_scale=0.0, ai_target=AIT, cache=cache)
    en0 = annual_facility_energy_kwh(DOM, "evaporative", limit_scale=1.0)
    e0 = en0["energy_kwh_yr"]
    rows.append(dict(policy="A0", variant="baseline", S_city_ml=a0["S_city_ml"] / 2.0,
                     y=a0["y"], phi_eff=a0["phi_eff"], CoC=a0["CoC_ai"],
                     energy_kwh_yr=e0, energy_increment_kwh_yr=0.0,
                     carbon_kgco2e_yr=e0 * CARBON_KG_PER_KWH,
                     capex_cny=0.0, opex_cny_yr=0.0, brine_ml_yr=0.0,
                     pue=en0["pue_mean"], tech="evaporative", wet_frac=1.0,
                     E_annual_ml=en0["E_annual_ml"], eta=a0["eta_transfer"],
                     status=a0["status"]))

    # ---------- A1: 水质提标 (无新增产能) ----------
    a1 = cm.city_outcome(DOM, PANEL, SAMPLE, pool_scale=POOL, gap_scale=GAP,
                         dp_scale=0.0, ai_target=AIT, limit_scale=LS_FULL, cache=cache)
    en1 = annual_facility_energy_kwh(DOM, "evaporative", limit_scale=LS_FULL)
    vol1_m3_yr = a1["M_ml"] * 1.0e6 / 2.0
    for tag, ek, ck in (("lo", A1_KWH_PER_M3[0], A1_CHEM_CNY_PER_M3[0]),
                        ("hi", A1_KWH_PER_M3[1], A1_CHEM_CNY_PER_M3[1])):
        adde = vol1_m3_yr * ek
        e = en1["energy_kwh_yr"] + adde
        rows.append(dict(policy="A1", variant=f"chem_{tag}", S_city_ml=a1["S_city_ml"] / 2.0,
                         y=a1["y"], phi_eff=a1["phi_eff"], CoC=a1["CoC_ai"],
                         energy_kwh_yr=e, energy_increment_kwh_yr=adde,
                         carbon_kgco2e_yr=e * CARBON_KG_PER_KWH,
                         capex_cny=0.0, opex_cny_yr=vol1_m3_yr * ck,
                         brine_ml_yr=0.0, pue=en1["pue_mean"], tech="evaporative",
                         wet_frac=1.0, E_annual_ml=en1["E_annual_ml"],
                         eta=a1["eta_transfer"], status=a1["status"]))

    # ---------- A2: 膜法新增产能 ----------
    en2 = annual_facility_energy_kwh(DOM, "evaporative", limit_scale=LS_FULL)
    for kappa in (0.05, 0.10, 0.20, 0.30, 0.50):
        a2 = cm.city_outcome(DOM, PANEL, SAMPLE, pool_scale=POOL, gap_scale=GAP,
                             dp_scale=kappa, ai_target=AIT, limit_scale=LS_FULL,
                             cache=cache)
        permeate_ml = P0 * kappa
        for rec in (0.60, 0.75):
            feed_m3_yr = (permeate_ml / rec) * 1.0e6 / 2.0
            permeate_m3_day = permeate_ml * ML_PER_YEAR_TO_M3_DAY
            brine_ml_yr = permeate_ml * (1.0 - rec) / rec / 2.0
            capex = 0.5 * permeate_m3_day * (REUSE_CAPEX_CNY_PER_M3D[0]
                                             + REUSE_CAPEX_CNY_PER_M3D[1])
            for tag, ek in (("lo", MEMBRANE_KWH_PER_M3[0]), ("hi", MEMBRANE_KWH_PER_M3[1])):
                adde = feed_m3_yr * ek
                e = en2["energy_kwh_yr"] + adde
                rows.append(dict(policy="A2", variant=f"ro_k{kappa}_r{rec}_{tag}",
                                 S_city_ml=a2["S_city_ml"] / 2.0, y=a2["y"],
                                 phi_eff=a2["phi_eff"], CoC=a2["CoC_ai"],
                                 energy_kwh_yr=e, energy_increment_kwh_yr=adde,
                                 carbon_kgco2e_yr=e * CARBON_KG_PER_KWH,
                                 capex_cny=capex, opex_cny_yr=0.0,
                                 brine_ml_yr=brine_ml_yr, pue=en2["pue_mean"],
                                 tech="evaporative", wet_frac=1.0,
                                 E_annual_ml=en2["E_annual_ml"],
                                 eta=a2["eta_transfer"], status=a2["status"]))

    # ---------- A3: 干式/混合冷却 (以排热湿分 w 为杠杆) ----------
    a3_specs = [("dry", 1.0), ("dry", 0.7), ("dry", 0.5), ("dry", 0.3), ("dry", 0.0),
                ("hybrid", None)]
    a3_meta = {}
    for tech, w in a3_specs:
        bl3, meta3 = dm.tech_annual_basis(DOM, tech, sample=SAMPLE, panel=PANEL,
                                          phi=AIT, wet_fraction=w)
        m0 = cm.m0_of(bl3, PANEL, q, cooling_tech=tech, wet_fraction=w)
        out = cm.solve_city(bl3, PANEL, SAMPLE, q, m0, P0, gap, 0.0, AIT,
                            cooling_tech=tech, wet_fraction=w,
                            period_days=MODEL_DAYS, cache=cache)
        key = f"{tech}_" + ("default" if w is None else f"wetfrac{w}")
        a3_meta[key] = meta3
        rows.append(dict(policy="A3", variant=key, S_city_ml=out["S_city_ml"] / 2.0,
                         y=out["y"], phi_eff=out["phi_eff"], CoC=out["CoC_ai"],
                         energy_kwh_yr=meta3["energy_kwh_yr"],
                         energy_increment_kwh_yr=meta3["energy_kwh_yr"] - e0,
                         carbon_kgco2e_yr=meta3["energy_kwh_yr"] * CARBON_KG_PER_KWH,
                         capex_cny=0.0, opex_cny_yr=0.0, brine_ml_yr=0.0,
                         pue=meta3["pue_mean"], tech=tech,
                         wet_frac=meta3["wet_frac_mean"],
                         E_annual_ml=meta3["E_annual_ml_yr"],
                         eta=out["eta_transfer"], status=out["status"]))

    df = pd.DataFrame(rows)
    df["capex_annual_cny"] = df.capex_cny * CRF

    def dominates(a, b):
        better = (a.S_city_ml >= b.S_city_ml and a.energy_kwh_yr <= b.energy_kwh_yr
                  and a.carbon_kgco2e_yr <= b.carbon_kgco2e_yr
                  and a.capex_annual_cny <= b.capex_annual_cny)
        strict = (a.S_city_ml > b.S_city_ml or a.energy_kwh_yr < b.energy_kwh_yr
                  or a.carbon_kgco2e_yr < b.carbon_kgco2e_yr
                  or a.capex_annual_cny < b.capex_annual_cny)
        return bool(better and strict)

    df["pareto_4d"] = [not any(dominates(rj, ri) for j, rj in df.iterrows() if j != i)
                       for i, ri in df.iterrows()]

    def dom2(a, b):
        return bool(a.S_city_ml >= b.S_city_ml and a.energy_kwh_yr <= b.energy_kwh_yr
                    and (a.S_city_ml > b.S_city_ml or a.energy_kwh_yr < b.energy_kwh_yr))
    df["pareto_S_energy"] = [not any(dom2(rj, ri) for j, rj in df.iterrows() if j != i)
                             for i, ri in df.iterrows()]

    df.to_csv(HERE / "T13_pareto.csv", index=False, encoding="utf-8-sig")

    # ---------- 账本自洽交叉核对 (adaptation.evaluate_adaptation, 只读) ----------
    a0_makeup = float(np.sum(dm.daily_plan_series(
        DOM, SAMPLE, tech="evaporative", panel=PANEL, phi=AIT).external_makeup_ml))
    ledger = [CoolingDayLedger(day_id="rep", water_demand_ml=a0_makeup,
                               reclaimed_supply_ml=max(a0["x_ai_ml"], 0.0),
                               freshwater_baseline_ml=a0_makeup,
                               solute_load_kg={"TDS": 443.0 * max(a0["x_ai_ml"], 0.0)
                                               * 1e3 * 1e-6})]
    ledger_checks = []
    for name, cfg in (("A0", dict(policy="A0")),
                      ("A1", dict(policy="A1",
                                  solute_removal_fractions={"TDS": 0.85, "hardness": 0.9},
                                  treatment_energy_kwh_per_ml=0.15)),
                      ("A2", dict(policy="A2", membrane_recovery_fraction=0.75,
                                  membrane_rejection_fractions={"TDS": 0.95},
                                  membrane_energy_kwh_per_ml=0.002))):
        r = evaluate_adaptation(ledger, AdaptationConfig.from_mapping(cfg))
        ledger_checks.append({"policy": name, "status": r.status,
                              "freshwater_saving_ml": r.freshwater_saving_ml,
                              "solute_closure_residual_kg": float(sum(
                                  abs(v) for v in r.solute_closure_residual_kg.values()))
                              if r.solute_closure_residual_kg else 0.0})

    summary = {
        "fixed": {"domain": DOM, "panel": PANEL, "sample": SAMPLE,
                  "pool_scale": POOL, "gap_scale": GAP, "ai_target": AIT,
                  "rule": "Ls", "days_per_year": DAYS_PER_YEAR,
                  "model_days": MODEL_DAYS, "crf_6pct_20yr": CRF,
                  "energy_basis": "annual sum of daily facility_energy_mwh (uniform for all policies)",
                  "A3_basis": "daily_model.tech_annual_basis (E_total=sum daily E; rep day = wet day)"},
        "parameters": {
            "reuse_capex_cny_per_m3d": list(REUSE_CAPEX_CNY_PER_M3D),
            "membrane_kwh_per_m3": list(MEMBRANE_KWH_PER_M3),
            "a1_kwh_per_m3": list(A1_KWH_PER_M3),
            "a1_chem_cny_per_m3": list(A1_CHEM_CNY_PER_M3),
            "carbon_kg_per_kwh": CARBON_KG_PER_KWH},
        "carbon_factor_provenance": "ratio Delta-carbon/Delta-energy in the engine's own "
                                    "intervention_water_energy_carbon.csv (=0.35 kgCO2e/kWh)",
        "declared_parameters_warning": "membrane/A1 energy and chemical intensities are "
                                       "literature-order DECLARED values; must be replaced "
                                       "with cited sources before submission",
        "A3_basis_meta": a3_meta,
        "n_scenarios": int(len(df)),
        "statuses": sorted(df.status.unique().tolist()),
        "S_city_range_ml": [float(df.S_city_ml.min()), float(df.S_city_ml.max())],
        "energy_range_kwh_yr": [float(df.energy_kwh_yr.min()), float(df.energy_kwh_yr.max())],
        "pareto_4d": df[df.pareto_4d][["policy", "variant", "S_city_ml", "energy_kwh_yr",
                                       "carbon_kgco2e_yr", "capex_annual_cny"]]
            .round(3).to_dict(orient="records"),
        "pareto_2d_S_energy": df[df.pareto_S_energy][["policy", "variant", "S_city_ml",
                                                      "energy_kwh_yr"]].round(3)
            .to_dict(orient="records"),
        "infeasible_or_negative": df[df.S_city_ml < 0][["policy", "variant", "S_city_ml"]]
            .round(3).to_dict(orient="records"),
        "ledger_crosscheck": ledger_checks,
        "limitations": [
            "A3 的能耗来自引擎 per-technology 的 technology_pue_adjustment, 与排热湿分 w "
            "无关 (dry +0.12 PUE, hybrid +0.04); 即引擎不给 '越干越耗电' 的连续律, "
            "故 A3 的能耗-水权衡是技术级而非 w 级。",
            "A3 已在**技术年度基座**上求值 (Σ_t E(t) + 湿日代表日), 不再是'典型日'。"
            "热浪期的湿分抬升已由逐日序列体现。",
            "capex 取下限-上限中值, 按 6%/20yr 折现; 未计征地/管网/电贴费。",
            "A1 的 S_city 绝对值 = 0: 仅消去水质惩罚, 不产生新增供给. 相对 A0 的改善 = |A0|。",
        ],
    }
    (HERE / "T13_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print(f"[T13] {len(df)} 方案 | S_city ∈ [{df.S_city_ml.min():,.1f}, {df.S_city_ml.max():,.1f}] ML/yr")
    print(f"  4D-Pareto: {df.pareto_4d.sum()} | 2D(S-能耗)-Pareto: {df.pareto_S_energy.sum()}")
    print(df[df.pareto_4d][["policy", "variant", "S_city_ml", "energy_kwh_yr",
                            "carbon_kgco2e_yr", "capex_annual_cny"]].round(1).to_string(index=False))
    print("  A3 (技术年度基座):")
    print(df[df.policy == "A3"][["variant", "S_city_ml", "E_annual_ml", "wet_frac",
                                 "energy_kwh_yr", "pue"]].round(2).to_string(index=False))
    print("  账本交叉核对:", [(c["policy"], c["status"]) for c in ledger_checks])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
