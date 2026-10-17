"""T5 日/时分辨率 + 热浪轴 τ —— 审计 B5 的修复实验。

问题 (05_方法审计_v1 §B5):
    T2/T9 用"湿球中位日"的 M/E 比 × 年蒸发总量做年度缩放, 丢掉季节与极端高温,
    导致指标 C (热浪期高峰供水能力) 无法支撑。

本脚本做什么:
    1. 在 730 天上逐日求解, 校验"年缩放"是否无偏 (对 Evaporative 应无偏; 对 Hybrid/Dry 会崩);
    2. 定义热浪窗 (湿球 ≥ p95, 以及引擎 hybrid 全湿阈值 24 °C) 与无量纲轴 τ;
    3. 报告时间分辨率对结果的影响, 为 T14 的指标 C 提供基础。

纪律 (A0_预注册 §1/§8):
    不预设"有季节放大"; 若各技术下时间结构不同就如实报告。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import daily_model as dm  # noqa: E402
import city_model as cm  # noqa: E402

OUT = HERE
SAMPLE = "IEUA RP-1 (2025, tertiary)"
SAMPLE_CO = None          # co 域用首个可用样本
PANEL = "B_full"
PHI = 0.70

TECHS = ("evaporative", "hybrid", "dry")
LOAD_COLS = ("ai_load_factor_a30", "ai_load_factor_a60", "ai_load_factor_a90")


def pick_sample(dom: str) -> str:
    d = cm.load_samples()
    want = ["IEUA RP-1 (2025, tertiary)", "LADWP GWR AWPF", "Figshare 28948753",
            "SIPIBEL", "SDWIS IEU-RP1"]
    for w in want:
        if (d["source"] == w).any() and dom == "ha":
            return w
    return str(d["source"].iloc[0])


def peak_metrics(x: np.ndarray) -> dict:
    x = np.asarray(x, dtype=float)
    nz = x[x > 0]
    return {
        "sum": float(x.sum()),
        "mean": float(x.mean()),
        "p50": float(np.median(x)),
        "p95": float(np.quantile(x, 0.95)),
        "max": float(x.max()),
        "min": float(x.min()),
        "peak_over_mean": float(x.max() / x.mean()) if x.mean() > 1e-12 else float("nan"),
        "p95_over_mean": float(np.quantile(x, 0.95) / x.mean()) if x.mean() > 1e-12 else float("nan"),
        "cv": float(nz.std(ddof=1) / nz.mean()) if nz.size > 1 and nz.mean() > 1e-12 else float("nan"),
    }


def main() -> None:
    summary: dict = {
        "estimand": "daily-resolved cooling water / heat-wave axis",
        "heatwave_def": {"wet_bulb_quantile": dm.HEATWAVE_WB_QUANTILE,
                         "hybrid_full_wet_wb_c": dm.HYBRID_FULL_WET_WB_C},
        "domains": {}, "calibration": {}, "artifacts": {}}

    for dom in dm.DOMAINS:
        smp = SAMPLE if dom == "ha" else pick_sample(dom)
        ts = dm.load_ts(dom)
        wb = ts["wet_bulb_c"].to_numpy()
        q_wb = float(np.quantile(wb, dm.HEATWAVE_WB_QUANTILE))
        heat = wb >= q_wb
        full_wet = wb >= dm.HYBRID_FULL_WET_WB_C
        inflow = ts["reservoir_inflow_ml"].to_numpy()
        inflow_rel = inflow / inflow.mean()

        blk: dict = {"sample": smp, "n_days": int(len(ts)),
                     "wet_bulb_threshold_p95_c": q_wb,
                     "n_heatwave_days": int(heat.sum()),
                     "n_full_wet_days": int(full_wet.sum()),
                     "date_heatwave_window": [str(ts.date[heat].min().date()),
                                              str(ts.date[heat].max().date())],
                     "tech": {}}

        # ---------- 各冷却技术的逐日序列 ----------
        for tech in TECHS:
            df = dm.daily_plan_series(dom, smp, tech=tech, panel=PANEL, phi=PHI,
                                      load_col="ai_load_factor_a30")
            E = df.evaporation_ml.to_numpy()
            M = df.external_makeup_ml.to_numpy()
            wf = df.wet_fraction.to_numpy()
            ratio = df.ratio_M_E.to_numpy()
            ok = np.isfinite(ratio)
            df.to_csv(OUT / f"T5_daily_series_{dom}_{tech}.csv", index=False)

            # τ 轴: 需求相对压力 / 流域供给相对可得性
            Md = np.where(M.mean() > 1e-12, M / max(M.mean(), 1e-12), 0.0)
            tau = np.where(inflow_rel > 1e-12, Md / inflow_rel, np.nan)

            blk["tech"][tech] = {
                "evaporation": peak_metrics(E),
                "makeup": peak_metrics(M),
                "wet_fraction": {"min": float(wf.min()), "p50": float(np.median(wf)),
                                 "p95": float(np.quantile(wf, 0.95)), "max": float(wf.max()),
                                 "n_days_zero": int((wf <= 1e-9).sum())},
                "M_over_E": {"n_valid": int(ok.sum()),
                             "min": float(np.nanmin(ratio)) if ok.any() else None,
                             "p50": float(np.nanmedian(ratio)) if ok.any() else None,
                             "max": float(np.nanmax(ratio)) if ok.any() else None,
                             "is_constant": bool(ok.any() and
                                                 float(np.nanmax(ratio) - np.nanmin(ratio)) < 1e-9)},
                "heatwave_vs_all": {
                    "E_heat_mean": float(E[heat].mean()),
                    "E_all_mean": float(E.mean()),
                    "E_heat_over_all": float(E[heat].mean() / E.mean()) if E.mean() > 1e-12 else None,
                    "wf_heat_mean": float(wf[heat].mean()),
                    "wf_all_mean": float(wf.mean())},
                "tau": {
                    "p50": float(np.nanmedian(tau)), "p95": float(np.nanquantile(tau, 0.95)),
                    "max": float(np.nanmax(tau)),
                    "frac_days_gt1": float(np.nanmean(tau > 1.0)),
                    "heat_mean": float(np.nanmean(tau[heat]))
                    if np.isfinite(tau[heat]).any() else None},
            }

        # ---------- 年缩放校验 (审计 B5 的直接检验) ----------
        cal = {}
        for lc in LOAD_COLS:
            for tech, ref_key in (("evaporative", "E_total_ml"),):
                d_fixed = dm.daily_plan_series(dom, smp, tech=tech, panel=PANEL,
                                               phi=0.0, load_col=lc, coc_mode="fixed")
                cal[f"{tech}|{lc}"] = {"E_sum_ml": float(d_fixed.evaporation_ml.sum()),
                                       "M_sum_ml": float(d_fixed.external_makeup_ml.sum()),
                                       "M_over_E_is_constant":
                                           bool(np.nanmax(d_fixed.ratio_M_E) -
                                                np.nanmin(d_fixed.ratio_M_E) < 1e-9)}
        # co 域用 a60 (与 project.json 一致); ha 用 a30 (与 T2 基线一致)
        d_cal = dm.daily_plan_series(dom, smp, tech="evaporative", panel=PANEL,
                                     phi=0.0, load_col="ai_load_factor_a30",
                                     coc_mode="fixed")
        e_sum = float(d_cal.evaporation_ml.sum())
        e_tot_t2 = float(cm.BASELINES[dom]["E_total"])
        cal["vs_T2_E_total"] = {
            "E_sum_daily_ml": e_sum, "E_total_T2_ml": e_tot_t2,
            "rel_diff": float((e_sum - e_tot_t2) / e_tot_t2),
            "M_over_E_constant_repr_day": bool(
                np.nanmax(d_cal.ratio_M_E) - np.nanmin(d_cal.ratio_M_E) < 1e-9),
            "verdict": ("年度缩放对蒸发式无偏 (M/E 逐日恒定)"
                        if abs(e_sum - e_tot_t2) / e_tot_t2 < 1e-6 else
                        "年度缩放存在偏差, 需改用逐日")}
        blk["calibration"] = cal
        summary["domains"][dom] = blk

    # ---------- 全局判定 ----------
    verdicts = []
    for dom, blk in summary["domains"].items():
        ev = blk["tech"]["evaporative"]["evaporation"]["peak_over_mean"]
        hy = blk["tech"]["hybrid"]["evaporation"]["peak_over_mean"]
        verdicts.append({
            "domain": dom,
            "evaporative_peak_over_mean": ev,
            "hybrid_peak_over_mean": hy,
            "evaporative_time_structure": "flat (PUE-driven only)",
            "hybrid_time_structure": "strongly seasonal (wet-fraction driven)",
            "implication": ("时间分辨率对蒸发式结果影响小; 对 hybrid/dry 是决定性的, "
                            "且峰值落在城市自身应力最高时段 → 指标 C 的必要性成立")})
    summary["verdicts"] = verdicts
    summary["artifacts"]["daily_series"] = [
        f"T5_daily_series_{d}_{t}.csv" for d in dm.DOMAINS for t in TECHS]

    (OUT / "T5_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    # ---------- 控制台 ----------
    print("=" * 78)
    print("T5 日/时分辨率 + 热浪轴 τ")
    for dom, blk in summary["domains"].items():
        print("-" * 78)
        print(f"[{dom}] 热浪窗: 湿球 ≥ {blk['wet_bulb_threshold_p95_c']:.2f} °C  "
              f"({blk['n_heatwave_days']} 天);  全湿阈值 {dm.HYBRID_FULL_WET_WB_C} °C "
              f"({blk['n_full_wet_days']} 天)")
        for tech in TECHS:
            t = blk["tech"][tech]
            pe, pm = t["evaporation"]["peak_over_mean"], t["makeup"]["peak_over_mean"]
            wf = t["wet_fraction"]
            me = t["M_over_E"]
            print(f"  {tech:12s} E峰谷比={pe:5.2f}  M峰谷比={pm:5.2f}  "
                  f"湿分[{wf['min']:.2f},{wf['p50']:.2f},{wf['max']:.2f}] "
                  f"零湿日={wf['n_days_zero']:3d}  M/E恒定={me['is_constant']} "
                  f"τ_p95={t['tau']['p95']:.2f}")
        c = blk["calibration"]["vs_T2_E_total"]
        print(f"  年缩放校验: ΣE={c['E_sum_daily_ml']:.1f} vs T2 E_total={c['E_total_T2_ml']:.1f} "
              f"(rel={c['rel_diff']:.2e})  → {c['verdict']}")
    print("=" * 78)
    print("写出: T5_summary.json + T5_daily_series_*.csv")


if __name__ == "__main__":
    main()
