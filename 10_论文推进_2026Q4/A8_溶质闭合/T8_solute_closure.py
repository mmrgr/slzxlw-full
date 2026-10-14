"""T8: 冷却-回用链路的逐溶质闭合审计.

三个层次:
 (a) 单塔日账本: 补水带入 -> 蒸发(0) / 飘损 / 排污 / 循环存量, 逐溶质残差;
 (b) 热力学稳态验证: c_loop = CoC * c_makeup 与水平衡 M = (BD+drift)*CoC 是否同时成立;
 (c) 内部回收的累积效应: 求解带内部回收+去除率时循环水浓度的固定点,
     给出"不超限所需的最小去除率 r_min(phi)".

模块用量: quality_state.partition_blowdown_solutes (未重写);
         data_center.calculate_data_center_plan (未重写).

审计修正 (2026-10-14, 对应 05_方法审计_v1 §A4):
  旧版把 `inflow - drift - blowdown` 当作闭合残差, 但稳态下它恒等于 -recirc_return
  (内部回收返回循环的质量份额), 按构造不为零 -> 旧报告把 2.79% 误报为 ~1e-16.
  本版改用正确的稳态守恒 M*c_makeup + recirc_return = (blowdown+drift)*c_loop,
  并分别报告: 真闭合残差、外部账残差、内部回收份额、水量平衡残差。
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(r"C:/Users/mmrgr/Desktop/论文/算力中心/07_代码_AI-UWM引擎/aiuwm_src")
sys.path.insert(0, str(REPO / "src"))
from aiuwm.data_center import calculate_data_center_plan  # noqa: E402
from aiuwm.quality_state import (  # noqa: E402
    QualityState,
    mix_quality_states,
    partition_blowdown_solutes,
    withdraw_quality_state,
)

HERE = Path(__file__).resolve().parent
R2 = REPO / "examples" / "cawcc_r2"
N_DAYS = 730
PANEL_B = {"TDS": 2200.0, "chloride": 500.0, "hardness": 700.0,
           "alkalinity": 500.0, "silica": 150.0}
SOURCE = "IEUA RP-1 (2025, tertiary)"


def load_sample(name: str) -> dict:
    d = pd.read_csv(HERE.parent / "A4_水化学参数域" / "T6_water_chemistry_samples.csv",
                    encoding="utf-8-sig")
    row = d[d.source == name].iloc[0]
    return {k: float(row[k]) for k in ("TDS", "chloride", "hardness", "alkalinity", "silica")
            if pd.notna(row.get(k))}


def baseline(dom: str):
    proj = json.loads((R2 / dom / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / dom / "timeseries.csv")
    i = int(ts["wet_bulb_c"].sub(ts["wet_bulb_c"].median()).abs().idxmin())
    r = ts.iloc[i]
    return proj, pd.Timestamp(r.date), {
        "temperature_c": float(r.temperature_c),
        "relative_humidity": float(r.relative_humidity_pct),
        "load_factor": float(r.ai_load_factor_a30)}


def main() -> int:
    print("=" * 78)
    print("T8 (a)(b) 单塔溶质账本 + 水平衡/质量平衡联立")
    print("=" * 78)
    q = load_sample(SOURCE)
    rows = []
    for dom in ("ha", "co"):
        proj, date_rep, drv = baseline(dom)
        comp0 = copy.deepcopy(proj["components"]["AI_DC1"])
        comp0["installed_it_capacity_mw"] = 1000.0
        comp0["cooling"]["coc_mode"] = "quality_limited"
        comp0["cooling"]["water_quality_limits"] = dict(PANEL_B)
        for phi in (0.0, 0.3, 0.6, 0.9):
            comp = copy.deepcopy(comp0)
            comp["water_sources"]["reclaimed"]["target_fraction"] = phi
            comp["water_sources"]["potable"]["target_fraction"] = 1.0 - phi
            pq = dict(comp["water_sources"]["potable"].get("quality", {}))
            for k, v in {"hardness": 120.0, "alkalinity": 100.0, "silica": 10.0}.items():
                pq.setdefault(k, v)
            comp["water_sources"]["potable"]["quality"] = pq
            pl = calculate_data_center_plan(comp, date_rep, drv,
                                            reclaimed_available_ml=1e9,
                                            reclaimed_quality_mg_l=q)
            coc_rep = float(pl.cycles_of_concentration)      # 引擎自报(设计)CoC
            # 混合补水质量 (按求解器返回的实际掺混比)
            frac = float(pl.quality_solver_reclaimed_fraction)
            pq_full = pq
            c_makeup = {}
            for sp in PANEL_B:
                c_makeup[sp] = frac * q.get(sp, 0.0) + (1.0 - frac) * pq_full.get(sp, 0.0)
            M_day = float(pl.external_makeup_ml)
            evap_day = float(pl.evaporation_ml)
            bd_reported, drift = float(pl.blowdown_ml), float(pl.drift_ml)
            ir = float(comp["cooling"].get("internal_recovery_fraction", 0.0))
            ret_f = float(comp["cooling"].get("blowdown_return_fraction", 1.0))
            # --- 口径诊断 (审计 A4 / C6) ---
            # (i) 有效 CoC 由水量账定: M/(M-E), 内部回收使其高于设计 CoC.
            coc_eff = M_day / max(M_day - evap_day, 1e-12)
            c_loop = {sp: c_makeup[sp] * coc_eff for sp in PANEL_B}
            c_loop_rep = {sp: c_makeup[sp] * coc_rep for sp in PANEL_B}
            # (ii) 水量平衡: M = E + drift + bd_gross*(1-ir) => bd_gross = (M-E-drift)/(1-ir)
            bd_wb_net = max(M_day - evap_day - drift, 0.0)
            bd_gross = bd_wb_net / max(1.0 - ir, 1e-12)
            # 溶质账用**水量自洽**的 bd_gross + 有效 CoC, 使闭合可被真正检验
            part = partition_blowdown_solutes(
                c_loop, bd_gross, ir,
                removal_fraction_by_solute={sp: 0.0 for sp in PANEL_B},
                return_fraction=ret_f)
            # (a) 期账本 —— 稳态守恒: M*c_makeup + recirc_return = (bd_gross + drift)*c_loop
            for sp in PANEL_B:
                inflow = M_day * c_makeup[sp]
                out_drift = drift * c_loop[sp]
                bd_mass = bd_gross * c_loop[sp]
                recirc = part.recovered_return_mass_kg[sp]
                removed = part.removed_mass_kg[sp]
                sewer = part.sewer_return_mass_kg[sp]
                unret = part.unreturned_mass_kg[sp]
                resid = part.residual_kg[sp]
                closure = inflow + recirc - (out_drift + bd_mass)
                ext_out = out_drift + removed + sewer + unret
                rows.append({
                    "domain": dom, "phi_req": phi, "solute": sp,
                    "CoC_reported": coc_rep, "CoC_effective": coc_eff, "frac_actual": frac,
                    "M_ml_day": M_day, "E_ml_day": evap_day,
                    "bd_reported_ml_day": bd_reported, "bd_gross_ml_day": bd_gross,
                    "drift_ml_day": drift,
                    "bd_reported_vs_wb_rel": abs(bd_reported - bd_gross) / max(bd_gross, 1e-12),
                    "water_balance_resid_ml": M_day - evap_day - drift - bd_gross * (1.0 - ir),
                    "c_makeup_mg_l": c_makeup[sp], "c_loop_mg_l": c_loop[sp],
                    "c_loop_reported_mg_l": c_loop_rep[sp],
                    "closure_residual_reported_coc_kg_day":
                        c_makeup[sp] * M_day * (1.0 - coc_rep / max(coc_eff, 1e-12)),
                    "inflow_kg_day": inflow,
                    "out_drift_kg_day": out_drift, "out_blowdown_kg_day": bd_mass,
                    "recirc_return_kg_day": recirc, "removed_kg_day": removed,
                    "sewer_kg_day": sewer, "unreturned_kg_day": unret,
                    "external_out_kg_day": ext_out,
                    "closure_residual_kg_day": closure,
                    "closure_rel": abs(closure) / max(inflow, 1e-12),
                    "external_closure_kg_day": inflow - ext_out,
                    "recirc_share": recirc / max(inflow, 1e-12),
                    "solute_partition_residual_kg_day": resid,
                })
    led = pd.DataFrame(rows)
    led.to_csv(HERE / "T8_solute_ledger.csv", index=False, encoding="utf-8-sig")
    print("\n--- (a) 真溶质闭合残差 |M*c_makeup + recirc - (bd_gross+drift)*c_L| (max / mean)")
    print(led.groupby("solute")["closure_residual_kg_day"].agg(
        ["max", "mean"]).to_string(float_format=lambda x: f"{x:.3e}"))
    print(f"外部账残差 (inflow - external_out) max = "
          f"{led.external_closure_kg_day.abs().max():.3e} kg/day")
    print(f"内部回收份额 recirc/inflow: "
          f"{led.recirc_share.min():.4f} – {led.recirc_share.max():.4f} "
          f"(旧口径误把它当作'闭合残差', 见审计 A4)")
    print(f"solute_partition_residual (模块内部分割) max = "
          f"{led.solute_partition_residual_kg_day.abs().max():.3e} kg/day")
    print(f"[口径诊断] 引擎自报 blowdown 与水量平衡反解值相对差 max = "
          f"{led.bd_reported_vs_wb_rel.max():.3%}  (审计 C6: 引擎内部口径不一致)")

    print("\n--- (b) 水量平衡、CoC 口径与 c_loop/c_makeup 自洽")
    chk = []
    for (dom, phi), g in led.groupby(["domain", "phi_req"]):
        r0 = g.iloc[0]
        ratio = r0.c_loop_mg_l / max(r0.c_makeup_mg_l, 1e-12)
        wb = r0.water_balance_resid_ml
        chk.append({"domain": dom, "phi": phi,
                    "CoC_reported": round(r0.CoC_reported, 4),
                    "CoC_effective": round(r0.CoC_effective, 4),
                    "rel_gap": round(abs(r0.CoC_reported - r0.CoC_effective)
                                     / max(r0.CoC_effective, 1e-12), 5),
                    "c_loop/c_makeup": round(ratio, 6),
                    "water_balance_resid_ml": round(wb, 9),
                    "bd_reported_ml": round(r0.bd_reported_ml_day, 3),
                    "bd_gross_ml": round(r0.bd_gross_ml_day, 3),
                    "match": abs(r0.CoC_effective - ratio) < 1e-9,
                    "water_balance_ok": abs(wb) < 1e-6 * max(r0.M_ml_day, 1e-12)})
    cdf = pd.DataFrame(chk)
    print(cdf.to_string(index=False))
    print(f"c_loop/c_makeup == CoC_effective 全部通过: {bool(cdf.match.all())}")
    print(f"水量平衡 |M-E-drift-bd_gross(1-ir)| max = "
          f"{cdf.water_balance_resid_ml.abs().max():.3e} ML/day  "
          f"(全部闭合: {bool(cdf.water_balance_ok.all())})")
    print(f"[口径诊断 C6] 引擎自报 CoC 与水量账有效 CoC 相对差 max = "
          f"{cdf.rel_gap.max():.3%} (内部回收抬升有效浓缩倍数)")
    print(f"[口径诊断 C6] 若直接用引擎自报 CoC 做溶质账, 表观不闭合 max = "
          f"{led.closure_residual_reported_coc_kg_day.abs().max():.3e} kg/day")

    # ---- (c) 内部回收的累积效应与最小去除率 ----
    print("\n" + "=" * 78)
    print("T8 (c) 内部回收累积: 不超限所需最小逐溶质去除率 r_min")
    print("=" * 78)
    crows = []
    for dom in ("ha", "co"):
        proj, date_rep, drv = baseline(dom)
        comp0 = copy.deepcopy(proj["components"]["AI_DC1"])
        comp0["installed_it_capacity_mw"] = 1000.0
        comp0["cooling"]["coc_mode"] = "quality_limited"
        comp0["cooling"]["water_quality_limits"] = dict(PANEL_B)
        ir = float(comp0["cooling"].get("internal_recovery_fraction", 0.0))
        for phi in (0.3, 0.6, 0.9):
            comp = copy.deepcopy(comp0)
            comp["water_sources"]["reclaimed"]["target_fraction"] = phi
            comp["water_sources"]["potable"]["target_fraction"] = 1.0 - phi
            pq = dict(comp["water_sources"]["potable"].get("quality", {}))
            for k, v in {"hardness": 120.0, "alkalinity": 100.0, "silica": 10.0}.items():
                pq.setdefault(k, v)
            comp["water_sources"]["potable"]["quality"] = pq
            pl = calculate_data_center_plan(comp, date_rep, drv,
                                            reclaimed_available_ml=1e9,
                                            reclaimed_quality_mg_l=q)
            coc = float(pl.cycles_of_concentration)
            frac = float(pl.quality_solver_reclaimed_fraction)
            evap = float(pl.evaporation_ml)
            for sp in PANEL_B:
                c_m = frac * q.get(sp, 0.0) + (1 - frac) * pq.get(sp, 0.0)
                lim = PANEL_B[sp]
                if c_m <= 0:
                    continue
                # 稳态 c_L 固定点: M c_m = (BD+drift) c_L + BD*ir*r*c_L - BD*ir*(1-r)*c_L
                #  M = E*coc/(coc-1) 已由计划给出; BD = E/(coc-1) - drift
                M = evap * coc / (coc - 1.0)
                drift = M * 0.0002
                bd = max(evap / (coc - 1.0) - drift, 0.0)
                for r in (0.0, 0.05, 0.10, 0.20, 0.50):
                    cL = c_m * coc                              # 初值
                    for _ in range(200):
                        inflow = M * c_m + bd * ir * (1 - r) * cL
                        outflow_coef = (bd + drift) + bd * ir * r
                        cL_new = inflow / outflow_coef if outflow_coef > 0 else 0.0
                        if abs(cL_new - cL) < 1e-12:
                            cL = cL_new
                            break
                        cL = 0.5 * (cL + cL_new)
                    crows.append({"domain": dom, "phi": phi, "solute": sp, "r_removal": r,
                                  "c_L_mg_l": cL, "limit_mg_l": lim,
                                  "exceeds_limit": bool(cL > lim),
                                  "CoC_effective": (cL / c_m) if c_m > 0 else np.nan})
    cdf2 = pd.DataFrame(crows)
    cdf2.to_csv(HERE / "T8_recirc_accumulation.csv", index=False, encoding="utf-8-sig")
    piv = cdf2.pivot_table(index=["domain", "phi", "solute"], columns="r_removal",
                           values="CoC_effective")
    print("\n有效 CoC (c_L/c_makeup) 随内部去除率变化:")
    print(piv.round(2).to_string())
    rmin = []
    for (dom, phi, sp), g in cdf2.groupby(["domain", "phi", "solute"]):
        ok = g[~g.exceeds_limit]
        rmin.append({"domain": dom, "phi": phi, "solute": sp,
                     "r_min_for_compliance": float(ok.r_removal.min()) if len(ok) else np.nan})
    rdf = pd.DataFrame(rmin)
    rdf.to_csv(HERE / "T8_min_removal.csv", index=False, encoding="utf-8-sig")
    print("\nr_min (使循环水浓度不超限):")
    print(rdf.pivot_table(index=["solute"], columns="phi", values="r_min_for_compliance",
                          aggfunc="max").to_string())

    summary = {
        "closure_definition": "steady state: M*c_makeup + recirc_return = (blowdown+drift)*c_loop",
        "closure_residual_max_kg_day": float(led.closure_residual_kg_day.abs().max()),
        "closure_rel_max": float(led.closure_rel.max()),
        "external_closure_max_kg_day": float(led.external_closure_kg_day.abs().max()),
        "recirc_share_range": [float(led.recirc_share.min()), float(led.recirc_share.max())],
        "partition_residual_max_kg_day": float(led.solute_partition_residual_kg_day.abs().max()),
        "water_balance_resid_max_ml": float(cdf.water_balance_resid_ml.abs().max()),
        "engine_blowdown_vs_waterbalance_max_rel": float(led.bd_reported_vs_wb_rel.max()),
        "engine_coc_reported_vs_effective_max_rel": float(cdf.rel_gap.max()),
        "closure_with_reported_coc_max_kg_day":
            float(led.closure_residual_reported_coc_kg_day.abs().max()),
        "coc_definition_selfconsistent": bool(cdf.match.all()),
        "n_ledger_rows": int(len(led)),
        "r_min_table": rdf.groupby("solute")["r_min_for_compliance"].max().to_dict(),
    }
    (HERE / "T8_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
