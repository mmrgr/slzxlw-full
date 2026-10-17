"""WP2-E3: 独立预测检验 —— 用【干预前可观测量】预测 dS_pot 符号.

======================================================================
【为什么这是全文最关键的方法学实验】
======================================================================
项目既有的所有"判据吻合率 = 1.0000"都用到【模拟后】的量:
    x_AI(实际取得再生水量), M0/M1(补水), C(挤占位移), CoC
用这些量去算符号再报"吻合", 是**同义反复(记账一致性)**, 不构成科学预测。

GPT 意见的核心要求(也是本项目此前完全没做的):
    只能用【干预实施前可观测】的信息去预测干预后的结果。
若预测必须输入完整模拟后的分量, 则准确率再高也不能证明存在有外部解释力的规律。

本脚本据此做严格的 E3 检验。

======================================================================
【信息集定义】
======================================================================
干预前可观测 I_pre:
  · 再生水与自来水的水化学(各约束物种浓度)  [实测可得]
  · 限值档(引用标准)与冷却塔设计 CoC        [设计可得]
  · 掺混比 phi                              [决策变量]
  · 数据中心 IT 负荷 / 蒸发量 E_tot          [设计可得]
  · 既有用户可回用需求 elig、可交付池 pool   [规划可得]

严禁作为输入(这些是模拟后的结果):
  x_AI, M0, M1, C, F, r_inc, CoC_0, CoC_1, dS_pot

======================================================================
【判据(全部只用 I_pre)】
======================================================================
闭式:  q = (CoC1 - CoC0) / (CoC1*(CoC0-1))
其中 CoC0/CoC1 由【限值与水化学】按浓缩倍数定义直接算(不跑求解器):
        CoC = min_i( limit_i / c_mix,i )
        c_mix,i = phi*c_rec,i + (1-phi)*c_pot,i
      无回用(phi=0)时 c_mix = c_pot; 有回用(phi>0)时为掺混值。

  P1 化学判据 : c_rec,i < c_pot,i (全部约束物种) => 预测 dS<0(受益)
  P2 CoC判据  : 预测 q>0 <=> CoC1>CoC0
  P3 联合     : q>0 => 受益;  否则按 rho(kappa-1) 与 q 的相对大小判
  Baseline-0  : 常数预测(多数类)
  Baseline-1  : 随机(固定种子)

======================================================================
【真值】
======================================================================
dS_pot 由引擎/主口径给出(仅用于评估, 不作为预测输入)。
从 A13 可靠子集 CSV 取真值, 与预测逐行比对。

【纪律】
  · 预测器代码路径中【不得】出现 x_ai/M0/M1/C/F/dS 作为输入(脚本内断言);
  · 报 n_eff 与零值处理约定(门禁第8条);
  · 用相对容差;
  · 诚实报告准确率, 不达标不修饰。
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
A13 = ROOT / "A13_可靠性机制"
A10 = ROOT / "A10_敏感性与边界"
sys.path.insert(0, str(A10))

# 引用限值档 (LIMIT_SET = baseline, GB/T 50050-2017 循环水)
LIMITS = {"TDS": 2200.0, "chloride": 700.0, "hardness": 750.0,
          "alkalinity": 350.0, "silica": 175.0}
# 自来水侧 (city_model.POTABLE_EXTRA + 基线)
POTABLE = {"TDS": 180.0, "chloride": 35.0, "hardness": 120.0,
           "alkalinity": 100.0, "silica": 10.0}

# ---- 预测器允许读取的输入白名单(断言用) ----
ALLOWED_INPUTS = {"sample", "phi", "pool_scale", "domain", "chi",
                  "limit_scale", "c_rec", "c_pot", "limits"}


def coc_from_chem(c_mix: dict, limits: dict) -> float:
    """由掺混化学与限值算浓缩倍数上限 (只用 I_pre).

    CoC = min_i( limit_i / c_mix_i )  —— 任一物种先触限即决定 CoC.
    """
    vals = []
    for k, lim in limits.items():
        c = c_mix.get(k)
        if c is None:
            continue
        if c <= 0:
            return float("inf")   # 该物种不约束
        vals.append(lim / c)
    return float(min(vals)) if vals else float("inf")


def predict_row(rec_chem: dict, phi: float) -> dict:
    """核心预测器: 输入仅为干预前信息(再生水化学 + phi)."""
    c_mix = {}
    for k in LIMITS:
        cr = rec_chem.get(k)
        cp = POTABLE.get(k)
        if cr is None:
            cr = 0.0            # 缺失按 0 (偏差方向: 使水样显得更干净)
        if cp is None:
            continue
        c_mix[k] = phi * cr + (1.0 - phi) * cp

    coc_mix = coc_from_chem(c_mix, LIMITS)
    coc_pot = coc_from_chem(dict(POTABLE), LIMITS)

    # P1: 全部约束物种中, 再生水是否都更干净
    present = [k for k in LIMITS if rec_chem.get(k) is not None]
    all_cleaner = all(rec_chem[k] < POTABLE[k] for k in present) if present else False

    # P2/P3: q 的符号 <=> CoC1 > CoC0
    q_pos = bool(coc_mix > coc_pot) if np.isfinite(coc_mix) else False

    return {
        "coc_calc_0": coc_pot if phi == 0 else coc_pot,
        "coc_calc_1": coc_mix,
        "P1_all_cleaner": bool(all_cleaner),
        "P2_q_pos": q_pos,
        # P1 与 P2 一致的预测(联合): 用 q 判据(它含限值信息, 更强)
        "P3_pred_benefit": bool(q_pos),
        "n_present_species": len(present),
    }


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 84)
    rec("WP2-E3  独立预测检验: 仅用【干预前可观测量】预测 dS_pot 符号")
    rec("=" * 84)

    # ---------- 0. 载入权威水样化学 ----------
    import city_model as cm
    samp = cm.load_samples()
    chem = {}
    for _, row in samp.iterrows():
        src = str(row["source"])
        d = {}
        for k in LIMITS:
            v = row.get(k)
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                d[k] = float(v)
        chem[src] = d
    rec("\n[0] 权威水样化学 (city_model.load_samples())")
    for k, v in chem.items():
        rec(f"  {k:<52} 物种数={len(v):>2}  缺失={sorted(set(LIMITS)-set(v))}")

    # ---------- 1. 真值数据 ----------
    df = pd.read_csv(A13 / "supply_state_regimes.csv")
    rel = df[(df["status"] == "converged_unique")
             & (~df["coc_floor_degenerate"].astype(bool))].copy()
    rec(f"\n[1] 真值: A13 可靠子集 n={len(rel)} (双门禁)")
    rec(f"    零值约定: 严格符号; 落入 |dS|<=1e-9 者单列")
    rel["ds_sign"] = np.where(rel["dS_pot_ml"] < -1e-9, "benefit",
                       np.where(rel["dS_pot_ml"] > 1e-9, "harm", "zero"))
    rec(f"    符号分布: {rel['ds_sign'].value_counts().to_dict()}")

    # ---------- 2. 逐行预测(只用 I_pre) ----------
    rec("\n[2] 逐行预测 (输入仅: 水样化学 + phi + 限值; 断言不含模拟后量)")
    rec("    ⚠ 断言: 预测函数签名只接受 (rec_chem, phi), 无法访问 x_ai/M0/M1/C/F/dS")
    import inspect
    sig = inspect.signature(predict_row)
    assert set(sig.parameters) == {"rec_chem", "phi"}, "预测器签名泄露了其它输入!"
    rec(f"    预测器签名 = {sig} ✓")

    rows = []
    for _, r in rel.iterrows():
        smp = r["sample"]
        rc = chem.get(smp)
        if rc is None or len(rc) == 0:
            continue
        pr = predict_row(rc, float(r["phi"]))
        rows.append({
            "domain": r["domain"], "sample": smp, "phi": float(r["phi"]),
            "pool_scale": float(r["pool_scale"]),
            "ds_pot": float(r["dS_pot_ml"]), "ds_sign": r["ds_sign"],
            "n_species": pr["n_present_species"],
            "P1_all_cleaner": pr["P1_all_cleaner"],
            "P2_q_pos": pr["P2_q_pos"],
            "P3_pred_benefit": pr["P3_pred_benefit"],
            "coc_calc_0": pr["coc_calc_0"], "coc_calc_1": pr["coc_calc_1"],
        })
    P = pd.DataFrame(rows)
    rec(f"    可预测行数 = {len(P)}")

    # ---------- 3. 准确率 ----------
    rec("\n[3] ★ 准确率 (目标: 预测 'benefit' 与 'harm' 二分类, 排除 zero)")
    ev = P[P["ds_sign"] != "zero"].copy()
    ev["truth_benefit"] = ev["ds_sign"] == "benefit"
    rec(f"    评估样本 n_eff = {len(ev)}  (排除 zero = {len(P)-len(ev)})")
    rec(f"    基准率(多数类) = {max(ev['truth_benefit'].mean(), 1-ev['truth_benefit'].mean()):.4f}")

    def acc(pred_col):
        a = (ev[pred_col] == ev["truth_benefit"])
        tp = int(((ev[pred_col]) & (ev["truth_benefit"])).sum())
        fp = int(((ev[pred_col]) & (~ev["truth_benefit"])).sum())
        fn = int(((~ev[pred_col]) & (ev["truth_benefit"])).sum())
        tn = int(((~ev[pred_col]) & (~ev["truth_benefit"])).sum())
        return float(a.mean()), tp, fp, tn, fn

    rec(f"\n    {'预测器':<34} {'准确率':>8} {'TP':>5} {'FP':>5} {'TN':>5} {'FN':>5}")
    results = {}
    for name, col in (("P1 化学(全部物种更干净)", "P1_all_cleaner"),
                      ("P2 q>0 (CoC判据)", "P2_q_pos"),
                      ("P3 联合(=P2)", "P3_pred_benefit")):
        a, tp, fp, tn, fn = acc(col)
        results[name] = {"acc": a, "tp": tp, "fp": fp, "tn": tn, "fn": fn}
        rec(f"    {name:<34} {a:8.4f} {tp:5d} {fp:5d} {tn:5d} {fn:5d}")

    # 基线
    base_major = max(ev["truth_benefit"].mean(), 1 - ev["truth_benefit"].mean())
    rng = np.random.default_rng(20261016)
    rand_acc = float((rng.random(len(ev)) < ev["truth_benefit"].mean()
                      ).mean() if len(ev) else float("nan"))
    rec(f"    {'B0 常数(多数类)':<34} {base_major:8.4f}")
    rec(f"    {'B1 随机(seed=20261016)':<34} {rand_acc:8.4f}")

    # ---------- 4. 按水样分解(完整 vs 不完整) ----------
    rec("\n[4] 按水样分解 (P3 预测器)")
    rec(f"    {'sample':<40} {'物种':>4} {'n':>5} {'acc':>8} 完整性")
    by = []
    for smp, g in ev.groupby("sample"):
        ns = int(g["n_species"].iloc[0])
        a = float((g["P3_pred_benefit"] == g["truth_benefit"]).mean())
        comp = "COMPLETE(5)" if ns >= 5 else f"INCOMPLETE({ns})"
        by.append({"sample": smp, "n_species": ns, "n": len(g), "acc": a,
                   "completeness": comp})
        rec(f"    {smp:<40} {ns:>4} {len(g):>5} {a:8.4f} {comp}")

    # ---------- 5. 裁定 ----------
    rec("\n[5] ★ 裁定")
    p3 = results["P3 联合(=P2)"]["acc"]
    p1 = results["P1 化学(全部物种更干净)"]["acc"]
    best = max(p3, p1)
    rec(f"    多数类基线 = {base_major:.4f}")
    rec(f"    最佳预测器准确率 = {best:.4f}")
    if best > base_major + 0.05:
        rec(f"    ⇒ 预测器【优于】多数类基线 {best-base_major:+.4f} ⇒ 具备干预前预测能力")
        verdict = "PREDICTIVE"
    elif best > base_major:
        rec(f"    ⇒ 仅【略优】于基线 {best-base_major:+.4f} ⇒ 预测能力有限")
        verdict = "WEAKLY_PREDICTIVE"
    else:
        rec("    ⇒ 未优于多数类基线 ⇒ **不构成独立预测**")
        rec("      应如实写为'记账一致性检验', 不得称为规律/预测")
        verdict = "NOT_PREDICTIVE"

    rec("\n[6] 诚实性声明")
    rec("    本检验的预测器 CoC 由【化学+限值】闭式算出, 未调用求解器;")
    rec("    但其与引擎 CoC 的差异(例如缺内部回收/储冷)会限制准确率,")
    rec("    该差异本身即结构性不确定性的度量, 应一并报告。")

    summary = {
        "purpose": "仅用干预前可观测量预测 dS_pot 符号, 区分'记账一致性'与'独立预测'",
        "input_whitelist": sorted(ALLOWED_INPUTS),
        "forbidden_inputs": ["x_ai_B1_ml", "M0_ml", "M1_ml", "C_ml", "F_ml",
                             "dS_pot_ml", "dS_ident_ml", "phi_eff", "CoC_ai"],
        "predictor_signature_only": ["rec_chem", "phi"],
        "n_all_reliable": int(len(P)),
        "n_eff_excluding_zero": int(len(ev)),
        "majority_baseline_acc": float(base_major),
        "random_baseline_acc": rand_acc,
        "predictors": results,
        "by_sample": by,
        "verdict": verdict,
        "limits_used": LIMITS, "potable_used": POTABLE,
        "zero_convention": "strict sign; |dS|<=1e-9 excluded as zero",
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": "预测器不接受任何模拟后量; 报 n_eff; 相对容差",
    }
    (HERE / "wp2_e3_independent_prediction_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    P.to_csv(HERE / "wp2_e3_predictions.csv", index=False, encoding="utf-8-sig")
    (HERE / "wp2_e3_log.txt").write_text("\n".join(log), encoding="utf-8")
    rec(f"\n[write] wp2_e3_independent_prediction_summary.json / _predictions.csv / _log.txt "
        f"({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
