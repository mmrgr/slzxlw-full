"""T1 — 三规则内生求解 + 传递恒等式的规则不变性检验 (go/no-go)

预注册: ../A0_预注册/preregistration.md
纪律:
  * 分配规则**只调用** aiuwm.reclaimed_allocation 的已评审函数, 不重写规则逻辑
  * 只读加载冻结曲线 stage1_cooling_curve.csv; 不写回仓库
  * 可选: 用主引擎在少数 phi 点上交叉核对 AI 实际取用的再生水量

待检验假设 (来自 v1 §11):
  H-rule: 城市级节水 S_city 的符号与大小依赖分配规则。
备择 (本轮要证的):
  H-inv : 在**固定池、无新增供给**时, S_city 与分配规则无关, 只由质量反馈决定:
          S_city = M(0) - M(phi_act) <= 0。规则只能改变 phi_act, 不能创造收益。
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / "07_代码_AI-UWM引擎" / "aiuwm_src"
sys.path.insert(0, str(REPO / "src"))

from aiuwm.reclaimed_allocation import (  # noqa: E402
    AllocationRequest,
    allocate_dedicated_incremental,
    allocate_shared_surplus,
)

R2 = REPO / "examples" / "cawcc_r2"
CURVE = HERE.parent / "A2_规则实验" / "stage1_cooling_curve.csv"
PREREG = HERE.parent / "A0_预注册" / "preregistration.md"

CAP_MW = 1000.0
REUSE_FRACTION = {"ha": 0.16, "co": 0.15}      # WWTW.central_reuse_fraction
# 中央回用处理能力不在此硬编码: T1b 已改为从引擎
# examples/cawcc_r2/{dom}/project.json 的 CENTRAL_REUSE.treatment_capacity 读取,
# 避免与 A2/endogenous_gamma.REUSE_PLANT_ML_DAY 出现第二处口径 (清理轮 2026-10-14)。
THETAS = [0.0, 0.1, 0.25, 0.5, 0.85, 1.0]      # 池扩容比例 dP = theta * P
RULES = ("engine_native", "pro_rata", "incumbent_first", "dedicated")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def load_curve(domain: str) -> pd.DataFrame:
    d = pd.read_csv(CURVE)
    d = d[d.domain == domain].sort_values("phi_actual").reset_index(drop=True)
    return d


def _ai_incumbent_claim(phi: float, m: float, pool: float) -> float:
    return min(max(phi, 0.0) * m, pool)


def allocate(rule: str, phi_req: float, m: float, pool: float, d_pool: float):
    """返回 (AI_alloc, INC_alloc_total)。全部通过已评审模块求解。"""
    ai_cap = max(0.0, phi_req) * m
    if ai_cap <= 0.0:
        return 0.0, pool
    if rule == "engine_native":
        # 现状基准: AI 优先占用存量池。用 shared 模块的 incumbent 通道表达
        # "两者都是受保护claim且合计恰好等于池量", 从而得到 AI 先取、INC 取余。
        ai_claim = _ai_incumbent_claim(phi_req, m, pool)
        inc_claim = max(0.0, pool - ai_claim)
        res = allocate_shared_surplus(
            "native", pool,
            [AllocationRequest("AI", demand_ml=ai_cap, incumbent_reclaimed_ml=ai_claim,
                               potable_baseline_ml=m),
             AllocationRequest("INC", demand_ml=pool, incumbent_reclaimed_ml=inc_claim,
                               potable_baseline_ml=pool)],
        )
        inc = sum(a.incumbent_allocated_ml for a in res.allocations if a.consumer_id == "INC")
        return min(ai_cap, pool), inc
    if rule == "pro_rata":
        # 无优先级: 两者都以"增量"身份竞争同一个固定池 → 模块内 pro-rata。
        res = allocate_shared_surplus(
            "prorata", pool,
            [AllocationRequest("AI", demand_ml=ai_cap, potable_baseline_ml=m),
             AllocationRequest("INC", demand_ml=pool, potable_baseline_ml=pool)],
        )
        ai = sum(a.total_allocated_ml for a in res.allocations if a.consumer_id == "AI")
        inc = sum(a.total_allocated_ml for a in res.allocations if a.consumer_id == "INC")
        return ai, inc
    if rule == "incumbent_first":
        # 既有用户全额受保护; AI 只能吃扩容增量。
        res = allocate_shared_surplus(
            "incfirst", pool + d_pool,
            [AllocationRequest("AI", demand_ml=ai_cap, potable_baseline_ml=m),
             AllocationRequest("INC", demand_ml=pool, incumbent_reclaimed_ml=pool,
                               potable_baseline_ml=pool)],
        )
        ai = sum(a.total_allocated_ml for a in res.allocations if a.consumer_id == "AI")
        inc = sum(a.incumbent_allocated_ml for a in res.allocations if a.consumer_id == "INC")
        return ai, inc
    if rule == "dedicated":
        # 专用新增增量: 不触碰既有池。模块刻意把 incumbent_allocations 置零
        # (因为专用供给不从共享池支取), 因此既有池保持原样 = pool。
        res = allocate_dedicated_incremental(
            "dedicated", d_pool,
            [AllocationRequest("AI", demand_ml=ai_cap, dedicated_supply_ml=min(ai_cap, d_pool),
                               potable_baseline_ml=m),
             AllocationRequest("INC", demand_ml=pool, incumbent_reclaimed_ml=pool,
                               potable_baseline_ml=pool)],
        )
        ai = sum(a.incremental_allocated_ml for a in res.allocations if a.consumer_id == "AI")
        # 既有用户池未被触碰 → 其再生水获得量仍为 pool (由模块 preserved 字段保证)
        inc = min(pool, res.preserved_incumbent_reclaimed_ml)
        return ai, inc
    raise ValueError(rule)


def fixed_point(rule, phi_req, m_of_phi, p_of_phi, theta, iters=80, tol=1e-12):
    """解 phi_act = AI_alloc / M(phi_act)。"""
    m0 = float(m_of_phi(0.0))
    phi = min(phi_req, 0.95)
    for _ in range(iters):
        m = float(m_of_phi(phi))
        p = float(p_of_phi(phi))
        ai, inc = allocate(rule, phi, m, p, theta * p)
        phi_new = (ai / m) if m > 0 else 0.0
        if abs(phi_new - phi) < tol:
            phi = phi_new
            break
        phi = 0.5 * (phi + phi_new)
    m = float(m_of_phi(phi))
    p = float(p_of_phi(phi))
    ai, inc = allocate(rule, phi, m, p, theta * p)
    phi = (ai / m) if m > 0 else 0.0
    s_ai = m0 - (m - ai)
    displacement = p - inc                      # 既有用户被迫补的自来水
    s_city = s_ai - displacement
    s_city_identity = m0 - m                    # S_city = M(0) - M(phi) 的预测值
    return {
        "phi_requested": phi_req, "phi_actual": phi, "theta": theta,
        "M_ml": m, "M0_ml": m0, "pool_ml": p, "d_pool_ml": theta * p,
        "AI_reclaimed_ml": ai, "INC_reclaimed_ml": inc,
        "S_AI_ml": s_ai, "displacement_ml": displacement,
        "S_city_ml": s_city, "S_city_identity_ml": s_city_identity,
        # 恒等式 S_city = M(0) - M(phi_act) 仅在"零净新增供给"时成立。
        # theta>0 时正确形式为 S_city = M(0) - M + (AI_alloc - displacement)。
        "identity_applicable": bool(theta <= 0.0),
        "identity_residual_pct": (
            100.0 * abs(s_city - s_city_identity)
            / max(abs(s_ai), abs(s_city_identity), 1e-6 * m0)
            if theta <= 0.0 else np.nan
        ),
        "general_closure_ml": s_city - (m0 - m + (ai - displacement)),
        "gamma": (displacement / ai) if ai > 1e-9 else np.nan,
        "delta": (1.0 - displacement / ai) if ai > 1e-9 else np.nan,
        "eta_transfer": (s_city / s_ai) if s_ai > 1e-9 else np.nan,
    }


def verify_against_engine(domain: str, phis=(0.3, 0.8)) -> list[dict]:
    """用主引擎在少数 phi 点上核对 AI 实际再生水取用量与池量。"""
    from aiuwm.full_engine import FullAIUWMModel
    project = json.loads((R2 / domain / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / domain / "timeseries.csv")
    out = []
    for g in phis:
        t = copy.deepcopy(project)
        dc = t["components"]["AI_DC1"]
        dc["installed_it_capacity_mw"] = CAP_MW
        dc["cooling_storage_capacity_ml"] = 0.0
        dc["cooling_storage_ml"] = 0.0
        dc["initial_cooling_storage_ml"] = 0.0
        dc["water_sources"]["reclaimed"]["target_fraction"] = g
        dc["water_sources"]["potable"]["target_fraction"] = 1.0 - g
        # 引擎基线样板 (E-6): 与另外 4 处有意重复, 见 daily_model.daily_reuse_supply 的说明
        r = FullAIUWMModel(t, ts).run()
        d = r.data_center_daily
        ww = r.component_daily[r.component_daily.component_id == "WWTW1"]["treated_ml"].sum()
        m = float(d["external_withdrawal_ml"].sum())
        ai = float(d["reclaimed_water_ml"].sum())
        out.append({
            "domain": domain, "phi_requested": g,
            "engine_M_ml": m, "engine_AI_reclaimed_ml": ai,
            "engine_phi_actual": ai / m if m else np.nan,
            "engine_pool_ml": float(ww) * REUSE_FRACTION[domain],
        })
    return out


def main() -> int:
    print(f"[prereg] {PREREG.stat().st_size}B sha256={file_hash(PREREG)}")
    rows, checks = [], []
    for domain in ("ha", "co"):
        c = load_curve(domain)
        phi_grid = c["phi_actual"].to_numpy()
        m_grid = c["M_ml"].to_numpy()
        p_grid = c["wwtw_treated_ml"].to_numpy() * REUSE_FRACTION[domain]

        def m_of_phi(x, pg=phi_grid, mg=m_grid):
            return float(np.interp(x, pg, mg))

        def p_of_phi(x, pg=phi_grid, pg2=p_grid):
            return float(np.interp(x, pg, pg2))

        for rule in RULES:
            # engine_native / pro_rata 没有新增供给通道, 只跑 theta=0
            thetas = THETAS if rule in ("incumbent_first", "dedicated") else [0.0]
            for th in thetas:
                for phi_req in [round(i / 20, 3) for i in range(0, 19)]:
                    r = fixed_point(rule, phi_req, m_of_phi, p_of_phi, th)
                    r.update({"domain": domain, "rule": rule})
                    rows.append(r)
        checks += verify_against_engine(domain)

    df = pd.DataFrame(rows)
    df.to_csv(HERE / "T1_rule_identity.csv", index=False, encoding="utf-8-sig")

    # ---- 关键判定: F1 (A3 修正版) ----
    # 审计 A3: theta=0 时 incumbent_first / dedicated 两条规则下 AI 实得恒为 0
    #          (池已被既有用户占满 / 无专用增量), 其 S_city=0 属**平凡通过**。
    #          真判据必须在"AI 实际获得再生水"的情景上检验。
    no_exp = df[np.isclose(df.theta, 0.0)].copy()
    no_exp["ai_active"] = no_exp["AI_reclaimed_ml"] > 1e-9
    f1_max = no_exp.groupby(["domain", "rule"])["S_city_ml"].max().unstack()
    f1_max_active = (no_exp[no_exp.ai_active]
                     .groupby(["domain", "rule"])["S_city_ml"].max().unstack())
    n_active = no_exp.groupby(["domain", "rule"])["ai_active"].sum().unstack()
    # 检验 1: theta=0 时 S_city 是否对所有规则都等于 M(0)-M(phi_act)
    resid = df.loc[df.identity_applicable, "identity_residual_pct"].max()
    # 检验 2: 通用收支闭合 (机器精度级)
    gen_resid = df["general_closure_ml"].abs().max()
    # 检验 3: 跨模块一致性 — incumbent_first 与 dedicated 在相同 (domain,theta,phi) 下应完全一致
    a = df[df.rule == "incumbent_first"].set_index(["domain", "theta", "phi_requested"])["S_city_ml"]
    b = df[df.rule == "dedicated"].set_index(["domain", "theta", "phi_requested"])["S_city_ml"]
    cross = float((a - b).abs().max()) if len(a) and len(b) else np.nan

    print("\n===== F1 检验 (A3 修正): theta=0 (固定池, 无新增供给)")
    print("  [a] AI 实得 > 0 的情景数 (n_active) —— 0 表示该规则下 AI 根本未取到水:")
    print(n_active.to_string())
    print("  [b] 全部情景的最大 S_city (ML) —— 含平凡情形:")
    print(f1_max.round(2).to_string())
    print("  [c] 仅在 AI 实得 > 0 的情景上的最大 S_city (ML)  <== 真正判据:")
    print(f1_max_active.round(2).to_string())
    print(f"\n检验1 恒等式残差(theta=0, {int(df.identity_applicable.sum())} 情景): max = {resid:.3e} %")
    print(f"检验2 通用收支闭合(全部 {len(df)} 情景): max = {gen_resid:.3e} ML")
    print(f"检验3 跨模块一致性(incumbent_first vs dedicated): max|diff| = {cross:.3e} ML")

    print("\n===== 扩容后 (theta>0) 各规则最大 S_city (ML)")
    print(df[df.theta > 0].groupby(["domain", "rule"])["S_city_ml"].max().unstack().round(1).to_string())

    print("\n===== 引擎交叉核对")
    ck = pd.DataFrame(checks)
    for _, r in ck.iterrows():
        subset = df[(df.domain == r.domain) & (df.rule == "engine_native")
                    & np.isclose(df.phi_requested, r.phi_requested)]
        model_ai = subset["AI_reclaimed_ml"].iloc[0] if len(subset) else np.nan
        print(f"  {r.domain} phi_req={r.phi_requested}: 引擎 AI={r.engine_AI_reclaimed_ml:.0f} ML "
              f"| 模型 AI={model_ai:.0f} ML | 引擎池={r.engine_pool_ml:.0f} ML | "
              f"偏差={100*(model_ai-r.engine_AI_reclaimed_ml)/max(r.engine_AI_reclaimed_ml,1e-9):+.2f}%")

    def _flat(frame: pd.DataFrame) -> dict:
        return {f"{d}|{r}": float(v) for (d, r), v in frame.stack().items()}

    summary = {
        "prereg_sha256_16": file_hash(PREREG),
        "n_scenarios": int(len(df)),
        "identity_residual_max_pct_theta0": float(resid),
        "general_closure_max_abs_ml": float(gen_resid),
        "cross_module_max_abs_diff_ml": float(cross) if np.isfinite(cross) else None,
        "F1_no_expansion_max_S_city_ml_ALL": _flat(f1_max),
        "F1_no_expansion_max_S_city_ml_AI_ACTIVE": _flat(f1_max_active),
        "F1_n_active_scenarios": _flat(n_active),
        "F1_triggered": bool((f1_max_active > 1e-6 * df["pool_ml"].max()).any().any()),
        "F1_trivial_rules_note": (
            "audit A3: at theta=0 the incumbent_first and dedicated rules allocate ZERO "
            "reclaimed water to the AI (pool already fully claimed / no dedicated increment), "
            "so their S_city=0 is a trivial pass. Only rules where AI actually receives "
            "reclaimed water are informative."),
        "S_city_is_conditional": (
            "S_city = M0 - M(phi_act) <= 0 holds conditional on (i) rigid incumbent service "
            "and (ii) fixed total reclaimed supply; it is an accounting statement, not a "
            "physical law (audit D1)."),
        "max_S_city_with_expansion_ml": _flat(
            df[df.theta > 0].groupby(["domain", "rule"])["S_city_ml"].max().unstack()
        ),
        "engine_crosscheck": checks,
    }
    (HERE / "T1_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\n[F1] 触发={summary['F1_triggered']}  (False = 恒等式在固定池下成立, 无规则能创造收益)")
    print(f"[write] {HERE/'T1_rule_identity.csv'}  {HERE/'T1_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
