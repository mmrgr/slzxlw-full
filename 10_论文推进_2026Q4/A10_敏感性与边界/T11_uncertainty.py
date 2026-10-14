"""T11: 概率化不确定性 —— P(S_city > 0) 与破坏阈值 dp* 的分位数.

方法
----
在控制量分布上做拉丁超立方抽样 (LHS), 每个情景用**真实模块**求解:
    y = S_city/M0   (无量纲城市净取水变化)
    dp* = 使 S_city 过零所需的新增回用产能 / P0  (二分求根; 无过零记为 NaN)

抽样维度 (LHS 单位超立方 -> 物理域):
    pool_scale [0.3,4]  gap_scale [0.3,4]  ai_target [0.10,0.95]
    + 离散: 域 {ha,co} × 面板 {A_engine2,B_full} × 水样 (5 选 1)

同时报告 P(S_city>0 | dp_scale = 参考值) 曲线 (0 / 0.5 / 1.0 / 2.0).

纪律 (规划 §2.6 硬要求)
    本表是"**给定情景与参数分布下的模型概率**", 不是真实城市未来事件的
    观测频率. 参数分布为均匀先验 (无外部先验数据), 结果对该选择敏感.
    抽样的 water sample 池含 1 组非再生水 (苦咸水) 与 2 组 TDS 估算值,
    故水样维上的概率不是"全球再生水分布"的频率.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import city_model as cm  # noqa: E402

RNG = np.random.default_rng(20261014)
N = 700
PANEL_NAMES = ("A_engine2", "B_full")
DP_REF = (0.0, 0.5, 1.0, 2.0)
DP_SCAN = np.linspace(0.0, 3.0, 7)


def lhs(n: int, k: int, rng) -> np.ndarray:
    """拉丁超立方抽样 (接受外部随机源).

    清理轮 2026-10-14 (E-4): `A9_无量纲折叠/T9_dimensionless_collapse.lhs` 是同名
    但**已分叉**的另一个实现 (用模块级 RNG, 不接受 rng 参数)。
    两者**故意不统一** —— 统一会改变 T9 的抽样序列, 使冻结产物
    T9_summary.json 的数值变动。改任一处前请先确认另一处的既有产物。
    """
    u = np.empty((n, k))
    for j in range(k):
        u[:, j] = (rng.permutation(n) + rng.random(n)) / n
    return u


def s_city_at(dom, panel, sample, pool, gap, ai, dp, cache) -> float:
    return cm.city_outcome(dom, panel, sample, pool_scale=pool, gap_scale=gap,
                           dp_scale=dp, ai_target=ai, cache=cache)["S_city_ml"]


def find_dp_star(dom, panel, sample, pool, gap, ai, cache):
    """返回 (dp*, sign_change_found). 先粗扫定位区间, 再二分."""
    vals = np.array([s_city_at(dom, panel, sample, pool, gap, ai, d, cache)
                     for d in DP_SCAN])
    sign = np.sign(vals)
    idx = np.where(np.diff(sign) != 0)[0]
    if len(idx) == 0:
        return np.nan, False
    i = int(idx[0])
    lo, hi = DP_SCAN[i], DP_SCAN[i + 1]
    flo = vals[i]
    for _ in range(28):
        mid = 0.5 * (lo + hi)
        fm = s_city_at(dom, panel, sample, pool, gap, ai, mid, cache)
        if np.sign(fm) == np.sign(flo):
            lo, flo = mid, fm
        else:
            hi = mid
    return 0.5 * (lo + hi), True


def main() -> int:
    samples = cm.load_samples()
    names = list(samples["source"])
    U = lhs(N, 5, RNG)
    pool_s = 0.3 * (4.0 / 0.3) ** U[:, 0]
    gap_s = 0.3 * (4.0 / 0.3) ** U[:, 1]
    ai_t = 0.10 + 0.85 * U[:, 2]
    samp_i = np.minimum((U[:, 3] * len(names)).astype(int), len(names) - 1)
    combo = np.minimum((U[:, 4] * 4).astype(int), 3)   # dom x panel

    rows = []
    cache: dict = {}
    for k in range(N):
        dom = "ha" if combo[k] % 2 == 0 else "co"
        panel = PANEL_NAMES[(combo[k] // 2) % 2]
        sample = names[samp_i[k]]
        q = cm.quality_dict(samples.iloc[samp_i[k]], cm.PANELS[panel])
        if not q:
            continue
        res = {"domain": dom, "panel": panel, "sample": sample,
               "pool_scale": pool_s[k], "gap_scale": gap_s[k], "ai_target": ai_t[k]}
        o = cm.city_outcome(dom, panel, sample, pool_scale=pool_s[k],
                            gap_scale=gap_s[k], dp_scale=1.0, ai_target=ai_t[k],
                            cache=cache)
        res.update({"y_dp1": o["y"], "S_city_dp1_ml": o["S_city_ml"],
                    "eta_dp1": o["eta_transfer"], "phi_eff_dp1": o["phi_eff"],
                    "Phi_dp1": o["Phi"], "status": o["status"]})
        for dref in DP_REF:
            res[f"S_city_dp{dref}_ml"] = s_city_at(dom, panel, sample, pool_s[k],
                                                   gap_s[k], ai_t[k], dref, cache)
        dp_star, found = find_dp_star(dom, panel, sample, pool_s[k], gap_s[k],
                                      ai_t[k], cache)
        res["dp_star"] = dp_star
        res["dp_star_found"] = bool(found)
        rows.append(res)

    df = pd.DataFrame(rows)
    df.to_csv(HERE / "T11_uncertainty_samples.csv", index=False, encoding="utf-8-sig")

    def ppos(col):
        v = pd.to_numeric(df[col], errors="coerce").dropna()
        return float((v > 0).mean()) if len(v) else float("nan")

    def q(col, ps=(0.05, 0.25, 0.5, 0.75, 0.95)):
        v = pd.to_numeric(df[col], errors="coerce").dropna()
        return {f"q{int(p*100)}": float(v.quantile(p)) for p in ps} if len(v) else {}

    summary = {
        "n_samples": int(len(df)),
        "discipline_note": "These are MODEL probabilities under uniform priors and the "
                           "frozen sample pool; they are NOT observed event frequencies.",
        "P_S_city_gt0": {f"dp{d}": ppos(f"S_city_dp{d}_ml") for d in DP_REF},
        "P_S_city_gt0_by_domain": {
            "dp1": {d: ppos_sub for d, ppos_sub in
                    ((d, float((pd.to_numeric(df[df.domain == d]["S_city_dp1.0_ml"],
                                              errors="coerce") > 0).mean()))
                     for d in df.domain.unique())}},
        "y_dp1_quantiles": q("y_dp1"),
        "S_city_dp1_quantiles": q("S_city_dp1_ml"),
        "dp_star_quantiles": q("dp_star"),
        "dp_star_found_share": float(df.dp_star_found.mean()),
        "n_dp_star_negative_or_nan": int((~df.dp_star_found).sum() + (df.dp_star <= 0).sum()),
        "eta_dp1_quantiles": q("eta_dp1"),
        "phi_eff_dp1_range": [float(df.phi_eff_dp1.min()), float(df.phi_eff_dp1.max())],
        "statuses": sorted(df.status.unique().tolist()),
    }
    (HERE / "T11_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print(f"[T11] n={len(df)} | 状态={summary['statuses']}")
    print("  P(S_city>0) @ dp:", {k: round(v, 3) for k, v in summary["P_S_city_gt0"].items()})
    print("  dp* 分位:", {k: round(v, 3) for k, v in summary["dp_star_quantiles"].items()})
    print(f"  dp* 有符号过零比例: {summary['dp_star_found_share']:.3f}")
    print("  y(dp=1) 分位:", {k: round(v, 3) for k, v in summary["y_dp1_quantiles"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
