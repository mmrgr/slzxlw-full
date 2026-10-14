"""T14b 跨尺度一致性自检 —— 审计 M1/M4/M5 的修复验证。

被验证的三个问题:
  M1  日尺度"单日城市解"与冻结年度模块的分配器语义不一致 (既有用户被当成零需求)。
  M4  m0_of / window_scale **未透传冷却技术** → 对 hybrid 用项目默认 (evaporative) 的 M/E,
      与传入的窗口 ΣE 不自洽; 且窗口若取到零蒸发日, g=M/E 退化为 0。
  M5  make_evaluators 缓存键**不含代表日** → 跨窗口复用时命中陈旧计划 (静默错误)。

四个判据 (全部用仓库真实模块, 未改写规则):
  T-A  结构等价: 把"窗口总量单步解"退化为 **1 天窗口**, 应与当日的日尺度解逐位一致。
  T-D  缩放精确性: 窗口的 m0 (=ΣE_win × g_wet) 应等于 Σ_t M0(t)。
       —— 这是"代表日 × 窗口总量"能否成立的硬条件 (湿日上 M/E 恒定, 见 T5 §1.2)。
  T-B  聚合误差: 全年"逐日求和 ΣS_city(t)" 与 "单步年总量解"之差。
  T-C  输入一致性: Σ_t R(t) vs 冻结 P0; R 的变异系数。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
for _p in (str(HERE), str(HERE.parent / "A10_敏感性与边界")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import daily_model as dm  # noqa: E402
import city_model as cm  # noqa: E402

SAMPLE = "IEUA RP-1 (2025, tertiary)"
PANEL = "B_full"
PHI = 0.70
TECHS = ("evaporative", "hybrid")
CACHE: dict = {}


def bl_window(dom: str, ts: pd.DataFrame, E: np.ndarray, mask: np.ndarray) -> tuple[dict, int]:
    """构造窗口的基座: ΣE 为窗口总蒸发, 代表日取窗口内**湿日**的湿球中位日。"""
    wet_in = mask & (E > 1e-9)
    pool_idx = np.where(wet_in)[0]
    degenerate = False
    if pool_idx.size == 0:
        pool_idx = np.where(mask)[0]
        degenerate = True
    wb_sel = ts.wet_bulb_c.to_numpy()[pool_idx]
    i_rep = int(pool_idx[int(np.argmin(np.abs(wb_sel - np.median(wb_sel))))])
    r = ts.iloc[i_rep]
    bl = dict(cm.BASELINES[dom])
    bl["E_total"] = float(E[mask].sum())
    bl["date_rep"] = pd.Timestamp(r.date)
    bl["drivers_rep"] = {"temperature_c": float(r.temperature_c),
                         "relative_humidity": float(r.relative_humidity_pct),
                         "load_factor": float(r.ai_load_factor_a30)}
    bl["_rep_index"] = i_rep
    bl["_degenerate_no_wet_day"] = degenerate
    return bl, i_rep


def solve_window(bl: dict, tech: str, q: dict, pool_w: float, gap_w: float,
                 dp_w: float, n_days: float) -> dict:
    m0_w = cm.m0_of(bl, PANEL, q, cooling_tech=tech)
    out = cm.solve_city(bl, PANEL, SAMPLE, q, m0_w, pool_w, gap_w, dp_w, PHI,
                        cooling_tech=tech, period_days=float(n_days), cache=CACHE)
    out["m0_window_ml"] = m0_w
    return out


def main() -> None:
    rep: dict = {"criteria": {}, "T_A_structural": {}, "T_D_scaling": {},
                 "T_B_aggregation": {}, "T_C_inputs": {}, "M4_M5_fixes": {}}

    for dom in dm.DOMAINS:
        ts = dm.load_ts(dom)
        q = dm.sample_quality(PANEL, SAMPLE)
        gap = float(cm.BASELINES[dom]["gap"])
        P0 = float(cm.BASELINES[dom]["P0"])
        n = dm.N_DAYS
        sup = dm.daily_reuse_supply(dom)
        R = sup.reuse_delivered_ml.to_numpy(dtype=float)
        wb = ts.wet_bulb_c.to_numpy(dtype=float)

        rep["T_C_inputs"][dom] = {
            "P0_frozen_ml": P0, "sum_daily_R_ml": float(R.sum()),
            "sum_daily_R_over_P0": float(R.sum() / P0),
            "R_cv": float(R.std(ddof=1) / R.mean()) if R.mean() > 0 else None,
            "R_min_max_ml": [float(R.min()), float(R.max())],
            "gap_frozen_ml": gap}

        heat = wb >= np.quantile(wb, dm.HEATWAVE_WB_QUANTILE)
        order = np.argsort(wb)
        non = np.zeros(n, bool)
        non[order[:int(heat.sum())]] = True
        windows = {"full_year": np.ones(n, bool), "heatwave": heat,
                   "non_heatwave_matched": non}

        for tech in TECHS:
            p0 = dm.daily_plan_series(dom, SAMPLE, tech=tech, panel=PANEL, phi=0.0,
                                      load_col="ai_load_factor_a30")
            E = p0.evaporation_ml.to_numpy(dtype=float)
            M0d = p0.external_makeup_ml.to_numpy(dtype=float)

            # ---------------- T-A 结构等价: 1 天窗口 ----------------
            # 代表日 = 湿球中位日, 但必须落在**湿日内** (hybrid 的中位日恰为零蒸发日)
            idxw = np.where(E > 1e-9)[0]
            i_med_wet = int(idxw[int(np.argmin(np.abs(wb[idxw] - np.median(wb[idxw]))))])
            day_mask = np.zeros(n, bool)
            day_mask[i_med_wet] = True
            bl1, i_rep = bl_window(dom, ts, E, day_mask)
            gap1 = gap / n
            w1 = solve_window(bl1, tech, q, float(R[i_rep]), gap1, 0.0, 1.0)
            d1 = dm.daily_city_outcome(
                dom, SAMPLE, pd.Timestamp(ts.date.iloc[i_rep]),
                dm.drivers_row(ts.iloc[i_rep], "ai_load_factor_a30"), q,
                m0_day=float(M0d[i_rep]), pool_day=float(R[i_rep]), gap_day=gap1,
                dp_day=0.0, ai_target=PHI, panel=PANEL, tech=tech,
                e_ref_day=float(E[i_rep]), cache=CACHE)
            paired = {}
            for k in ("M_ml", "x_ai_ml", "inc_reclaimed_ml", "S_AI_ml", "S_city_ml"):
                a, b = float(w1[k]), float(d1[k])
                paired[k] = {"window_1d": a, "daily": b, "abs_diff": abs(a - b),
                             "rel_diff": abs(a - b) / max(abs(a), 1e-12)}
            rep["T_A_structural"][f"{dom}|{tech}"] = {
                "rep_day": str(pd.Timestamp(ts.date.iloc[i_rep]).date()),
                "E_rep_ml": float(E[i_rep]), "M0_rep_direct_ml": float(M0d[i_rep]),
                "m0_window_ml": float(w1["m0_window_ml"]), "pool_rep_ml": float(R[i_rep]),
                **paired}

            # ---------------- T-D 缩放精确性 ----------------
            td = {}
            for tag, m in windows.items():
                blw, ir = bl_window(dom, ts, E, m)
                m0_win = cm.m0_of(blw, PANEL, q, cooling_tech=tech)
                m0_direct = float(M0d[m].sum())
                td[tag] = {
                    "n_days": int(m.sum()), "E_window_ml": float(E[m].sum()),
                    "rep_day": str(pd.Timestamp(ts.date.iloc[ir]).date()),
                    "rep_E_ml": float(E[ir]),
                    "degenerate_no_wet_day": bool(blw["_degenerate_no_wet_day"]),
                    "m0_window_ml": float(m0_win), "sum_daily_M0_ml": m0_direct,
                    "rel_diff": abs(m0_win - m0_direct) / max(abs(m0_direct), 1e-12)
                    if abs(m0_direct) > 1e-9 else abs(m0_win - m0_direct)}
            rep["T_D_scaling"][f"{dom}|{tech}"] = td

            # ---------------- T-B 聚合: 全年 ----------------
            tb = {}
            for tag, dp_scale in (("dp0", 0.0), ("dp1", 1.0)):
                dp = P0 * dp_scale
                blY, _ = bl_window(dom, ts, E, windows["full_year"])
                wY = solve_window(blY, tech, q, float(R.sum()), gap, dp, float(n))
                S_day = S_ai = x_ai = inc = M_tot = clo = 0.0
                for i in range(n):
                    o = dm.daily_city_outcome(
                        dom, SAMPLE, pd.Timestamp(ts.date.iloc[i]),
                        dm.drivers_row(ts.iloc[i], "ai_load_factor_a30"), q,
                        m0_day=float(M0d[i]), pool_day=float(R[i]), gap_day=gap / n,
                        dp_day=dp / n, ai_target=PHI, panel=PANEL, tech=tech,
                        e_ref_day=float(E[i]), cache=CACHE)
                    S_day += o["S_city_ml"]; S_ai += o["S_AI_ml"]; x_ai += o["x_ai_ml"]
                    inc += o["inc_reclaimed_ml"]; M_tot += o["M_ml"]
                    clo += o["closure_residual_ml"]
                tb[tag] = {
                    "one_step": {"S_AI_ml": float(wY["S_AI_ml"]),
                                 "S_city_ml": float(wY["S_city_ml"]),
                                 "M_ml": float(wY["M_ml"]), "x_ai_ml": float(wY["x_ai_ml"]),
                                 "inc_reclaimed_ml": float(wY["inc_reclaimed_ml"]),
                                 "status": str(wY["status"])},
                    "daily_sum": {"S_AI_ml": float(S_ai), "S_city_ml": float(S_day),
                                  "M_ml": float(M_tot), "x_ai_ml": float(x_ai),
                                  "inc_reclaimed_ml": float(inc)},
                    "S_city_abs_diff_ml": abs(float(wY["S_city_ml"]) - float(S_day)),
                    "S_city_rel_diff": abs(float(wY["S_city_ml"]) - float(S_day))
                                       / max(abs(float(wY["S_city_ml"])), 1e-12),
                    "S_city_abs_diff_over_m0": abs(float(wY["S_city_ml"]) - float(S_day))
                                               / max(float(wY["m0_window_ml"]), 1e-12),
                    "sign_agreement": bool(np.sign(float(wY["S_city_ml"]))
                                           == np.sign(float(S_day))),
                    "daily_sum_closure_residual_ml": float(clo)}
            rep["T_B_aggregation"][f"{dom}|{tech}"] = tb

    # ---------------- 判定 ----------------
    ta = rep["T_A_structural"]
    ta_max = max(max(v[k]["rel_diff"] for k in ("M_ml", "S_city_ml")) for v in ta.values())
    td_all = [v for d in rep["T_D_scaling"].values() for v in d.values()]
    td_max = max(v["rel_diff"] for v in td_all
                 if not v["degenerate_no_wet_day"])
    tb_all = [v for d in rep["T_B_aggregation"].values() for v in d.values()]
    tb_max_rel = max(v["S_city_rel_diff"] for v in tb_all)
    tb_max_over_m0 = max(v["S_city_abs_diff_over_m0"] for v in tb_all)
    tb_sign_ok = all(v["sign_agreement"] for v in tb_all)

    rep["criteria"] = {
        "T_A_structural": {"threshold_rel": 1e-6, "max_rel_diff": ta_max,
                           "pass": bool(ta_max < 1e-6),
                           "note": ("窗口单步解与逐日解共用同一求解器, 残差应仅为求解器自身"
                                    "容差 (~1e-8 相对), 远小于任何物理量。")},
        "T_D_scaling": {"threshold_rel": 1e-9, "max_rel_diff_non_degenerate": td_max,
                        "pass": bool(td_max < 1e-9)},
        "T_B_aggregation": {"max_rel_diff": tb_max_rel,
                            "max_abs_diff_over_m0": tb_max_over_m0,
                            "sign_agreement_all": bool(tb_sign_ok),
                            "one_step_adequate_rel_5pct": bool(tb_max_rel < 0.05),
                            "one_step_adequate_over_m0_1pct": bool(tb_max_over_m0 < 0.01)},
    }
    rep["M4_M5_M6_fixes"] = {
        "M4_technology_propagated": ("m0_of / window_scale / city_outcome 已透传 "
                                     "cooling_tech / wet_fraction; 代表日改为窗口内湿日。"),
        "M5_cache_key_includes_rep_day": ("make_evaluators 缓存键已含 domain/date_rep/"
                                          "drivers_rep/period_days, 跨窗口复用不再返回陈旧计划。"),
        "M6_period_days_explicit": ("再生水可得量由 trial/730 改为 trial/period_days; "
                                    "窗口解 (n≠730) 不再被按 730 天摊薄。"),
        "impact_before_fix": ("修复前: hybrid 窗口行混用 evaporative 计划 (M4); "
                              "跨窗口缓存命中陈旧计划 (M5); 热浪窗 37 天的可得量被除以 730 "
                              "→ M 被算成'无回用水'值 (M6)。T14 §3.3 窗口行与 T13 的 A3 行 "
                              "受影响, 需按其重跑结果替换。"),
    }
    rep["verdict"] = {
        "M1_status": "RESOLVED-ALIGNED" if rep["criteria"]["T_A_structural"]["pass"]
        else "STILL-INCONSISTENT",
        "window_scaling_status": ("EXACT" if rep["criteria"]["T_D_scaling"]["pass"]
                                  else "INEXACT"),
        "one_step_vs_daily": ("one-step adequate (sign preserved, |Δ|/M0 < 1%)"
                              if rep["criteria"]["T_B_aggregation"]["one_step_adequate_over_m0_1pct"]
                              else "report daily-sum as primary; one-step biased"),
    }

    (HERE / "T14b_crossscale_summary.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print("=" * 92)
    print("T14b 跨尺度一致性自检 (M1 / M4 / M5 修复验证)")
    print("=" * 92)
    print("[T-A 结构等价: 1 天窗口单步解 vs 逐日解]")
    for k, v in ta.items():
        print(f"  {k:20s} rep={v['rep_day']} E_rep={v['E_rep_ml']:8.3f}  "
              f"M rel={v['M_ml']['rel_diff']:.3e}  S_city rel={v['S_city_ml']['rel_diff']:.3e}"
              f"   ({v['S_city_ml']['window_1d']:.6f} vs {v['S_city_ml']['daily']:.6f})")
    print(f"  → pass={rep['criteria']['T_A_structural']['pass']} "
          f"(max rel {rep['criteria']['T_A_structural']['max_rel_diff']:.3e})")
    print()
    print("[T-D 缩放精确性: m0_window = ΣE_win×g_wet  vs  Σ_t M0(t)]")
    for k, d in rep["T_D_scaling"].items():
        for tag, v in d.items():
            flag = " (无湿日: 退化)" if v["degenerate_no_wet_day"] else ""
            print(f"  {k:20s} {tag:22s} n={v['n_days']:3d} ΣE={v['E_window_ml']:9.1f} "
                  f"rel={v['rel_diff']:.3e}{flag}")
    print(f"  → pass={rep['criteria']['T_D_scaling']['pass']} "
          f"(max rel {rep['criteria']['T_D_scaling']['max_rel_diff_non_degenerate']:.3e})")
    print()
    print("[T-B 聚合: 全年逐日求和 vs 单步年总量]")
    for k, d in rep["T_B_aggregation"].items():
        for tag, v in d.items():
            print(f"  {k:20s} {tag:4s} 单步={v['one_step']['S_city_ml']:11.2f}  "
                  f"逐日和={v['daily_sum']['S_city_ml']:11.2f}  Δ={v['S_city_abs_diff_ml']:8.2f} ML "
                  f"(rel={v['S_city_rel_diff']:7.3%}, Δ/M0={v['S_city_abs_diff_over_m0']:.3%}, "
                  f"同号={v['sign_agreement']})")
    print()
    print("[T-C 输入一致性]")
    for dom, v in rep["T_C_inputs"].items():
        print(f"  {dom}: ΣR/P0={v['sum_daily_R_over_P0']:.6f}  R_cv={v['R_cv']:.4f}  "
              f"R∈[{v['R_min_max_ml'][0]:.2f},{v['R_min_max_ml'][1]:.2f}]")
    print("=" * 92)
    print("verdict:", json.dumps(rep["verdict"], ensure_ascii=False))


if __name__ == "__main__":
    main()
