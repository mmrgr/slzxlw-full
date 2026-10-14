"""日尺度城市模型封装 (T5 / T14 复用) —— 审计 B5 的修复件。

全部经仓库真实模块求解, 不重写任何规则:
    daily 物理/水化学 : data_center.calculate_data_center_plan  (逐日 date + 逐日 drivers)
    分配              : reclaimed_allocation.solve_joint_quality_allocation
    整链再生水供给     : full_engine.FullAIUWMModel -> area_daily.reuse_delivered_ml

为什么需要它 (审计 B5):
    T2/T9 用"湿球中位日"的 M/E 比 × 年蒸发总量做年度缩放。
    本封装在 730 天上逐日求解, 直接给出 E(t)/M(t)/湿分(t)/PUE(t),
    使"最不利时段"可测 —— 这是指标 C (热浪期高峰供水能力) 的前置条件。

口径 (与 A0_预注册/preregistration.md 一致):
    E(t)    : 冷却塔逐日蒸发 (不含排污与飘损)
    M(t)    : 数据中心逐日总外部补水
    M/E     : 由 CoC 决定; 蒸发式下经数值验证为**逐日常数**, 故年缩放对蒸发式无偏
    湿分 w(t): hybrid/dry 下随湿球温度变化 —— 季节性的物理来源
"""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(r"C:/Users/mmrgr/Desktop/论文/算力中心/07_代码_AI-UWM引擎/aiuwm_src")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                                  # 10_论文推进_2026Q4
SIB = ROOT / "A10_敏感性与边界"                      # 复用 city_model 的面板/基座定义
for p in (str(REPO / "src"), str(SIB)):
    if p not in sys.path:
        sys.path.insert(0, p)

import city_model as cm  # noqa: E402  复用 PANELS / base_comp / quality_dict / baselines
from aiuwm.data_center import calculate_data_center_plan  # noqa: E402
from aiuwm.full_engine import FullAIUWMModel  # noqa: E402
from aiuwm.reclaimed_allocation import (  # noqa: E402
    JointPlanEvaluation,
    JointQualityRequest,
    solve_joint_quality_allocation,
)

R2 = REPO / "examples" / "cawcc_r2"
DOMAINS = ("ha", "co")
N_DAYS = 730
COC_DESIGN = cm.COC_DESIGN_DEFAULT

# 热浪窗定义 (事先固定, 见 08_阶段结果_T5-T14.md)
HEATWAVE_WB_QUANTILE = 0.95      # 湿球 ≥ p95
HYBRID_FULL_WET_WB_C = 24.0      # 引擎 hybrid 全湿阈值 (hybrid_full_wet_bulb_c 默认值)

TECHNOLOGIES = ("evaporative", "hybrid", "dry")


# ----------------------------------------------------------------- 输入
def load_ts(dom: str) -> pd.DataFrame:
    return pd.read_csv(R2 / dom / "timeseries.csv", parse_dates=["date"])


def load_cols(dom: str) -> list[str]:
    ts = load_ts(dom)
    return [c for c in ts.columns if c.startswith("ai_load_factor")]


def drivers_row(r, load_col: str) -> dict:
    """构造逐日 drivers: 引擎在 load_mode='timeseries' 下按列名取值。"""
    return {"temperature_c": float(r.temperature_c),
            "relative_humidity": float(r.relative_humidity_pct),
            load_col: float(r[load_col])}


def sample_quality(panel_name: str, sample: str) -> dict:
    d = cm.load_samples()
    row = d[d["source"] == sample].iloc[0]
    return cm.quality_dict(row, cm.PANELS[panel_name])


# ----------------------------------------------------------------- 逐日物理
def comp_for(dom: str, panel_name: str, phi: float, tech: str, lock: float,
             load_col: str, coc_mode: str = "quality_limited",
             wet_fraction: float | None = None) -> dict:
    comp = cm.base_comp(cm.BASELINES[dom], panel_name, float(phi),
                        coc_design=COC_DESIGN, limit_scale=float(lock),
                        cooling_tech=tech, wet_fraction=wet_fraction)
    comp["cooling"]["coc_mode"] = str(coc_mode)
    comp["load_mode"] = "timeseries"
    comp["load_factor_column"] = load_col
    return comp


def daily_plan_series(dom: str, sample: str, *, tech: str = "evaporative",
                      panel: str = "B_full", phi: float = 0.0,
                      limit_scale: float = 1.0,
                      wet_fraction: float | None = None,
                      load_col: str = "ai_load_factor_a30",
                      coc_mode: str = "quality_limited",
                      ts: pd.DataFrame | None = None) -> pd.DataFrame:
    """逐日求解 AI 计划, 返回 730 行日序列 (E/M/湿分/PUE/能量/排污/回流/耗水)。

    ts: 可选的驱动序列 (默认读 examples/cawcc_r2/{dom}/timeseries.csv)。
        合成气象的**实现敏感性**检验需要传入备用实现 (见 T14e)。
    """
    ts = load_ts(dom) if ts is None else ts.reset_index(drop=True)
    q = sample_quality(panel, sample)
    comp = comp_for(dom, panel, phi, tech, limit_scale, load_col,
                    coc_mode=coc_mode, wet_fraction=wet_fraction)
    avail = 1e9 if phi > 0 else None
    recs = []
    for _, r in ts.iterrows():
        p = calculate_data_center_plan(comp, pd.Timestamp(r.date),
                                       drivers_row(r, load_col),
                                       reclaimed_available_ml=avail,
                                       reclaimed_quality_mg_l=q)
        recs.append({
            "date": pd.Timestamp(r.date),
            "temp_c": float(r.temperature_c),
            "rh_pct": float(r.relative_humidity_pct),
            "wet_bulb_c": float(r.wet_bulb_c),
            "rain_mm": float(r.rainfall_mm),
            "reservoir_inflow_ml": float(r.reservoir_inflow_ml),
            "load_factor": float(r[load_col]),
            "evaporation_ml": float(p.evaporation_ml),
            "drift_ml": float(p.drift_ml),
            "blowdown_ml": float(p.blowdown_ml),
            "internal_recovery_ml": float(p.internal_recovery_ml),
            "external_makeup_ml": float(p.external_makeup_ml),
            "consumption_ml": float(p.consumption_ml),
            "return_flow_ml": float(p.return_flow_ml),
            "wet_fraction": float(p.wet_cooling_fraction),
            "pue": float(p.pue),
            "facility_energy_mwh": float(p.facility_energy_mwh),
            "coc": float(p.cycles_of_concentration),
            "target_reclaimed_fraction": float(p.target_reclaimed_fraction),
            "reclaimed_fraction_used": float(
                p.quality_solver_reclaimed_fraction
                if p.quality_solver_status not in ("not_applicable",)
                else p.target_reclaimed_fraction),
            "solver_status": str(p.quality_solver_status),
            "solver_residual": float(p.quality_solver_residual),
        })
    df = pd.DataFrame(recs)
    df["ratio_M_E"] = np.where(df.evaporation_ml > 1e-12,
                               df.external_makeup_ml / df.evaporation_ml.replace(0, np.nan),
                               np.nan)
    return df


def daily_reuse_supply(dom: str) -> pd.DataFrame:
    """整链引擎的逐日再生水交付序列 (= 冻结口径 P0 的日分解)。"""
    bl = cm.BASELINES[dom]
    ts = load_ts(dom)
    eng = copy.deepcopy(bl["proj"])
    dc = eng["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = 1000.0
    for k in ("cooling_storage_capacity_ml", "cooling_storage_ml",
              "initial_cooling_storage_ml"):
        dc[k] = 0.0
    dc["water_sources"]["reclaimed"]["target_fraction"] = 0.0
    dc["water_sources"]["potable"]["target_fraction"] = 1.0
    a = FullAIUWMModel(eng, ts).run().area_daily
    keep = ["date", "reuse_delivered_ml", "potable_delivered_ml",
            "demand_industrial_ml", "demand_municipal_misc_ml",
            "sanitary_sewage_ml", "runoff_to_sewer_ml"]
    keep = [c for c in keep if c in a.columns]
    out = a[keep].copy()
    out["date"] = pd.to_datetime(out["date"])
    return out


# ----------------------------------------------------------------- 技术年度基座
def tech_annual_basis(dom: str, tech: str, *, sample: str = "IEUA RP-1 (2025, tertiary)",
                      panel: str = "B_full", phi: float = 0.7,
                      wet_fraction: float | None = None, limit_scale: float = 1.0,
                      load_col: str = "ai_load_factor_a30") -> tuple[dict, dict]:
    """构造某冷却技术的**年度基座** (供 T13 的 A3 使用)。

    为什么需要 (审计 M7):
        `city_model.city_outcome` 用域内"湿球中位日"作代表日; 但 hybrid/dry 的湿球中位日
        恰好是**零蒸发日** → E=0 → g=M/E 退化为 0 → 该技术的全部水量被算成 0。
        于是 T13 的 A3 整块失效。

    做法:
        E_total     = 真实逐日求和的年总蒸发 (已含技术效应)
        date_rep    = 该技术**湿日**中位湿球日 (无湿日则退化为窗口内中位日)
        period_days = 730

    返回 (bl, meta)。meta 含年蒸发 / 年设施能耗 / PUE / 湿分 / 零湿日数。
    """
    ts = load_ts(dom)
    ser = daily_plan_series(dom, sample, tech=tech, panel=panel, phi=phi,
                            limit_scale=limit_scale, wet_fraction=wet_fraction,
                            load_col=load_col)
    E = ser.evaporation_ml.to_numpy(dtype=float)
    wb = ts.wet_bulb_c.to_numpy(dtype=float)
    wet = E > 1e-9
    idx = np.where(wet)[0]
    degenerate = False
    if idx.size == 0:
        idx = np.arange(len(ts))
        degenerate = True
    i_rep = int(idx[int(np.argmin(np.abs(wb[idx] - np.median(wb[idx]))))])
    r = ts.iloc[i_rep]
    bl = dict(cm.BASELINES[dom])
    bl["E_total"] = float(E.sum())
    bl["date_rep"] = pd.Timestamp(r.date)
    bl["drivers_rep"] = {"temperature_c": float(r.temperature_c),
                         "relative_humidity": float(r.relative_humidity_pct),
                         "load_factor": float(r[load_col])}
    meta = {
        "domain": dom, "tech": tech, "wet_fraction_override": wet_fraction,
        "rep_day": str(pd.Timestamp(r.date).date()),
        "degenerate_no_wet_day": bool(degenerate),
        "E_annual_ml_730d": float(E.sum()),
        "E_annual_ml_yr": float(E.sum() / 2.0),
        "energy_mwh_yr": float(ser.facility_energy_mwh.sum() / 2.0),
        "energy_kwh_yr": float(ser.facility_energy_mwh.sum() / 2.0 * 1000.0),
        "pue_mean": float(ser.pue.mean()),
        "wet_frac_mean": float(ser.wet_fraction.mean()),
        "n_zero_wet_days": int((~wet).sum()),
        "n_days": int(len(ser)),
    }
    return bl, meta


# ----------------------------------------------------------------- 日尺度城市解
def daily_city_outcome(dom: str, sample: str, date, drivers: dict, q: dict, *,
                       m0_day: float, pool_day: float, gap_day: float, dp_day: float,
                       ai_target: float, panel: str = "B_full",
                       tech: str = "evaporative", limit_scale: float = 1.0,
                       load_col: str = "ai_load_factor_a30",
                       e_ref_day: float | None = None,
                       period_days: float = 1.0,
                       cache: dict | None = None,
                       inc_claim: float = 0.0) -> dict:
    """单日城市情景求解 —— 评估器语义**逐条对齐** city_model.make_evaluators。

    与 730 天版的唯一差别是时间步 = 1 天:
        AI 侧 external_makeup = E_period * (M_repday / E_repday)
            —— 与年度版 `e_tot * g` 结构**完全相同**, 只是期间总蒸发换成当日蒸发;
               故 `e_ref_day` 必须传**当日 phi=0 的蒸发量** (期间总蒸发)。
        INC 侧 external_makeup = req.max_reclaimed_ml
            —— 与年度版一致 (既有用户的基准需求 = 其缺口)。
               旧版返回 0 会让既有用户"零需求", 导致分配结果与年度模块不可比 (审计 M1)。

    规则本身仍调用仓库已评审函数 solve_joint_quality_allocation, 未改写。
    """
    cache = cache if cache is not None else {}
    comp = comp_for(dom, panel, 0.0, tech, limit_scale, load_col)
    comp["water_sources"]["reclaimed"]["target_fraction"] = 0.0  # 由 ev_ai 内部按 frac 设
    avail = 1e9
    n_period = max(float(period_days), 1e-12)   # 单日步长 -> 1.0

    def ev_ai(req: JointQualityRequest, trial: float) -> JointPlanEvaluation:
        frac = float(np.clip(req.target_reclaimed_fraction, 0.0, 1.0))
        key = ("d", dom, panel, sample, str(tech), round(limit_scale, 6),
               round(frac, 6), round(float(trial), 9), load_col, str(date),
               round(n_period, 6),
               None if e_ref_day is None else round(float(e_ref_day), 9))
        if key in cache:
            return cache[key]
        c = copy.deepcopy(comp)
        c["water_sources"]["reclaimed"]["target_fraction"] = frac
        c["water_sources"]["potable"]["target_fraction"] = 1.0 - frac
        p = calculate_data_center_plan(c, pd.Timestamp(date), drivers,
                                       reclaimed_available_ml=min(float(trial) / n_period,
                                                                  avail),
                                       reclaimed_quality_mg_l=q)
        ev = float(p.evaporation_ml)
        g = (float(p.external_makeup_ml) / ev) if ev > 1e-12 else 0.0
        e_period = float(e_ref_day) if e_ref_day is not None else ev
        out = JointPlanEvaluation(
            external_makeup_ml=e_period * g,
            cycles_of_concentration=float(p.cycles_of_concentration),
            reclaimed_quality_mg_l={k: float(v) for k, v in q.items()},
            quality_solver_status=str(p.quality_solver_status),
            quality_solver_residual=(abs(float(p.quality_solver_residual))
                                     if math.isfinite(float(p.quality_solver_residual)) else 0.0))
        cache[key] = out
        return out

    def ev_inc(req: JointQualityRequest, trial: float) -> JointPlanEvaluation:
        return JointPlanEvaluation(external_makeup_ml=float(req.max_reclaimed_ml or 0.0),
                                   cycles_of_concentration=1.0,
                                   reclaimed_quality_mg_l={},
                                   quality_solver_status="converged",
                                   quality_solver_residual=0.0)

    reqs = [
        JointQualityRequest("AI", target_reclaimed_fraction=float(ai_target),
                            potable_baseline_ml=float(m0_day)),
        JointQualityRequest("INC", target_reclaimed_fraction=1.0,
                            incumbent_reclaimed_ml=float(inc_claim),
                            max_reclaimed_ml=max(float(inc_claim), float(gap_day), 1e-12),
                            potable_baseline_ml=float(gap_day)),
    ]
    sid = (f"{dom}|{panel}|{sample}|Ls|d{date}|p{pool_day:.3f}|g{gap_day:.3f}"
           f"|d{dp_day:.3f}|a{ai_target:.3f}|{tech}|{limit_scale:.3f}")
    r = solve_joint_quality_allocation(
        sid, float(pool_day) + float(dp_day), reqs,
        lambda req, tr: ev_ai(req, tr) if req.consumer_id == "AI" else ev_inc(req, tr))
    ai = next(x for x in r.allocations if x.consumer_id == "AI")
    inc = next(x for x in r.allocations if x.consumer_id == "INC")
    M = float(ai.external_makeup_ml)
    x_ai = float(ai.reclaimed_allocated_ml)
    inc_recl = float(inc.reclaimed_allocated_ml)
    s_ai = (float(m0_day) - M) + x_ai
    s_city = s_ai + inc_recl - float(pool_day)
    return {"M_ml": M, "x_ai_ml": x_ai, "inc_reclaimed_ml": inc_recl,
            "S_AI_ml": s_ai, "S_city_ml": s_city,
            "eta_transfer": (s_city / s_ai) if s_ai > 1e-9 else float("nan"),
            "phi_eff": (x_ai / M) if M > 1e-9 else 0.0,
            "CoC_ai": float(ai.cycles_of_concentration),
            "status": r.status, "closure_residual_ml": float(r.closure_residual_ml),
            "roots": int(r.root_count)}
