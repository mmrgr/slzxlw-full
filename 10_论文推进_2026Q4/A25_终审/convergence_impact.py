"""A25 审计: 求解器收敛缺陷的系统性影响量化.

【缺陷】
  多个产物把【求解器未收敛/多解】的情景计入头条统计。
  未收敛情景的特征: 分配量退化为 0, 但仍计算出 displaced/dS 等派生量。

  实测各产物的不可靠行数:
    supply_state_regimes (A17)  58/1152 =  5.0%
    potable_flows        (A13c) 35/408  =  8.6%
    ablation_matrix      (A15)   2/64   =  3.1%
    holdout_fit_ha       (A15)  16/204  =  7.8%
    holdout_holdout_co   (A15)  19/204  =  9.3%
    holdout_predictions  (A15)  48/816  =  5.9%
    grid_resolution      (A15) 541/14196=  3.8%

【本脚本】
  对每个产物计算: 全样本 vs 仅可靠样本 的关键统计量, 判断头条结论是否改变。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = {}

RELIABLE = {"converged_unique", "ok"}


def load(rel: str, status_col: str = "status") -> pd.DataFrame:
    d = pd.read_csv(ROOT / rel, encoding="utf-8-sig")
    d["_ok"] = d[status_col].astype(str).isin(RELIABLE)
    return d


def report(name: str, d: pd.DataFrame, metrics: dict[str, callable]) -> None:
    a, b = d, d[d["_ok"]]
    print(f"\n=== {name} ===")
    print(f"  全样本 n={len(a)}  可靠 n={len(b)}  (剔除 {len(a)-len(b)})")
    row = {"n_all": int(len(a)), "n_ok": int(len(b)),
           "n_excluded": int(len(a) - len(b)),
           "share_excluded_pct": round((len(a) - len(b)) / max(len(a), 1) * 100, 2)}
    for label, fn in metrics.items():
        try:
            va, vb = fn(a), fn(b)
            same = (str(va) == str(vb))
            row[label] = {"all": va, "ok": vb, "unchanged": same}
            mark = "" if same else "   <-- 改变"
            print(f"    {label:34} 全={va}   可靠={vb}{mark}")
        except Exception as e:  # noqa: BLE001
            print(f"    {label:34} 计算失败: {e}")
    OUT[name] = row


# ---------------- A17 ----------------
d17 = load("A13_可靠性机制/supply_state_regimes.csv")
d17["q"] = (d17.M0_ml - d17.M1_ml) / d17.M1_ml
report("A17 supply_state_regimes", d17, {
    "n_dS_neg": lambda x: int((x.dS_pot_ml < -1e-6).sum()),
    "n_dS_pos": lambda x: int((x.dS_pot_ml > 1e-6).sum()),
    "n_zero_disp": lambda x: int((x.displaced_ml.abs() < 1e-6).sum()),
    "n_xai_zero": lambda x: int((x.x_ai_B1_ml.abs() < 1e-9).sum()),
    "n_q_pos": lambda x: int((x.q > 1e-9).sum()),
    "n_qpos_but_harmful": lambda x: int(((x.q > 1e-9) & (x.dS_pot_ml > 1e-6)).sum()),
    "identity_resid_max": lambda x: float(
        (x.dS_pot_ml - (x.displaced_ml - (x.M0_ml - x.M1_ml) - x.x_ai_B1_ml)).abs().max()),
    "criterion_agreement": lambda x: round(float(
        (((x.x_ai_B1_ml + (x.M0_ml - x.M1_ml)) > x.displaced_ml) == (x.dS_pot_ml < -1e-6)).mean()), 6),
})

# ---------------- A13c ----------------
d13 = load("A13_可靠性机制/potable_flows.csv")
rep = {}
if {"M0_ml", "M1_ml"}.issubset(d13.columns):
    rep["n_rows"] = lambda x: int(len(x))
# 检查有哪些列
print("\n[A13c potable_flows 列]", list(d13.columns)[:24])
for cand in ("dS_pot_ml", "C_claimed_ml", "x_ai_ml", "M0_ml", "M1_ml", "phi"):
    if cand in d13.columns:
        rep[f"mean_{cand}"] = (lambda c: (lambda x: round(float(x[c].mean()), 3)))(cand)
report("A13c potable_flows", d13, rep)

# ---------------- A15 ablation ----------------
dab = load("A15_稳健性/ablation_matrix.csv")
rep_ab = {}
for c in dab.columns:
    if "gate" in c.lower() or "pass" in c.lower():
        rep_ab[f"all_{c}"] = (lambda c: (lambda x: bool(x[c].astype(str).str.lower()
                                                       .isin(["true", "1"]).all())))(c)
report("A15 ablation_matrix", dab, rep_ab or {"n_rows": lambda x: int(len(x))})

# ---------------- A15 holdout ----------------
for f in ("holdout_fit_ha.csv", "holdout_holdout_co.csv"):
    d = load(f"A15_稳健性/{f}")
    rep = {}
    for c in d.columns:
        if "gate" in c.lower() or "pass" in c.lower():
            rep[f"all_{c}"] = (lambda c: (lambda x: bool(x[c].astype(str).str.lower()
                                                          .isin(["true", "1"]).all())))(c)
    report(f"A15 {f}", d, rep or {"n_rows": lambda x: int(len(x))})

# ---------------- A15 grid resolution ----------------
dg = load("A15_稳健性/grid_resolution_points.csv")
report("A15 grid_resolution_points", dg, {
    "n_rows": lambda x: int(len(x)),
    "n_feasible": lambda x: int(x.get("feasible", pd.Series(dtype=bool)).astype(str)
                               .str.lower().isin(["true", "1"]).sum())
    if "feasible" in dg.columns else lambda x: -1,
})

(HERE / "convergence_impact.json").write_text(
    json.dumps(OUT, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print("\n[write] convergence_impact.json")
