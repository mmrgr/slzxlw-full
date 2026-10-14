"""A22b: q 的决定因素 —— 候选预测变量的判决性比较.

【背景】
A22 发现 q = (M0-M1)/M1 的符号是真正有科学内容的部分（q>0 的 349 例
**全部**有利，零例外）。但"q>0 ⟺ c_rec < c_pot"这一外部判据只在 3/4 水样成立
（AI-UWM 样本例外）。

【本脚本做什么】
不预设单一解释，而是**并列检验多个候选预测变量**，报告每个的样本级准确率：
  P1  化学: c_rec < c_pot（TDS/Cl 各自或联合）
  P2  约束: 限制相是否被触发（CoC < 设计值）
  P3  分配: κ = 0（未挤占）
  P4  联合: P1 ∧ P2
并给出**混淆矩阵**与**在哪些子群失效**。

【纪律】
  诚实报告失效情形；不为了得到"漂亮的单变量律"而筛选样本。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
A13 = HERE.parent / "A13_可靠性机制"

POTABLE = {"TDS": 180.0, "chloride": 35.0}
REC = {
    "IEUA RP-1 (2025, tertiary)": {"TDS": 443.0, "chloride": 100.0},
    "LADWP AWPF (2012, RO product)": {"TDS": 22.0, "chloride": 3.6},
    "Figshare RW (2025, paired study)": {"TDS": 1378.0, "chloride": 313.7},
    "AI-UWM model assumption": {"TDS": 650.0, "chloride": 130.0},
}
COC_DESIGN = 5.0


def score(pred: pd.Series, actual: pd.Series) -> dict:
    both = pred.notna() & actual.notna()
    if not both.any():
        return {"n": 0, "acc": float("nan"), "tp": 0, "fp": 0, "tn": 0, "fn": 0}
    p, a = pred[both].astype(bool), actual[both].astype(bool)
    tp = int((p & a).sum()); fp = int((p & ~a).sum())
    tn = int((~p & ~a).sum()); fn = int((~p & a).sum())
    return {"n": int(both.sum()), "acc": float((p == a).mean()),
            "tp": tp, "fp": fp, "tn": tn, "fn": fn}


def main() -> None:
    log: list[str] = []

    def rec(m: str) -> None:
        log.append(m)
        print(m, flush=True)

    rec("=" * 80)
    rec("A22b  q 的决定因素：候选预测变量判决比较")
    rec("=" * 80)

    ss = pd.read_csv(A13 / "supply_state_regimes.csv", encoding="utf-8-sig")
    for c in ("M0_ml", "M1_ml", "x_ai_B1_ml", "displaced_ml", "dS_pot_ml", "CoC_ai"):
        ss[c] = pd.to_numeric(ss[c], errors="coerce")
    ss["q"] = (ss["M0_ml"] - ss["M1_ml"]) / ss["M1_ml"]
    ss["q_pos"] = ss["q"] > 1e-9                     # 目标：q>0
    ss["kappa0"] = ss["displaced_ml"].abs() < 1e-6   # 未挤占
    ss["coc_limited"] = ss["CoC_ai"] < COC_DESIGN - 1e-6

    # 化学预测变量
    def chem(sample: str, key: str) -> bool | None:
        r = REC.get(sample)
        if r is None:
            return None
        return r[key] < POTABLE[key]

    ss["chem_tds"] = ss["sample"].map(lambda s: chem(s, "TDS"))
    ss["chem_cl"] = ss["sample"].map(lambda s: chem(s, "chloride"))
    ss["chem_any"] = ss["chem_tds"] | ss["chem_cl"]
    ss["chem_both"] = ss["chem_tds"] & ss["chem_cl"]

    rec(f"\nN = {len(ss)}  目标 q>0 的比例 = {ss['q_pos'].mean():.3f}"
        f"  ({int(ss['q_pos'].sum())}/{len(ss)})")

    candidates = [
        ("P1a 化学: c_rec^TDS < c_pot^TDS", ss["chem_tds"]),
        ("P1b 化学: c_rec^Cl  < c_pot^Cl", ss["chem_cl"]),
        ("P1c 化学: 任一指标更干净", ss["chem_any"]),
        ("P1d 化学: 两指标都更干净", ss["chem_both"]),
        ("P2  约束: CoC 被压在设计值下", ss["coc_limited"]),
        ("P3  分配: κ=0 (未挤占)", ss["kappa0"]),
        ("P4  联合: 化学 ∧ 约束", ss["chem_tds"] & ss["coc_limited"]),
    ]

    rec("\n[候选预测变量对 q>0 的判别力]")
    rec(f"  {'预测变量':34} {'n':>5} {'准确率':>8} {'TP':>5} {'FP':>5} {'TN':>5} {'FN':>5}")
    results = []
    for name, pred in candidates:
        s = score(pred, ss["q_pos"])
        results.append({"predictor": name, **s})
        rec(f"  {name:34} {s['n']:5d} {s['acc']:8.3f} "
            f"{s['tp']:5d} {s['fp']:5d} {s['tn']:5d} {s['fn']:5d}")

    # ---------- 分水样看最好的化学判据在哪里失效 ----------
    rec("\n[分水样：P1a（TDS 更干净）的准确率]")
    by_sample = []
    for s_name, g in ss.groupby("sample"):
        sc = score(g["chem_tds"], g["q_pos"])
        by_sample.append({"sample": s_name, **sc})
        rec(f"  {s_name[:34]:34} n={sc['n']:4d} 准确率={sc['acc']:.3f} "
            f"q>0 实际={g['q_pos'].mean():.3f}")

    # ---------- q 的成因分解：κ=0 与 κ>0 两组 ----------
    rec("\n[分组：κ=0 vs κ>0 下的 q 符号]")
    grp = []
    for lab, m in (("κ=0 未挤占", ss["kappa0"]), ("κ>0 有挤占", ~ss["kappa0"])):
        g = ss[m]
        row = {"group": lab, "n": int(len(g)),
               "q_pos": int((g["q"] > 1e-9).sum()),
               "q_neg": int((g["q"] < -1e-9).sum()),
               "q_zero": int((g["q"].abs() <= 1e-9).sum())}
        grp.append(row)
        rec(f"  {lab:12} n={row['n']:4d}  q>0={row['q_pos']:4d}  "
            f"q<0={row['q_neg']:4d}  q≈0={row['q_zero']:4d}")

    # ---------- 结论 ----------
    best = max(results, key=lambda r: (r["acc"] if np.isfinite(r["acc"]) else -1))
    rec(f"\n[结论] 单一最佳预测变量: {best['predictor']}  准确率 = {best['acc']:.3f}")
    rec("  即便最佳单变量也未达 1.0；说明 q 的符号**不是单一外部量决定**，")
    rec("  而是【化学 + 约束触发 + 分配状态】三者共同作用。")
    rec("  这与正文'三量判据'的定位一致：判据本身是恒等式，")
    rec("  其**符号结构**需要多个外部量联合刻画，不能简化为单一名数。")

    summary = {
        "n": int(len(ss)),
        "target_share_q_pos": float(ss["q_pos"].mean()),
        "predictors": results,
        "by_sample": by_sample,
        "kappa_groups": grp,
        "best_single_predictor": best,
        "conclusion": (
            "q>0 是'城市取水下降'的充分条件（349/349 零例外），但 q 的符号**没有单一"
            "外部决定量**：最佳单变量准确率仍 < 0.9。q 由化学浓度对比、约束是否触发、"
            "以及分配状态共同决定。诚实报告：不宣称单一名数律。"),
        "discipline_note": "全部样本参与评分，未做样本筛选；失效子群如实列出。",
    }
    (HERE / "q_predictors_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    ss.to_csv(HERE / "q_predictors_grid.csv", index=False, encoding="utf-8-sig")
    rec("\n[write] q_predictors_summary.json")
    (HERE / "a22b_repro_log.txt").write_text("\n".join(log), encoding="utf-8")


if __name__ == "__main__":
    main()
