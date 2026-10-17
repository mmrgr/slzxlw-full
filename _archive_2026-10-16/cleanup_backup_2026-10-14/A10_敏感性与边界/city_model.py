"""共享城市模型封装 (T10-T12 复用).

全部经仓库真实模块求解, 未重写任何规则:
    物理/水化学 : data_center.calculate_data_center_plan (coc_mode='quality_limited')
    分配        : reclaimed_allocation.solve_joint_quality_allocation

冻结口径 (见 A0_预注册/preregistration.md + preregistration_amendment_1.md):
    S_AI   = (M0 - M) + x_ai
    S_city = S_AI + inc_recl - pool
    y      = S_city / M0
    eta    = S_city / S_AI      (仅当 S_AI > 0 时报出, 否则 NA)
    chi    = CoC_lim / CoC_design  (水质严重度因子, 无量纲)

审计教训 (05_方法审计_v1 §A1/D5):
    y = Phi*(w-u) 是代数恒等式; 这里只把它当作**估计量**, 不当作可迁移规律.
    delta 由分配结果决定, 不是外生参数.
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
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from aiuwm.data_center import calculate_data_center_plan  # noqa: E402
from aiuwm.reclaimed_allocation import (  # noqa: E402
    JointPlanEvaluation,
    JointQualityRequest,
    solve_joint_quality_allocation,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                      # 10_论文推进_2026Q4
R2 = REPO / "examples" / "cawcc_r2"
DOMAINS = ("ha", "co")
N_DAYS = 730

# 引擎冷却水质限值占位值 (审计 B3: 会在论文定稿前替换为带引用的准则)
PANEL_A = {"TDS": 2200.0, "chloride": 500.0}
PANEL_B = {"TDS": 2200.0, "chloride": 500.0, "hardness": 700.0,
           "alkalinity": 500.0, "silica": 150.0}
POTABLE_EXTRA = {"hardness": 120.0, "alkalinity": 100.0, "silica": 10.0}
PANELS = {"A_engine2": PANEL_A, "B_full": PANEL_B}

COC_DESIGN_DEFAULT = 5.0


# ----------------------------------------------------------------- 输入
def load_samples() -> pd.DataFrame:
    d = pd.read_csv(ROOT / "A4_水化学参数域" / "T6_water_chemistry_samples.csv",
                    encoding="utf-8-sig")
    return d.copy()


def quality_dict(row: pd.Series, panel: dict) -> dict:
    return {sp: float(row[sp]) for sp in panel
            if sp in row.index and pd.notna(row.get(sp))}


def baseline(dom: str) -> dict:
    summ = json.loads((ROOT / "A7_质量分配联合" / "T2_summary.json")
                      .read_text(encoding="utf-8"))
    b = summ["baselines"][dom]
    ts = pd.read_csv(R2 / dom / "timeseries.csv")
    i = int(ts["wet_bulb_c"].sub(ts["wet_bulb_c"].median()).abs().idxmin())
    r = ts.iloc[i]
    drv = {"temperature_c": float(r.temperature_c),
           "relative_humidity": float(r.relative_humidity_pct),
           "load_factor": float(r.ai_load_factor_a30)}
    return {"domain": dom, "P0": float(b["P0_ml"]), "gap": float(b["gap_ml"]),
            "E_total": float(b["E_total_ml"]),
            "date_rep": pd.Timestamp(r.date), "drivers_rep": drv,
            "proj": json.loads((R2 / dom / "project.json").read_text(encoding="utf-8"))}


BASELINES = {d: baseline(d) for d in DOMAINS}


def base_comp(bl: dict, panel_name: str, phi: float, *,
              coc_design: float = COC_DESIGN_DEFAULT,
              limit_scale: float = 1.0,
              cooling_tech: str | None = None,
              wet_fraction: float | None = None) -> dict:
    """构造 AI 数据中心组件. limit_scale 整体缩放水质限值以控制 chi.

    cooling_tech / wet_fraction 用于 A3 (hybrid/dry 干式或混合冷却) 情景:
    引擎按 technology 自动施加 technology_pue_adjustment (dry +0.12 PUE,
    hybrid +0.04, efficient_evaporative -0.02), 无需外部造参数.
    """
    comp = copy.deepcopy(bl["proj"]["components"]["AI_DC1"])
    comp["installed_it_capacity_mw"] = 1000.0
    comp["cooling"]["coc_mode"] = "quality_limited"
    comp["cooling"]["cycles_of_concentration"] = float(coc_design)
    comp["cooling"]["water_quality_limits"] = {
        k: float(v) * float(limit_scale) for k, v in PANELS[panel_name].items()}
    if cooling_tech is not None:
        comp["cooling"]["technology"] = str(cooling_tech)
    if wet_fraction is not None:
        comp["cooling"]["heat_rejection_wet_fraction"] = float(wet_fraction)
    comp["water_sources"]["reclaimed"]["target_fraction"] = float(phi)
    comp["water_sources"]["potable"]["target_fraction"] = 1.0 - float(phi)
    pq = dict(comp["water_sources"]["potable"].get("quality", {}))
    if panel_name == "B_full":
        for k, v in POTABLE_EXTRA.items():
            pq.setdefault(k, v)
    comp["water_sources"]["potable"]["quality"] = pq
    return comp


def make_evaluators(bl: dict, panel_name: str, q: dict, *,
                    coc_design: float = COC_DESIGN_DEFAULT,
                    limit_scale: float = 1.0,
                    cooling_tech: str | None = None,
                    wet_fraction: float | None = None,
                    e_scale: float = 1.0,
                    period_days: float = N_DAYS,
                    cache: dict | None = None):
    """返回 (ev_ai, ev_inc). 缓存键含 trial 与 target, 保证 available 变化生效.

    e_scale: 蒸发水量相对基线的倍数 (A3 干式/混合冷却通过它把 E 降低传导进来).
    period_days: **本次求解所代表的天数**。分配的 trial 是"该周期的再生水总量",
                 引擎需要**逐日**可得量, 故除以周期天数。

    审计修复:
      M5 缓存键必须含代表日与逐日驱动, 否则 `date_rep` 在窗口之间变化时会命中陈旧计划。
      M6 `period_days` 必须显式化 —— 旧实现硬编码 N_DAYS=730, 于是把 37 天的热浪窗
         可得量除以 730 (差 19.7×), 窗口解的 M 被算成"无回用水"的值。
    """
    e_tot = bl["E_total"] * float(e_scale)
    cache = cache if cache is not None else {}
    bl_key = (str(bl.get("domain")), str(bl.get("date_rep")),
              tuple(sorted((str(k), round(float(v), 6))
                           for k, v in (bl.get("drivers_rep") or {}).items())))
    n_period = max(float(period_days), 1e-12)

    def ev_ai(req: JointQualityRequest, trial: float) -> JointPlanEvaluation:
        frac = float(np.clip(req.target_reclaimed_fraction, 0.0, 1.0))
        key = ("ai", bl_key, round(frac, 9), round(float(trial), 6),
               panel_name, round(coc_design, 6), round(limit_scale, 9),
               str(cooling_tech), (None if wet_fraction is None else round(wet_fraction, 6)),
               round(float(e_scale), 6), round(n_period, 6))
        if key in cache:
            return cache[key]
        comp = base_comp(bl, panel_name, frac, coc_design=coc_design,
                         limit_scale=limit_scale, cooling_tech=cooling_tech,
                         wet_fraction=wet_fraction)
        p = calculate_data_center_plan(comp, bl["date_rep"], bl["drivers_rep"],
                                       reclaimed_available_ml=float(trial) / n_period,
                                       reclaimed_quality_mg_l=q)
        ev = float(p.evaporation_ml)
        g = (float(p.external_makeup_ml) / ev) if ev > 1e-12 else 0.0
        res = float(p.quality_solver_residual)
        out = JointPlanEvaluation(
            external_makeup_ml=e_tot * g,
            cycles_of_concentration=float(p.cycles_of_concentration),
            reclaimed_quality_mg_l={k: float(v) for k, v in q.items()},
            quality_solver_status=str(p.quality_solver_status),
            quality_solver_residual=(abs(res) if math.isfinite(res) else 0.0))
        cache[key] = out
        return out

    def ev_inc(req: JointQualityRequest, trial: float) -> JointPlanEvaluation:
        return JointPlanEvaluation(external_makeup_ml=float(req.max_reclaimed_ml or 0.0),
                                   cycles_of_concentration=1.0,
                                   reclaimed_quality_mg_l={},
                                   quality_solver_status="converged",
                                   quality_solver_residual=0.0)
    return ev_ai, ev_inc


def m0_of(bl: dict, panel_name: str, q: dict, *,
          coc_design: float = COC_DESIGN_DEFAULT, limit_scale: float = 1.0,
          cooling_tech: str | None = None, wet_fraction: float | None = None,
          e_scale: float = 1.0) -> float:
    """无水回用时的外部补水基线 (M0 = E_total × e_scale × M/E).

    审计修复 (M4): 原实现未透传冷却技术与蒸发缩放, 于是对 hybrid/dry 会用**项目默认技术**
    (evaporative) 的 M/E, 且忽略 e_scale, 与调用方传入的 E_total 不自洽。现全部透传。
    """
    comp = base_comp(bl, panel_name, 0.0, coc_design=coc_design,
                     limit_scale=limit_scale, cooling_tech=cooling_tech,
                     wet_fraction=wet_fraction)
    p = calculate_data_center_plan(comp, bl["date_rep"], bl["drivers_rep"],
                                   reclaimed_available_ml=0.0,
                                   reclaimed_quality_mg_l=q)
    g0 = float(p.external_makeup_ml) / max(float(p.evaporation_ml), 1e-12)
    return bl["E_total"] * float(e_scale) * g0


def plan_raw(bl: dict, panel_name: str, q: dict, phi: float, *,
             available_ml_day: float = 1e9,
             coc_design: float = COC_DESIGN_DEFAULT, limit_scale: float = 1.0,
             cooling_tech: str | None = None, wet_fraction: float | None = None):
    """直接取引擎原始计划 (用于读取 PUE/能耗/蒸发等 A3 需要的字段)."""
    comp = base_comp(bl, panel_name, float(phi), coc_design=coc_design,
                     limit_scale=limit_scale, cooling_tech=cooling_tech,
                     wet_fraction=wet_fraction)
    return calculate_data_center_plan(comp, bl["date_rep"], bl["drivers_rep"],
                                      reclaimed_available_ml=float(available_ml_day),
                                      reclaimed_quality_mg_l=q)


def solve_city(bl: dict, panel_name: str, sample: str, q: dict, m0: float,
               pool: float, gap: float, dp: float, ai_target: float,
               *, coc_design: float = COC_DESIGN_DEFAULT,
               limit_scale: float = 1.0,
               cooling_tech: str | None = None,
               wet_fraction: float | None = None,
               e_scale: float = 1.0,
               period_days: float = N_DAYS,
               cache: dict | None = None,
               inc_claim: float = 0.0) -> dict:
    """真实模块求解一个城市情景 (Ls 规则: 既有用户对竞争池主张 0).

    period_days: 本次求解代表的天数 (默认 730 = 冻结基座口径)。
                 窗口化求解必须传入窗口天数, 否则再生水可得量被按 730 天摊薄 (M6)。
    """
    ev_ai, ev_inc = make_evaluators(bl, panel_name, q, coc_design=coc_design,
                                    limit_scale=limit_scale, cooling_tech=cooling_tech,
                                    wet_fraction=wet_fraction, e_scale=e_scale,
                                    period_days=period_days, cache=cache)
    reqs = [
        JointQualityRequest("AI", target_reclaimed_fraction=float(ai_target),
                            potable_baseline_ml=m0),
        JointQualityRequest("INC", target_reclaimed_fraction=1.0,
                            incumbent_reclaimed_ml=inc_claim,
                            max_reclaimed_ml=max(inc_claim, gap, 1e-9),
                            potable_baseline_ml=gap),
    ]
    sid = (f"{bl['domain']}|{panel_name}|{sample}|Ls|{pool:.1f}|{gap:.1f}"
           f"|{dp:.1f}|{ai_target:.3f}|{coc_design:.2f}|{limit_scale:.3f}")
    r = solve_joint_quality_allocation(
        sid, pool + dp, reqs,
        lambda req, tr: ev_ai(req, tr) if req.consumer_id == "AI" else ev_inc(req, tr))
    ai = next(x for x in r.allocations if x.consumer_id == "AI")
    inc = next(x for x in r.allocations if x.consumer_id == "INC")
    M = float(ai.external_makeup_ml)
    x_ai = float(ai.reclaimed_allocated_ml)
    inc_recl = float(inc.reclaimed_allocated_ml)
    s_ai = (m0 - M) + x_ai
    s_city = s_ai + inc_recl - pool
    eta = (s_city / s_ai) if s_ai > 1e-9 else float("nan")
    phi_eff = x_ai / M if M > 1e-9 else 0.0
    coeff = (M / m0) if m0 > 1e-9 else float("nan")
    return {
        "M_ml": M, "x_ai_ml": x_ai, "inc_reclaimed_ml": inc_recl, "pool_ml": pool,
        "dp_ml": dp, "S_AI_ml": s_ai, "S_city_ml": s_city, "y": (s_city / m0) if m0 > 1e-9 else float("nan"),
        "eta_transfer": eta, "phi_eff": phi_eff, "Phi": coeff,
        "CoC_ai": float(ai.cycles_of_concentration),
        "status": r.status, "closure_residual_ml": float(r.closure_residual_ml),
        "roots": int(r.root_count),
    }


def city_outcome(dom: str, panel_name: str, sample: str, *,
                 pool_scale: float = 1.0, gap_scale: float = 1.0,
                 dp_scale: float = 1.0, ai_target: float = 0.7,
                 coc_design: float = COC_DESIGN_DEFAULT,
                 limit_scale: float = 1.0,
                 cooling_tech: str | None = None,
                 wet_fraction: float | None = None,
                 e_scale: float = 1.0,
                 period_days: float = N_DAYS,
                 cache: dict | None = None,
                 samples: pd.DataFrame | None = None) -> dict:
    """归一化控制 -> 物理量 -> 真实求解. 返回 S_city/y/eta/chi 等."""
    samples = load_samples() if samples is None else samples
    bl = BASELINES[dom]
    row = samples[samples["source"] == sample].iloc[0]
    q = quality_dict(row, PANELS[panel_name])
    m0 = m0_of(bl, panel_name, q, coc_design=coc_design, limit_scale=limit_scale,
               cooling_tech=cooling_tech, wet_fraction=wet_fraction, e_scale=e_scale)
    pool = bl["P0"] * float(pool_scale)
    gap = bl["gap"] * float(gap_scale)
    dp = bl["P0"] * float(dp_scale)
    out = solve_city(bl, panel_name, sample, q, m0, pool, gap, dp, ai_target,
                     coc_design=coc_design, limit_scale=limit_scale,
                     cooling_tech=cooling_tech, wet_fraction=wet_fraction,
                     e_scale=e_scale, period_days=period_days, cache=cache)
    out.update({"domain": dom, "panel": panel_name, "sample": sample,
                "pool_scale": float(pool_scale), "gap_scale": float(gap_scale),
                "dp_scale": float(dp_scale), "ai_target": float(ai_target),
                "m0_ml": m0, "chi": float(limit_scale), "e_scale": float(e_scale),
                "period_days": float(period_days)})
    return out


# ----------------------------------------------------------------- 控制空间
CONTROL_BOUNDS = {
    "pool_scale": (0.3, 4.0),
    "gap_scale": (0.3, 4.0),
    "dp_scale": (0.0, 3.0),
    "ai_target": (0.10, 0.95),
}
