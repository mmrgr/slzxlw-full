"""T2: 质量-分配联合求解 (替代 T1 的简化 min 判据).

估计量 (与代码一致; 审计 B6 修正了此前 stale 的 docstring):
    S_AI   = (M0 - M) + x_ai        AI 自来水取水节约 (含设施自身替代量 x_ai)
    S_city = S_AI + inc_recl - P0   城市水源取水变化 (守恒形式)
    eta    = S_city / S_AI          仅在 S_AI > 0 时报出, 否则记 NA (审计 B7)
    Delta_QL = [Y(Q1,L1)-Y(Q0,L1)] - [Y(Q1,L2)-Y(Q0,L2)],  Y = S_city

L 维设计 (审计 B4 修正):
    原设计只有两个 L 端点, 但它们**同时**改变了既有用户的 claim 与 capacity,
    使 L 不是单一因子。现改为 2x2 全因子:
        claim    ∈ {0, P0}   —— 既有用户被认定的既得权利
        capacity ∈ {gap, P0} —— 其可用再生水上限
    并保留原 Ld / Ls 作为两个选定端点:
        Ld = (claim=P0, cap=P0);  Ls = (claim=0, cap=gap)
    Q0 固定 CoC (coc_mode='fixed'), Q1 水质限制 (coc_mode='quality_limited')。
    全部经仓库真实模块求解, 未重写规则。
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2] / "07_代码_AI-UWM引擎" / "aiuwm_src"
sys.path.insert(0, str(REPO / "src"))
from aiuwm.data_center import calculate_data_center_plan  # noqa: E402
from aiuwm.full_engine import FullAIUWMModel  # noqa: E402
from aiuwm.reclaimed_allocation import (  # noqa: E402
    JointPlanEvaluation,
    JointQualityRequest,
    solve_joint_quality_allocation,
)

HERE = Path(__file__).resolve().parent
R2 = REPO / "examples" / "cawcc_r2"
DOMAINS = ("ha", "co")
N_DAYS = 730

PANEL_A = {"TDS": 2200.0, "chloride": 500.0}
PANEL_B = {"TDS": 2200.0, "chloride": 500.0, "hardness": 700.0,
           "alkalinity": 500.0, "silica": 150.0}
POTABLE_EXTRA = {"hardness": 120.0, "alkalinity": 100.0, "silica": 10.0}

PHI_GRID = [round(i * 0.05, 2) for i in range(0, 19)]
DP_FRACS = [0.0, 0.5, 1.0, 2.0]


def load_samples() -> pd.DataFrame:
    d = pd.read_csv(HERE.parent / "A4_水化学参数域" / "T6_water_chemistry_samples.csv",
                    encoding="utf-8-sig").rename(columns={"source": "sample"})
    return d[["sample", "sclass", "TDS", "chloride", "hardness",
              "alkalinity", "silica"]].copy()


def quality_dict(row: pd.Series, panel: dict) -> dict:
    return {sp: float(row[sp]) for sp in panel
            if sp in row.index and pd.notna(row.get(sp))}


def drivers_of(row) -> dict:
    return {"temperature_c": float(row.temperature_c),
            "relative_humidity": float(row.relative_humidity_pct),
            "load_factor": float(row.ai_load_factor_a30)}


def baseline(dom: str) -> dict:
    """φ=0 基线: E_total, M0 (逐日 DC 求和) + P0, gap, reuse_elig (整链引擎)."""
    proj = json.loads((R2 / dom / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / dom / "timeseries.csv")

    comp = copy.deepcopy(proj["components"]["AI_DC1"])
    comp["installed_it_capacity_mw"] = 1000.0
    comp["cooling"]["coc_mode"] = "fixed"
    comp["water_sources"]["reclaimed"]["target_fraction"] = 0.0
    comp["water_sources"]["potable"]["target_fraction"] = 1.0
    e_tot = m0 = 0.0
    for _, r in ts.iterrows():
        p = calculate_data_center_plan(comp, pd.Timestamp(r.date), drivers_of(r))
        e_tot += p.evaporation_ml
        m0 += p.external_makeup_ml

    eng = copy.deepcopy(proj)
    dc = eng["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = 1000.0
    dc["cooling_storage_capacity_ml"] = 0.0
    dc["cooling_storage_ml"] = 0.0
    dc["initial_cooling_storage_ml"] = 0.0
    dc["water_sources"]["reclaimed"]["target_fraction"] = 0.0
    dc["water_sources"]["potable"]["target_fraction"] = 1.0
    # 引擎基线样板 (E-6): 与另外 4 处有意重复, 见 daily_model.daily_reuse_supply 的说明
    a = FullAIUWMModel(eng, ts).run().area_daily
    p0 = float(a["reuse_delivered_ml"].sum())
    elig = float((a["demand_industrial_ml"] + a["demand_municipal_misc_ml"]).sum())
    i_rep = int(ts["wet_bulb_c"].sub(ts["wet_bulb_c"].median()).abs().idxmin())
    r = ts.iloc[i_rep]
    return {"domain": dom, "proj": proj, "ts": ts, "E_total": e_tot, "M0": m0,
            "P0": p0, "gap": max(0.0, elig - p0), "reuse_elig": elig,
            "date_rep": pd.Timestamp(r.date), "drivers_rep": drivers_of(r)}


def make_ai_evaluator(comp0, q, bl, q_mode, cache):
    e_tot, date_rep, drv = bl["E_total"], bl["date_rep"], bl["drivers_rep"]

    def evaluate(req: JointQualityRequest, trial: float) -> JointPlanEvaluation:
        frac = float(np.clip(req.target_reclaimed_fraction, 0.0, 1.0))
        key = (q_mode, round(trial, 9), round(frac, 9))
        if key in cache:
            return cache[key]
        comp = copy.deepcopy(comp0)
        comp["cooling"]["coc_mode"] = "fixed" if q_mode == "Q0" else "quality_limited"
        comp["water_sources"]["reclaimed"]["target_fraction"] = frac
        comp["water_sources"]["potable"]["target_fraction"] = 1.0 - frac
        plan = calculate_data_center_plan(
            comp, date_rep, drv,
            reclaimed_available_ml=trial / N_DAYS,
            reclaimed_quality_mg_l=q if q_mode == "Q1" else None)
        evap = float(plan.evaporation_ml)
        g = (float(plan.external_makeup_ml) / evap) if evap > 1e-12 else 0.0
        res = float(plan.quality_solver_residual)
        out = JointPlanEvaluation(
            external_makeup_ml=e_tot * g,
            cycles_of_concentration=float(plan.cycles_of_concentration),
            reclaimed_quality_mg_l={k: float(v) for k, v in q.items()},
            quality_solver_status=str(plan.quality_solver_status),
            quality_solver_residual=(abs(res) if np.isfinite(res) else 0.0))
        cache[key] = out
        return out
    return evaluate


def make_inc_evaluator(capacity: float):
    """既有用户: 无冷却浓缩回路, CoC = 1 (不浓缩), 质量状态平凡收敛."""
    def evaluate(req: JointQualityRequest, trial: float) -> JointPlanEvaluation:
        return JointPlanEvaluation(external_makeup_ml=capacity,
                                   cycles_of_concentration=1.0,
                                   reclaimed_quality_mg_l={},
                                   quality_solver_status="converged",
                                   quality_solver_residual=0.0)
    return evaluate


def m0_for(comp0, q, bl, q_mode) -> float:
    comp = copy.deepcopy(comp0)
    comp["cooling"]["coc_mode"] = "fixed" if q_mode == "Q0" else "quality_limited"
    comp["water_sources"]["reclaimed"]["target_fraction"] = 0.0
    comp["water_sources"]["potable"]["target_fraction"] = 1.0
    p = calculate_data_center_plan(comp, bl["date_rep"], bl["drivers_rep"],
                                   reclaimed_available_ml=0.0,
                                   reclaimed_quality_mg_l=q if q_mode == "Q1" else None)
    g0 = float(p.external_makeup_ml) / max(float(p.evaporation_ml), 1e-12)
    return bl["E_total"] * g0


def main() -> int:
    samples = load_samples()
    bls = {d: baseline(d) for d in DOMAINS}
    for d, b in bls.items():
        print(f"[baseline] {d}: P0={b['P0']:,.0f} ML | 可回用需求={b['reuse_elig']:,.0f} "
              f"| gap={b['gap']:,.0f} | E_total={b['E_total']:,.0f} | M0={b['M0']:,.0f}")

    # ---- Phase 1: CoC 曲线 ----
    crows = []
    for dom, bl in bls.items():
        comp0 = copy.deepcopy(bl["proj"]["components"]["AI_DC1"])
        comp0["installed_it_capacity_mw"] = 1000.0
        for pname, panel in (("A_engine2", PANEL_A), ("B_full", PANEL_B)):
            for _, s in samples.iterrows():
                q = quality_dict(s, panel)
                if not q:
                    continue
                for phi in PHI_GRID:
                    comp = copy.deepcopy(comp0)
                    comp["cooling"]["coc_mode"] = "quality_limited"
                    comp["cooling"]["water_quality_limits"] = dict(panel)
                    comp["water_sources"]["reclaimed"]["target_fraction"] = phi
                    comp["water_sources"]["potable"]["target_fraction"] = 1.0 - phi
                    pq = dict(comp["water_sources"]["potable"].get("quality", {}))
                    if pname == "B_full":
                        for k, v in POTABLE_EXTRA.items():
                            pq.setdefault(k, v)
                    comp["water_sources"]["potable"]["quality"] = pq
                    pl = calculate_data_center_plan(comp, bl["date_rep"], bl["drivers_rep"],
                                                    reclaimed_available_ml=1e9,
                                                    reclaimed_quality_mg_l=q)
                    ev = float(pl.evaporation_ml)
                    crows.append({"domain": dom, "panel": pname, "sample": s["sample"],
                                  "phi_requested": phi,
                                  "CoC": float(pl.cycles_of_concentration),
                                  "g_ratio": (float(pl.external_makeup_ml) / ev) if ev > 1e-12 else np.nan,
                                  "status": str(pl.quality_solver_status)})
    curve = pd.DataFrame(crows)
    curve.to_csv(HERE / "T2_coc_curves.csv", index=False, encoding="utf-8-sig")
    print(f"\n[Phase1] CoC 曲线 {len(curve)} 点; status={curve.status.unique().tolist()}")

    # ---- Phase 2: 四格配对 ----
    rows = []
    for dom, bl in bls.items():
        p0, gap = bl["P0"], bl["gap"]
        comp0 = copy.deepcopy(bl["proj"]["components"]["AI_DC1"])
        comp0["installed_it_capacity_mw"] = 1000.0
        for pname, panel in (("A_engine2", PANEL_A), ("B_full", PANEL_B)):
            for _, s in samples.iterrows():
                q = quality_dict(s, panel)
                if not q:
                    continue
                base_comp = copy.deepcopy(comp0)
                base_comp["cooling"]["water_quality_limits"] = dict(panel)
                pq = dict(base_comp["water_sources"]["potable"].get("quality", {}))
                if pname == "B_full":
                    for k, v in POTABLE_EXTRA.items():
                        pq.setdefault(k, v)
                base_comp["water_sources"]["potable"]["quality"] = pq
                for q_mode in ("Q0", "Q1"):
                    cache: dict = {}
                    ev_ai = make_ai_evaluator(base_comp, q, bl, q_mode, cache)
                    m0 = m0_for(base_comp, q, bl, q_mode)
                    # B4 修正: L 维 = 2x2 全因子 (claim x capacity), 不再是单一"模式"
                    for l_mode, inc_inc, inc_cap in (
                        ("Ld_claimP0_capP0", p0, p0),
                        ("Ls_claim0_capGap", 0.0, gap),
                        ("L_claim0_capP0", 0.0, p0),
                        ("L_claimP0_capGap", p0, gap),
                    ):
                        ev_inc = make_inc_evaluator(inc_cap)
                        for dpf in DP_FRACS:
                            dp = dpf * p0
                            reqs = [
                                JointQualityRequest("AI", target_reclaimed_fraction=0.9,
                                                    potable_baseline_ml=m0),
                                JointQualityRequest("INC", target_reclaimed_fraction=1.0,
                                                    incumbent_reclaimed_ml=inc_inc,
                                                    max_reclaimed_ml=max(inc_inc, inc_cap),
                                                    potable_baseline_ml=gap),
                            ]
                            sid = f"{dom}|{pname}|{s['sample']}|{q_mode}|{l_mode}|{dpf}"
                            r = solve_joint_quality_allocation(
                                sid, p0 + dp, reqs,
                                lambda req, tr, e=ev_ai, i=ev_inc:
                                e(req, tr) if req.consumer_id == "AI" else i(req, tr))
                            ai = next(x for x in r.allocations if x.consumer_id == "AI")
                            inc = next(x for x in r.allocations if x.consumer_id == "INC")
                            M = float(ai.external_makeup_ml)
                            x_ai = float(ai.reclaimed_allocated_ml)
                            inc_recl = float(inc.reclaimed_allocated_ml)
                            # 守恒形式 (与 B2 含既有用户再生水使用一致):
                            #   S_AI   = M0 - (M - x_ai)
                            #   S_city = W_B2 - W_B1 = S_AI + inc_recl - P0
                            s_ai = (m0 - M) + x_ai
                            s_city = s_ai + inc_recl - p0
                            disp = max(0.0, p0 - inc_recl)
                            rows.append({
                                "domain": dom, "panel": pname, "sample": s["sample"],
                                "Q": q_mode, "L": l_mode, "dP_frac": dpf, "dP_ml": dp,
                                "P0_ml": p0, "gap_ml": gap, "M0_ml": m0, "M_ml": M,
                                "x_ai_ml": x_ai, "inc_reclaimed_ml": inc_recl,
                                "displacement_ml": disp,
                                "S_AI_ml": s_ai, "S_city_ml": s_city,
                                # B7: 按预注册, S_AI <= 0 时 eta 记 NA
                                "eta_transfer": (s_city / s_ai) if s_ai > 1e-9 else np.nan,
                                "CoC_ai": float(ai.cycles_of_concentration),
                                "frac_ai": float(ai.reclaimed_fraction),
                                # A26: 该列语义随 Q 而变 —— Q1(quality_limited) 为真实求解状态;
                                # Q0(coc_mode='fixed') **不调用**水质求解器, 其值为占位符。
                                # 故对 Q0 行该列**不可**用于"是否收敛"的判断。
                                # 权威词表见 A26_语义统一/CHI_SEMANTICS.md §4.2。
                                "status": r.status,
                                "status_is_placeholder": bool(q_mode == "Q0"),
                                "quality_solver_invoked": bool(q_mode == "Q1"),
                                "quality_integration_status": r.quality_integration_status,
                                "closure_residual_ml": float(r.closure_residual_ml),
                                "fp_residual_ml": float(r.max_fixed_point_residual_ml),
                                "roots": int(r.root_count), "iterations": int(r.iterations),
                            })
    cells = pd.DataFrame(rows)
    cells.to_csv(HERE / "T2_cell_results.csv", index=False, encoding="utf-8-sig")
    print(f"[Phase2] {len(cells)} 行 | status={cells.status.unique().tolist()} "
          f"| 闭合残差 max={cells.closure_residual_ml.abs().max():.2e} ML "
          f"| 固定点残差 max={cells.fp_residual_ml.max():.2e} | roots={sorted(cells.roots.unique())}")

    # ---- Phase 3: 交互项 (B4: L 维已拆为 claim x capacity) ----
    L_ENDPOINTS = ("Ld_claimP0_capP0", "Ls_claim0_capGap")
    inter = []
    for (dom, panel, sample, dpf), g in cells.groupby(["domain", "panel", "sample", "dP_frac"]):
        piv = g.set_index(["Q", "L"])["S_city_ml"]
        need = [(q, l) for q in ("Q0", "Q1") for l in
                ("Ld_claimP0_capP0", "Ls_claim0_capGap",
                 "L_claim0_capP0", "L_claimP0_capGap")]
        if not all(k in piv.index for k in need):
            continue

        def dq(lbl: str) -> float:
            return float(piv[("Q1", lbl)] - piv[("Q0", lbl)])

        d_ld, d_ls = dq(L_ENDPOINTS[0]), dq(L_ENDPOINTS[1])
        # 固定 cap=gap, claim 由 0 -> P0 的效应
        d_claim = dq("L_claimP0_capGap") - dq("Ls_claim0_capGap")
        # 固定 claim=0, cap 由 gap -> P0 的效应
        d_cap = dq("L_claim0_capP0") - dq("Ls_claim0_capGap")
        inter.append({"domain": dom, "panel": panel, "sample": sample, "dP_frac": dpf,
                      "d_Q_given_Ld_ml": d_ld, "d_Q_given_Ls_ml": d_ls,
                      "d_QL_ml": d_ld - d_ls,
                      "d_Q_claim_effect_ml": d_claim, "d_Q_capacity_effect_ml": d_cap})
    idf = pd.DataFrame(inter)
    idf.to_csv(HERE / "T2_interaction.csv", index=False, encoding="utf-8-sig")

    summary = {
        "n_curve_points": int(len(curve)), "n_cells": int(len(cells)),
        "closure_residual_max_ml": float(cells.closure_residual_ml.abs().max()),
        "fp_residual_max_ml": float(cells.fp_residual_ml.max()),
        "root_counts": sorted(int(x) for x in cells.roots.unique()),
        "statuses": sorted(cells.status.unique().tolist()),
        "baselines": {d: {"P0_ml": b["P0"], "gap_ml": b["gap"],
                          "reuse_elig_ml": b["reuse_elig"], "E_total_ml": b["E_total"]}
                      for d, b in bls.items()},
        "S_city_mean_by_Q_L": {f"{k[0]}|{k[1]}": v for k, v in
                               cells.groupby(["Q", "L"])["S_city_ml"].mean().round(1).items()},
        "d_QL_abs_max_ml": float(idf.d_QL_ml.abs().max()), 
    }
    (HERE / "T2_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print("\n===== S_city (ML) 按 Q x L 分组")
    print(cells.groupby(["Q", "L"])["S_city_ml"]
          .agg(["mean", "min", "max"]).round(0).to_string())
    print(f"\n===== |Delta_QL| 最大 = {summary['d_QL_abs_max_ml']:,.0f} ML")
    print("\n----- 交互项明细 (panel B_full, dP_frac=1.0)")
    print(idf[(idf.panel == "B_full") & (idf.dP_frac == 1.0)]
          .round(0).to_string(index=False))
    print("\n----- T1 vs T2 阈值对照 (panel A_engine2, 水样=AI-UWM model)")
    sub = cells[(cells.panel == "A_engine2")
                & (cells["sample"].str.contains("model", case=False))
                & (cells.Q == "Q1")]
    print(sub.round(1).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
