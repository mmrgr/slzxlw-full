"""T14e 数据溯源审计 + 合成气象实现敏感性 + 指标 B 的流域归属闭环。

本轮查出的**最重要问题**（此前被忽略, 且我上轮的表述是错的）:
    `examples/cawcc_r2/parameter_sources.csv` 明确标注:
        driver_series, synthetic, "合成分成: 正弦季节 + AR(1) 噪声, 固定种子", synthetic
        reservoir_inflow_mean, 265/290 ML/d, "场景标定(设计) ... 非实测率定", scenario-tuned
    即 `timeseries.csv` 的气温/湿度/湿球/降雨 **不是实测气象**, 而是**合成驱动序列**;
    水库来水是**为设计目标反算**的, 不是实测率定。

    因此 T5 的热浪窗、指标 C 的失效概率、τ 轴, 全部**条件于一个已声明的合成生成器**,
    不是条件于观测气候。上一轮把 timeseries 描述为"真实气象"是**错误**, 此处更正。

本脚本做三件事:
    S1 溯源分类: 逐项列出进入 T5/T14 链的输入及其 evidence_type。
    S2 实现敏感性: 用仓库自带的 `build_r2_domains.build_drivers` (同参数, 换种子)
       生成 N 组备用气象实现, 重算热浪窗统计与需求季节因子, 报告分布,
       并检验"定性结论是否在**每一组**实现下都成立"。
    S3 指标 B: 给出**不依赖流域水文**的严格版本 (取水 − 回流, 按来源份额),
       并把"流域净耗水"明确列为需外部数据的分项; 同时**停用**基于合成来水的 τ 轴。

纪律: 不把合成实现当作"不确定性区间"出售 —— 它只是**生成器实现**的散布,
      不含气候变化的真实不确定性。
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
import city_model as cm   # noqa: E402

REPO = Path(r"C:/Users/mmrgr/Desktop/论文/算力中心/07_代码_AI-UWM引擎/aiuwm_src")
SCRIPTS = REPO / "scripts"
R2 = REPO / "examples" / "cawcc_r2"

SAMPLE, PANEL, PHI = "IEUA RP-1 (2025, tertiary)", "B_full", 0.70
N_REAL = 24
SEED0 = 20260918
SEED_STEP = 101

CHAIN_INPUTS = [
    "driver_series", "reservoir_inflow_mean", "reservoir_capacity",
    "reservoir_initial_storage", "abstraction_capacity", "wtw_capacity",
    "wwtw_capacity", "reuse_treatment_capacity", "central_reuse_fraction",
    "coc_quality_limits_tds", "coc_quality_limits_chloride",
    "ai_load_factor_mean", "training_fraction", "inference_peak_factor",
    "cooling_storage", "grid_connection_capacity", "local_connection_capacity",
    "population", "domestic_demand", "industrial_demand",
]


def load_provenance() -> pd.DataFrame:
    d = pd.read_csv(R2 / "parameter_sources.csv", encoding="utf-8-sig")
    d.columns = [c.strip() for c in d.columns]
    return d


def main() -> None:
    rep: dict = {"S1_provenance": {}, "S2_realisation_sensitivity": {},
                 "S3_indicator_B": {}, "corrections": {}}

    # ------------------------------------------------------------------ S1
    prov = load_provenance()
    prov["evidence_type"] = prov["evidence_type"].astype(str).str.strip()
    keep = prov[prov["parameter"].isin(CHAIN_INPUTS)]
    rep["S1_provenance"] = {
        "file": str(R2 / "parameter_sources.csv"),
        "evidence_type_counts_all": prov["evidence_type"].value_counts().to_dict(),
        "chain_inputs": keep[["parameter", "value", "unit", "source",
                              "evidence_type"]].fillna("").to_dict(orient="records"),
        "synthetic_or_tuned_in_chain": keep[
            keep["evidence_type"].isin(["synthetic", "scenario-tuned"])]
        [["parameter", "source", "evidence_type"]].to_dict(orient="records"),
    }
    rep["corrections"] = {
        "driver_series": ("`timeseries.csv` 的气温/湿度/湿球/降雨由 "
                          "`scripts/build_r2_domains.build_drivers` 生成 "
                          "(正弦季节 + AR(1) 噪声, 固定种子 20260918 / co 20261019), "
                          "**不是实测气象**。上一轮阶段报告称其为'真实气象'属表述错误, 已更正。"),
        "reservoir_inflow": ("`reservoir_inflow_ml` 是**场景标定**量 (为使弃水率<10%、"
                             "库容年内循环而反算), 非实测率定 → 基于它的 τ 轴**停用**。"),
        "coc_quality_limits": ("引擎占位限值在 parameter_sources 中标注为 "
                               "'ASHRAE 冷却水处理: 结垢/腐蚀控制**量级**' (literature), "
                               "即**量级引用而非标准值**; 且其 钙硬度+总碱度=1200 mg/L "
                               "超出 GB/T 50050-2017 的 1100 判据 → 已由 T6b 的引用档取代。"),
    }

    # ------------------------------------------------------------------ S2
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    try:
        import build_r2_domains as b2                              # noqa: PLC0415
    except Exception as exc:                                       # noqa: BLE001
        rep["S2_realisation_sensitivity"] = {"error": repr(exc)[:300]}
        b2 = None

    if b2 is not None:
        out = {}
        for dom in dm.DOMAINS:
            dom_cfg = b2.DOMAINS[dom]
            idx = list(b2.DOMAINS).index(dom)
            rows = []
            for k in range(N_REAL):
                seed = SEED0 + SEED_STEP * idx + 7919 * k
                tsr = b2.build_drivers(dom_cfg, "2029-01-01", 2, seed)
                tsr["date"] = pd.to_datetime(tsr["date"])
                wb = tsr["wet_bulb_c"].to_numpy(dtype=float)
                thr = float(np.quantile(wb, 0.95))
                m_hw = wb >= thr
                top37 = np.zeros(wb.size, bool)
                top37[np.argsort(wb)[-37:]] = True
                row = {"seed": int(seed), "wb_p95_c": thr,
                       "wb_max_c": float(wb.max()),
                       "n_wb_ge_p95": int(m_hw.sum()),
                       "n_wb_ge_24c": int((wb >= 24.0).sum())}
                for tech in ("evaporative", "hybrid"):
                    ser = dm.daily_plan_series(dom, SAMPLE, tech=tech, panel=PANEL,
                                               phi=PHI, load_col="ai_load_factor_a30",
                                               ts=tsr)
                    M = ser.external_makeup_ml.to_numpy(dtype=float)
                    E = ser.evaporation_ml.to_numpy(dtype=float)
                    peak = float(M.max() / M.mean()) if M.mean() > 1e-12 else float("nan")
                    # 需求峰与湿球热浪窗的重合度 (按 M 排序的前 37 天)
                    topM = np.zeros(M.size, bool)
                    topM[np.argsort(M)[-37:]] = True
                    inter = float((topM & top37).sum() / 37.0)
                    row[f"{tech}_seasonal_factor"] = peak
                    row[f"{tech}_n_zero_wet_days"] = int((E <= 1e-9).sum())
                    row[f"{tech}_peak_in_wb_top37_share"] = inter
                    row[f"{tech}_M_window_over_year"] = float(M[m_hw].mean() / M.mean()) \
                        if M.mean() > 1e-12 else float("nan")
                rows.append(row)
            df = pd.DataFrame(rows)
            num = [c for c in df.columns if c != "seed"]
            out[dom] = {
                "n_realisations": int(len(df)),
                "stats": {c: {"min": float(df[c].min()), "p25": float(df[c].quantile(.25)),
                              "median": float(df[c].median()),
                              "p75": float(df[c].quantile(.75)),
                              "max": float(df[c].max())} for c in num},
                "qualitative_checks": {
                    "hybrid_seasonal_factor_gt_2_all": bool(
                        (df["hybrid_seasonal_factor"] > 2.0).all()),
                    "hybrid_seasonal_gt_diurnal_all": bool(
                        (df["hybrid_seasonal_factor"] > 1.0577).all()),
                    "evaporative_seasonal_factor_lt_1.3_all": bool(
                        (df["evaporative_seasonal_factor"] < 1.3).all()),
                    "evaporative_peak_in_wb_top37_ge_half_all": bool(
                        (df["evaporative_peak_in_wb_top37_share"] >= 0.5).all()),
                    "hybrid_peak_in_wb_top37_ge_half_all": bool(
                        (df["hybrid_peak_in_wb_top37_share"] >= 0.5).all()),
                    "wb_p95_range_c": [float(df["wb_p95_c"].min()),
                                       float(df["wb_p95_c"].max())],
                    "n_wb_ge_24c_median": float(df["n_wb_ge_24c"].median()),
                },
                "per_realisation": df.round(4).to_dict(orient="records"),
            }
            df.round(4).to_csv(HERE / f"T14e_realisations_{dom}.csv", index=False,
                               encoding="utf-8-sig")
        rep["S2_realisation_sensitivity"] = {
            "generator": "scripts/build_r2_domains.build_drivers (正弦季节 + AR(1) 噪声)",
            "n_realisations_per_domain": N_REAL,
            "seed_base": SEED0, "seed_step_per_domain": SEED_STEP, "seed_step_per_realisation": 7919,
            "by_domain": out,
            "interpretation": ("这是**生成器实现**的散布, 不是气候不确定性, 也不是观测区间; "
                              "它的用途是回答'结论是否依赖某一次随机实现'。"),
        }

    # ------------------------------------------------------------------ S3
    b_rows = {}
    for dom in dm.DOMAINS:
        p0 = dm.daily_plan_series(dom, SAMPLE, tech="evaporative", panel=PANEL, phi=0.0)
        p1 = dm.daily_plan_series(dom, SAMPLE, tech="evaporative", panel=PANEL, phi=PHI)
        fr = np.clip(p1.reclaimed_fraction_used.to_numpy(dtype=float), 0.0, 1.0)
        w2 = p0.external_makeup_ml.to_numpy(dtype=float)
        w1 = p1.external_makeup_ml.to_numpy(dtype=float) * (1.0 - fr)
        r2 = p0.return_flow_ml.to_numpy(dtype=float)
        r1 = p1.return_flow_ml.to_numpy(dtype=float) * (1.0 - fr)
        net2, net1 = w2 - r2, w1 - r1
        b_rows[dom] = {
            "withdrawal_ml_yr": [float(w2.sum() / 2.0), float(w1.sum() / 2.0)],
            "return_ml_yr": [float(r2.sum() / 2.0), float(r1.sum() / 2.0)],
            "net_consumption_ml_yr": [float(net2.sum() / 2.0), float(net1.sum() / 2.0)],
            "delta_withdrawal_ml_yr": float((w2.sum() - w1.sum()) / 2.0),
            "delta_net_ml_yr": float((net2.sum() - net1.sum()) / 2.0),
            "relative_uncertainty_declared_missing": [
                "流域分配系数 (取水/回流归属同一流域的份额)",
                "回归流时滞与河道损失",
                "跨流域调水与地下水交换",
            ],
        }
    rep["S3_indicator_B"] = {
        "strict_version": ("取水 − 回流, 并按来源份额严格归属再生水。此项**不需要**流域水文, "
                           "只依赖设施水量平衡, 故可作为**上界**报告。"),
        "basin_version_status": "NOT_IDENTIFIABLE_FROM_AVAILABLE_DATA",
        "required_external_data": [
            "经校验的流域水文模型/实测径流序列 (替换 scenario-tuned 的 reservoir_inflow)",
            "取水口与排放口所在流域的对应关系 (本研究未指定具体流域)",
            "回归流时滞、河道损失与最小生态流量约束",
        ],
        "previous_tau_status": "RETIRED (基于 scenario-tuned 来水, 不作为任何结论依据)",
        "basin_free_stress_axis": ("改用 τ_cool(t) = M(t)/mean(M) —— 只依赖设施侧需求, "
                                   "不含合成来水, 见 T5/T14 的季节因子"),
        "by_domain": b_rows,
    }

    (HERE / "T14e_provenance_basin_summary.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    # ------------------------------------------------------------------ 控制台
    print("=" * 96)
    print("T14e 数据溯源 / 合成气象实现敏感性 / 指标 B 归属")
    print("=" * 96)
    print("[S1] parameter_sources.csv 中进入 T5/T14 链的输入")
    for r in rep["S1_provenance"]["chain_inputs"]:
        print(f"   {r['parameter']:28s} {str(r['value'])[:18]:20s} "
              f"[{r['evidence_type']}]  {str(r['source'])[:60]}")
    print(f"   -> synthetic/scenario-tuned: "
          f"{[r['parameter'] for r in rep['S1_provenance']['synthetic_or_tuned_in_chain']]}")
    if "error" not in rep["S2_realisation_sensitivity"]:
        print("-" * 96)
        print(f"[S2] 合成气象实现敏感性 (每域 {N_REAL} 组备用实现)")
        for dom, d in rep["S2_realisation_sensitivity"]["by_domain"].items():
            s = d["stats"]
            print(f"  [{dom}] 湿球 p95 ∈ [{s['wb_p95_c']['min']:.2f},{s['wb_p95_c']['max']:.2f}]°C "
                  f"(中位 {s['wb_p95_c']['median']:.2f}) | ≥24°C 天数中位 {s['n_wb_ge_24c']['median']:.0f}")
            for tech in ("evaporative", "hybrid"):
                k = f"{tech}_seasonal_factor"
                kk = f"{tech}_peak_in_wb_top37_share"
                print(f"       {tech:12s} 季节因子 ∈ [{s[k]['min']:.2f},{s[k]['max']:.2f}] "
                      f"(中位 {s[k]['median']:.2f}) | 需求峰落在湿球 top37 内的比例 "
                      f"∈ [{s[kk]['min']:.2f},{s[kk]['max']:.2f}]")
            print(f"       定性检验: {json.dumps(d['qualitative_checks'], ensure_ascii=False)}")
    print("-" * 96)
    print("[S3] 指标 B")
    for dom, v in rep["S3_indicator_B"]["by_domain"].items():
        print(f"  [{dom}] 取水节约 {v['delta_withdrawal_ml_yr']:,.0f} ML/yr | "
              f"净耗水减少 {v['delta_net_ml_yr']:,.0f} ML/yr (上界)")
    print(f"  流域版本状态: {rep['S3_indicator_B']['basin_version_status']}")
    print(f"  τ 轴状态: {rep['S3_indicator_B']['previous_tau_status']}")
    print("=" * 96)
    print("写出: T14e_provenance_basin_summary.json + T14e_realisations_{ha,co}.csv")


if __name__ == "__main__":
    main()
