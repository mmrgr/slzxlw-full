"""WP4-2: "缺失物种按 0" 偏差的方向与幅度 (任务 B).

======================================================================
【为什么这一步决定不完整水样能否用于任何结论】
======================================================================
`city_model.quality_dict` 只挑出水样中**存在**的物种; 而限值面板 B_full 要求 5 个。
于是缺失物种的浓度被当作 **0** ⇒ 该物种的限值**永不触发** ⇒ 水样显得比实际更"干净"
⇒ CoC 偏高、q 偏正 ⇒ **系统性地偏向"回用有益"**。

本脚本量化: 把缺失项 (i) 按 0 (现状) vs (ii) 用一个**合理区间**填充, 看
    · q 的符号是否翻转
    · dS_pot 的符号是否翻转
    · 量级变化多少
从而判定: 不完整水样能否进入任何结论。

【填充区间的构造 (保守、可辩护, 非自造)】
对每个缺失物种 sp, 用**同一权威表内其他水样**的观测值构造区间:
    lo = 表中该物种的 min, hi = 表中该物种的 max, mid = median
这是"数据内插", 不引入外部数值; 并同时报出极端上界 (取 hi 的 2 倍) 作压力测试。
⚠ 明确声明: 这不是对该水样真实浓度的估计, 而是**偏差方向的敏感性边界**。

【范围】
  · Figshare RW (2025, paired study)  —— 真再生水, 缺 alkalinity/silica
  · AI-UWM model assumption          —— 自设假设值, 缺 hardness/alkalinity/silica
  · Figshare BW                       —— **苦咸水, 非再生水**: 仅作对照, 不进再生水结论

【纪律】
  · 引擎只读; 不自造化学值 (填充值全部由权威表内其他观测导出并显式标注);
  · 缺失物种显式列出; 主口径/次口径严格分开;
  · 符号翻转判定用相对容差, 并声明零值约定与 n_eff。
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

PANEL = "B_full"
DOMS = ("ha", "co")
PHI_TEST = 0.6                    # 与 WP3 H4 口径可比的回用档
POOL_GRID = (1.0, 2.0, 3.0)
CORE = tuple(cm.PANELS[PANEL].keys())
COC_FLOOR = 1.000001
ZERO_ABS = 1e-6

# 完整物种水样 (主口径) —— 用于构造填充区间 + 作为"基准对照"
COMPLETE = ("IEUA RP-1 (2025, tertiary)", "LADWP AWPF (2012, RO product)")
# 不完整水样 (次口径待评估)
INCOMPLETE = ("Figshare RW (2025, paired study)", "AI-UWM model assumption")
# 苦咸水 (非再生水): 仅对照
BRACKISH = ("Figshare BW (5 g·L<sup>-1</sup>) (2025, paired study)",)


def q_of(row: pd.Series) -> dict:
    """抽取面板要求的物种; 缺失【不写入】(引擎/分析路径随后按 0 处理)。"""
    return {sp: float(row[sp]) for sp in CORE
            if sp in row.index and pd.notna(row.get(sp))}


def missing_of(q: dict) -> list[str]:
    return [sp for sp in CORE if sp not in q]


def build_fill_ranges(tbl: pd.DataFrame) -> dict:
    """由权威表内**完整水样**的观测构造每个物种的填充区间。

    只用完整物种水样 (IEUA/LADWP) 作为供体, 避免用同类缺失水样互相填充 (循环)。
    """
    out: dict[str, dict] = {}
    donors = tbl[tbl["source"].isin(COMPLETE)]
    for sp in CORE:
        if sp not in donors.columns:
            continue
        v = pd.to_numeric(donors[sp], errors="coerce").dropna()
        if not len(v):
            continue
        out[sp] = {"lo": float(v.min()), "mid": float(v.median()), "hi": float(v.max()),
                   "n_donors": int(len(v)),
                   "donor_values": [float(x) for x in v]}
    return out


def solve_with(dom: str, name: str, q: dict, phi: float, pool_scale: float) -> dict:
    """B1/B2 双支路求解 (口径与 wp4_complete_samples.solve_scenario 完全一致)。"""
    bl = cm.BASELINES[dom]
    pool = bl["P0"] * float(pool_scale)
    gap = bl["gap"]
    m0_ = cm.m0_of(bl, PANEL, q)
    r2 = cm.solve_city(bl, PANEL, name, q, m0=m0_, pool=pool, gap=gap, dp=0.0,
                       ai_target=float(phi), cache={})
    r1 = cm.solve_city(bl, PANEL, name, q, m0=m0_, pool=pool, gap=gap, dp=0.0,
                       ai_target=0.0, cache={})
    M0, M1 = r1["M_ml"], r2["M_ml"]
    CoC0, CoC1 = r1["CoC_ai"], r2["CoC_ai"]
    x_ai, inc_B1, inc_B2 = r2["x_ai_ml"], r1["inc_reclaimed_ml"], r2["inc_reclaimed_ml"]
    C = max(0.0, inc_B2 - inc_B1)
    F = (M0 - M1) + x_ai
    dS = C - F
    den = CoC1 * (CoC0 - 1.0)
    qq = ((CoC1 - CoC0) / den) if abs(den) > 1e-300 else float("nan")
    degenerate = bool(min(CoC0, CoC1) <= COC_FLOOR + 1e-12)
    ok = bool(str(r2["status"]) == "converged_unique"
              and r1["roots"] == 1 and abs(r1["closure_residual_ml"]) <= 1e-9
              and not degenerate)
    return {"M0_ml": M0, "M1_ml": M1, "CoC0": CoC0, "CoC1": CoC1,
            "C_ml": C, "F_ml": F, "x_ai_ml": x_ai, "q": qq, "dS_pot_ml": dS,
            "status_B2": str(r2["status"]), "degenerate": degenerate, "reliable": ok}


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m: str = "") -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 92)
    rec("WP4-2  「缺失物种按 0」偏差的方向与幅度 (任务 B)")
    rec("=" * 92)

    tbl = cm.load_samples()
    fill = build_fill_ranges(tbl)

    rec("\n[0] 填充区间 (来源: 权威表内**完整物种水样** IEUA/LADWP 的观测; 非自造)")
    rec(f"  {'species':<12} {'lo':>10} {'mid':>10} {'hi':>10} {'n_donors':>9}  捐赠值")
    for sp, d in fill.items():
        vals = ", ".join(f"{v:g}" for v in d["donor_values"])
        rec(f"  {sp:<12} {d['lo']:10.4g} {d['mid']:10.4g} {d['hi']:10.4g} "
            f"{d['n_donors']:>9}  [{vals}]")
    rec("  ⚠ 区间为该物种在**其他真实水样**中的取值范围, 用于界定偏差方向,")
    rec("    不是对缺测水样真实浓度的估计。")

    # ---------------- 1. 逐水样 × 处理 × 情景 ----------------
    rec("\n[1] 逐水样偏差扫描 (phi=0.6; 处理 A=按0现状 / B=区间下界 / C=区间中位 "
        "/ D=区间上界 / E=2×上界压力档)")
    rows = []
    for grp, names in (("INCOMPLETE", INCOMPLETE), ("BRACKISH_CONTROL", BRACKISH)):
        for name in names:
            row = tbl[tbl["source"] == name].iloc[0]
            present = q_of(row)
            miss = missing_of(present)
            for treat, mode in (("A_zero", None), ("B_impute_lo", "lo"),
                                ("C_impute_mid", "mid"), ("D_impute_hi", "hi"),
                                ("E_impute_2x_hi", "2hi")):
                q = dict(present)
                for sp in miss:
                    if mode is None or sp not in fill:
                        continue
                    d = fill[sp]
                    q[sp] = {"lo": d["lo"], "mid": d["mid"], "hi": d["hi"],
                             "2hi": 2.0 * d["hi"]}[mode]
                for dom in DOMS:
                    for ps in POOL_GRID:
                        try:
                            r = solve_with(dom, name, q, PHI_TEST, ps)
                        except Exception as e:  # noqa: BLE001
                            rows.append({"group": grp, "sample": name, "treatment": treat,
                                         "domain": dom, "pool_scale": ps,
                                         "missing": ",".join(miss), "n_missing": len(miss),
                                         "error": f"{type(e).__name__}:{e}",
                                         "reliable": False})
                            continue
                        rows.append({"group": grp, "sample": name, "treatment": treat,
                                     "domain": dom, "pool_scale": ps,
                                     "missing": ",".join(miss), "n_missing": len(miss),
                                     "imputed_values": json.dumps(
                                         {sp: q[sp] for sp in miss if sp in q},
                                         ensure_ascii=False),
                                     **r})
    d = pd.DataFrame(rows)
    ok = d[d["reliable"].astype(bool)].copy()

    # ---------------- 2. 偏差方向与幅度 ----------------
    rec("\n[2] ★ 偏差方向与幅度 (q 与 dS_pot 的符号是否翻转)")
    rec(f"  {'group':<18} {'sample':<32} {'treat':<14} {'n':>3} {'q中位':>10} "
        f"{'dS中位':>12} {'q符号':>7} {'dS符号':>7}")
    summary_rows = []
    for grp in ("INCOMPLETE", "BRACKISH_CONTROL"):
        for name in list(INCOMPLETE) + list(BRACKISH):
            sub = ok[(ok["group"] == grp) & (ok["sample"] == name)]
            if not len(sub):
                continue
            base = sub[sub["treatment"] == "A_zero"]
            for treat in ("A_zero", "B_impute_lo", "C_impute_mid", "D_impute_hi",
                          "E_impute_2x_hi"):
                s = sub[sub["treatment"] == treat]
                if not len(s):
                    continue
                q_med = float(s["q"].median())
                d_med = float(s["dS_pot_ml"].median())
                q_sgn = "pos" if q_med > 1e-12 else ("neg" if q_med < -1e-12 else "zero")
                d_sgn = ("pos" if d_med > ZERO_ABS else
                         ("neg" if d_med < -ZERO_ABS else "zero"))
                q_flip = (len(base) and
                          np.sign(float(base["q"].median())) != np.sign(q_med))
                d_flip = (len(base) and
                          np.sign(float(base["dS_pot_ml"].median())) != np.sign(d_med))
                rec(f"  {grp:<18} {name[:32]:<32} {treat:<14} {len(s):>3} {q_med:10.5f} "
                    f"{d_med:12.4g} {q_sgn:>7} {d_sgn:>7}"
                    f"{'  ←q翻转' if q_flip else ''}{'  ←dS翻转' if d_flip else ''}")
                summary_rows.append({
                    "group": grp, "sample": name, "treatment": treat, "n_rel": int(len(s)),
                    "q_median": q_med, "dS_median_ml": d_med,
                    "q_sign": q_sgn, "dS_sign": d_sgn,
                    "q_sign_flip_vs_zero": bool(q_flip), "dS_sign_flip_vs_zero": bool(d_flip),
                    "CoC1_median": float(s["CoC1"].median()),
                    "n_degenerate": int(s["degenerate"].sum()),
                })

    # ---------------- 3. 与完整水样基准对比 ----------------
    rec("\n[3] ★ 与完整物种水样 (主口径基准) 的对比 @phi=0.6")
    bench = {}
    for name in COMPLETE:
        row = tbl[tbl["source"] == name].iloc[0]
        q = q_of(row)
        for dom in DOMS:
            r = solve_with(dom, name, q, PHI_TEST, 1.0)
            bench[f"{dom}|{name[:14]}"] = {"q": r["q"], "dS_pot_ml": r["dS_pot_ml"],
                                           "CoC1": r["CoC1"]}
    for k, v in bench.items():
        rec(f"  {k:<24} q={v['q']:+.5f}  CoC1={v['CoC1']:.4f}  dS={v['dS_pot_ml']:+.4g} ML")
    rec("  (基准水样组成完整, 无需填补, 故其 q/dS 不受本偏差影响)")

    # ---------------- 4. 裁定 ----------------
    summ = pd.DataFrame(summary_rows)
    flips = summ[summ["q_sign_flip_vs_zero"] | summ["dS_sign_flip_vs_zero"]]
    inc_flips = flips[flips["group"] == "INCOMPLETE"]
    n_inc_units = int(summ[summ["group"] == "INCOMPLETE"]["sample"].nunique())
    n_inc_rows = int(len(summ[summ["group"] == "INCOMPLETE"]))

    rec("\n[4] ★ 裁定: 不完整水样能否用于任何结论?")
    rec(f"  不完整水样数 = {n_inc_units} (Figshare RW, AI-UWM assumption)")
    rec(f"  处理组行数 = {n_inc_rows}; 出现符号翻转的行数 = {len(inc_flips)}")
    if len(inc_flips):
        rec("  ✗ 存在符号翻转 ⇒ 「缺失按 0」的偏差**足以改变结论符号**")
        for _, r in inc_flips.iterrows():
            rec(f"      {r['sample'][:34]:<34} {r['treatment']:<14} "
                f"q:{r['q_sign']} dS:{r['dS_sign']}")
        verdict = ("INCOMPLETE_SAMPLES_UNUSABLE_FOR_ANY_SIGN_CLAIM: "
                   "缺失按 0 的偏差可翻转 q 与/或 dS_pot 的符号")
    else:
        rec("  ⚠ 本次未观察到符号翻转 ⇒ 需进一步检查量级偏差是否影响结论强度")
        verdict = "NO_SIGN_FLIP_OBSERVED_BUT_MAGNITUDE_BIAS_PRESENT"
    rec("  无论翻转与否: 不完整水样**不得**进入主图或主结论; 只能进 SI 并标注缺失项与偏差方向。")

    # 苦咸水对照
    rec("\n[5] 苦咸水对照 (Figshare BW, 非再生水)")
    bw = summ[summ["group"] == "BRACKISH_CONTROL"]
    if len(bw):
        for _, r in bw.iterrows():
            rec(f"  {r['treatment']:<14} q中位={r['q_median']:+.5f} "
                f"dS中位={r['dS_median_ml']:+.4g} CoC1中位={r['CoC1_median']:.4f} "
                f"退化={r['n_degenerate']}")
    rec("  ⇒ Figshare BW 为苦咸水(非再生水), 必须**完全排除**在任何再生水组成统计之外。")

    out = {
        "task": "WP4-2 缺失物种按 0 的偏差方向与幅度",
        "phi_used": PHI_TEST, "pool_grid": list(POOL_GRID), "panel": PANEL,
        "core_species": list(CORE),
        "fill_ranges_from_donors": fill,
        "fill_donor_note": ("填充区间由权威表内完整物种水样 (IEUA/LADWP) 的观测导出, "
                            "非自造; 用于界定偏差方向, 不是对缺测真实浓度的估计。"),
        "complete_samples_baseline": bench,
        "by_treatment": summary_rows,
        "n_incomplete_units": n_inc_units,
        "n_incomplete_treatment_rows": n_inc_rows,
        "n_sign_flips_incomplete": int(len(inc_flips)),
        "sign_flip_rows": inc_flips.to_dict("records") if len(inc_flips) else [],
        "verdict": verdict,
        "n_eff_incomplete": int(len(ok[ok["group"] == "INCOMPLETE"])),
        "zero_value_convention": f"|dS_pot| < {ZERO_ABS} ML 记为 0",
        "recommendation": {
            "main_text_figures": ["IEUA RP-1 (2025, tertiary)",
                                  "LADWP AWPF (2012, RO product)"],
            "SI_only_with_missing_flagged": ["Figshare RW (2025, paired study)",
                                             "AI-UWM model assumption"],
            "must_exclude_entirely": [
                "Figshare BW (5 g·L<sup>-1</sup>) (2025, paired study) — 苦咸水, 非再生水"],
        },
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": ("引擎只读; 填充值全部由权威表内观测导出并显式标注; "
                            "主口径与次口径严格分开; 缺失物种显式列出; 报 n_eff 与零值约定。"),
    }
    (HERE / "wp4_missing_species_impact_summary.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    d.to_csv(HERE / "wp4_missing_species_impact.csv", index=False, encoding="utf-8-sig")
    (HERE / "wp4_missing_species_impact_log.txt").write_text("\n".join(log), encoding="utf-8")
    rec(f"\n[write] wp4_missing_species_impact.csv / _summary.json / _log.txt "
        f"({time.time() - t0:.1f}s)")


if __name__ == "__main__":
    main()
