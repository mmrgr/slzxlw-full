"""task-4 / 交付物 1: 先验敏感性 (红队 M5/P2 阻塞项).

问题
----
现有 P(S_city>0) ≈ 0.62 是在 **均匀先验** 下、对 {pool_scale, gap_scale, dp_scale,
ai_target} 做 LHS 得到的**模型概率**, 不是观测频率。红队 M5/P2 要求: 换先验后
这个数漂移到哪里? 若漂移很大, 全稿必须写成"在均匀先验下"。

做法
----
对三个控制量 (pool_scale, gap_scale, dp_scale) 各配一套先验:
    uniform     : 对所有取值同等无知
    log-uniform : 只知量级 (Jeffreys 先验), 偏向小值
    triangular  : 名义值最可能, 端点最不可能
9 种组合 (3x3, pool 先验 x gap 先验), 每种 ≥500 LHS 样本。dp_scale 单独再扫
三套先验, 因为它是论文的主控变量。

**关键设计决定 (见 robustness_summary.md §0)**: dp_scale 保留在抽样维里会与
"池预算 = pool*(1+dp)" 的引擎实现耦合, 使 dp>=1 的分位把可用池推到超过既有
用户缺口, 于是 S_city>0 由**位移记账**驱动。故主表同时报:
    口径 A: dp_scale = 0 固定 (纯份额问题, A13 恒等式适用)
    口径 B: dp_scale = 1.0 固定 (T11b 原口径, 可复现 0.62)
并额外报 dp_scale∈[0,1] 连续下的 P(dp* <= 1) —— 即"最小可行新增产能"视角。

产出: prior_sensitivity.csv, prior_bounds.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _common as C  # noqa: E402
import city_model as cm  # noqa: E402

N_LHS = 600                      # ≥500/套, 满足任务要求
PRIORS = ("uniform", "log-uniform", "triangular")
SEED = 20261014

# 主控变量的先验组合: (pool_prior, gap_prior) x 3 套 dp 先验
PAIRS = [(p, g) for p in PRIORS for g in PRIORS]


def draw(n, rng, pool_p, gap_p, dp_p):
    """一次 LHS -> 物理控制量. 4 维: pool, gap, dp, ai_target(恒均匀)."""
    U = C.lhs(n, 4, rng)
    pool = C.map_prior(U[:, 0], *C.CTRL["pool_scale"], pool_p)
    gap = C.map_prior(U[:, 1], *C.CTRL["gap_scale"], gap_p)
    dp = C.map_prior(U[:, 2], *C.CTRL["dp_scale"], dp_p)
    ai = C.map_prior(U[:, 3], *C.AI_TARGET_RANGE, "uniform")
    return pool, gap, dp, ai


def evaluate(pool, gap, ai, doms, panels, samp_idx, names, samples, cache,
             dp_fixed=None, dp_vals=None):
    """求解样本. dp_fixed 为 None 时用 dp_vals (连续), 否则固定该值."""
    n = len(pool)
    s_dpA = np.full(n, np.nan)        # 口径 A: dp=0
    s_dpB = np.full(n, np.nan)        # 口径 B: dp=1.0
    s_own = np.full(n, np.nan)        # 样本自带 dp (若给 dp_vals)
    for k in range(n):
        dom, panel = doms[k], panels[k]
        smp = names[samp_idx[k]]
        try:
            s_dpA[k] = C.s_city(dom, panel, smp, pool=pool[k], gap=gap[k],
                                dp=0.0, ai=ai[k], cache=cache)
            s_dpB[k] = C.s_city(dom, panel, smp, pool=pool[k], gap=gap[k],
                                dp=1.0, ai=ai[k], cache=cache)
            if dp_vals is not None:
                s_own[k] = C.s_city(dom, panel, smp, pool=pool[k], gap=gap[k],
                                    dp=dp_vals[k], ai=ai[k], cache=cache)
        except Exception:                              # noqa: BLE001
            continue
    return s_dpA, s_dpB, s_own


def main() -> int:
    t0 = time.time()
    samples = cm.load_samples()
    names = list(samples["source"])
    cache: dict = {}
    rng = np.random.default_rng(SEED)

    rows: list[dict] = []
    print("=" * 78)
    print("task-4 / 交付物1: 先验敏感性 P(S_city>0)")
    print(f"  {len(PAIRS)} 组 pool x gap 先验组合, 每组 {N_LHS} 样本, dp 三套先验")
    print("=" * 78)

    for (pp, gp) in PAIRS:
        for dpp in PRIORS:
            pool, gap, dp, ai = draw(N_LHS, rng, pp, gp, dpp)
            doms = np.where(rng.random(N_LHS) < 0.5, "ha", "co")
            panels = np.where(rng.random(N_LHS) < 0.5, "A_engine2", "B_full")
            samp_idx = np.minimum((rng.random(N_LHS) * len(names)).astype(int),
                                  len(names) - 1)
            # 有效离子组过滤 (与 T11 一致: 空质量字典跳过)
            ok = np.array([bool(cm.quality_dict(samples.iloc[samp_idx[k]],
                                                cm.PANELS[panels[k]]))
                           for k in range(N_LHS)])
            pool, gap, dp, ai = pool[ok], gap[ok], dp[ok], ai[ok]
            doms, panels, samp_idx = doms[ok], panels[ok], samp_idx[ok]

            sA, sB, sOwn = evaluate(pool, gap, ai, doms, panels, samp_idx,
                                    names, samples, cache, dp_vals=dp)
            n_eff = int(np.sum(np.isfinite(sA)))
            # 连续 dp 口径: "新增产能需求 dp* <= 1" 的比例
            reach = np.isfinite(sOwn) & (sOwn > 0)
            rows.append({
                "pool_prior": pp, "gap_prior": gp, "dp_prior": dpp,
                "n_drawn": N_LHS, "n_effective": n_eff,
                "P_gt0_dpA_dp0": float(np.nanmean(sA > 0)),
                "P_gt0_dpB_dp1": float(np.nanmean(sB > 0)),
                "P_reach_dp_le1": float(np.nanmean(reach)),
                "pool_mean": float(pool.mean()), "pool_median": float(np.median(pool)),
                "gap_mean": float(gap.mean()), "gap_median": float(np.median(gap)),
                "dp_mean": float(dp.mean()), "dp_median": float(np.median(dp)),
                "S_city_dpA_median_ml": float(np.nanmedian(sA)),
                "S_city_dpB_median_ml": float(np.nanmedian(sB)),
            })
            print(f"  {pp:12} x {gp:12} x dp:{dpp:12} | "
                  f"n={n_eff:4d} | P(dp0)={rows[-1]['P_gt0_dpA_dp0']:.4f} "
                  f"P(dp1)={rows[-1]['P_gt0_dpB_dp1']:.4f} "
                  f"P(d*<=1)={rows[-1]['P_reach_dp_le1']:.4f}")

    df = pd.DataFrame(rows)
    df.to_csv(HERE / "prior_sensitivity.csv", index=False, encoding="utf-8-sig")

    # ---------------- 漂移区间 ----------------
    def span(col):
        v = pd.to_numeric(df[col], errors="coerce")
        return {"min": float(v.min()), "max": float(v.max()),
                "median": float(v.median()), "span": float(v.max() - v.min())}

    def span_row(sub):
        """一组先验组合下, 三个统计量的 [min,max]."""
        return {"P_gt0_dpA_dp0": [float(sub.P_gt0_dpA_dp0.min()),
                                  float(sub.P_gt0_dpA_dp0.max())],
                "P_gt0_dpB_dp1": [float(sub.P_gt0_dpB_dp1.min()),
                                  float(sub.P_gt0_dpB_dp1.max())],
                "P_reach_dp_le1": [float(sub.P_reach_dp_le1.min()),
                                   float(sub.P_reach_dp_le1.max())]}

    # dp 先验的边际效应 (对 pool/gap 先验取极值)
    by_dp = {p: span_row(df[df.dp_prior == p]) for p in PRIORS}

    summary = {
        "n_configs": int(len(df)),
        "n_lhs_per_config": N_LHS,
        "seed": SEED,
        "priors": {
            "uniform": "线性, 对所有取值同等无知",
            "log-uniform": "几何, 只知量级 (Jeffreys); 均值远低于区间中点",
            "triangular": "众数=区间中点, 端点最不可能",
        },
        "prior_moments": {
            k: {"mean": C.prior_mean(*C.CTRL[k], "log-uniform"),
                "median": C.prior_median(*C.CTRL[k], "log-uniform"),
                "uniform_mean": 0.5 * (C.CTRL[k][0] + C.CTRL[k][1])}
            for k in ("pool_scale", "gap_scale")},
        "drift_dp0": span("P_gt0_dpA_dp0"),
        "drift_dp1": span("P_gt0_dpB_dp1"),
        "drift_reach_dp_le1": span("P_reach_dp_le1"),
        "drift_by_dp_prior": span_row,
        "by_dp_prior": by_dp,
        "T11b_frozen_reference": C.T11B_P,
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": (
            "MODEL probabilities under the stated priors and the frozen sample pool; "
            "NOT observed event frequencies. The water-sample dimension is drawn "
            "uniformly over 5 lab samples of which 1 is non-reclaimed (brackish) and 2 "
            "have estimated TDS, so it carries no global-frequency meaning."),
    }

    # Gate 判定
    g = C.GateLog()
    dA, dB = summary["drift_dp0"], summary["drift_dp1"]
    g.add("M5-P2 先验漂移必须量化", True,
          f"dp0 span={dA['span']:.3f}; dp1 span={dB['span']:.3f}",
          "必须给出明确漂移区间 (区间宽度 > 0 即算量化)",
          f"9 组先验 x {N_LHS} 样本; P(dp=0)∈[{dA['min']:.3f},{dA['max']:.3f}], "
          f"P(dp=1)∈[{dB['min']:.3f},{dB['max']:.3f}]")
    # 关键: 0.62 是否在先验漂移区间内 stays robust?
    lo, hi = dB["min"], dB["max"]
    g.add("0.62 是否对先验稳健 (<0.10 绝对漂移)", (hi - lo) < 0.10,
          f"dp1 极差 = {hi - lo:.3f}",
          "极差 < 0.10 => 可保留单一数字; 否则必须限定先验",
          f"P(dp=1) 从 {lo:.3f} 到 {hi:.3f}, 冻结值 {C.T11B_P[1.0]} 落在区间内 = "
          f"{lo <= C.T11B_P[1.0] <= hi}")
    # G3: dp=0 口径是否与 A13 恒等式一致
    g.add("A13 恒等式在 dp=0 口径成立", bool(dA["max"] <= 0.02),
          f"max P(dp=0) = {dA['max']:.4f}",
          "dp=0 时 available=pool => x_ai+inc≡pool => S_city≡M0-M<=0, 故 P 应≈0",
          f"9 组先验下 P(S_city>0|dp=0) 最大仅 {dA['max']:.4f}")

    summary["gates"] = g.to_json()
    C.write_json(HERE / "prior_bounds.json", summary)

    print("\n" + "=" * 78)
    print(f"口径 A (dp=0):   P(S_city>0) ∈ [{dA['min']:.4f}, {dA['max']:.4f}]"
          f"  中位 {dA['median']:.4f}")
    print(f"口径 B (dp=1):   P(S_city>0) ∈ [{lo:.4f}, {hi:.4f}]  中位 {dB['median']:.4f}")
    print(f"   冻结 0.62 在区间内 = {lo <= 0.62 <= hi}")
    print(f"P(dp*<=1) 达标的比例 ∈ [{summary['drift_reach_dp_le1']['min']:.4f}, "
          f"{summary['drift_reach_dp_le1']['max']:.4f}]")
    print(f"耗时 {summary['runtime_s']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
