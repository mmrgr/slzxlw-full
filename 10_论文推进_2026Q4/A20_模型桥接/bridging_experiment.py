"""A20: 模型桥接实验 —— 代表日周期模型 vs 逐日模型 (GPT 意见2 §WP1.4).

【为什么必须做】
A13c/A17 的核心结果建立在 `city_model.city_outcome` 上, 它用**代表日**冷却物理 +
按周期总蒸发缩放 (`e_tot * g`)。GPT 指出: 这**不能自动证明**逐日动态下结论仍成立。

本脚本对**同一组输入**分别求:
    M1_simplified / M0_simplified   —— city_model (代表日 + 周期缩放)
    M1_daily      / M0_daily        —— daily_model.daily_city_outcome 逐日求和
并比较:
    R1 冷却物理量 (M, phi_eff, CoC) 的一致性
    R2 dS_pot 的符号与量级是否保持
    R3 若不一致, 差异来自哪种被简化掉的机制, 误差随压力条件如何变化

【口径】沿用 A13c/A17 的排放—索取平衡 (不用已撤回的 psi/Delta):
    F = M0 - (1-phi_eff)*M1 ;  C = inc_B2 - inc_B1 ;  dS_pot = C - F
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
A12 = ROOT / "A12_时间分辨率"
for p in (A10, A12):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import city_model as cm            # noqa: E402
import daily_model as dm           # noqa: E402

SAMPLES = ["IEUA RP-1 (2025, tertiary)", "LADWP AWPF (2012, RO product)",
           "Figshare RW (2025, paired study)"]
DOMS = ("ha", "co")
# 覆盖 A 态 (池用尽) 与 C 态 (有余量)
POOL_SCALES = (1.0, 2.0, 3.0)
PHIS = (0.4, 0.8)
CHI = 0.5
N_DAYS = cm.N_DAYS


def simplified(dom: str, sample: str, ps: float, phi: float, cache: dict) -> dict:
    """代表日 + 周期缩放 (city_model 口径), 周期 = 730 天."""
    r1 = cm.city_outcome(dom, "B_full", sample, pool_scale=ps, gap_scale=1.0,
                         dp_scale=0.0, ai_target=phi, limit_scale=CHI,
                         period_days=N_DAYS, cache=cache)
    r0 = cm.city_outcome(dom, "B_full", sample, pool_scale=ps, gap_scale=1.0,
                         dp_scale=0.0, ai_target=0.0, limit_scale=CHI,
                         period_days=N_DAYS, cache=cache)
    F = r0["M_ml"] - (1.0 - r1["phi_eff"]) * r1["M_ml"]
    C = max(0.0, r0["inc_reclaimed_ml"] - r1["inc_reclaimed_ml"])
    return {"model": "simplified", "M0": r0["M_ml"], "M1": r1["M_ml"],
            "phi_eff": r1["phi_eff"], "CoC": r1["CoC_ai"],
            "inc_B2": r0["inc_reclaimed_ml"], "inc_B1": r1["inc_reclaimed_ml"],
            "x_ai": r1["x_ai_ml"], "F": F, "C": C, "dS_pot": C - F,
            "status": r1["status"]}


def daily_sum(dom: str, sample: str, ps: float, phi: float, cache: dict) -> dict:
    """逐日求和 (daily_model 口径). 池/缺口按日摊分, 与年度版同口径."""
    bl = cm.BASELINES[dom]
    elig = bl["P0"] + bl["gap"]
    pool_total = bl["P0"] * float(ps)
    ts = dm.load_ts(dom)
    q = dm.sample_quality("B_full", sample)
    dates = pd.to_datetime(ts["date"])
    n = len(ts)
    pool_day = pool_total / n
    gap_day = bl["gap"] / n

    # 逐日: 先求 phi=0 的当日外部补水 (= E * g), 再求两个情景
    # ⚠ 修正 (2026-10-14): 原版用 r0.get("E_day", r0["M_ml"]) 取蒸发,
    #   但 daily_city_outcome 不返回 E_day -> 退化成用 M(phi=0) 当 e_ref,
    #   导致 e_ref 被放大 g 倍 (实测 ratio 1.60), 全部结果失真。
    #   正确做法: e_ref_day 必须是**当日蒸发 E**, 而 E 需从 calculate_data_center_plan 取。
    from aiuwm.data_center import calculate_data_center_plan as _cdcp
    import copy as _copy
    agg = {k: 0.0 for k in ("M0", "M1", "inc_B2", "inc_B1", "x_ai", "E0")}
    cocs, phis, st = [], [], []
    for i in range(n):
        row = ts.iloc[i]
        drv = dm.drivers_row(row, "ai_load_factor_a30")
        d = dates.iloc[i]
        try:
            # 当日蒸发 E: 用与 ev_ai 相同的构造, 但直接读 evaporation_ml
            comp = dm.comp_for(dom, "B_full", 0.0, "evaporative", CHI,
                               "ai_load_factor_a30")
            comp["water_sources"]["reclaimed"]["target_fraction"] = 0.0
            comp["water_sources"]["potable"]["target_fraction"] = 1.0
            p0 = _cdcp(comp, pd.Timestamp(d), drv, reclaimed_available_ml=0.0,
                       reclaimed_quality_mg_l=q)
            e0 = float(p0.evaporation_ml)
            r0b = dm.daily_city_outcome(dom, sample, d, drv, q, m0_day=0.0,
                                        pool_day=pool_day, gap_day=gap_day,
                                        dp_day=0.0, ai_target=0.0,
                                        limit_scale=CHI, e_ref_day=e0,
                                        period_days=1.0, cache=cache)
            r1b = dm.daily_city_outcome(dom, sample, d, drv, q, m0_day=0.0,
                                        pool_day=pool_day, gap_day=gap_day,
                                        dp_day=0.0, ai_target=phi,
                                        limit_scale=CHI, e_ref_day=e0,
                                        period_days=1.0, cache=cache)
        except Exception:  # noqa: BLE001
            continue
        agg["M0"] += float(r0b["M_ml"])
        agg["M1"] += float(r1b["M_ml"])
        agg["inc_B2"] += float(r0b["inc_reclaimed_ml"])
        agg["inc_B1"] += float(r1b["inc_reclaimed_ml"])
        agg["x_ai"] += float(r1b["x_ai_ml"])
        agg["E0"] += e0
        cocs.append(float(r1b["CoC_ai"]))
        phis.append(float(r1b["phi_eff"]))
        st.append(str(r1b["status"]))

    F = agg["M0"] - (1.0 - (agg["x_ai"] / agg["M1"] if agg["M1"] > 0 else 0.0)) * agg["M1"]
    C = max(0.0, agg["inc_B2"] - agg["inc_B1"])
    return {"model": "daily", "M0": agg["M0"], "M1": agg["M1"],
            "phi_eff": (agg["x_ai"] / agg["M1"]) if agg["M1"] > 0 else 0.0,
            "CoC": float(np.mean(cocs)) if cocs else np.nan,
            "inc_B2": agg["inc_B2"], "inc_B1": agg["inc_B1"],
            "x_ai": agg["x_ai"], "F": F, "C": C, "dS_pot": C - F,
            "status": f"n_days={len(cocs)}"}


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 78)
    rec("A20 模型桥接: 代表日周期模型 vs 逐日模型")
    rec("=" * 78)

    cache: dict = {}
    rows = []
    for dom in DOMS:
        for smp in SAMPLES:
            for ps in POOL_SCALES:
                for phi in PHIS:
                    s = simplified(dom, smp, ps, phi, cache)
                    try:
                        dd = daily_sum(dom, smp, ps, phi, cache)
                    except Exception as e:  # noqa: BLE001
                        rec(f"  [daily 失败] {dom} {smp} ps={ps} phi={phi}: "
                            f"{type(e).__name__}: {e}")
                        continue
                    for r in (s, dd):
                        rows.append({"domain": dom, "sample": smp, "pool_scale": ps,
                                     "phi": phi, **r})
    d = pd.DataFrame(rows)
    d.to_csv(HERE / "bridging_comparison.csv", index=False, encoding="utf-8-sig")
    rec(f"\n完成 {len(d)} 行 (每情景 2 个模型)")

    if len(d) == 0:
        raise SystemExit("全部失败")

    piv = d.pivot_table(index=["domain", "sample", "pool_scale", "phi"],
                        columns="model",
                        values=["M0", "M1", "phi_eff", "CoC", "C", "F", "dS_pot"])

    # ---------- R1: 冷却物理量一致性 ----------
    rec("\n[R1] 冷却物理量一致性 (simplified vs daily)")
    cmp = d.pivot_table(index=["domain", "sample", "pool_scale", "phi"],
                        columns="model", values=["M0", "M1", "phi_eff", "CoC", "dS_pot"])
    for q in ("M0", "M1", "phi_eff", "CoC", "dS_pot"):
        if (q, "simplified") not in cmp.columns or (q, "daily") not in cmp.columns:
            continue
        a, b = cmp[(q, "simplified")], cmp[(q, "daily")]
        ok = a.notna() & b.notna()
        if not ok.any():
            continue
        rel = ((a[ok] - b[ok]).abs() / b[ok].abs().clip(lower=1e-9))
        rec(f"  {q:9}: n={int(ok.sum()):3d}  中位相对差={rel.median():.4f}  "
            f"最大={rel.max():.4f}")

    # ---------- R2: dS_pot 符号是否保持 ----------
    rec("\n[R2] ★ dS_pot 符号一致性")
    if ("dS_pot", "simplified") in cmp.columns:
        s_sig = np.sign(cmp[("dS_pot", "simplified")].round(6))
        d_sig = np.sign(cmp[("dS_pot", "daily")].round(6))
        both = s_sig.notna() & d_sig.notna()
        agree = (s_sig[both] == d_sig[both]).mean() if both.any() else float("nan")
        rec(f"  符号一致率 = {agree:.3f}  (n={int(both.sum())})")
        rec(cmp[["dS_pot"]].round(0).to_string())

    summary = {
        "n_rows": int(len(d)),
        "models": sorted(d["model"].unique().tolist()),
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": (
            "两模型对同一输入求解; 代表日模型用 730 天周期缩放, 逐日模型逐日求和。"
            "差异来源须归因, 不得只报告'差不多'。口径为排放—索取平衡, 不用已撤回的 psi/Delta。"),
    }
    (HERE / "bridging_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    rec(f"\n完成 {summary['runtime_s']}s")
    (HERE / "a20_repro_log.txt").write_text("\n".join(log), encoding="utf-8")


if __name__ == "__main__":
    main()
