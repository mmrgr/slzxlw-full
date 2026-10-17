"""WP4-1: 在【完整物种】水样上用主口径算出城市级 dS_pot (任务 A).

======================================================================
【主估计量 —— 唯一口径, 来自 WP2 §2 (B1 − B2), 不得混入 B0】
======================================================================
    dS_pot = C - F = (inc_B2 - inc_B1) - (M0 - M1) - x_ai

其中 (与 A13/supply_state_regimes.py 的既有调用口径逐条一致):
    B1 = 有数据中心, **不用**再生水 (ai_target=0)   -> M0, inc_B1, CoC0
    B2 = 有数据中心, **使用**再生水 (ai_target=phi) -> M1, inc_B1.., CoC1, x_ai
    C  = inc_B2 - inc_B1   既有用户被挤占后须补回量 (挤占位移)
    F  = (M0 - M1) + x_ai  数据中心净索取 (质量惩罚 + 直接取水)

符号约定 (WP2 §2 纪律 2):
    dS_pot > 0  => 城市净取水【上升】(有害)
    dS_pot < 0  => 城市净取水【下降】(有益)

q 口径 (H2, A22/q_theory.py):
    q = (CoC1 - CoC0) / (CoC1 * (CoC0 - 1))
    物理含义: 水质导致的单位补水变化。q>0 <=> CoC1>CoC0 (再生水更干净)。

======================================================================
【本脚本做什么】
======================================================================
1. 权威读取 city_model.load_samples() 的水样表 (不自造任何化学数值);
2. 只取【完整物种】水样 (IEUA / LADWP) 进主口径 —— 主线 P0;
   pool_scale=1 时 LADWP 作外部效度锚点;
3. 在 ha, co 两个域 × phi∈{0,0.2,0.4,0.6,0.8} × pool_scale∈{1,2,3} 上
   求 M0, M1, CoC0, CoC1, C, F, x_ai, dS_pot;
4. 双门禁: status=="converged_unique" 且 ~coc_floor_degenerate;
   报告 n_eff (有效情景数) 与剔除数与原因;
5. 逐情景报 q 与 dS_pot 符号; 检验 H3 (q>0 是否为城市受益的充分条件);
6. 统一恒等式残差用【相对容差】检验 (量级可达 1e10, 绝对容差无意义)。

【纪律】
  · 引擎 07_代码_AI-UWM引擎/aiuwm_src/ 只读, 永不修改;
  · 求解失败/退化情景必须显式标记并从统计中剔除, 报剔除数与原因;
  · 不编造数据; 缺失物种必须显式标记, 不静默按 0 (见 wp4_missing_species_impact.py)。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
A10 = ROOT / "A10_敏感性与边界"
sys.path.insert(0, str(A10))
import city_model as cm  # noqa: E402

# ------------------------------------------------------------------ 常量
PANEL = "B_full"                 # 5 物种引用档 (GB/T 50050-2017), 见 A27
DOMS = ("ha", "co")
PHI_GRID = (0.0, 0.2, 0.4, 0.6, 0.8)
POOL_GRID = (1.0, 2.0, 3.0)
COC_FLOOR = 1.000001             # 引擎 CoC 下限 (A27 退化检测阈值)

# 组成完整性口径: 面板要求的 5 个约束物种 (PANEL B_full 的键)
CORE = tuple(cm.PANELS[PANEL].keys())
ALL_SPECIES = ("TDS", "chloride", "Ca", "Mg", "Na", "SO4",
               "alkalinity", "silica", "pH", "hardness")

# 主口径水样 (完整物种): 由 main() 从 load_samples() 权威确认后填充
PRIMARY_SAMPLES: dict[str, dict] = {}
# 所有水样 (含不完整), 用于任务 B
ALL_SAMPLES: dict[str, dict] = {}

REL_TOL = 1e-9                   # 恒等式相对容差
ZERO_ABS = 1e-6                  # 符号计数的零值处理: |dS| < 1e-6 ML 记为 0


# ------------------------------------------------------------ 水样读取
def _species_of(row: pd.Series) -> dict:
    """从权威行中抽取面板要求的物种值 (缺失者【不写入】, 而非写 0)。

    ⚠ 关键: 这里显式不补 0。引擎/分析路径会把缺失物种按 0 处理 (已知缺陷),
    故 q 中缺席即代表"组成不完整", 由调用方显式标记。
    """
    q: dict[str, float] = {}
    for sp in CORE:
        if sp in row.index and pd.notna(row.get(sp)):
            q[sp] = float(row[sp])
    return q


def completeness(q: dict) -> dict:
    missing = [sp for sp in CORE if sp not in q]
    return {"n_species": len([sp for sp in CORE if sp in q]),
            "missing": missing,
            "status": "COMPLETE" if not missing else "INCOMPLETE"}


def load_authoritative() -> pd.DataFrame:
    """权威水样化学 —— 唯一来源 city_model.load_samples()。"""
    return cm.load_samples()


# ------------------------------------------------------------ 单情景求解
def solve_scenario(dom: str, sample: str, q: dict, phi: float, pool_scale: float,
                   *, cache: dict) -> dict:
    """求 B1 与 B2 两情景, 返回主估计量的全部构成量。

    关键设计: **每次调用使用独立 cache**。
    make_evaluators 的缓存键现已含 q (M5 已于 2026-10-15 修复), 但为彻底排除
    "共享 cache 导致跨水样复用陈旧计划"的历史缺陷复发风险, 本脚本仍每情景新建,
    并在 summary 中记录 cache_key_includes_q 的自检结果。
    """
    bl = cm.BASELINES[dom]
    pool = bl["P0"] * float(pool_scale)
    gap = bl["gap"]
    dp = bl["P0"] * 0.0          # dp_scale=0: 不放大池 (与 A13 参照口径一致)

    # B2: AI 使用再生水
    r2 = cm.solve_city(bl, PANEL, sample, q,
                       m0=cm.m0_of(bl, PANEL, q), pool=pool, gap=gap, dp=dp,
                       ai_target=float(phi), cache=cache)
    # B1: AI 不使用再生水 (ai_target=0)
    r1 = cm.solve_city(bl, PANEL, sample, q,
                       m0=cm.m0_of(bl, PANEL, q), pool=pool, gap=gap, dp=dp,
                       ai_target=0.0, cache=cache)

    # solve_city 不透传 quality_solver_status; 直接探一次 B1 的引擎计划以取得该词表值
    # (只用于**诊断标注**, 不参与数值判定)。
    _p1 = cm.plan_raw(bl, PANEL, q, 0.0, available_ml_day=0.0)
    b1_qstat = str(_p1.quality_solver_status)

    M0, M1 = r1["M_ml"], r2["M_ml"]                 # B1 补水 / B2 补水
    CoC0, CoC1 = r1["CoC_ai"], r2["CoC_ai"]
    x_ai = r2["x_ai_ml"]                            # B2 下 AI 实际取得的再生水
    inc_B1, inc_B2 = r1["inc_reclaimed_ml"], r2["inc_reclaimed_ml"]

    # ⚠ 关键口径澄清 (2026-10-16, 本轮实测):
    #   inc_B2 - inc_B1 在 pool < 既有用户可回用需求时**恒等于 -x_ai**
    #   (AI 的全部取水直接从既有用户手中夺走)。此时若直接把负值当 C,
    #   则 dS = -x_ai - (M0-M1) - x_ai 会**重复扣减 x_ai** (双计)。
    #   故必须与 A13 已评审口径一致, 取 max(0, ...): 被夺走(=负位移)不是"补回", C 记 0。
    #   实测验证: ps=1 时 inc_B2-inc_B1 = -x_ai (完全一致); ps>=2 时 = 0。
    displaced_raw = inc_B2 - inc_B1                 # 带符号位移 (可为负)
    C = max(0.0, displaced_raw)                     # 挤占位移 (既有用户须补回量)
    F = (M0 - M1) + x_ai                            # 数据中心净索取
    dS = C - F                                      # 主估计量

    # H2 闭式 q
    den = CoC1 * (CoC0 - 1.0)
    q_chem = ((CoC1 - CoC0) / den) if abs(den) > 1e-300 else float("nan")

    # 门禁
    # ⚠ B1 支路的 status 词表缺陷 (本轮实测发现, 必须显式处理):
    #   B1 (ai_target=0, 不使用再生水) 时引擎返回 quality_solver_status='not_applicable'
    #   (因为没有再生水 -> 水质求解器不会被调用)。而联合求解器的 quality_ready
    #   白名单是 {"converged","ready"} (reclaimed_allocation.py:477), 不含
    #   'not_applicable', 于是 status 被判为 'quality_not_converged'。
    #   但 B1 实为**健康解**: root_count=1, closure_residual=0.0, CoC=3.5 明确。
    #   => 这是 CHI_SEMANTICS.md §4 警告的"状态词表跨路径不一致"缺陷, 不是数值失败。
    #   处理: 单独记录 B1 的 not_applicable 标记, 并按**双门禁**判定:
    #     ① B2 必须 converged_unique; ② B1 必须单根且闭合 (root=1 且 residual~0);
    #     ③ 两者均不触 CoC 下限。
    b1_not_applicable = bool(b1_qstat == "not_applicable")
    b1_healthy = bool(r1["roots"] == 1 and abs(r1["closure_residual_ml"]) <= 1e-9
                      and np.isfinite(M0) and M0 > 0)
    status = str(r2["status"])
    degenerate = bool(min(CoC0, CoC1) <= COC_FLOOR + 1e-12)
    converged_unique = status == "converged_unique"
    reliable = bool(converged_unique and b1_healthy and not degenerate)

    return {
        "domain": dom, "sample": sample, "phi": float(phi),
        "pool_scale": float(pool_scale), "panel": PANEL,
        # --- 构成量 ---
        "M0_ml": M0, "M1_ml": M1, "CoC0": CoC0, "CoC1": CoC1,
        "C_ml": C, "F_ml": F, "x_ai_ml": x_ai,
        "displaced_raw_ml": displaced_raw,
        "inc_B1_ml": inc_B1, "inc_B2_ml": inc_B2,
        # --- 结局 ---
        "dS_pot_ml": dS, "q": q_chem,
        "q_sign": int(np.sign(round(q_chem, 12))) if np.isfinite(q_chem) else 0,
        "dS_sign": int(np.sign(dS)) if abs(dS) >= ZERO_ABS else 0,
        # --- 门禁 ---
        "status_B2": status, "status_B1": str(r1["status"]),
        "b1_quality_status": b1_qstat,
        "b1_not_applicable": b1_not_applicable,
        "b1_healthy": b1_healthy,
        "converged_unique": converged_unique,
        "coc_floor_degenerate": degenerate,
        "reliable": reliable,
        "phi_eff": r2["phi_eff"],
        "roots_B2": int(r2["roots"]), "roots_B1": int(r1["roots"]),
        "closure_residual_B2_ml": float(r2["closure_residual_ml"]),
    }


# ------------------------------------------------------------ 检验
def relative_residual(pred: pd.Series, obs: pd.Series) -> pd.Series:
    """相对残差 |pred-obs| / max(|obs|, scale)。量级 1e10 时绝对容差无意义。"""
    scale = np.maximum(np.abs(obs), 1e-30)
    return (pred - obs).abs() / scale


def h3_test(d: pd.DataFrame) -> dict:
    """H3: q>0 是城市受益 (dS_pot<0) 的【充分条件】。

    WP2 §4 冻结: 证伪条件 = 出现 1 例 q>0 而 dS>0。
    零值处理: |dS| < ZERO_ABS 记为 0, 不计入正/负。
    """
    ok = d[d["reliable"]].copy()
    n_eff = int(len(ok))
    if n_eff == 0:
        return {"n_eff": 0, "verdict": "NOT_IDENTIFIABLE",
                "reason": "可靠子集为空; 缺列/空集不得计为 PASS (门禁第 4 条)"}
    pos = ok[ok["q"] > 0]
    neg = ok[ok["q"] < 0]
    zero = ok[ok["q"].abs() <= 1e-12]
    n_qpos = int(len(pos))
    counterexamples = pos[pos["dS_pot_ml"] >= ZERO_ABS]
    verdict = ("SUPPORTED" if (n_qpos > 0 and len(counterexamples) == 0)
               else ("REFUTED" if len(counterexamples) else "NOT_IDENTIFIABLE"))
    return {
        "n_eff": n_eff,
        "zero_value_convention": f"|dS_pot| < {ZERO_ABS} ML 记为 0, 不计入正负计数",
        "n_q_positive": n_qpos,
        "n_q_negative": int(len(neg)),
        "n_q_zero": int(len(zero)),
        "n_qpos_and_beneficial": int((pos["dS_pot_ml"] < -ZERO_ABS).sum()),
        "n_qpos_and_harmful": int(len(counterexamples)),
        "n_qpos_and_zero": int((pos["dS_pot_ml"].abs() <= ZERO_ABS).sum()),
        "n_qneg": int(len(neg)),
        "n_qneg_and_beneficial": int((neg["dS_pot_ml"] < -ZERO_ABS).sum()),
        "n_qneg_and_harmful": int((neg["dS_pot_ml"] > ZERO_ABS).sum()),
        "verdict": verdict,
        "counterexample_examples": counterexamples[
            ["domain", "sample", "phi", "pool_scale", "q", "dS_pot_ml"]
        ].head(5).to_dict("records") if len(counterexamples) else [],
    }


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m: str = "") -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 88)
    rec("WP4-1  完整物种水样上的城市级 dS_pot (主口径 B1 − B2)")
    rec("=" * 88)

    # ---------------- 0. 权威水样读取 ----------------
    rec("\n[0] 权威水样化学 (唯一来源: city_model.load_samples(), 不自造数值)")
    samples = load_authoritative()
    rec(f"  权威表共 {len(samples)} 条; 面板 {PANEL} 要求 {len(CORE)} 个约束物种: {list(CORE)}")
    rec(f"  {'sample':<58} {'n':>3} {'缺失':<26} 状态")
    meta: dict[str, dict] = {}
    for _, row in samples.iterrows():
        name = str(row["source"])
        q = _species_of(row)
        c = completeness(q)
        meta[name] = {**c, "is_reclaimed": bool(row.get("is_reclaimed", True)),
                      "sclass": str(row.get("sclass", ""))}
        ALL_SAMPLES[name] = q
        miss = ",".join(c["missing"]) if c["missing"] else "-"
        rec(f"  {name:<58} {c['n_species']:>3} {miss:<26} {c['status']}")

    # 主口径: 仅在完整物种水样上跑 (任务 A 的硬要求)
    primary = [n for n, m in meta.items() if m["status"] == "COMPLETE"]
    rec(f"\n  ⇒ 完整物种水样 (主口径) = {len(primary)} 个: {primary}")
    incomplete = [n for n, m in meta.items() if m["status"] != "COMPLETE"]
    rec(f"  ⇒ 不完整水样 (次口径, 本次不用于主结论) = {incomplete}")
    rec("  ⚠ Figshare BW 为 brackish(苦咸水), 非再生水 —— 本脚本根本不纳入。")

    if len(primary) == 0:
        raise SystemExit("✗ 无完整物种水样 => 主口径 NOT_IDENTIFIABLE, 不得计为 PASS")

    global PRIMARY_SAMPLES
    PRIMARY_SAMPLES = {n: ALL_SAMPLES[n] for n in primary}

    # ---------------- cache 键自检 (M5 复发防护) ----------------
    rec("\n[0b] make_evaluators 缓存键自检 (M5 历史缺陷: 键缺 q 会导致跨水样复用)")
    cache_probe: dict = {}
    coc_by_sample = {}
    for n, q in PRIMARY_SAMPLES.items():
        bl = cm.BASELINES["ha"]
        ev, _ = cm.make_evaluators(bl, PANEL, q, cache=cache_probe)
        coc_by_sample[n] = None
    cocs = []
    for n, q in PRIMARY_SAMPLES.items():
        ev_ai, _ = cm.make_evaluators(cm.BASELINES["ha"], PANEL, q, cache=cache_probe)
        r = cm.city_outcome("ha", PANEL, n, pool_scale=1.0, dp_scale=0.0,
                            ai_target=0.4, cache=cache_probe)
        cocs.append(round(float(r["CoC_ai"]), 6))
    distinct = len(set(cocs))
    rec(f"  共享 cache 下各水样 CoC@(ha,ps=1,phi=0.4) = {cocs}")
    rec(f"  不同取值个数 = {distinct}/{len(cocs)} "
        f"=> {'✓ 缓存键含 q, 组成维度有效' if distinct == len(cocs) else '✗ 疑似键缺 q, 组成维度失效!'}")

    # ---------------- 1. 主扫描 ----------------
    rec(f"\n[1] 主扫描: {len(PRIMARY_SAMPLES)} 完整水样 × {len(DOMS)} 域 × "
        f"phi∈{PHI_GRID} × pool_scale∈{POOL_GRID}")
    rows = []
    excluded: list[dict] = []
    for dom in DOMS:
        for name, q in PRIMARY_SAMPLES.items():
            for ps in POOL_GRID:
                for phi in PHI_GRID:
                    try:
                        r = solve_scenario(dom, name, q, phi, ps, cache={})
                    except Exception as e:  # noqa: BLE001
                        excluded.append({"domain": dom, "sample": name, "phi": phi,
                                         "pool_scale": ps, "reason":
                                         f"SOLVE_RAISED:{type(e).__name__}:{e}"})
                        rec(f"    ERROR {dom}/{name}/phi={phi}/ps={ps}: "
                            f"{type(e).__name__}: {e}")
                        continue
                    r.update({k: v for k, v in meta[name].items()})
                    rows.append(r)
                    if not r["reliable"]:
                        reasons = []
                        if not r["converged_unique"]:
                            reasons.append("B2_NOT_CONVERGED_UNIQUE:" + r["status_B2"])
                        if not r["b1_healthy"]:
                            reasons.append("B1_UNHEALTHY")
                        if r["coc_floor_degenerate"]:
                            reasons.append("COC_FLOOR_DEGENERATE")
                        excluded.append({
                            "domain": dom, "sample": name, "phi": phi, "pool_scale": ps,
                            "reason": "+".join(reasons),
                            "CoC0": r["CoC0"], "CoC1": r["CoC1"]})

    d = pd.DataFrame(rows)
    if len(d) == 0:
        raise SystemExit("✗ 全部情景失败 => NOT_IDENTIFIABLE")
    # 附加制度标签 (供产物可追溯; 不改变任何数值)
    _elig = {dm: cm.BASELINES[dm]["P0"] + cm.BASELINES[dm]["gap"] for dm in DOMS}
    _p0 = {dm: cm.BASELINES[dm]["P0"] for dm in DOMS}
    d["elig_ml"] = d["domain"].map(_elig)
    d["pool_nominal_ml"] = d["domain"].map(_p0) * d["pool_scale"]
    d["pool_exhausted_B1"] = d["inc_B1_ml"] >= d["pool_nominal_ml"] - 1e-6
    d["inc_saturated_B1"] = d["inc_B1_ml"] >= d["elig_ml"] - 1e-6
    d.to_csv(HERE / "wp4_results.csv", index=False, encoding="utf-8-sig")
    rec(f"\n  求得 {len(d)} 情景, 剔除 {len(excluded)} 情景 "
        f"(n_eff = {int(d['reliable'].sum())})")
    if excluded:
        ex = pd.DataFrame(excluded)
        rec(f"  剔除原因分布: {ex['reason'].value_counts().to_dict()}")

    ok = d[d["reliable"]].copy()

    # ---------------- 2. 双层门禁 ----------------
    rec("\n[2] 双层门禁报告")
    rec("  门禁① B2 支路 status == 'converged_unique'")
    rec("  门禁② B1 支路 单根且闭合 (root=1, |closure_residual|<=1e-9)")
    rec("  门禁③ 两支路 CoC 均不触引擎下限 (CoC > 1.000001)")
    n_b1_na = int(d["b1_not_applicable"].sum())
    rec(f"\n  ⚠ B1 支路 quality_solver_status='not_applicable' 的情景数 = {n_b1_na}/{len(d)}")
    rec("     原因: ai_target=0 -> 无再生水 -> 水质求解器不被调用 -> 引擎返回 not_applicable,")
    rec("     但联合求解器白名单仅含 {'converged','ready'} (reclaimed_allocation.py:477),")
    rec("     故 status 被判 'quality_not_converged'。**这是词表不一致, 不是数值失败**")
    rec("     (见 A26_语义统一/CHI_SEMANTICS.md §4)。B1 经核验为健康解: root=1, 闭合残差=0。")
    rec(f"  n_all_total         = {len(d)}")
    rec(f"  门禁①通过 (B2 cu)    = {int(d['converged_unique'].sum())}")
    rec(f"  门禁②通过 (B1 健康)  = {int(d['b1_healthy'].sum())}")
    rec(f"  CoC 触下限 (门禁③失败) = {int(d['coc_floor_degenerate'].sum())}")
    rec(f"  ★ n_eff             = {len(ok)}")
    gate = {
        "gate_1_B2_converged_unique": int(d["converged_unique"].sum()),
        "gate_2_B1_healthy_single_root_closed": int(d["b1_healthy"].sum()),
        "gate_3_coc_not_degenerate": int((~d["coc_floor_degenerate"]).sum()),
        "n_all": int(len(d)),
        "n_eff": int(len(ok)),
        "n_excluded": int(len(d) - len(ok)),
        "excluded_share_pct": round((len(d) - len(ok)) / max(len(d), 1) * 100, 2),
        "status_counts_B2": d["status_B2"].value_counts().to_dict(),
        "status_counts_B1": d["status_B1"].value_counts().to_dict(),
        "b1_quality_status_counts": d["b1_quality_status"].value_counts().to_dict(),
        "n_b1_not_applicable": n_b1_na,
        "n_coc_floor_degenerate": int(d["coc_floor_degenerate"].sum()),
        "n_excluded_non_converged": int((~d["converged_unique"]).sum()),
        "coc_floor_threshold": COC_FLOOR,
        "zero_value_convention": f"|dS_pot| < {ZERO_ABS} ML 记为 0",
        "b1_status_vocabulary_defect": (
            "B1(ai_target=0) 的 quality_solver_status='not_applicable' 未被联合求解器白名单 "
            "{'converged','ready'} 接受, 导致 status='quality_not_converged'。B1 实为健康解 "
            "(root=1, closure_residual=0)。按 CHI_SEMANTICS §4 属状态词表跨路径不一致。"),
    }
    if len(ok) == 0:
        gate["verdict"] = "NOT_IDENTIFIABLE"
        rec("  ✗ 可靠子集为空 => NOT_IDENTIFIABLE, 不得计为 PASS (门禁第 4 条)")

    # ---------------- 3. 恒等式残差 (相对容差) ----------------
    rec("\n[3] 恒等式检验 (相对容差; 量级可达 1e10, 绝对容差无意义)")
    # (a) 主估计量定义自洽: dS == C - F
    rel_a = relative_residual(ok["C_ml"] - ok["F_ml"], ok["dS_pot_ml"])
    # (b) 守恒重排: dS == max(0, inc_B2 - inc_B1) - (M0 - M1) - x_ai
    #     注意 C 必须含 max(0,.), 否则在短缺域会与 x_ai 双计 (见 solve_scenario 注释)。
    pred_b = (np.maximum(0.0, ok["inc_B2_ml"] - ok["inc_B1_ml"])
              - (ok["M0_ml"] - ok["M1_ml"]) - ok["x_ai_ml"])
    rel_b = relative_residual(pred_b, ok["dS_pot_ml"])
    # (b') 用【未截断】位移直接算 —— 应**失败**, 以证明 max(0,.) 是必要的而非装饰
    pred_b_raw = ((ok["inc_B2_ml"] - ok["inc_B1_ml"])
                  - (ok["M0_ml"] - ok["M1_ml"]) - ok["x_ai_ml"])
    rel_b_raw = relative_residual(pred_b_raw, ok["dS_pot_ml"])
    max_scale = float(ok["dS_pot_ml"].abs().max()) if len(ok) else float("nan")
    ident = {
        "definition_dS_eq_C_minus_F_max_rel_residual": float(rel_a.max()) if len(ok) else None,
        "conservation_rearrangement_max_rel_residual": float(rel_b.max()) if len(ok) else None,
        "conservation_rearrangement_RAW_displacement_max_rel_residual":
            float(rel_b_raw.max()) if len(ok) else None,
        "relative_tolerance_used": REL_TOL,
        "max_abs_dS_ml_order_of_magnitude": max_scale,
        "passes": bool(len(ok) and rel_a.max() <= REL_TOL and rel_b.max() <= REL_TOL),
        "note": ("两式均为代数重排, 不构成科学发现 (WP2 §2.1). "
                 "报出仅作记账一致性检验。C 必须含 max(0,.)。"),
    }
    rec(f"  (a) dS = C - F          最大相对残差 = {ident['definition_dS_eq_C_minus_F_max_rel_residual']:.3e}"
        f"  {'✓ PASS' if ident['definition_dS_eq_C_minus_F_max_rel_residual'] <= REL_TOL else '✗ FAIL'}")
    rec(f"  (b) dS = max(0,Δinc) - ΔM - x_ai 最大相对残差 = "
        f"{ident['conservation_rearrangement_max_rel_residual']:.3e}"
        f"  {'✓ PASS' if ident['conservation_rearrangement_max_rel_residual'] <= REL_TOL else '✗ FAIL'}")
    rec(f"  (b') 对照: 若【不截断】Δinc 则残差 = "
        f"{ident['conservation_rearrangement_RAW_displacement_max_rel_residual']:.3e}"
        f"  => max(0,.) 是必要的 (否则 x_ai 双计)")
    rec(f"  参考: 可靠子集 max|dS_pot| = {max_scale:.4g} ML (绝对容差在此量级下不适用)")

    # (c) 位移恒等式实测 —— 三种制度 (本轮实测确认):
    #     ① 池在 B1 被既有用户用尽 (inc_B1 ≈ pool): AI 的每一滴都从既有用户夺走
    #        => 带符号位移 == -x_ai  (故 C 必须取 max(0,.) = 0)
    #     ② 池在 B1 已使既有用户饱和 (inc_B1 ≈ elig) 且 B2 仍饱和: 位移 == 0
    #     ③ 部分情形: 池介于两者之间, 位移介于 -x_ai 与 0 之间 (无须假定, 如实报出)
    elig_map = {dm: cm.BASELINES[dm]["P0"] + cm.BASELINES[dm]["gap"] for dm in DOMS}
    ok = ok.copy()
    ok["elig_ml"] = ok["domain"].map(elig_map)
    r1m = ok[ok["pool_exhausted_B1"] & ~ok["inc_saturated_B1"]]
    r2m = ok[ok["inc_saturated_B1"]]
    r3m = ok[~(ok["pool_exhausted_B1"] | ok["inc_saturated_B1"])]
    id_disp = {
        "regime1_pool_exhausted_n": int(len(r1m)),
        "regime1_max_abs_diff_from_minus_x_ai": (
            float((r1m["displaced_raw_ml"] + r1m["x_ai_ml"]).abs().max())
            if len(r1m) else None),
        "regime2_incumbent_saturated_n": int(len(r2m)),
        "regime2_max_abs_displacement": (
            float(r2m["displaced_raw_ml"].abs().max()) if len(r2m) else None),
        "regime3_partial_n": int(len(r3m)),
        "n_clamped_C_to_zero": int((ok["displaced_raw_ml"] <= 0).sum()),
        "note": ("池在 B1 被既有用户用尽时带符号位移恒等于 -x_ai; 此时 C 必须取 max(0,.) 记 0, "
                 "否则 dS 会重复扣减 x_ai (双计)。与 A13 已评审口径一致。"
                 "其余制度位移为 0 或介于 -x_ai 与 0 之间。"),
    }
    if len(r1m):
        m = id_disp["regime1_max_abs_diff_from_minus_x_ai"]
        rec(f"  (c1) 制度① 池在 B1 被用尽 n={len(r1m)}: |位移 + x_ai| 最大 = {m:.3e} ML "
            f"=> {'✓ 位移恒等于 -x_ai (故 C 取 max(0,.) 必要)' if m < 1e-6 else '⚠ 偏离'}")
    if len(r2m):
        m2 = id_disp["regime2_max_abs_displacement"]
        rec(f"  (c2) 制度② B1 已使既有用户饱和 n={len(r2m)}: |位移| 最大 = {m2:.3e} ML "
            f"=> {'✓ 无挤占' if m2 < 1e-6 else '⚠ 偏离'}")
    if len(r3m):
        rec(f"  (c3) 制度③ 部分情形 n={len(r3m)}: 位移 ∈ "
            f"[{r3m['displaced_raw_ml'].min():.4g}, {r3m['displaced_raw_ml'].max():.4g}] ML "
            f"(介于 -x_ai 与 0 之间, 如实报出不假定)")

    # ---------------- 4. 逐情景符号分布 ----------------
    rec("\n[4] ★ 逐情景结果 (主口径, 完整物种水样, 仅可靠子集)")
    cols = ["domain", "sample", "pool_scale", "phi", "M0_ml", "M1_ml", "CoC0", "CoC1",
            "C_ml", "F_ml", "x_ai_ml", "q", "dS_pot_ml"]
    for dom in DOMS:
        for name in PRIMARY_SAMPLES:
            sub = ok[(ok["domain"] == dom) & (ok["sample"] == name)]
            if not len(sub):
                continue
            rec(f"\n  --- {dom.upper()} / {name} ---")
            disp = sub[cols].copy()
            for c in ("M0_ml", "M1_ml", "C_ml", "F_ml", "x_ai_ml", "dS_pot_ml"):
                disp[c] = disp[c].map(lambda v: f"{v:.4g}")
            rec(disp.to_string(index=False))

    rec("\n[4b] ★ dS_pot 符号分布 (按域 × 水样 × pool_scale)")
    g = ok.groupby(["domain", "sample", "pool_scale"]).agg(
        n=("dS_pot_ml", "size"),
        n_neg=("dS_pot_ml", lambda s: int((s < -ZERO_ABS).sum())),
        n_zero=("dS_pot_ml", lambda s: int((s.abs() <= ZERO_ABS).sum())),
        n_pos=("dS_pot_ml", lambda s: int((s > ZERO_ABS).sum())),
        dS_min=("dS_pot_ml", "min"), dS_max=("dS_pot_ml", "max"),
        q_min=("q", "min"), q_max=("q", "max")).reset_index()
    rec(g.round(4).to_string(index=False))

    overall = {
        "n_eff": int(len(ok)),
        "n_dS_negative_beneficial": int((ok["dS_pot_ml"] < -ZERO_ABS).sum()),
        "n_dS_zero": int((ok["dS_pot_ml"].abs() <= ZERO_ABS).sum()),
        "n_dS_positive_harmful": int((ok["dS_pot_ml"] > ZERO_ABS).sum()),
        "n_q_positive": int((ok["q"] > 1e-12).sum()),
        "n_q_negative": int((ok["q"] < -1e-12).sum()),
        "dS_median_ml": float(ok["dS_pot_ml"].median()),
        "dS_min_ml": float(ok["dS_pot_ml"].min()),
        "dS_max_ml": float(ok["dS_pot_ml"].max()),
    }
    rec(f"\n  合计 n_eff={overall['n_eff']}: "
        f"dS<0 (受益) = {overall['n_dS_negative_beneficial']}, "
        f"dS=0 = {overall['n_dS_zero']}, "
        f"dS>0 (有害) = {overall['n_dS_positive_harmful']}")
    rec(f"  q>0 = {overall['n_q_positive']}, q<0 = {overall['n_q_negative']}")

    # 每个水样的方向 (phi=0.6 回用档 vs CoC0 基线; 与 WP3 口径可比)
    # 注: CoC0 / M0 来自每行的 B1 支路 (不依赖 phi=0 行; 后者因 B2≡B1 退化已被剔除)。
    rec("\n[4c] ★ 逐水样方向 (CoC0=无回用基线 vs CoC1@phi=0.6, 与 WP3 口径可比)")
    rec(f"  {'domain':>6} {'sample':<40} {'ps':>4} {'CoC0':>8} {'CoC1':>9} "
        f"{'q':>10} {'dS_pot(ML)':>13} 方向")
    for dom in DOMS:
        for name in PRIMARY_SAMPLES:
            for ps in POOL_GRID:
                s1 = ok[(ok["domain"] == dom) & (ok["sample"] == name)
                        & (ok["pool_scale"] == ps) & (ok["phi"] == 0.6)]
                if not len(s1):
                    continue
                c0 = float(s1["CoC0"].iloc[0])
                c1 = float(s1["CoC1"].iloc[0])
                qq = float(s1["q"].iloc[0])
                ds = float(s1["dS_pot_ml"].iloc[0])
                direction = ("回用有益 (dS<0)" if ds < -ZERO_ABS
                             else ("回用有害 (dS>0)" if ds > ZERO_ABS else "中性"))
                rec(f"  {dom:>6} {name:<40} {ps:>4.0f} {c0:8.4f} {c1:9.4f} "
                    f"{qq:10.5f} {ds:13.4g} {direction}")

    # ---------------- 5. H3 ----------------
    rec("\n[5] ★ H3 检验: q>0 是城市受益 (dS_pot<0) 的【充分条件】?")
    h3 = h3_test(d)
    rec(f"  n_eff = {h3['n_eff']}  (零值约定: {h3['zero_value_convention']})")
    if h3["verdict"] == "NOT_IDENTIFIABLE" and h3["n_eff"] == 0:
        rec(f"  ✗ NOT_IDENTIFIABLE: {h3.get('reason')}")
    else:
        rec(f"  q>0 情景 = {h3['n_q_positive']}  |  其中 dS<0 (受益) = "
            f"{h3['n_qpos_and_beneficial']}, dS>0 (有害, 反例) = {h3['n_qpos_and_harmful']}, "
            f"dS=0 = {h3['n_qpos_and_zero']}")
        rec(f"  q<0 情景 = {h3['n_q_negative']}  |  其中 dS<0 = {h3['n_qneg_and_beneficial']}, "
            f"dS>0 = {h3['n_qneg_and_harmful']}")
        if h3["verdict"] == "SUPPORTED":
            rec("  ✓ H3 成立: 可靠子集内 q>0 的每一例 dS_pot 均为负 => 无充分性反例")
        elif h3["verdict"] == "REFUTED":
            rec(f"  ✗ H3 被证伪: 出现 {h3['n_qpos_and_harmful']} 例 q>0 而 dS>0")
            for c in h3["counterexample_examples"]:
                rec(f"      {c}")
        else:
            rec("  ⚠ NOT_IDENTIFIABLE: q>0 组为空 => 不得计为 PASS (门禁第 4/8 条)")

    # ---------------- 6. 汇总 ----------------
    by_sample = {}
    for name in PRIMARY_SAMPLES:
        s = ok[ok["sample"] == name]
        if not len(s):
            by_sample[name] = {"n_eff": 0, "status": "NOT_IDENTIFIABLE"}
            continue
        by_sample[name] = {
            "n_eff": int(len(s)),
            "n_species": meta[name]["n_species"], "missing": meta[name]["missing"],
            "CoC0_range": [float(s["CoC0"].min()), float(s["CoC0"].max())],
            "CoC1_range": [float(s["CoC1"].min()), float(s["CoC1"].max())],
            "q_range": [float(s["q"].min()), float(s["q"].max())],
            "q_sign_uniform": bool((s["q"] > 0).all() or (s["q"] < 0).all()),
            "n_dS_negative": int((s["dS_pot_ml"] < -ZERO_ABS).sum()),
            "n_dS_zero": int((s["dS_pot_ml"].abs() <= ZERO_ABS).sum()),
            "n_dS_positive": int((s["dS_pot_ml"] > ZERO_ABS).sum()),
        }

    # H4 跨组成反转: 比较两个完整水样的 dS_pot 符号方向
    h4 = {}
    for dom in DOMS:
        for ps in POOL_GRID:
            ss = {n: ok[(ok["domain"] == dom) & (ok["sample"] == n)
                        & (ok["pool_scale"] == ps) & (ok["phi"] == 0.6)]
                  for n in PRIMARY_SAMPLES}
            if all(len(v) for v in ss.values()) and len(ss) == 2:
                a, b = list(ss.values())
                da, db = float(a["dS_pot_ml"].iloc[0]), float(b["dS_pot_ml"].iloc[0])
                qa, qb = float(a["q"].iloc[0]), float(b["q"].iloc[0])
                h4[f"{dom}|ps={ps:.0f}"] = {
                    "dS_by_sample": {list(PRIMARY_SAMPLES)[0]: da, list(PRIMARY_SAMPLES)[1]: db},
                    "q_by_sample": {list(PRIMARY_SAMPLES)[0]: qa, list(PRIMARY_SAMPLES)[1]: qb},
                    "sign_reversal": bool(np.sign(da) != np.sign(db) and da != 0 and db != 0),
                    "q_sign_reversal": bool(np.sign(qa) != np.sign(qb) and qa != 0 and qb != 0),
                }
    rec("\n[6] ★ H4 跨组成符号反转 (两个完整水样, phi=0.6)")
    for k, v in h4.items():
        rec(f"  {k}: dS={ {a: f'{b:.4g}' for a, b in v['dS_by_sample'].items()} } "
            f"q={ {a: f'{b:.5f}' for a, b in v['q_by_sample'].items()} } "
            f"符号反转={'是' if v['sign_reversal'] else '否'}")

    summary = {
        "task": "WP4-1 完整物种水样上的城市级 dS_pot (主口径 B1 − B2)",
        "estimator": "dS_pot = C - F = (inc_B2 - inc_B1) - (M0 - M1) - x_ai",
        "sign_convention": "dS_pot>0 => 城市净取水上升(有害); <0 => 下降(有益)",
        "panel": PANEL, "panel_limits": cm.PANELS[PANEL],
        "core_species_required": list(CORE),
        "phi_grid": list(PHI_GRID), "pool_grid": list(POOL_GRID), "domains": list(DOMS),
        "samples_authoritative": meta,
        "primary_samples_complete": primary,
        "incomplete_samples_excluded_from_primary": incomplete,
        "brackish_excluded": [n for n in meta if "brackish" in meta[n].get("sclass", "").lower()
                              or "BW" in n],
        "cache_key_probe_coc": cocs,
        "cache_key_includes_q": bool(distinct == len(cocs)),
        "gates": gate,
        "identity": ident,
        "displacement_identity": id_disp,
        "overall_symbol_distribution": overall,
        "h3_test": h3,
        "h4_sign_reversal": h4,
        "by_sample": by_sample,
        "by_domain_sample_pool": g.to_dict("records"),
        "excluded_scenarios": excluded,
        "n_excluded_total": len(excluded),
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": (
            "引擎只读; 主口径仅完整物种水样; 求解失败/退化情景显式标记并剔除; "
            "恒等式用相对容差; 符号计数声明零值约定与实际 n_eff; 空集/缺列标 NOT_IDENTIFIABLE。"),
        "regression_note": (
            "每情景使用独立 cache, 以排除 M5(缓存键缺 q) 历史缺陷复发; "
            "并另用共享 cache 探针自检组成维度是否仍生效。"),
    }
    (HERE / "wp4_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (HERE / "wp4_run_log.txt").write_text("\n".join(log), encoding="utf-8")
    rec(f"\n[write] wp4_results.csv / wp4_summary.json / wp4_run_log.txt "
        f"({time.time() - t0:.1f}s)")


if __name__ == "__main__":
    main()
