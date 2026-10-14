#!/usr/bin/env python
# ⛔ OBSOLETE / 已作废 (2026-10-14) —— 请勿运行, 勿引用其产物。
# 作废原因: 见 A13_可靠性机制/AUDIT_2026-10-14_撤回声明.md
#   该脚本使用已撤回的 psi/Delta 公式 (D 取错量 + 取水量与缺口相减)。
# 替代品: A13_可靠性机制/potable_flow_corrected.py (核心)
#        A15_稳健性/ablation_matrix_corrected.py (消融)
#        A15_稳健性/holdout_validation_corrected.py (留出+边界)
# 保留本文件仅作审计留痕。

"""A13b: 两通道对消与原理解析 -- 论文的核心机制.

发现
----
再生水冷却对城市水系统同时作用两条符号相反的通道:

  通道 Q (水质): phi 升高 -> 浓缩倍数下降 -> 补水 M 升高 -> S_algebra = M0-M 变负
                 (损害城市)
  通道 R (可靠性): phi 升高 -> AI 自来水取用下降 -> psi 下降 -> Delta = W*max(0,psi-1) 下降
                 (改善城市)

净效应 = -(M-M0) - W*max(0,psi-1);  两条通道此前从未被同时核算。

本脚本:
  1. 正交性检验: 在 dp=0 (无新增产能) 下证明通道 R 独立于 T12 的产能边界曲面;
  2. 临界 phi*: psi(phi*) = 1 的解析解与数值解对比;
  3. 通道分解: 量化 Q/R 各自贡献;
  4. 解析式验证: psi(phi) 的闭式推导.
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
import reliability_model as rm  # noqa: E402
import city_model as cm  # noqa: E402


def analytic_psi(dom: str, panel: str, sample: str, phi: float, W_scale: float,
                 D_scale: float, limit_scale: float, cache: dict) -> float:
    """解析预测: psi = (D + (1-phi_eff) M(phi)) / W,  W = W_scale*(D+m0)."""
    r = cm.city_outcome(dom, panel, sample, ai_target=phi, dp_scale=0.0,
                        limit_scale=limit_scale, cache=cache)
    bl = cm.BASELINES[dom]
    D = bl["gap"] * D_scale
    W = (D + r["m0_ml"]) * W_scale
    return (D + (1.0 - r["phi_eff"]) * r["M_ml"]) / W


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    SAMPLES = ["IEUA RP-1 (2025, tertiary)", "LADWP AWPF (2012, RO product)",
               "Figshare RW (2025, paired study)"]
    DOMS = ["ha", "co"]
    cache: dict = {}

    rec("=" * 72)
    rec("A13b 两通道对消 / 临界 phi* / 正交性")
    rec("=" * 72)

    # ---------- 1. 正交性: dp=0 下通道 R 是否存在 ----------
    rec("\n[1] 正交性检验: dp=0 (无新增产能) 下, 可靠性通道是否仍起作用")
    rows = []
    for dom in DOMS:
        for smp in SAMPLES:
            for ws in (0.80, 0.85, 0.90, 0.95, 1.00, 1.05):
                for phi in np.arange(0.0, 0.81, 0.05):
                    phi = round(float(phi), 2)
                    r = rm.solve_with_reliability(
                        dom, "B_full", smp, W_scale=ws, D_scale=1.0,
                        ai_target=phi, dp_scale=0.0, limit_scale=0.5, cache=cache)
                    psi_an = analytic_psi(dom, "B_full", smp, phi, ws, 1.0, 0.5, cache)
                    rows.append({
                        "domain": dom, "sample": smp, "W_scale": ws, "phi": phi,
                        "psi_num": r["psi"], "psi_analytic": psi_an,
                        "psi_err": abs(r["psi"] - psi_an),
                        "Delta_ml": r["Delta_ml"], "S_algebra_ml": r["S_algebra_ml"],
                        "S_city_ml": r["S_city_ml"],
                        "channel_Q_ml": r["S_algebra_ml"],          # 质量通道 (<=0)
                        "channel_R_ml": -r["Delta_ml"],             # 可靠性通道 (>=0 表示改善, 取负损失)
                        "dp_ml": r["dp_ml"],
                    })
    d = pd.DataFrame(rows)
    d.to_csv(HERE / "two_channel_decomposition.csv", index=False, encoding="utf-8-sig")
    rec(f"  {len(d)} 情景; psi 解析 vs 数值 最大误差 = {d['psi_err'].max():.3e}")
    rec(f"  >> 解析式 psi=(D+(1-phi_eff)M(phi))/W 验证通过 = "
        f"{bool(d['psi_err'].max() < 1e-9)}")

    # dp 是否全为 0 (证明与产能扩张无关)
    rec(f"  dp_ml 全为 0 = {bool((d['dp_ml'].abs() < 1e-9).all())} "
        f"(说明本检验不含新增产能, 与 T12 边界曲面正交)")

    # ---------- 2. 临界 phi* ----------
    rec("\n[2] 临界混合比 phi*: psi(phi*) = 1  (解析解)")
    crit = []
    for dom in DOMS:
        for smp in SAMPLES:
            for ws in (0.80, 0.85, 0.90, 0.95, 1.00):
                sub = d[(d["domain"] == dom) & (d["sample"] == smp) &
                        np.isclose(d["W_scale"], ws)].sort_values("phi")
                if len(sub) < 3:
                    continue
                above = sub[sub["psi_num"] > 1.0 + 1e-9]["phi"]
                below = sub[sub["psi_num"] <= 1.0 + 1e-9]["phi"]
                pstar = float(below.min()) if len(below) else np.nan
                crit.append({"domain": dom, "sample": smp, "W_scale": ws,
                             "psi_at_phi0": float(sub["psi_num"].iloc[0]),
                             "psi_at_phi08": float(sub["psi_num"].iloc[-1]),
                             "phi_star": pstar,
                             "reachable": bool(len(below) > 0),
                             "channelQ_loss_at_phi08": float(-sub["S_algebra_ml"].iloc[-1]),
                             "channelR_gain_at_phi08": float(sub["Delta_ml"].iloc[0])})
    cdf = pd.DataFrame(crit)
    cdf.to_csv(HERE / "critical_phi_star.csv", index=False, encoding="utf-8-sig")
    rec(cdf.to_string(index=False))

    # ---------- 3. 两通道分解 ----------
    rec("\n[3] 两通道分解 (phi: 0 -> 0.8, dp=0)")
    dec = []
    for dom in DOMS:
        for smp in SAMPLES:
            for ws in (0.80, 0.90, 0.95, 1.00):
                sub = d[(d["domain"] == dom) & (d["sample"] == smp) &
                        np.isclose(d["W_scale"], ws)].sort_values("phi")
                a = sub[sub["phi"] == 0.0]
                b = sub[sub["phi"] == 0.8]
                if not len(a) or not len(b):
                    continue
                a, b = a.iloc[0], b.iloc[0]
                dQ = float(b["S_algebra_ml"] - a["S_algebra_ml"])   # <0 恶化
                dR = float(-(b["Delta_ml"] - a["Delta_ml"]))        # >0 改善(损失减少)
                dec.append({"domain": dom, "sample": smp, "W_scale": ws,
                            "dQ_ml": dQ, "dR_ml": dR, "net_ml": dQ + dR,
                            "check_net_equals_dS": abs((dQ + dR) -
                                                       (b["S_city_ml"] - a["S_city_ml"]))})
    ddf = pd.DataFrame(dec)
    ddf.to_csv(HERE / "channel_decomposition.csv", index=False, encoding="utf-8-sig")
    rec(f"  分解自洽性: 最大残差 = {ddf['check_net_equals_dS'].max():.3e} ML")
    rec(f"  通道 Q (水质) 平均变化 = {ddf['dQ_ml'].mean():+.1f} ML  (负=恶化)")
    rec(f"  通道 R (可靠性) 平均变化 = {ddf['dR_ml'].mean():+.1f} ML  (正=改善)")
    rec(f"  两通道符号相反的比例 = "
        f"{float(((ddf['dQ_ml'] < 0) & (ddf['dR_ml'] > 0)).mean()):.1%}")
    rec(f"  通道 R 显著(>1 ML)的情景数 = {int((ddf['dR_ml'] > 1).sum())}/{len(ddf)}")

    # 符号相反 → 存在净效应为零的 phi_zero
    rec("\n  净效应过零点 phi0 (S_city 最优点) 是否存在:")
    zero_rows = []
    for dom in DOMS:
        for ws in (0.90, 0.95, 1.00):
            sub = d[(d["domain"] == dom) & np.isclose(d["W_scale"], ws) &
                    (d["sample"] == SAMPLES[0])].sort_values("phi")
            if len(sub) < 3:
                continue
            dy = np.diff(sub["S_city_ml"].values)
            sign_change = np.where(np.sign(dy[:-1]) != np.sign(dy[1:]))[0]
            zero_rows.append({"domain": dom, "W_scale": ws,
                              "S_city_at_phi0": float(sub["S_city_ml"].iloc[0]),
                              "S_city_at_phi08": float(sub["S_city_ml"].iloc[-1]),
                              "is_monotone": bool(len(sign_change) == 0),
                              "argmax_phi": float(sub.loc[sub["S_city_ml"].idxmax(), "phi"])})
    zdf = pd.DataFrame(zero_rows)
    zdf.to_csv(HERE / "net_optimum.csv", index=False, encoding="utf-8-sig")
    rec(zdf.to_string(index=False))

    summary = {
        "n_scenarios": int(len(d)),
        "psi_analytic_max_err": float(d["psi_err"].max()),
        "psi_analytic_verified": bool(d["psi_err"].max() < 1e-9),
        "dp_all_zero": bool((d["dp_ml"].abs() < 1e-9).all()),
        "phi_star_by_W": {str(w): (float(np.nanmedian(cdf[cdf["W_scale"] == w]["phi_star"]))
                                   if cdf[cdf["W_scale"] == w]["phi_star"].notna().any()
                                   else None)
                          for w in sorted(cdf["W_scale"].unique())},
        "reachable_share": float(cdf["reachable"].mean()),
        "channel_opposite_sign_share": float(((ddf["dQ_ml"] < 0) & (ddf["dR_ml"] > 0)).mean()),
        "channel_Q_mean_ml": float(ddf["dQ_ml"].mean()),
        "channel_R_mean_ml": float(ddf["dR_ml"].mean()),
        "decomposition_max_residual_ml": float(ddf["check_net_equals_dS"].max()),
        "n_nonmonotone_S_city": int((~zdf["is_monotone"]).sum()),
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": (
            "通道 R 在 dp=0 (无新增产能) 下成立, 故本机制与 T12 的产能边界曲面正交。"
            "两通道符号相反, 净效应是二者之和 —— 这解释为何单一通道核算会给出误导性结论。"
            "模型内结论, 非观测频率。"),
    }
    (HERE / "two_channel_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    rec("\n" + "=" * 72)
    rec(f"完成 {summary['runtime_s']}s")
    (HERE / "a13b_repro_log.txt").write_text("\n".join(log), encoding="utf-8")


if __name__ == "__main__":
    main()
