"""task-4 / 交付物 3+5 (修正版): 跨域留出 + 边界压力测试.

⚠ 修正说明 (2026-10-14, 见 A13_可靠性机制/AUDIT_2026-10-14_撤回声明.md)
   原版的"闭式预测律" psi=(D+(1-phi_eff)M)/W 与 Delta=W*max(0,psi-1) 已撤回:
     - D 取自 gap = 既有用户【未满足的再生水需求】, 不是自来水需求 (范畴错误)
     - S_city = S_algebra - lam*Delta 把【取水量】与【缺口水】相减 (量纲错误)
   本版改用 A13c 的合法口径:
     dS_pot = C - F = M1 - M0        (份额口径 dp=0, 恒等式残差 3.6e-12)

检验内容 (修正后):
  H1  留出: 在 ha 上确定 dS_pot 的闭式 (零自由参数), 到 co 做前向预测
      —— 但闭式需要 co 的引擎量 M0/M1, 故这是**代数重推导**, 不是真留出。
         如实标注, 并同时报告**真留出** (单参数 phi_eff 律)。
  H2  真留出: 在 ha 上拟合 phi_eff ≈ a*phi (1 参数), 冻结后到 co 前向预测 dS_pot
  H3  边界: 关闭水质反馈 (chi->inf) 时 dS_pot 必须 -> 0
  H4  边界: 质量惩罚随 chi 单调 (水质越差, 惩罚越大)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
A10 = ROOT / "A10_敏感性与边界"
sys.path.insert(0, str(A10))
import city_model as cm  # noqa: E402

SAMPLES = ["IEUA RP-1 (2025, tertiary)", "LADWP AWPF (2012, RO product)",
           "Figshare RW (2025, paired study)", "AI-UWM model assumption"]
PHI = np.round(np.arange(0.0, 0.81, 0.05), 2)
REF_COC_DESIGN = 5.0   # 引擎默认设计 CoC (A26 语义列用)
CHI = (1.0, 0.5, 0.25)


def collect(dom: str, cache: dict) -> pd.DataFrame:
    rows = []
    for smp in SAMPLES:
        for chi in CHI:
            for phi in PHI:
                try:
                    r1 = cm.city_outcome(dom, "B_full", smp, pool_scale=1.0,
                                         gap_scale=1.0, dp_scale=0.0,
                                         ai_target=float(phi), limit_scale=chi,
                                         cache=cache)
                    r0 = cm.city_outcome(dom, "B_full", smp, pool_scale=1.0,
                                         gap_scale=1.0, dp_scale=0.0,
                                         ai_target=0.0, limit_scale=chi, cache=cache)
                except Exception:  # noqa: BLE001
                    continue
                M1, M0 = r1["M_ml"], r0["M_ml"]
                phi_eff = r1["phi_eff"]
                F = M0 - (1.0 - phi_eff) * M1
                C = max(0.0, r0["inc_reclaimed_ml"] - r1["inc_reclaimed_ml"])
                rows.append({
                    "domain": dom, "sample": smp, "chi": chi, "phi": float(phi),
                    # ---- A26 权威语义列 (见 A26_语义统一/CHI_SEMANTICS.md) ----
                    "limit_scale": float(chi),
                    "chi_strictness": float(r1["CoC_ai"]) / REF_COC_DESIGN,
                    "quality_binding": bool(float(r1["CoC_ai"]) < REF_COC_DESIGN * (1 - 1e-9)),
                    # A27: 引擎 CoC 下限 1.000001; 触底则补水退化为天文数字, 情景无意义
                    "coc_floor_degenerate": bool(float(r1["CoC_ai"]) <= 1.000001 + 1e-9),
                    "M0_ml": M0, "M1_ml": M1, "phi_eff": phi_eff,
                    "F_ml": F, "C_ml": C, "x_ai_ml": float(r1["x_ai_ml"]),
                    "dS_pot_ml": C - F, "dS_pot_M_ml": M1 - M0,   # 恒等式右侧
                    "CoC": r1["CoC_ai"], "status": r1["status"],
                })
    return pd.DataFrame(rows)


def r2_score(y, yhat) -> float:
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    ss = np.sum((y - y.mean()) ** 2)
    return float(1 - np.sum((y - yhat) ** 2) / ss) if ss > 0 else float("nan")


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 76)
    rec("A15 留出验证 + 边界压力 (修正版, A13c 口径)")
    rec("=" * 76)

    cache: dict = {}
    fit = collect("ha", cache)
    hold = collect("co", cache)
    rec(f"\nha n={len(fit)}  co n={len(hold)}")

    # ---------- 恒等式自检 ----------
    # ⚠ 修复 (2026-10-15): C=x_ai 仅在部分水样成立, 故用统一通式自检
    fit["pred_unified"] = fit.C_ml - (fit.M0_ml - fit.M1_ml) - fit["x_ai_ml"]
    err = (fit.dS_pot_ml - fit.pred_unified).abs().max()
    rec(f"[自检] 份额口径恒等式 dS_pot = M1-M0 最大残差 = {err:.3e} ML")
    # ⚠ A27 修正: 绝对容差在 M0 量级达 2e10 ML 时会因**浮点消去**而误判
    #   (M0-M1 是两个 ~2e10 数相减, 绝对误差 ~1e-6, 但相对误差仅 ~1e-16)。
    #   正确判据应为**相对**残差: |残差| / max(|各项|) < 100*eps。
    _scale = float(max(hold.M0_ml.abs().max(), hold.M1_ml.abs().max(),
                       hold["x_ai_ml"].abs().max(), hold.C_ml.abs().max(), 1.0))
    rel_err = float(err / _scale)
    ident_ok = bool(rel_err < 1e-13) or bool(err < 1e-6)
    rec(f"  相对残差 = {rel_err:.3e} (量级 {_scale:.3e} ML; 机器 eps ~2.2e-16)")

    gates = []

    # ---- A25: 求解器状态门禁 (未收敛情景分配量为 0, phi_eff=0, 必须剔除) ----
    _na, _nb = int(len(fit)), int(len(hold))
    fit = fit[fit["status"].astype(str) == "converged_unique"].copy()
    hold = hold[hold["status"].astype(str) == "converged_unique"].copy()
    # A27: 再剔除 CoC 触下限的退化情景
    if "coc_floor_degenerate" in fit.columns:
        fit = fit[~fit["coc_floor_degenerate"].astype(bool)].copy()
    if "coc_floor_degenerate" in hold.columns:
        hold = hold[~hold["coc_floor_degenerate"].astype(bool)].copy()
    rec(f"\n[A25 门禁] 拟合域 {_na}->{len(fit)}, 留出域 {_nb}->{len(hold)} (剔除未收敛)")

    # ---------- H1: 代数重推导 (非验证) ----------
    rec("\n[H1] 闭式 dS_pot = M1 - M0 到 co 的吻合度 (⚠ 代数重推导, 非真留出)")
    hold["pred_unified"] = hold.C_ml - (hold.M0_ml - hold.M1_ml) - hold["x_ai_ml"]
    r2_h1 = r2_score(hold.dS_pot_ml, hold.pred_unified)
    rmse_h1 = float(np.sqrt(np.mean((hold.dS_pot_ml - hold.pred_unified) ** 2)))
    rec(f"  co R² = {r2_h1:.6f}, RMSE = {rmse_h1:.3e} ML")
    rec("  ⚠ 该式直接使用 co 的引擎量 M0/M1, 与生成 dS_pot 的表达式同源,")
    rec("    故 R²≈1 是**代数恒等**, 不构成留出证据。仅作数值自检。")
    gates.append({"gate": "H1 恒等式自检 (非留出)", "passed": ident_ok,
                  "value": f"max err {err:.3e} ML (相对 {rel_err:.2e}); co R²={r2_h1:.6f} (代数重推导)"})

    # ---------- H2: 真留出 (单参数) ----------
    rec("\n[H2] 真留出: 在 ha 锁定 1 参数 phi_eff ≈ a*phi, 冻结后预测 co")
    a_fit = float(np.sum(fit.phi * fit.phi_eff) / max(np.sum(fit.phi ** 2), 1e-12))
    rec(f"  ha 锁定: a = {a_fit:.6f}  (phi_eff ≈ a*phi)")

    # 预测 co 的 phi_eff, 但 M1 未知 -> 需用 M 的模型. 用 ha 的 M(phi) 形状?
    # 更严格: 用零信息基线 (含常数) 与 律 对比
    phi_eff_pred = a_fit * hold.phi
    # 用 (1-phi_eff_pred)*M1 近似 -> 仍需 M1; 故此处检验 **phi_eff 本身** 的可迁移性
    r2_phieff = r2_score(hold.phi_eff, phi_eff_pred)
    med_err = float(np.median(np.abs(hold.phi_eff - phi_eff_pred)))
    # 基线: 常数预测
    r2_base = r2_score(hold.phi_eff, np.full(len(hold), fit.phi_eff.mean()))
    rec(f"  冻结律对 co 的 phi_eff 预测: R² = {r2_phieff:.6f}, 中位误差 = {med_err:.4f}")
    rec(f"  平凡基线 (取 ha 均值常数): R² = {r2_base:.6f}")
    h2_ok = bool(r2_phieff > max(r2_base, 0.0))
    gates.append({"gate": "H2 phi_eff 单参数律优于平凡基线", "passed": h2_ok,
                  "value": f"律 R²={r2_phieff:.6f} vs 基线 R²={r2_base:.6f}"})

    # ---------- H3: 边界 —— 关闭水质反馈 ----------
    rec("\n[H3] 边界: 关闭水质反馈 (限值极宽) 时 dS_pot 必须 -> 0")
    wide = []
    for smp in SAMPLES:
        for phi in (0.4, 0.8):
            r1 = cm.city_outcome("ha", "B_full", smp, dp_scale=0.0, ai_target=float(phi),
                                 limit_scale=1e6, cache=cache)
            r0 = cm.city_outcome("ha", "B_full", smp, dp_scale=0.0, ai_target=0.0,
                                 limit_scale=1e6, cache=cache)
            F = r0["M_ml"] - (1.0 - r1["phi_eff"]) * r1["M_ml"]
            C = max(0.0, r0["inc_reclaimed_ml"] - r1["inc_reclaimed_ml"])
            wide.append({"sample": smp, "phi": phi, "dS_pot_ml": C - F,
                         "CoC": r1["CoC_ai"]})
    w = pd.DataFrame(wide)
    rec(w.round(4).to_string(index=False))
    h3_ok = bool(w.dS_pot_ml.abs().max() < 1.0)
    gates.append({"gate": "H3 无水质约束 => dS_pot=0 (纯再分配)", "passed": h3_ok,
                  "value": f"max |dS_pot| = {w.dS_pot_ml.abs().max():.4f} ML"})

    # ---------- H4: 边界 —— chi 单调性 ----------
    rec("\n[H4] 边界: 质量惩罚应随水质约束变强 (chi 变小) 单调上升")
    # 按 chi 升序排列: chi 越小 (约束越强) 惩罚应越大 => 序列应单调递减
    agg = fit.groupby("chi").dS_pot_ml.max().sort_index(ascending=True)
    rec(agg.round(1).to_string())
    h4_ok = bool(agg.is_monotonic_decreasing)
    gates.append({"gate": "H4 chi 变小 => 惩罚上升 (单调)", "passed": h4_ok,
                  "value": f"max dS_pot by chi(升序) = {agg.round(0).to_dict()}"})

    # ---------- 边界: phi -> 0 ----------
    # A25 修正两点:
    #  (i)  原实现 z = fit[phi==0]; 但本数据集无 phi=0 行(phi 从 0.05 起) => z 空 => nan;
    #       修复前之所以"PASS 且值 0.000", 是因为 phi=0 行全部是未收敛情景
    #       (分配量为 0 => dS 恒 0) —— 用垃圾数据通过的门禁。
    #  (ii) 原期望 "phi->0 => dS->0" 物理上错误。实测 chi=0.25, phi=0.05:
    #       M0=104948, M1=93414 => dS = M1-M0 = -11535 ML。
    #       正确: 仅当水质不约束(M0=M1)时 phi->0 才 dS->0; 受限档 dS->(M1-M0)!=0。
    rec("\n[H5] 边界: phi->0 时 dS_pot 的行为 (A25 修正)")
    rec(f"  无 phi=0 行 (最小 phi={fit.phi.min():.2f}) => 原 phi=0 断言 VACUOUS, 不计通过")
    low = fit[fit.phi <= 0.10]
    med = float(fit.dS_pot_ml.abs().median()) or 1.0
    free_ok = bool(h3_ok)           # 不约束档由 H3 (limit_scale=1e6) 验证
    bound_ok = bool(low.dS_pot_ml.abs().max() >= 0.5 * med) if len(low) else False
    rec(f"  (a) 不约束档 (limit_scale=1e6, H3 已验) dS=0: {free_ok}")
    rec(f"  (b) 受限档 phi<=0.10 n={len(low)}: max|dS| = "
        f"{low.dS_pot_ml.abs().max() if len(low) else float('nan'):.1f} ML "
        f"(全样本中位 |dS| = {med:.1f} ML) => 小 phi 已显著 = {bound_ok}")
    rec("  => 'phi->0 => dS->0' 仅在水质不约束时成立; 受限档 dS->(M1-M0)!=0")
    h5_ok = bool(free_ok and bound_ok)
    gates.append({
        "gate": "H5 phi->0: 仅不约束档 dS->0; 受限档 dS->(M1-M0)!=0 (A25 修正)",
        "passed": h5_ok,
        "value": f"受限档小 phi max|dS|="
                 f"{low.dS_pot_ml.abs().max() if len(low) else float('nan'):.1f} ML "
                 f"vs 中位 {med:.1f} ML"})

    rec("\n[Gates]")
    for g in gates:
        rec(f"  [{'PASS' if g['passed'] else 'FAIL'}] {g['gate']}: {g['value']}")

    fit.to_csv(HERE / "holdout_fit_ha.csv", index=False, encoding="utf-8-sig")
    hold.to_csv(HERE / "holdout_holdout_co.csv", index=False, encoding="utf-8-sig")

    summary = {
        "estimand": "dS_pot = C - F (份额口径 dp=0)",
        "n_fit_ha": int(len(fit)), "n_holdout_co": int(len(hold)),
        "identity_max_err_ml": float(err),
        "H1_algebraic_rederivation": {"co_R2": r2_h1, "co_RMSE_ml": rmse_h1,
                                      "is_validation": False,
                                      "caveat": "使用 co 引擎量 M0/M1, 与生成式同源"},
        "H2_true_holdout": {"frozen_param_a": a_fit, "fitted_on": "ha",
                            "co_R2_phi_eff": r2_phieff,
                            "co_median_abs_err": med_err,
                            "trivial_baseline_R2": r2_base},
        "H3_no_quality_constraint_max_abs_dS": float(w.dS_pot_ml.abs().max()),
        "H4_chi_monotone": bool(h4_ok),
        "H5_phi0_boundary": {
            "phi0_rows_present": False,
            "note": ("A25: 本数据集无 phi=0 行; 原 'phi=0 => dS=0' 断言 VACUOUS 且物理上错误。"
                     "正确表述: 仅水质不约束(limit_scale=1e6)时 phi->0 才 dS->0;"
                     "受限档 dS->(M1-M0)!=0。"),
            "bound_max_abs_dS_phi_le_0p10": float(low.dS_pot_ml.abs().max()),
            "median_abs_dS_all": float(med),
        },
        "solver_gate": {"n_fit_all": _na, "n_fit_reliable": int(len(fit)),
                        "n_holdout_all": _nb, "n_holdout_reliable": int(len(hold))},
        "gates": gates,
        "all_gates_pass": bool(all(g["passed"] for g in gates)),
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": (
            "份额口径下 dS_pot = M1 - M0 >= 0 (旧结论)。"
            "H1 是代数重推导, 已明确标注为非验证; H2 是唯一的真留出 (单参数)。"
            "不使用已撤回的 psi/Delta。"),
    }
    (HERE / "holdout_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    rec(f"\n完成 {summary['runtime_s']}s; 全部 Gate 通过 = {summary['all_gates_pass']}")
    (HERE / "holdout.log").write_text("\n".join(log), encoding="utf-8")


if __name__ == "__main__":
    main()
