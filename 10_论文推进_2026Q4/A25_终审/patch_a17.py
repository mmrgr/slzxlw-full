"""A25 修复脚本: 修补 A17 supply_state_regimes.py 的两处缺陷.

【缺陷 1】critical_pool_scale 用错公式
  现值: elig/P0 = (P0+gap)/P0         (与实测零挤占吻合率仅 0.78)
  正确: 零挤占 <=> pool >= gap + x_ai_B1
        ⇒ 门槛 pool_scale* = gap/P0 + x_ai_B1/P0  (随 phi/chi/水样变化)
  修正: 报告真实门槛的分布(min/median/max), 并保留旧值但明确标注为"非门槛"。

【缺陷 2】未按求解器状态过滤
  1152 情景中 58 个为 no_convergence / non_unique, 其分配量退化为 0,
  但仍产出 displaced/dS 等派生量, 污染头条统计。
  修正: 新增 reliable 子集统计, 并在 summary 中同时报告两者。
"""
from __future__ import annotations

from pathlib import Path

p = (Path(__file__).resolve().parent.parent / "A13_可靠性机制"
     / "supply_state_regimes.py")
s = p.read_text(encoding="utf-8")

# ---------- 1. 修正临界边界报告段 ----------
old4 = '''    # ---------- 4. 临界边界可预测性 ----------
    rec("\\n[4] 状态边界是否由外生量决定")
    for dom in DOMS:
        crit = elig_of(dom) / cm.BASELINES[dom]["P0"]
        rec(f"  D-{dom.upper()}: 理论临界 pool_scale = elig/P0 = {crit:.3f}")
        s = d[d["domain"] == dom]
        trans = s.groupby("pool_scale")["state_by_alloc"].agg(
            lambda x: ",".join(sorted(set(x))))
        rec(f"    实测: {trans.to_dict()}")
'''
new4 = '''    # ---------- 4. 临界边界可预测性 (A25 修正) ----------
    # A25 审计发现: 旧值 elig/P0 = (P0+gap)/P0 与实测零挤占仅 ~0.78 吻合, 不是 surplus 门槛。
    # 正确判据: 零挤占 ⟺ pool >= gap + x_ai_B1 ⇒ pool_scale* = gap/P0 + x_ai_B1/P0。
    rec("\\n[4] 状态边界是否由外生量决定 (A25 已修正)")
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
'''
assert old4 in s, "§4 段未匹配"
s = s.replace(old4, new4)

# ---------- 2. summary: 替换 critical_pool_scale + 增加 reliable 统计 ----------
old_crit_line = '''        "critical_pool_scale": {dm: float(elig_of(dm) / cm.BASELINES[dm]["P0"])
                                for dm in DOMS},'''
new_crit = '''        # A25 修正: 旧值保留但明确标注为"非门槛"; 真实门槛见 threshold_audit.
        "critical_pool_scale_OLD_NOT_A_THRESHOLD": {
            dm: float(elig_of(dm) / cm.BASELINES[dm]["P0"]) for dm in DOMS},
        "surplus_threshold_true": thr_true_all,
        "reliable_subset": _reliable_stats(d),'''
assert old_crit_line in s, "critical_pool_scale 行未匹配"
s = s.replace(old_crit_line, new_crit)

# ---------- 3. 插入 _reliable_stats 辅助函数 ----------
helper = '''

def _reliable_stats(d) -> dict:
    """A25: 只统计求解器可靠(converged_unique)的情景, 并报告未收敛数。

    未收敛情景的分配量退化为 0, 但仍会产出 displaced/dS 等派生量, 必须剔除。
    """
    import pandas as _pd
    st = d["status"].astype(str) if "status" in d.columns else _pd.Series(["?"] * len(d))
    ok = d[st == "converged_unique"]
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
        "note": ("头条统计须以 reliable 子集为准; 未收敛情景的分配量为 0, 派生量不可用。"),
    }
'''
s = s.replace("\n\ndef main() -> None:", helper + "\n\ndef main() -> None:")

p.write_text(s, encoding="utf-8")
print("[patched] supply_state_regimes.py")
print("  - §4 临界边界改为真实判据 + 新旧吻合率对照")
print("  - summary: critical_pool_scale -> 标注为非门槛 + surplus_threshold_true")
print("  - summary: 新增 reliable_subset 统计")
