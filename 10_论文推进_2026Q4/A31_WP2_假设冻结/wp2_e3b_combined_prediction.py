"""WP2-E3b: 加入【干预前可得】的分配信息后, 独立预测能否成立?

======================================================================
【动机】
======================================================================
E3 已证: 仅用【水化学】(q) 预测 dS 符号的准确率 0.6712 < 多数类基线 0.8608。
诊断表明 dS/M1 = rho(kappa-1) - q, 其中 rho(kappa-1) 是【挤占/分配项】,
不由水化学决定。故仅靠化学不可能判定净符号 —— 这是结构性不可识别, 非预测器不佳。

但 dS 的符号判据(代数重排)是:
      dS < 0  <=>  x_AI + (M0 - M1)  >  挤占位移
即:  "AI 的取水 + 质量惩罚"  是否超过  "既有用户的挤占位移"。

其中两项在【干预前】部分可得:
  · pool_scale = 可交付再生水池 / 基线需求  (规划量, 干预前可得)
  · phi                                     (决策变量)
  · 水化学 => q                             (干预前可得)

故本脚本检验: 化学(q) + 分配(pool_scale) 的【联合】判据能否超过多数类基线。
若可以, 则本文拥有一个真正的 E3 级预测结果 —— 这正是 GPT 要求的"独立预测检验"。

【严格性】
  · 仍【不】使用 x_AI / M0 / M1 / C / F / dS 作为输入;
  · 允许使用 pool_scale / phi / 水化学 (均为干预前可得);
  · 报 n_eff 与零值约定;
  · 交叉验证: 按 domain 或 sample 分组做 leave-one-group-out, 防泄漏;
  · 诚实报告, 不达标不修饰。
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

LIMITS = {"TDS": 2200.0, "chloride": 700.0, "hardness": 750.0,
          "alkalinity": 350.0, "silica": 175.0}
POTABLE = {"TDS": 180.0, "chloride": 35.0, "hardness": 120.0,
           "alkalinity": 100.0, "silica": 10.0}
COC_DESIGN = 3.5   # 由 A13 基线算得(CoC_ai 上界 5.0 为引擎约束)


def coc_from_chem(c_mix: dict, limits: dict) -> float:
    vals = []
    for k, lim in limits.items():
        c = c_mix.get(k)
        if c is None or c <= 0:
            continue
        vals.append(lim / c)
    return float(min(vals)) if vals else float("inf")


def main() -> None:
    t0 = time.time()
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 84)
    rec("WP2-E3b  化学(q) + 分配(pool_scale) 联合的独立预测检验")
    rec("=" * 84)

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

    df = pd.read_csv(A13 / "supply_state_regimes.csv")
    rel = df[(df["status"] == "converged_unique")
             & (~df["coc_floor_degenerate"].astype(bool))].copy()

    # ---------- 构造【干预前】特征 ----------
    def feats(smp: str, phi: float, pool_scale: float) -> dict:
        rc = chem.get(smp, {})
        c_mix = {}
        for k, lim in LIMITS.items():
            cr = rc.get(k, 0.0)
            cp = POTABLE[k]
            c_mix[k] = phi * cr + (1 - phi) * cp
        coc1 = coc_from_chem(c_mix, LIMITS)
        coc0 = coc_from_chem(dict(POTABLE), LIMITS)
        q = ((coc1 - coc0) / (coc1 * (coc0 - 1))) if (np.isfinite(coc1) and coc0 > 1) else 0.0
        # 干预前可得的 "AI 取水量上限" 代理: phi * pool (池中我能拿到的量)
        return {"q": q, "coc1": coc1, "coc0": coc0, "phi": float(phi),
                "pool_scale": float(pool_scale),
                "phi_x_pool": float(phi) * float(pool_scale)}

    F = pd.DataFrame([feats(r["sample"], r["phi"], r["pool_scale"])
                      for _, r in rel.iterrows()])
    Y = (rel["dS_pot_ml"] < -1e-9).astype(int).values      # 1 = benefit
    zero_mask = (rel["dS_pot_ml"].abs() <= 1e-9).values
    rec(f"\n[1] 样本: n_all={len(rel)}, 评估用 n_eff={(~zero_mask).sum()} (排除 zero={zero_mask.sum()})")

    # ---------- 候选判据 ----------
    rec("\n[2] 候选判据(全部只用干预前特征)")
    cands = {
        "C1  仅化学 q>0":                     (F["q"] > 0).values,
        "C2  仅分配 pool_scale>=2":            (F["pool_scale"] >= 2).values,
        "C3  q>0 且 pool_scale>=2":            ((F["q"] > 0) & (F["pool_scale"] >= 2)).values,
        "C4  q>0 或 pool_scale>=2":            ((F["q"] > 0) | (F["pool_scale"] >= 2)).values,
        "C5  q + a*(pool_scale-1) > 0":        ((F["q"] + 0.30 * (F["pool_scale"] - 1)) > 0).values,
        "C6  phi_x_pool >= 0.8":              (F["phi_x_pool"] >= 0.8).values,
    }
    m = ~zero_mask
    majority = max(Y[m].mean(), 1 - Y[m].mean())
    rec(f"    多数类基线 = {majority:.4f}   (benefit 占比 {Y[m].mean():.4f})")
    rec(f"\n    {'判据':<36} {'准确率':>8} {'TP':>5} {'FP':>5} {'TN':>5} {'FN':>5}")
    res = {}
    best_name, best_acc = None, -1.0
    for name, pred in cands.items():
        p = pred[m]
        t = Y[m].astype(bool)
        acc = float((p == t).mean())
        tp = int((p & t).sum()); fp = int((p & ~t).sum())
        tn = int((~p & ~t).sum()); fn = int((~p & t).sum())
        res[name] = {"acc": acc, "tp": tp, "fp": fp, "tn": tn, "fn": fn}
        star = ""
        if acc > best_acc:
            best_acc, best_name = acc, name
        rec(f"    {name:<36} {acc:8.4f} {tp:5d} {fp:5d} {tn:5d} {fn:5d}{star}")
    rec(f"\n    最佳 = {best_name}  acc={best_acc:.4f}  (基线 {majority:.4f})")

    # ---------- 交叉验证: leave-one-sample-out (防泄漏) ----------
    rec("\n[3] 交叉验证: leave-one-group-out (按水样, 防数据泄漏)")
    rec("    规则: 在其余水样上选最佳判据, 在被留出水样上评估")
    names = list(cands)
    per_fold = []
    samples = rel["sample"].values
    for held in sorted(set(samples)):
        tr = m & (samples != held)
        te = m & (samples == held)
        if te.sum() == 0 or tr.sum() == 0:
            continue
        # 在训练折选最佳
        accs = {n: float((cands[n][tr] == Y[tr].astype(bool)).mean()) for n in names}
        pick = max(accs, key=accs.get)
        te_acc = float((cands[pick][te] == Y[te].astype(bool)).mean())
        base_te = max(Y[te].mean(), 1 - Y[te].mean())
        per_fold.append({"held_out": held, "picked": pick, "train_acc": accs[pick],
                         "test_acc": te_acc, "test_baseline": base_te,
                         "n_test": int(te.sum())})
        rec(f"    held={held[:34]:<36} pick={pick[:22]:<24} "
            f"train={accs[pick]:.3f} test={te_acc:.4f} base={base_te:.4f}")
    if per_fold:
        mean_test = float(np.mean([f["test_acc"] for f in per_fold]))
        mean_base = float(np.mean([f["test_baseline"] for f in per_fold]))
        rec(f"\n    折外平均准确率 = {mean_test:.4f}   折外平均基线 = {mean_base:.4f}")
        gain = mean_test - mean_base
        rec(f"    增量 = {gain:+.4f}")
    else:
        mean_test = mean_base = gain = float("nan")

    # ---------- 裁定 ----------
    rec("\n[4] ★ 裁定")
    m = ~zero_mask
    if best_acc > majority + 0.02:
        rec(f"    全样本: 最佳判据 {best_acc:.4f} > 基线 {majority:.4f} (+{best_acc-majority:.4f}) ⇒ 优于基线")
    else:
        rec(f"    全样本: 最佳判据未显著优于基线")
    if np.isfinite(gain) and gain > 0.02:
        verdict = "PREDICTIVE_OUT_OF_SAMPLE"
        rec(f"    ✓ 折外(防泄漏)仍优于基线 {gain:+.4f} ⇒ **构成独立预测**")
    elif np.isfinite(gain) and gain >= -0.02:
        verdict = "WEAK_OR_NONE"
        rec(f"    ⚠ 折外增量 {gain:+.4f} ⇒ 预测能力弱或不稳定, 不得作为主要主张")
    else:
        verdict = "NOT_PREDICTIVE"
        rec(f"    ✗ 折外劣于基线 {gain:+.4f} ⇒ 不构成独立预测")

    rec("\n[5] 诚实性声明")
    rec("    · pool_scale 是【规划量】(可交付池/需求), 干预前可得, 但真实城市未必公开;")
    rec("    · 本判据的迁移性受限于 pool_scale 的可获得性, 须在 Limitations 声明;")
    rec("    · 全样本最佳判据是【事后选择】, 故折外结果才是可信指标。")

    summary = {
        "purpose": "检验 化学(q)+分配(pool_scale) 联合判据能否构成干预前独立预测",
        "n_all": int(len(rel)), "n_eff": int(m.sum()), "n_zero_excluded": int(zero_mask.sum()),
        "majority_baseline": float(majority),
        "candidate_criteria": res,
        "best_full_sample": {"name": best_name, "acc": float(best_acc)},
        "leave_one_sample_out": per_fold,
        "oos_mean_test_acc": float(mean_test) if np.isfinite(mean_test) else None,
        "oos_mean_baseline": float(mean_base) if np.isfinite(mean_base) else None,
        "oos_gain": float(gain) if np.isfinite(gain) else None,
        "verdict": verdict,
        "forbidden_inputs_confirmed": ["x_ai_B1_ml", "M0_ml", "M1_ml", "C_ml", "F_ml", "dS_pot_ml"],
        "runtime_s": round(time.time() - t0, 1),
        "discipline_note": "预测仅用干预前特征; leave-one-group-out 防泄漏; 报 n_eff",
    }
    (HERE / "wp2_e3b_combined_prediction_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    F.assign(y=Y, zero=zero_mask).to_csv(HERE / "wp2_e3b_features.csv",
                                         index=False, encoding="utf-8-sig")
    (HERE / "wp2_e3b_log.txt").write_text("\n".join(log), encoding="utf-8")
    rec(f"\n[write] wp2_e3b_combined_prediction_summary.json / _features.csv / _log.txt "
        f"({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
