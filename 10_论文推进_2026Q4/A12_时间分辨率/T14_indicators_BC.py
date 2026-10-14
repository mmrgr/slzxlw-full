"""T14 指标 B/C —— 流域净耗水 + 高峰供水能力 (日尺度, 禁止年均值替代)。

预注册约束 (A0_预注册/preregistration.md §1):
    B 流域净耗水   = 取水 − 回流至河道        —— 需流域水文数据; 仅作扩展分析
    C 高峰供水能力 = 热浪期供水余量/失效概率   —— **不得用年均值替代**
    硬约束: A/B/C 不得合并成单一"可持续性得分"

方法学纪律 (重要, 承接 T5 的一致性核查):
    日尺度求解若自建"单日城市解", 会与冻结年度模块的分配器语义不一致
    (实测: 日尺度下既有用户得 0、竞争池未被用尽; 年度模块为 37:63 且池用尽)。
    因此 **S_city 的分组比较一律复用冻结模块 `city_model.solve_city`**,
    只把它的时间尺度参数 (E_total / 代表日 / 池 / 缺口) 换成**窗口总量**;
    分配规则代码路径与冻结版本逐字相同。

指标 C 的落点:
    C1 逐日需求峰值化与 τ 轴;
    C2 替代覆盖率与峰值缺口 (给定 AI 占池份额 σ);
    C3 **峰值失效临界规模 s*(σ)** —— 指标 C 的核心可报量;
    C4 热浪窗 vs 匹配非热浪窗 vs 全年 的 S_city (冻结模块, 窗口总量)。
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

SAMPLE = "IEUA RP-1 (2025, tertiary)"
PANEL = "B_full"
PHI = 0.70
SHARES = (0.30, 0.50, 0.70, 1.00)      # σ: AI 可用的再生水池份额 (政策参数)
SCALE_GRID = np.round(np.arange(0.25, 3.01, 0.05), 4)


def peaks(x) -> dict:
    x = np.asarray(x, dtype=float)
    m = float(x.mean())
    return {"annual_ml": float(x.sum()), "mean_ml_day": m, "max_ml_day": float(x.max()),
            "min_ml_day": float(x.min()),
            "peak_over_mean": float(x.max() / m) if m > 1e-12 else float("nan")}


def window_scale(dom: str, tech: str, mask: np.ndarray, *, tag: str,
                 p0: pd.DataFrame | None = None,
                 sup: pd.DataFrame | None = None) -> dict:
    """在给定窗口上, 用**冻结模块**求 S_city (时间尺度换成窗口总量)。

    审计修复 (M4): 必须透传 `cooling_tech`, 否则 make_evaluators 会用项目默认技术
    (evaporative) 求 M/E, 与传入的窗口 ΣE 不自洽 —— 混合式窗口会因此完全错。

    代表日选取: 必须在窗口内**蒸发 > 0 的湿日**中取湿球中位日。
    对 hybrid/dry, 窗口(尤其冷窗)可能整体零蒸发, 此时 M/E 无定义;
    若强行取零蒸发日会使 g=M/E 退化为 0 (M4 的另一半)。
    """
    ts = dm.load_ts(dom)
    q = dm.sample_quality(PANEL, SAMPLE)
    p0 = dm.daily_plan_series(dom, SAMPLE, tech=tech, panel=PANEL, phi=0.0,
                              load_col="ai_load_factor_a30") if p0 is None else p0
    E = p0.evaporation_ml.to_numpy()
    sup = dm.daily_reuse_supply(dom) if sup is None else sup
    R = sup.reuse_delivered_ml.to_numpy()
    n = int(mask.sum())

    # 代表日: 窗口 ∧ 湿日 中取湿球中位日 (无湿日则退化为窗口内湿球中位日)
    wet_in_win = mask & (E > 1e-9)
    pool_idx = np.where(wet_in_win)[0]
    if pool_idx.size == 0:
        pool_idx = np.where(mask)[0]
    wb_sel = ts.wet_bulb_c.to_numpy()[pool_idx]
    i_rep = int(pool_idx[int(np.argmin(np.abs(wb_sel - np.median(wb_sel))))])
    r = ts.iloc[i_rep]

    bl_w = dict(cm.BASELINES[dom])
    bl_w["E_total"] = float(E[mask].sum())
    bl_w["date_rep"] = pd.Timestamp(r.date)
    bl_w["drivers_rep"] = {"temperature_c": float(r.temperature_c),
                           "relative_humidity": float(r.relative_humidity_pct),
                           "load_factor": float(r.ai_load_factor_a30)}
    m0_w = cm.m0_of(bl_w, PANEL, q, cooling_tech=tech)
    pool_w = float(R[mask].sum())
    gap_w = float(cm.BASELINES[dom]["gap"]) * n / dm.N_DAYS
    out = cm.solve_city(bl_w, PANEL, SAMPLE, q, m0_w, pool_w, gap_w, 0.0, PHI,
                        cooling_tech=tech, period_days=float(n))
    out.update({"window": tag, "n_days": n, "E_window_ml": float(E[mask].sum()),
                "pool_window_ml": pool_w, "gap_window_ml": gap_w, "m0_window_ml": m0_w,
                "rep_day": str(pd.Timestamp(r.date).date()), "tech": tech,
                "sum_daily_M0_ml": float(p0.external_makeup_ml.to_numpy()[mask].sum()),
                "m0_consistency_rel": abs(m0_w - float(p0.external_makeup_ml.to_numpy()[mask].sum()))
                                      / max(abs(m0_w), 1e-12)})
    return out


def main() -> None:
    summary: dict = {
        "discipline": ("指标 B/C 分列不合并; 全部日尺度; S_city 分组复用冻结模块, "
                       "仅替换时间尺度参数; 日尺度自建解算器的语义差异已记录, 不用于结论。"),
        "params": {"phi": PHI, "shares": list(SHARES), "panel": PANEL, "sample": SAMPLE},
        "indicator_B": {}, "indicator_C": {}, "S_city_windows": {}}

    for dom in dm.DOMAINS:
        ts = dm.load_ts(dom)
        wb = ts.wet_bulb_c.to_numpy()
        heat = wb >= np.quantile(wb, dm.HEATWAVE_WB_QUANTILE)
        n_hw = int(heat.sum())
        # 匹配非热浪窗: 按湿球排序取与热浪窗等量的最低湿球日
        order = np.argsort(wb)
        non = order[:n_hw]
        sup = dm.daily_reuse_supply(dom)
        R = sup.reuse_delivered_ml.to_numpy()

        b_blk, c_blk = {}, {}
        for tech in ("evaporative", "hybrid"):
            p0 = dm.daily_plan_series(dom, SAMPLE, tech=tech, panel=PANEL, phi=0.0,
                                      load_col="ai_load_factor_a30")
            p1 = dm.daily_plan_series(dom, SAMPLE, tech=tech, panel=PANEL, phi=PHI,
                                      load_col="ai_load_factor_a30")
            M0 = p0.external_makeup_ml.to_numpy()
            M1 = p1.external_makeup_ml.to_numpy()
            frac1 = np.clip(p1.reclaimed_fraction_used.to_numpy(), 0.0, 1.0)

            # ---------------- 指标 B ----------------
            wd2, wd1 = M0, M1 * (1.0 - frac1)
            ret0 = p0.return_flow_ml.to_numpy()
            ret1 = p1.return_flow_ml.to_numpy() * (1.0 - frac1)
            B2, B1 = wd2 - ret0, wd1 - ret1
            b_blk[tech] = {
                "withdrawal_B2": peaks(wd2), "withdrawal_B1": peaks(wd1),
                "return_B2": peaks(ret0), "return_B1_strict": peaks(ret1),
                "net_B2": peaks(B2), "net_B1": peaks(B1),
                "annual_withdrawal_saving_ml": float(wd2.sum() - wd1.sum()),
                "annual_net_saving_ml": float(B2.sum() - B1.sum()),
                "net_peak_over_mean_B2": peaks(B2)["peak_over_mean"],
                "net_peak_over_mean_B1": peaks(B1)["peak_over_mean"],
                "caveat": "回归流按来源份额严格归属, 故净耗水差为**上界**估计。"}

            # ---------------- 指标 C ----------------
            ent1 = PHI * M1
            c1 = {"demand_entitlement": peaks(ent1), "reclaimed_supply": peaks(R),
                  "tau_p95": None, "tau_heat_mean": None}
            inflow_rel = ts.reservoir_inflow_ml.to_numpy() / ts.reservoir_inflow_ml.mean()
            Md = np.where(M1.mean() > 1e-12, M1 / max(M1.mean(), 1e-12), 0.0)
            tau = Md / inflow_rel
            c1["tau_p95"] = float(np.nanquantile(tau, 0.95))
            c1["tau_heat_mean"] = float(np.nanmean(tau[heat]))
            c1["tau_max"] = float(np.nanmax(tau))
            c1["frac_days_tau_gt1"] = float(np.nanmean(tau > 1.0))

            # C2 覆盖率与缺口 (按 σ)
            cov = {}
            for s in SHARES:
                avail = s * R
                cov[f"sigma_{s:.2f}"] = {
                    "coverage_mean": dm.coverage(avail, ent1),
                    "coverage_heatwave": dm.coverage(avail, ent1, heat),
                    "failure_prob_overall": float(np.mean(avail < ent1 - 1e-9)),
                    "failure_prob_heatwave": float(np.mean(avail[heat] < ent1[heat] - 1e-9)),
                    "failure_prob_non_heatwave": float(np.mean(avail[~heat] < ent1[~heat] - 1e-9)),
                    "peak_shortfall_ml_day": float(np.max(np.maximum(0.0, ent1 - avail)))}
            c1["coverage_by_share"] = cov

            # C3 峰值失效临界规模 s*(σ)
            boundary = {}
            for s in SHARES:
                avail = s * R
                hit = np.nan
                for sc in SCALE_GRID:
                    if np.max((sc * ent1) - avail) > 1e-9:
                        hit = float(sc)
                        break
                boundary[f"sigma_{s:.2f}"] = hit
            c1["failure_scale_s_star"] = boundary
            c1["failure_scale_note"] = ("s* = 使 **任一** 时刻 'AI 目标再生水抽水' 超过 "
                                        "σ·R(t) 的最小 AI 部署倍数 (相对 1000 MW IT); "
                                        "None/NaN 表示在 0.25–3.0 区间内不失效。")
            c1["s_star_at_full_pool"] = boundary["sigma_1.00"]
            c_blk[tech] = c1

            # ---------------- C4 窗口 S_city (冻结模块) ----------------
            wblk = {}
            for tag, m in (("full_year", np.ones(len(ts), bool)),
                           ("heatwave", heat), ("non_heatwave_matched", np.zeros(len(ts), bool))):
                if tag == "non_heatwave_matched":
                    mm = np.zeros(len(ts), bool); mm[non] = True
                else:
                    mm = m
                o = window_scale(dom, tech, mm, tag=tag, p0=p0, sup=sup)
                wblk[tag] = {k: o[k] for k in
                             ("window", "n_days", "E_window_ml", "pool_window_ml",
                              "gap_window_ml", "m0_window_ml", "S_AI_ml", "S_city_ml",
                              "eta_transfer", "phi_eff", "CoC_ai", "status",
                              "closure_residual_ml", "roots", "rep_day", "tech",
                              "sum_daily_M0_ml", "m0_consistency_rel")}
            c_blk[tech]["S_city_by_window"] = wblk

        summary["indicator_B"][dom] = b_blk
        summary["indicator_C"][dom] = c_blk

    (HERE / "T14_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    # ---------------- 控制台 ----------------
    print("=" * 86)
    print("T14 指标 B / 指标 C —— 日尺度")
    for dom in dm.DOMAINS:
        print("=" * 86)
        for tech in ("evaporative", "hybrid"):
            b, c = summary["indicator_B"][dom][tech], summary["indicator_C"][dom][tech]
            print(f"[{dom}/{tech}]")
            print(f"  B 净耗水: B2={b['net_B2']['annual_ml']:.0f} B1={b['net_B1']['annual_ml']:.0f} ML/yr "
                  f"Δ={b['annual_net_saving_ml']:.0f} (取水节约 {b['annual_withdrawal_saving_ml']:.0f}); "
                  f"净耗水峰谷比 B2={b['net_peak_over_mean_B2']:.2f} B1={b['net_peak_over_mean_B1']:.2f}")
            print(f"  C 需求峰谷比={c['demand_entitlement']['peak_over_mean']:.2f}  "
                  f"τ_p95={c['tau_p95']:.2f} 热浪τ均={c['tau_heat_mean']:.2f} τ>1占比={c['frac_days_tau_gt1']:.3f}")
            for s in SHARES:
                k = f"sigma_{s:.2f}"
                v = c["coverage_by_share"][k]
                st = c["failure_scale_s_star"][k]
                print(f"    σ={s:.2f}: 覆盖(全年)={v['coverage_mean']:.3f} 热浪={v['coverage_heatwave']:.3f} "
                      f"失效P(全/热/非)={v['failure_prob_overall']:.3f}/{v['failure_prob_heatwave']:.3f}/"
                      f"{v['failure_prob_non_heatwave']:.3f}  峰值缺口={v['peak_shortfall_ml_day']:.2f}  "
                      f"s*={'—' if (st is None or st!=st) else f'{st:.2f}'}")
            for tag in ("full_year", "heatwave", "non_heatwave_matched"):
                o = c["S_city_by_window"][tag]
                print(f"    S_city[{tag:20s}] n={o['n_days']:3d} E_w={o['E_window_ml']:9.1f} "
                      f"S_AI={o['S_AI_ml']:9.1f} S_city={o['S_city_ml']:9.1f} "
                      f"η={o['eta_transfer']:.3f} φ_eff={o['phi_eff']:.3f} "
                      f"rep={o['rep_day']} M0自检={o['m0_consistency_rel']:.2e}")
    print("=" * 86)


if __name__ == "__main__":
    main()
