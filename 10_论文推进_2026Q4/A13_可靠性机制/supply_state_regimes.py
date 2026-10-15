"""A17 / E1: 三供给状态反例检验 (GPT 意见2 §四、§十 E1).

【为什么必须做】
GPT 指出并已由 Lead 实测确认: 现有模型把"固定池"与"必然挤占"绑定得过于紧密。
真实的再生水供给有三种物理上不同的状态:

    A 短缺 (shortage):  可交付再生水 < 既有用户需求  -> 必然挤占
    B 充分占用 (binding): 池恰好被既有用户用满        -> 临界
    C 存在余量 (surplus): 池 > 既有用户需求, 有闲置余量 -> AI 可用余量, 不挤占

现有模型的 pool_scale 扫描实际上混合了 A/B/C 三态, 却未显式区分。
本脚本用**引擎原生量**显式定义三态并检验:

  R1 在 surplus 态, dS_pot 的符号是否与 shortage 态相同?
  R2 三态的临界边界能否用外生量预测?
  R3 "固定池 => 净收益不可能为正" 是否只在 A 态成立?

【口径】
沿用 A13c 的排放—索取平衡 (不用已撤回的 psi/Delta):
    F = M0 - (1-phi_eff)*M1                    AI 释放的自来水
    C = inc_recl(B2) - inc_recl(B1)            既有用户须补回量 (同情景 B2 基准)
    dS_pot = C - F

【三态的引擎原生定义】
    elig = 既有用户可回用需求 (reuse_elig_ml)
    pool = 名义可交付再生水 (P0 * pool_scale)
    surplus_state = "surplus" if pool > elig else ("binding" if |pool-elig|<=tol else "shortage")
    另由引擎实际分配确认: inc_recl(B2) 是否达到其 max_reclaimed (gap)
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
DOMS = ("ha", "co")


def elig_of(dom: str) -> float:
    """既有用户可回用需求 = 已交付 + 缺口 = P0 + gap.

    引擎定义 (A7/T2_joint_quality_allocation.py:97-102):
        p0   = reuse_delivered_ml
        elig = demand_industrial + demand_municipal_misc
        gap  = max(0, elig - p0)
    city_model.BASELINES 只暴露 P0/gap, 故此处反推 elig。
    """
    bl = cm.BASELINES[dom]
    return bl["P0"] + bl["gap"]


def classify(elig: float, pool: float, tol_frac: float = 0.02) -> str:
    """三态判定 (相对容差)."""
    rel = (pool - elig) / max(elig, 1e-9)
    if rel > tol_frac:
        return "surplus"
    if rel < -tol_frac:
        return "shortage"
    return "binding"


COC_DESIGN_REF = 5.0   # 引擎默认设计 CoC (见 city_model.COC_DESIGN_DEFAULT)


def run_case(dom: str, sample: str, pool_scale: float, phi: float, *,
             chi: float = 0.5, cache: dict) -> dict:
    """求 B1 与 B2, 返回排放—索取平衡量与三态标签.

    ⚠ limit_scale 语义 (2026-10-14 实测澄清, 重要):
        `limit_scale` 是**水质限值的整体缩放因子**, 不是 chi = CoC_lim/CoC_design。
        实测 (ha, phi=0.4):
            limit_scale = 1e6  -> CoC = 5.0000 (= 设计值, **真正不约束**)
            limit_scale = 5.0  -> CoC = 5.0000 (不约束)
            limit_scale = 1.0  -> CoC = 4.6034 (**仍然约束**)
            limit_scale = 0.98 -> CoC = 4.5118  (≈ GSA 实机加药上界 4.91/5.0)
            limit_scale = 0.5  -> CoC = 2.3165  (≈ PHREEQC 无加药 2.52/5.0)
            limit_scale = 0.25 -> CoC = 1.1952  (外推压力档, 无实测支撑)
        故本脚本用 `water_quality_free=True` (limit_scale=1e6) 表示"不约束"极限,
        而把 limit_scale ∈ {0.98, 0.50} 作为**有实测/文献支撑**的档位,
        limit_scale=0.25 仅作外推压力档 (extrapolated=True)。

    chi 档位 (Lead 裁定 2026-10-14, 依据 A19_水化学包络 CoC ∈ [2.1, 4.9]):
        1.00  = 水质不约束 (极限情形, dS_pot 应恰好为 0) —— 用 limit_scale=1e6 实现
        0.98  = GSA/NREL 2023 实机加药运行上界  <-- 有实测支撑
        0.50  = PHREEQC 无加药 25C 与 GB/T 50050-2017 基准  <-- 有实测支撑
        0.25  = GB/T 19923-2024 补充水 strict 档, **外推压力档, 无实测支撑**
    """
    bl = cm.BASELINES[dom]
    elig = elig_of(dom)
    pool = bl["P0"] * float(pool_scale)

    r1 = cm.city_outcome(dom, "B_full", sample, pool_scale=pool_scale,
                         gap_scale=1.0, dp_scale=0.0, ai_target=float(phi),
                         limit_scale=chi, cache=cache)
    r0 = cm.city_outcome(dom, "B_full", sample, pool_scale=pool_scale,
                         gap_scale=1.0, dp_scale=0.0, ai_target=0.0,
                         limit_scale=chi, cache=cache)

    M1, M0 = r1["M_ml"], r0["M_ml"]
    F = M0 - (1.0 - r1["phi_eff"]) * M1
    C = max(0.0, r0["inc_reclaimed_ml"] - r1["inc_reclaimed_ml"])
    dS = C - F

    # 引擎实际分配确认: 既有用户在 B2 是否拿满其需求?
    inc_demand = bl["gap"]              # 既有用户最大可主张量
    inc_B2 = r0["inc_reclaimed_ml"]
    inc_B1 = r1["inc_reclaimed_ml"]
    inc_sat = bool(inc_B2 >= inc_demand - 1e-6)   # 既有用户已满足
    unused = max(0.0, pool - inc_B2 - r0["x_ai_ml"])   # B2 下闲置的再生水

    return {
        "domain": dom, "sample": sample,
        "pool_scale": float(pool_scale), "phi": float(phi), "chi": float(chi),
        # ---- A26 权威语义列 (见 A26_语义统一/CHI_SEMANTICS.md) ----
        # 注: 本脚本的 `chi` **就是** limit_scale; 此处显式并列以便跨表安全。
        "limit_scale": float(chi),
        "chi_strictness": float(r1["CoC_ai"]) / float(COC_DESIGN_REF),
        "quality_binding": bool(float(r1["CoC_ai"]) < COC_DESIGN_REF * (1.0 - 1e-9)),
        # ---- A27 退化检测 ----
        # 引擎 CoC 下限为 1.000001。当限值严于/等于水源浓度时 CoC 被钉在下限,
        # 补水退化为天文数字 (实测可达 2e10 ML), 该情景**无物理意义**。
        "coc_floor_degenerate": bool(float(r1["CoC_ai"]) <= 1.000001 + 1e-9),
        "pool_ml": pool, "elig_ml": elig, "inc_demand_ml": inc_demand,
        "state_by_pool": classify(elig, pool),
        # ⚠ 状态判定必须以【是否真的发生挤占】为准, 而不是"池是否有余量":
        #   B2 有闲置 ≠ B1 时 AI 从余量取水。若 B1 仍挤占 (C>0), 则实质是 shortage。
        "state_by_alloc": (
            "shortage" if (inc_B2 - inc_B1) > 1e-6
            else ("surplus" if inc_sat else "binding")),
        "inc_B2_ml": inc_B2, "inc_B1_ml": inc_B1, "inc_saturated": inc_sat,
        "displaced_ml": inc_B2 - inc_B1,
        "unused_B2_ml": unused,
        "x_ai_B1_ml": r1["x_ai_ml"], "x_ai_B2_ml": r0["x_ai_ml"],
        "M0_ml": M0, "M1_ml": M1, "phi_eff": r1["phi_eff"],
        "F_ml": F, "C_ml": C, "dS_pot_ml": dS,
        "dS_ident_ml": M1 - M0,
        "CoC_ai": r1["CoC_ai"],
        "status": r1["status"],
    }


def _reliable_stats(d) -> dict:
    """A25: 只统计求解器可靠(converged_unique)的情景, 并报告未收敛数。

    未收敛情景的分配量退化为 0, 但仍会产出 displaced/dS 等派生量, 必须剔除。
    """
    import pandas as _pd
    st = d["status"].astype(str) if "status" in d.columns else _pd.Series(["?"] * len(d))
    ok = d[st == "converged_unique"]
    # A27: 再剔除 CoC 触下限的退化情景 (补水可达 2e10 ML, 无物理意义)
    if "coc_floor_degenerate" in d.columns:
        _deg = ok["coc_floor_degenerate"].astype(bool)
        ok = ok[~_deg]
    def _n(df, mask):
        return int(mask.sum()) if len(df) else 0
    q_all = (d["M0_ml"] - d["M1_ml"]) / d["M1_ml"] if "M1_ml" in d.columns else None
    q_ok = (ok["M0_ml"] - ok["M1_ml"]) / ok["M1_ml"] if len(ok) and "M1_ml" in ok.columns else None
    return {
        "n_all": int(len(d)),
        "n_reliable": int(len(ok)),
        "n_excluded": int(len(d) - len(ok)),
        "excluded_share_pct": round((len(d) - len(ok)) / max(len(d), 1) * 100, 2),
        "status_counts": st.value_counts().to_dict(),
        "reliable_n_dS_neg": _n(ok, ok["dS_pot_ml"] < -1e-6),
        "reliable_n_dS_pos": _n(ok, ok["dS_pot_ml"] > 1e-6),
        "reliable_n_zero_disp": _n(ok, ok["displaced_ml"].abs() < 1e-6),
        "reliable_n_q_pos": int((q_ok > 1e-9).sum()) if q_ok is not None else None,
        "reliable_n_qpos_but_harmful": int(((q_ok > 1e-9) & (ok["dS_pot_ml"] > 1e-6)).sum())
        if q_ok is not None else None,
        "n_coc_floor_degenerate": int(d.get("coc_floor_degenerate",
                                             _pd.Series([False] * len(d))).sum()),
        "note": ("头条统计须以 reliable 子集为准; 未收敛情景的分配量为 0, 派生量不可用; "
                 "CoC 触下限(<=1.000001)的退化情景亦已剔除 (A27)。"),
    }


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 78)
    rec("A17 / E1: 三供给状态反例检验 (shortage / binding / surplus)")
    rec("=" * 78)

    cache: dict = {}
    # pool_scale 覆盖三态: elig/P0 ≈ 2.38 (ha) / 2.57 (co)
    POOL = (0.5, 1.0, 1.5, 2.0, 2.2, 2.4, 2.6, 3.0, 4.0)
    PHI = (0.2, 0.4, 0.6, 0.8)
    # 主扫描档位: (标签, 传给引擎的 limit_scale)
    #   "free" 用 1e6 才是真正不约束 (实测 CoC=5.0000)
    CHI_MAIN = (("free", 1e6), ("0.98", 0.98), ("0.50", 0.50))
    CHI_EXTRAP = ("0.25", 0.25)   # 外推压力档

    rows = []
    for dom in DOMS:
        for smp in SAMPLES:
            for ps in POOL:
                for phi in PHI:
                    # 主扫描: 有实测/文献支撑的档位
                    for label, ls in CHI_MAIN:
                        try:
                            r = run_case(dom, smp, ps, phi, chi=ls, cache=cache)
                            r["chi_label"] = label
                            r["extrapolated"] = False
                            rows.append(r)
                        except Exception as e:  # noqa: BLE001
                            rec(f"  ERROR {dom} {smp} ps={ps} phi={phi} "
                                f"chi={label}: {type(e).__name__}: {e}")
    # 外推档单独跑, 标记 extrapolated=True
    extra = []
    elabel, els = CHI_EXTRAP
    for dom in DOMS:
        for smp in SAMPLES:
            for ps in POOL:
                for phi in PHI:
                    try:
                        r = run_case(dom, smp, ps, phi, chi=els, cache=cache)
                        r["chi_label"] = elabel
                        r["extrapolated"] = True
                        extra.append(r)
                    except Exception:  # noqa: BLE001
                        pass
    d = pd.DataFrame(rows + extra)
    d.to_csv(HERE / "supply_state_regimes.csv", index=False, encoding="utf-8-sig")
    rec(f"\n完成 {len(d)} 情景 "
        f"(主扫描 chi_label∈{[c[0] for c in CHI_MAIN]}; 另含外推档 {elabel})")

    if len(d) == 0:
        raise SystemExit("全部失败")

    # ---------- 0. 恒等式自检 ----------
    err = (d["dS_pot_ml"] - d["dS_ident_ml"]).abs().max()
    rec(f"[自检1] 单口径恒等式 dS_pot = M1-M0 最大残差 = {err:.3e} ML "
        f"(仅在 A 态应成立)")

    # 统一通式自检: dS = displaced - (M0-M1) - x_ai
    d["pred_unified"] = d["displaced_ml"] - (d["M0_ml"] - d["M1_ml"]) - d["x_ai_B1_ml"]
    err_u = (d["dS_pot_ml"] - d["pred_unified"]).abs().max()
    rec(f"[自检2] ★ 统一通式 dS = 挤占位移 - 质量惩罚 - x_ai "
        f"最大残差 = {err_u:.3e} ML  (应 ~1e-11)")

    # 两分支退化自检
    a_mask = (d["displaced_ml"] - d["x_ai_B1_ml"]).abs() < 1.0
    c_mask = d["displaced_ml"].abs() < 1e-6
    eA = ((d.loc[a_mask, "dS_pot_ml"] - (d.loc[a_mask, "M1_ml"]
                                         - d.loc[a_mask, "M0_ml"])).abs().max()
          if a_mask.any() else float("nan"))
    eC = ((d.loc[c_mask, "dS_pot_ml"]
           - (-(d.loc[c_mask, "M0_ml"] - d.loc[c_mask, "M1_ml"])
              - d.loc[c_mask, "x_ai_B1_ml"])).abs().max()
          if c_mask.any() else float("nan"))
    rec(f"[自检3] A 态(a 池用尽, n={int(a_mask.sum())}) 退化残差 = {eA:.3e} ML")
    rec(f"[自检4] C 态(c 未挤占, n={int(c_mask.sum())}) 退化残差 = {eC:.3e} ML")

    # ---------- 1. 三态下的 dS_pot 符号 ----------
    rec("\n[1] ★ 按【分配实际状态】分组的 dS_pot 符号")
    g = d.groupby("state_by_alloc").agg(
        n=("dS_pot_ml", "size"),
        dS_min=("dS_pot_ml", "min"), dS_max=("dS_pot_ml", "max"),
        dS_mean=("dS_pot_ml", "mean"),
        n_neg=("dS_pot_ml", lambda s: int((s < -1e-6).sum())),
        n_pos=("dS_pot_ml", lambda s: int((s > 1e-6).sum())),
        unused_mean=("unused_B2_ml", "mean"))
    rec(g.round(1).to_string())

    # ---------- 1b. chi 极限: 水质不约束时 dS_pot 应恰好为 0 ----------
    rec("\n[1b] ★ chi 极限检验 (水质不约束 => 纯再分配)")
    label_col = "chi_label" if "chi_label" in d.columns else "chi"
    for lab in [c[0] for c in CHI_MAIN] + [CHI_EXTRAP[0]]:
        s = d[d[label_col].astype(str) == lab]
        if not len(s):
            continue
        tag = " (外推压力档, 不代表实测运行)" if lab == CHI_EXTRAP[0] else ""
        rec(f"  limit_scale={lab:>5}: n={len(s):4d}  "
            f"max|dS_pot|={s['dS_pot_ml'].abs().max():9.4f} ML  "
            f"中位={s['dS_pot_ml'].median():9.1f}  "
            f"范围[{s['dS_pot_ml'].min():.0f}, {s['dS_pot_ml'].max():.0f}]{tag}")
    free = d[d[label_col].astype(str) == "free"]
    if len(free):
        rec(f"  >>> 'free' (limit_scale=1e6, CoC=设计值) 的 max|dS_pot| = "
            f"{free['dS_pot_ml'].abs().max():.4f} ML  —— 应为 0 (纯再分配)")

    # ---------- 2. 三态对比 (核心反例) ----------
    rec("\n[2] ★ 核心反例: 同样 AI 负荷, 余量态 vs 短缺态")
    for dom in DOMS:
        sub = d[d["domain"] == dom]
        for phi in (0.4, 0.8):
            s = sub[np.isclose(sub["phi"], phi)]
            sh = s[s.state_by_alloc == "shortage"]["dS_pot_ml"]
            su = s[s.state_by_alloc == "surplus"]["dS_pot_ml"]
            if len(sh) and len(su):
                rec(f"  D-{dom.upper()} phi={phi}: shortage dS∈[{sh.min():.0f},{sh.max():.0f}] "
                    f"| surplus dS∈[{su.min():.0f},{su.max():.0f}]")

    # 关键: surplus 态是否存在 dS_pot < 0
    su = d[d.state_by_alloc == "surplus"]
    sh = d[d.state_by_alloc == "shortage"]
    rec(f"\n  surplus 态: n={len(su)}, dS_pot<0 的个数 = "
        f"{int((su['dS_pot_ml'] < -1e-6).sum()) if len(su) else 'NA'}")
    rec(f"  shortage 态: n={len(sh)}, dS_pot<0 的个数 = "
        f"{int((sh['dS_pot_ml'] < -1e-6).sum()) if len(sh) else 'NA'}")

    # ---------- 3. 是否真的"不挤占" ----------
    rec("\n[3] surplus 态下 AI 是否真的不挤占既有用户?")
    if len(su):
        rec(f"  既有用户 B2 拿满其需求的比例 = {su['inc_saturated'].mean():.3f}")
        rec(f"  B2 下闲置再生水 均值 = {su['unused_B2_ml'].mean():.0f} ML")
        rec(f"  C (既有用户须补回) 均值 = {su['C_ml'].mean():.1f} ML"
            f"  -> 应为 ~0 (未挤占)")
        rec(f"  F (AI 释放自来水) 均值 = {su['F_ml'].mean():.0f} ML")
        rec(f"  => dS_pot 均值 = {su['dS_pot_ml'].mean():.1f} ML")

    # ---------- 4. 临界边界可预测性 (A25 修正) ----------
    # A25 审计发现: 旧值 elig/P0 = (P0+gap)/P0 与实测零挤占仅 ~0.78 吻合, 不是 surplus 门槛。
    # 正确判据: 零挤占 ⟺ pool >= gap + x_ai_B1 ⇒ pool_scale* = gap/P0 + x_ai_B1/P0。
    rec("\n[4] 状态边界是否由外生量决定 (A25 已修正)")
    thr_true_all = {}
    for dom in DOMS:
        bl = cm.BASELINES[dom]
        P0, gap = bl["P0"], bl["gap"]
        old_crit = elig_of(dom) / P0
        s = d[d["domain"] == dom].copy()
        s["thr_true"] = gap / P0 + pd.to_numeric(s["x_ai_B1_ml"], errors="coerce") / P0
        z = s[pd.to_numeric(s["displaced_ml"], errors="coerce").abs() < 1e-6]
        pred_true = s["pool_scale"] >= s["thr_true"] - 1e-6
        zero = pd.to_numeric(s["displaced_ml"], errors="coerce").abs() < 1e-6
        acc_true = float((pred_true == zero).mean())
        pred_old = s["pool_scale"] >= old_crit - 1e-6
        acc_old = float((pred_old == zero).mean())
        thr_true_all[dom] = {
            "old_formula_elig_over_P0": float(old_crit),
            "old_accuracy": acc_old,
            "true_threshold_min": float(s["thr_true"].min()),
            "true_threshold_median": float(s["thr_true"].median()),
            "true_threshold_max": float(s["thr_true"].max()),
            "true_criterion_accuracy": acc_true,
            "observed_first_surplus_pool_scale": float(z["pool_scale"].min()) if len(z) else None,
        }
        rec(f"  D-{dom.upper()}:")
        rec(f"    旧公式 elig/P0 = {old_crit:.3f}  (与实测零挤占吻合率 {acc_old:.3f})  <- 不是门槛")
        rec(f"    真实门槛 gap/P0 + x_ai/P0 ∈ [{s['thr_true'].min():.3f}, "
            f"{s['thr_true'].max():.3f}], 中位 {s['thr_true'].median():.3f}")
        rec(f"    真实判据吻合率 = {acc_true:.3f}")
        rec(f"    实测首个 surplus 的 pool_scale = "
            f"{float(z['pool_scale'].min()) if len(z) else 'NA'}")

    summary = {
        "n_scenarios": int(len(d)),
        "identity_max_err_ml": float(err),
        "unified_identity_max_err_ml": float(err_u),
        "branch_A_deg_residual_ml": float(eA),
        "branch_C_deg_residual_ml": float(eC),
        "n_branch_A": int(a_mask.sum()),
        "n_branch_C": int(c_mask.sum()),
        "by_state": {k: {"n": int(v["n"]), "dS_min": float(v["dS_min"]),
                         "dS_max": float(v["dS_max"]), "dS_mean": float(v["dS_mean"]),
                         "n_negative": int(v["n_neg"]), "n_positive": int(v["n_pos"]),
                         "unused_mean_ml": float(v["unused_mean"])}
                     for k, v in g.iterrows()},
        "surplus_n_negative": int((su["dS_pot_ml"] < -1e-6).sum()) if len(su) else None,
        "shortage_n_negative": int((sh["dS_pot_ml"] < -1e-6).sum()) if len(sh) else None,
        "surplus_C_mean_ml": float(su["C_ml"].mean()) if len(su) else None,
        "surplus_F_mean_ml": float(su["F_ml"].mean()) if len(su) else None,
        "surplus_dS_mean_ml": float(su["dS_pot_ml"].mean()) if len(su) else None,
        # A25 修正: 旧值保留但明确标注为"非门槛"; 真实门槛见 threshold_audit.
        "critical_pool_scale_OLD_NOT_A_THRESHOLD": {
            dm: float(elig_of(dm) / cm.BASELINES[dm]["P0"]) for dm in DOMS},
        "surplus_threshold_true": thr_true_all,
        "reliable_subset": _reliable_stats(d),
        "semantics": {
            "chi_meaning": ("本产物的 `chi` **就是** limit_scale (限值整体缩放因子), "
                            "**不是** chi=CoC_lim/CoC_design。权威定义见 A26_语义统一/CHI_SEMANTICS.md。"),
            "authoritative_columns": ["limit_scale", "chi_strictness", "quality_binding"],
            "chi_strictness_note": "由引擎实测 CoC 反解, 仅具相对意义(依赖占位限值)。",
        },
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": (
            "三态由引擎实际分配判别 (既有用户是否拿满 + B2 是否闲置), 不用 pool 名义比较。"
            "口径为 A13c 排放—索取平衡 (dS_pot=C-F), 不使用已撤回的 psi/Delta。"
            "模型内结论, 非观测频率。"),
    }
    (HERE / "supply_state_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    rec(f"\n完成 {summary['runtime_s']}s")
    (HERE / "a17_repro_log.txt").write_text("\n".join(log), encoding="utf-8")


if __name__ == "__main__":
    main()
