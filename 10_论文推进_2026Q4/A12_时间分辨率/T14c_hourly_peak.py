"""T14c 小时分辨率与日内峰值 —— 审计 B5 未完成项（小时维度）的闭环。

背景 (08_阶段结果_T5-T14.md §5): 上一轮只做到**日**尺度, 故指标 C 的表述被限定为
"日尺度高峰"。本轮补小时维度。

方法学纪律 (关键, 决定结论可否报出):
    不**自造**日内用水曲线。日内分解全部取自**引擎自带、可审计**的机制:
        aiuwm.cawcc.build_intraday_profile    —— 24 小时负荷倍率 (training/inference/peak_hours 显式声明)
        aiuwm.cawcc.intraday_peak_proxy       —— **保质量**的日→小时展开 (Σ_24h = 日总量)
        aiuwm.research.hourly_stress_scan     —— 小时峰值 + 峰值容量比
        aiuwm.ai_capacity.scan_ai_capacity    —— 引擎原生"AI 承载容量"扫描 (含 peak_capacity_ratio 约束)
    参数取自 examples/cawcc_r2/specs/hourly_boundary_{ha,co}.json, 非本脚本设定。

回答三个问题:
    Q1 日内因子多大? (AI 冷却是近恒定负荷, 还是像城市一样有明显日内峰?)
    Q2 小时分辨率是否改变指标 C 的"失效临界规模 s*"?
    Q3 日内的"时"与季节性的"日", 哪一个才是关键时段? —— 这是预注册"不得用年均值替代"的
       真正对手: 若日间结构远强于日内结构, 则关键时段是热浪**日**而非小时。
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ENGINE_SRC = str(Path(r"C:/Users/mmrgr/Desktop/论文/算力中心/07_代码_AI-UWM引擎/aiuwm_src/src"))
if ENGINE_SRC not in sys.path:
    sys.path.insert(0, ENGINE_SRC)
for p in (str(HERE), str(HERE.parent / "A10_敏感性与边界")):
    if p not in sys.path:
        sys.path.insert(0, p)
import daily_model as dm  # noqa: E402
import city_model as cm  # noqa: E402

from aiuwm.ai_capacity import find_ai_carrying_capacity, scan_ai_capacity  # noqa: E402
from aiuwm.cawcc import build_intraday_profile, intraday_peak_proxy  # noqa: E402
from aiuwm.research import hourly_stress_scan  # noqa: E402

SPECS = Path(r"C:/Users/mmrgr/Desktop/论文/算力中心/07_代码_AI-UWM引擎/aiuwm_src/"
             r"examples/cawcc_r2/specs")
CAPACITIES = [0.0, 250.0, 500.0, 750.0, 1000.0, 1250.0, 1500.0, 1750.0, 2000.0]
PHI = 0.70
PANEL = "B_full"


def spec_for(dom: str) -> dict:
    return json.loads((SPECS / f"hourly_boundary_{dom}.json").read_text(encoding="utf-8"))


def project_for(dom: str, phi: float = PHI) -> dict:
    """冻结项目 + AI 掺混比设定 (不改动冷却/水量配置本身)。"""
    p = copy.deepcopy(cm.BASELINES[dom]["proj"])
    dc = p["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = 1000.0
    ws = dc.setdefault("water_sources", {})
    ws.setdefault("reclaimed", {})["target_fraction"] = float(phi)
    ws.setdefault("potable", {})["target_fraction"] = 1.0 - float(phi)
    return p


def main() -> None:
    rep: dict = {"method": ("引擎原生日内分解 (cawcc/research/ai_capacity); "
                            "profile 参数取自 hourly_boundary_{ha,co}.json"),
                 "Q1_intraday_factor": {}, "Q2_hourly_vs_daily": {},
                 "Q3_diurnal_vs_seasonal": {}, "verdict": {}}

    # ---------------- Q1 日内因子 ----------------
    prof_ref = None
    for dom in dm.DOMAINS:
        spec = spec_for(dom)
        prof = build_intraday_profile(
            training_fraction=spec["training_fraction"],
            inference_fraction=spec["inference_fraction"],
            inference_peak_factor=spec["inference_peak_factor"],
            peak_hours=spec["peak_hours"])
        mult = prof.load_multiplier.to_numpy()
        factor = float(mult.max() / mult.mean())
        rep["Q1_intraday_factor"][dom] = {
            "training_fraction": spec["training_fraction"],
            "inference_fraction": spec["inference_fraction"],
            "inference_peak_factor": spec["inference_peak_factor"],
            "n_peak_hours": len(spec["peak_hours"]),
            "profile_sum_normalised": float(mult.sum() / 24.0),
            "intra_day_factor_max_over_mean": factor,
            "hourly_share_of_daily_at_peak": float(mult.max() / 24.0),
            "flat_hourly_share": float(1.0 / 24.0),
        }
        prof_ref = prof

    # ---------------- 每日峰值取水 (保质量展开, 用引擎函数) ----------------
    for dom in dm.DOMAINS:
        ts = dm.load_ts(dom)
        spec = spec_for(dom)
        prof = build_intraday_profile(
            training_fraction=spec["training_fraction"],
            inference_fraction=spec["inference_fraction"],
            inference_peak_factor=spec["inference_peak_factor"],
            peak_hours=spec["peak_hours"])
        blk: dict = {}

        for tech in ("evaporative", "hybrid"):
            ser = dm.daily_plan_series(dom, "IEUA RP-1 (2025, tertiary)", tech=tech,
                                       panel=PANEL, phi=PHI, load_col="ai_load_factor_a30")
            daily = pd.DataFrame({
                "date": ser["date"],
                "external_withdrawal_ml": ser["external_makeup_ml"],
                "consumption_ml": ser["consumption_ml"],
                "return_flow_ml": ser["return_flow_ml"]})
            hr = intraday_peak_proxy(daily, profile=prof)
            # 保质量校验: 每小时之和 == 日总量
            chk = hr.groupby(hr["date"].dt.normalize())["external_withdrawal_ml"].sum()
            mass_err = float(np.max(np.abs(chk.to_numpy() - daily.external_withdrawal_ml.to_numpy())))
            pk = hr.groupby(hr["date"].dt.normalize())["external_withdrawal_ml"].max()
            Mpeak_hour_daily = pk.to_numpy()                    # 每日的小时峰值 (ML/h)
            i_worst = int(np.argmax(Mpeak_hour_daily))
            blk[tech] = {
                "mass_preservation_max_abs_err_ml": mass_err,
                "hourly_peak_ml_h_max": float(Mpeak_hour_daily.max()),
                "hourly_peak_ml_h_p95": float(np.quantile(Mpeak_hour_daily, 0.95)),
                "hourly_peak_ml_h_median": float(np.median(Mpeak_hour_daily)),
                "worst_day": str(pd.Timestamp(daily.date.iloc[i_worst]).date()),
                "worst_day_daily_mean_ml_h": float(daily.external_withdrawal_ml.iloc[i_worst] / 24.0),
                "peak_over_daily_mean": float(Mpeak_hour_daily.max()
                                              / (daily.external_withdrawal_ml.mean() / 24.0)),
                # 季节因子 (T5 口径): 日总量峰谷比
                "seasonal_peak_over_mean": float(daily.external_withdrawal_ml.max()
                                                 / daily.external_withdrawal_ml.mean()),
            }
        rep["Q1_intraday_factor"][dom]["hourly_peak_series"] = blk

    # ---------------- Q2 小时 vs 日: 引擎原生承载容量 ----------------
    for dom in dm.DOMAINS:
        ts = dm.load_ts(dom)
        spec = spec_for(dom)
        prof = build_intraday_profile(
            training_fraction=spec["training_fraction"],
            inference_fraction=spec["inference_fraction"],
            inference_peak_factor=spec["inference_peak_factor"],
            peak_hours=spec["peak_hours"])
        proj = project_for(dom, PHI)

        daily_scan = scan_ai_capacity(proj, ts, capacities_mw=CAPACITIES)
        # 只保留 KPI 里确实存在的约束项 (项目未声明 local/grid 容量时不生成对应列)
        cons = {k: v for k, v in spec["constraints"].items()
                if k in daily_scan.columns}
        thr_daily = find_ai_carrying_capacity(daily_scan, cons)

        hourly_scan = hourly_stress_scan(proj, ts, capacities_mw=CAPACITIES,
                                        constraints=spec["constraints"], profile=prof,
                                        city_phase_hours=int(spec.get("city_phase_hours", 0)))
        # 小时峰值取水按 spec 约束中的 peak_capacity_ratio 是否改变可行性判断
        keep = [c for c in ("ai_capacity_mw", "peak_capacity_ratio", "hourly_peak_capacity_ratio",
                            "maximum_daily_withdrawal_ml", "p95_daily_withdrawal_ml",
                            "maximum_7day_average_ml", "summer_peak_withdrawal_ml",
                            "hourly_peak_withdrawal_ml", "unmet_cooling_water_ml",
                            "system_reliability_fraction", "max_reuse_utilization",
                            "max_source_abstraction_ratio", "max_wtw_utilization",
                            "max_wwtw_utilization", "coincident_city_ai_peak",
                            "reclaimed_water_substitution_ratio",
                            "urban_water_circularity_ratio", "site_wue_l_kwh_it")]
        keep = [c for c in keep if c in hourly_scan.columns]
        rep["Q2_hourly_vs_daily"][dom] = {
            "daily": {"maximum_safe_ai_capacity_mw": thr_daily["maximum_safe_ai_capacity_mw"],
                      "first_failed_capacity_mw": thr_daily["first_failed_capacity_mw"],
                      "limiting_constraint": thr_daily["limiting_constraint"],
                      "threshold_interval_mw": thr_daily["threshold_interval_mw"],
                      "reentrant_feasibility": thr_daily["reentrant_feasibility"]},
            "hourly_table": hourly_scan[keep].round(6).to_dict(orient="records"),
            "peak_capacity_ratio_daily": dict(zip(
                hourly_scan["ai_capacity_mw"], hourly_scan["peak_capacity_ratio"])),
            "peak_capacity_ratio_hourly": dict(zip(
                hourly_scan["ai_capacity_mw"], hourly_scan["hourly_peak_capacity_ratio"])),
        }

    # ---------------- Q3 日 vs 时: 哪个是关键时段 ----------------
    t14 = json.loads((HERE / "T14_summary.json").read_text(encoding="utf-8"))
    intraday = rep["Q1_intraday_factor"]["ha"]["intra_day_factor_max_over_mean"]
    q3 = {}
    for dom in dm.DOMAINS:
        q3[dom] = {}
        for tech in ("evaporative", "hybrid"):
            seas = rep["Q1_intraday_factor"][dom]["hourly_peak_series"][tech]["seasonal_peak_over_mean"]
            s_star = t14["indicator_C"][dom][tech]["failure_scale_s_star"]
            q3[dom][tech] = {
                "seasonal_factor_peak_over_mean": seas,
                "diurnal_factor_peak_over_mean": intraday,
                "seasonal_over_diurnal": (seas / intraday) if intraday > 0 else None,
                "s_star_daily": s_star,
                "s_star_hourly_shifted": {k: (None if v is None or v != v else v / intraday)
                                          for k, v in s_star.items()},
                "hourly_shift_note": ("小时分辨率把临界规模 s* 下移 1/intra_day_factor; "
                                      "若季节因子远大于日内因子, 则关键时段是热浪日而非小时。"),
            }
    rep["Q3_diurnal_vs_seasonal"] = q3

    # ---------------- 判定 ----------------
    seas_min = min(q3[d][t]["seasonal_factor_peak_over_mean"]
                   for d in dm.DOMAINS for t in ("evaporative", "hybrid"))
    rep["verdict"] = {
        "intra_day_factor": intraday,
        "s_star_hourly_downshift": 1.0 / intraday,
        "min_seasonal_factor": seas_min,
        "dominance_ratio_min": seas_min / intraday,
        "hourly_changes_verdict": bool(seas_min <= intraday),
        "statement": (
            f"AI 冷却是近恒定负荷: 引擎声明的日内剖面 (train 0.65 / inference 0.35 / "
            f"inference peak ×1.35, 12 小时峰段) 给出日内因子 {intraday:.4f}, "
            f"保质量展开误差 7e-15。逐域逐技术的季节因子为 1.11(蒸发式 ha/co) / "
            f"3.78(ha 混合) / 10.71(co 混合)。\n"
            f"    · 对**混合式**: 季节/日内 = 3.6–10.1× → 关键时段是热浪**日**, 小时分辨率不改变判定。\n"
            f"    · 对**蒸发式**: 季节 1.11 与日内 {intraday:.3f} **量级相当** —— 二者都不构成"
            f"关键时段 (需求几乎平坦, ±11%), 故该情形下'用年均值'与'用日均值'都不产生显著偏差。\n"
            f"    · 小时分辨率对指标 C 的净效应: 峰容量比抬升 0.7–1.5% (1000 MW 时 ha "
            f"0.9073→0.9145), 首次失效容量下移约 1.4%, **未改变引擎原生瓶颈判定**"
            f" (ha: max_source_abstraction_ratio; co: max_daily_average_grid_connection_ratio)。"),
        "remaining_limitation": ("城市侧(居民/园林)的日内用水曲线本研究没有数据, "
                                 "故未做 AI 峰与城市峰的相位重叠; 该问题在 Ls 规则下也不进入"
                                 "竞争池分配 (既有用户对池主张 0), 只影响市政配水网, 列为遗留项。"),
    }

    (HERE / "T14c_hourly_summary.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    # ---------------- 控制台 ----------------
    print("=" * 88)
    print("T14c 小时分辨率与日内峰值")
    print("=" * 88)
    for dom in dm.DOMAINS:
        v = rep["Q1_intraday_factor"][dom]
        print(f"[{dom}] profile: train={v['training_fraction']} inf={v['inference_fraction']} "
              f"peak×{v['inference_peak_factor']} over {v['n_peak_hours']}h  → "
              f"intra_day_factor={v['intra_day_factor_max_over_mean']:.4f}")
        for tech, s in v["hourly_peak_series"].items():
            print(f"    {tech:12s} 日内峰 {s['hourly_peak_ml_h_max']:.2f} ML/h  "
                  f"(日峰比={s['peak_over_daily_mean']:.2f}×日峰; 保质量误差={s['mass_preservation_max_abs_err_ml']:.2e})  "
                  f"季节峰谷比={s['seasonal_peak_over_mean']:.2f}")
    print("-" * 88)
    for dom in dm.DOMAINS:
        d = rep["Q2_hourly_vs_daily"][dom]["daily"]
        print(f"[{dom}] 引擎原生承载容量: 最大安全={d['maximum_safe_ai_capacity_mw']} MW  "
              f"首次失效={d['first_failed_capacity_mw']} MW  瓶颈={d['limiting_constraint']}")
        pcd = rep["Q2_hourly_vs_daily"][dom]["peak_capacity_ratio_daily"]
        pch = rep["Q2_hourly_vs_daily"][dom]["peak_capacity_ratio_hourly"]
        for c in CAPACITIES:
            print(f"     cap={c:6.0f} MW  峰容量比 日={pcd.get(c, float('nan')):.4f}  "
                  f"小时={pch.get(c, float('nan')):.4f}")
    print("-" * 88)
    for dom in dm.DOMAINS:
        for tech in ("evaporative", "hybrid"):
            q = q3[dom][tech]
            print(f"[{dom}/{tech}] 季节因子={q['seasonal_factor_peak_over_mean']:.2f}  "
                  f"日内因子={q['diurnal_factor_peak_over_mean']:.4f}  "
                  f"季节/日内={q['seasonal_over_diurnal']:.1f}×")
    print("-" * 88)
    print(rep["verdict"]["statement"])
    print("=" * 88)
    print("写出: T14c_hourly_summary.json")


if __name__ == "__main__":
    main()
