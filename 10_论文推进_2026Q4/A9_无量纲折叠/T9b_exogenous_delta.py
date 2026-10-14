"""T9b — δ 的外生可预测性检验（审计 A1/A2/D5 修复, 2026-10-14）

背景
----
T9 的折叠  y = Φ·(w − u)  经审计确认为**代数恒等式**：δ 的定义
    δ := 1 − (pool − inc_recl)/x_ai
正是为使该式成立而设，所以残差 ~1e-15 与 R²=1 是数学必然，不构成证据。

真正的可迁移性问题是：
    **分配结果 δ 能否由外生参数预测？**
    （δ 若只能被"定义出来"，则折叠坐标只是把待解释的变异搬进坐标轴。）

本脚本用 T9 的同一批 LHS 情景（T9_collapse_points.csv），在外生参数
    P   = 该情景的再生水池规模 (pool_ml)
    G   = 既有用户未满足缺口 (gap_ml)
    ΔP  = 新增回用产能 (dp_ml)
上检验若干**零拟合**的解析候选式，并报告 R² / MAE / 命中率。

预注册判据（见 A0_预注册/preregistration_amendment_1.md）：
  δ 的外生预测 R² ≥ 0.90 且 中位相对误差 ≤ 20% ⇒ 可迁移性成立；
  否则 ⇒ 折叠坐标不具跨城市可迁移性，主张须限定到已模拟的参数域。

输出: T9b_delta_prediction.csv / T9b_summary.json / fig7_exogenous_delta.png
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

CANDIDATES = {
    "A_dp_over_pool_plus_dp": lambda P, G, dP: dP / max(P + dP, 1e-9),
    "B_dp_over_pool_plus_dp_minus_gap": lambda P, G, dP: dP / max(P + dP - min(G, P), 1e-9),
    "C_dp_minus_gap_shortfall_over_dp": lambda P, G, dP: ((dP - max(0.0, G - P)) / dP)
    if dP > 1e-9 else 0.0,
}


def metrics(y, yhat) -> dict:
    m = np.isfinite(y) & np.isfinite(yhat)
    y, yhat = np.asarray(y)[m], np.asarray(yhat)[m]
    if len(y) < 3:
        return {"n": int(len(y)), "R2": np.nan, "MAE": np.nan, "med_rel_err": np.nan}
    res = y - yhat
    ss = np.sum((y - y.mean()) ** 2)
    denom = np.where(np.abs(y) > 1e-9, np.abs(y), np.nan)
    return {
        "n": int(len(y)),
        "R2": float(1.0 - np.sum(res ** 2) / ss) if ss > 0 else np.nan,
        "MAE": float(np.mean(np.abs(res))),
        "RMSE": float(np.sqrt(np.mean(res ** 2))),
        "med_rel_err": float(np.nanmedian(np.abs(res) / denom)),
        "hit_rate_0.05": float(np.mean(np.abs(res) <= 0.05)),
        "hit_rate_0.10": float(np.mean(np.abs(res) <= 0.10)),
        "bias": float(np.mean(res)),
    }


def main() -> int:
    pts = pd.read_csv(HERE / "T9_collapse_points.csv", encoding="utf-8-sig")
    summ = json.loads((ROOT / "A7_质量分配联合" / "T2_summary.json")
                      .read_text(encoding="utf-8"))
    pts["gap_ml"] = pts.apply(
        lambda r: float(summ["baselines"][r["domain"]]["gap_ml"]) * r["gap_scale"], axis=1)

    print("=" * 78)
    print("T9b  δ 的外生可预测性检验 (零拟合解析候选式)")
    print("=" * 78)
    print(f"情景数 {len(pts)}; δ ∈ [{pts.delta.min():.3f}, {pts.delta.max():.3f}]; "
          f"ΔP/P ∈ [{ (pts.dp_ml/pts.pool_ml).min():.3f}, {(pts.dp_ml/pts.pool_ml).max():.3f}]")
    qs = np.nanquantile(pts.delta, [0, .05, .25, .5, .75, .95, 1.0])
    print("δ 分位 [0,5,25,50,75,95,100]%: " + ", ".join(f"{x:.2f}" for x in qs))
    phys_mask = (pts.delta >= -1e-9) & (pts.delta <= 1.0 + 1e-9)
    phys = pts[phys_mask]
    print(f"δ 落在物理域 [0,1] 的比例: {len(phys)}/{len(pts)} = {len(phys)/len(pts):.1%}"
          f"  (域外值意味着分配规则把池或新增产能分给了被认定权利之外的一方)")

    rows = []
    for name, f in CANDIDATES.items():
        raw = pts.apply(lambda r: f(r.pool_ml, r.gap_ml, r.dp_ml), axis=1)
        pred = np.clip(raw, 0.0, 1.0)
        mt = metrics(pts.delta, pred)
        rows.append({"model": name, **mt})
        pts[f"delta_pred_{name}"] = pred
    tab = pd.DataFrame(rows).set_index("model")
    pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
    print("\n--- 候选式表现 (对 δ 的真值)")
    print(tab.round(4).to_string())

    best = tab.R2.idxmax()
    print(f"\n最佳候选: {best}  (R2={tab.loc[best,'R2']:.4f}, "
          f"MAE={tab.loc[best,'MAE']:.4f}, 中位相对误差={tab.loc[best,'med_rel_err']:.1%})")

    # ---- 物理域子样本上的表现 (排除 x_ai -> 0 的病态外推) ----
    phys = pts[phys_mask]
    prows = []
    for name in CANDIDATES:
        mt = metrics(phys.delta, phys[f"delta_pred_{name}"])
        prows.append({"model": name, **mt})
    ptab = pd.DataFrame(prows).set_index("model")
    print(f"\n--- 物理域子样本 (n={len(phys)}) 上的候选式表现")
    print(ptab.round(4).to_string())

    # ---- 用 δ_pred 代入折叠式预测城市收益 (端到端可迁移性) ----
    d_pred = pts[f"delta_pred_{best}"].to_numpy()
    w_pred = pts.phi_eff.to_numpy() * d_pred
    y_pred_exo = pts.Phi.to_numpy() * (w_pred - pts.u.to_numpy())
    mt_y = metrics(pts.y_num, y_pred_exo)
    print(f"\n--- 端到端: 用 δ_pred 预测归一化城市收益 y (无任何拟合)")
    print(f"  R2={mt_y['R2']:.4f}  MAE={mt_y['MAE']:.4f}  "
          f"中位相对误差={mt_y['med_rel_err']:.1%}  |bias|={abs(mt_y['bias']):.4f}")

    # ---- 符号正确性 (论文实际关心的是"收益是否为正") ----
    sgn_pred = np.sign(y_pred_exo)
    sgn_true = np.sign(pts.y_num.to_numpy())
    valid = np.isfinite(sgn_pred) & np.isfinite(sgn_true) & (np.abs(pts.y_num) > 1e-9)
    agree = float(np.mean(sgn_pred[valid] == sgn_true[valid])) if valid.any() else np.nan
    print(f"  收益符号判别准确率 (排除 y≈0): {agree:.1%}  (n={int(valid.sum())})")

    out = pts[["domain", "panel", "sample", "pool_ml", "gap_ml", "dp_ml", "ai_target",
               "phi_eff", "Phi", "delta", f"delta_pred_{best}", "y_num"]].copy()
    out["y_pred_exogenous"] = y_pred_exo
    out["sign_correct"] = sgn_pred == sgn_true
    out.to_csv(HERE / "T9b_delta_prediction.csv", index=False, encoding="utf-8-sig")

    thr_r2, thr_rel = 0.90, 0.20
    passed = bool(tab.loc[best, "R2"] >= thr_r2 and tab.loc[best, "med_rel_err"] <= thr_rel)
    summary = {
        "prereg_criteria": {"R2_min": thr_r2, "median_rel_err_max": thr_rel},
        "candidates": tab.reset_index().to_dict("records"),
        "best_model": best,
        "best_model_formula": "clip( dP / max(P + dP - min(G,P), eps), 0, 1 )",
        "delta_prediction_pass": passed,
        "delta_quantiles": {k: float(v) for k, v in zip(
            ["0", "5", "25", "50", "75", "95", "100"], qs)},
        "physical_domain_share": float(len(phys) / len(pts)),
        "physical_domain_candidates": ptab.reset_index().to_dict("records"),
        "physical_domain_best_R2": float(ptab.R2.max()),
        "end_to_end_y": mt_y,
        "sign_agreement": agree,
        "n_scenarios": int(len(pts)),
        "interpretation": (
            "delta is predictable from exogenous parameters "
            "(P, G, dP) with a zero-fit analytic rule"
            if passed else
            "delta is NOT predictable from exogenous parameters at the pre-registered "
            "tolerance; the collapse coordinate is descriptive, not transferable"),
    }
    (HERE / "T9b_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\n预注册判据 R2>={thr_r2}, 中位相对误差<={thr_rel:.0%} → "
          f"{'PASS' if passed else 'FAIL'}")
    print(f"[write] {HERE/'T9b_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
