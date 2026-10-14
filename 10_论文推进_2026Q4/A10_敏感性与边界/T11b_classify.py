"""T11b: T11 结果的分层后处理 (不重跑引擎).

问题
----
T11 的破坏阈值 dp* 的分位数被 "knife-edge" 主导: 因条件零和恒等式, 约 62% 的
情景在 dp=0 处 S_city ≈ 0^- (机器精度级负值), 二分求根把 dp* 解到 ~1e-9.
若直接报 dp* 中位数 = 0, 会掩盖真正需要新增产能的那批情景.

分层
----
以 S_city(dp=1) 的绝对值作尺度:
    edge       : |S_city(dp=0)| <= 1% * |S_city(dp=1)|   -> dp* 无信息
    negative   : S_city(dp=0) <  -1% * |S_city(dp=1)|     -> 真需要新增产能
    positive   : S_city(dp=0) >  0                        -> 本就净获益
只在 `negative` 组报告 dp* 分布, 并给出 edge 占比.

同时报告 P(S_city>0) 曲线、按域分组、以及剔除病态尾部 (|y|>5) 的稳健分位.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
EDGE = 0.01


def main() -> int:
    d = pd.read_csv(HERE / "T11_uncertainty_samples.csv", encoding="utf-8-sig")
    s0 = pd.to_numeric(d["S_city_dp0.0_ml"], errors="coerce")
    s1 = pd.to_numeric(d["S_city_dp1.0_ml"], errors="coerce")
    scale = s1.abs().clip(lower=1e-12)

    d = d.assign(_s0=s0, _s1=s1, _scale=scale)
    d["class"] = np.where(s0 > 0, "positive",
                          np.where(s0.abs() <= EDGE * scale, "edge", "negative"))

    def q(series, ps=(0.05, 0.25, 0.5, 0.75, 0.95)):
        v = pd.to_numeric(series, errors="coerce").dropna()
        return {f"q{int(p*100)}": float(v.quantile(p)) for p in ps}

    neg = d[d["class"] == "negative"]
    dpr = {}
    for col, name in (("dp_star", "dp_star_all"),):
        pass
    summary = {
        "n": int(len(d)),
        "status_counts": d.status.value_counts().to_dict(),
        "class_counts": d["class"].value_counts().to_dict(),
        "class_share": (d["class"].value_counts(normalize=True)).round(4).to_dict(),
        "P_S_city_gt0": {f"dp{k}": float((pd.to_numeric(d[f"S_city_dp{k}_ml"],
                                                        errors="coerce") > 0).mean())
                         for k in ("0.0", "0.5", "1.0", "2.0")},
        "P_S_city_gt0_by_domain_dp1": {
            dom: float((pd.to_numeric(g["S_city_dp1.0_ml"], errors="coerce") > 0).mean())
            for dom, g in d.groupby("domain")},
        "dp_star_quantiles_negative_only": q(neg.dp_star),
        "n_negative": int(len(neg)),
        "dp_star_share_gt_0.1_in_negative": float((neg.dp_star > 0.1).mean()) if len(neg) else None,
        "dp_star_share_gt_0.5_in_negative": float((neg.dp_star > 0.5).mean()) if len(neg) else None,
        "y_dp1_quantiles_all": q(d.y_dp1),
        "y_dp1_quantiles_excl_illconditioned": q(d.loc[d.y_dp1.abs() <= 5.0, "y_dp1"]),
        "illconditioned_share_abs_y_gt5": float((d.y_dp1.abs() > 5.0).mean()),
        "S_city_dp1_quantiles_ML": q(d["S_city_dp1_ml"]),
        "discipline_note": "MODEL probabilities under uniform priors and the frozen sample "
                           "pool; NOT observed event frequencies. 'edge' cases sit on the "
                           "conditional zero-sum knife-edge S_city(dp=0)~0 and carry no dp* info.",
        "reading": "P(S_city>0) jumps from ~0 at dp=0 to ~0.62 for any dp>=0.5 and then "
                   "saturates: adding reuse capacity beyond the incumbent-gap/pool balance "
                   "cannot fix the ~38% of configurations where displacement dominates.",
    }
    (HERE / "T11b_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print(f"[T11b] n={summary['n']} | status={summary['status_counts']}")
    print("  分类占比:", summary["class_share"])
    print("  P(S_city>0) @dp:", {k: round(v, 3) for k, v in summary["P_S_city_gt0"].items()})
    print("  dp* (仅 negative 组, n=%d):" % len(neg),
          {k: round(v, 3) for k, v in summary["dp_star_quantiles_negative_only"].items()})
    print(f"  negative 组中 dp*>0.1 占比: {summary['dp_star_share_gt_0.1_in_negative']:.3f},"
          f" >0.5: {summary['dp_star_share_gt_0.5_in_negative']:.3f}")
    print("  y(dp=1) 分位(剔除 |y|>5):",
          {k: round(v, 3) for k, v in summary["y_dp1_quantiles_excl_illconditioned"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
