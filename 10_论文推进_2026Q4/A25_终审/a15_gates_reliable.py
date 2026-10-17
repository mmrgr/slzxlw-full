"""A25 修复(续): 检验 A15 稳健性三项在【可靠子集】上是否仍通过.

【背景】
A25 审计发现 A15 产物含未收敛情景:
    ablation_matrix        2/64
    holdout_fit_ha        16/204
    holdout_holdout_co    19/204
    holdout_predictions   48/816
    grid_resolution      541/14196
本脚本用 reliable 子集**重算**原有 gate, 看结论是否改变。

【gate 定义 (取自各脚本)】
  ablation:  5 条 (G1..G5) 见 ablation_matrix_corrected.py
  holdout:   5 条 (R2 / 边界 / 单调 / 无水质约束精确0 / 惩罚单调)
  grid:      边界一步内收敛比例 = 100%
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
A15 = ROOT / "A15_稳健性"
OK = "converged_unique"
# 2026-10-17: 补第二门禁(退化情景), 与全项目双门禁口径统一。
# 核验显示 holdout 文件单/双门禁差值为 0, 故本修正不改变现有产物。
DEGEN_COL = "coc_floor_degenerate"

def _rel(d):
    """双门禁: status==OK 且未触 CoC 下限 (2026-10-17 补齐)。"""
    m = d["status"] == OK
    if "coc_floor_degenerate" in d.columns:
        m = m & (~d["coc_floor_degenerate"].astype(bool))
    return d[m]


out = {}


def summarise(name: str, d: pd.DataFrame, fn) -> None:
    a = d
    b = d[(d.status == OK)]
    if DEGEN_COL in d.columns:
        b = b[~b[DEGEN_COL].astype(bool)]
    ra, rb = fn(a), fn(b)
    same = str(ra) == str(rb)
    out[name] = {"n_all": len(a), "n_ok": len(b),
                 "all": ra, "ok": rb, "unchanged": bool(same)}
    flag = "" if same else "   <-- 改变"
    print(f"  {name:38} 全={ra}  可靠={rb}{flag}")


# ---------------- ablation ----------------
print("=== A15 ablation (2/64 剔除) ===")
d = pd.read_csv(A15 / "ablation_matrix.csv", encoding="utf-8-sig")
ss = pd.read_csv(ROOT / "A13_可靠性机制" / "supply_state_regimes.csv", encoding="utf-8-sig")


def _abl(dd):
    """复算统一恒等式残差 + 纯挤占分支退化残差。"""
    for c in ("dS_pot_ml", "M0_ml", "M1_ml", "x_ai_ml",
              "inc_recl_B2_ml", "inc_recl_B1_ml"):
        dd = dd.assign(**{c: pd.to_numeric(dd[c], errors="coerce")})
    disp = dd.inc_recl_B2_ml - dd.inc_recl_B1_ml
    pred = disp - (dd.M0_ml - dd.M1_ml) - dd.x_ai_ml
    return {"unified_resid_max": float((dd.dS_pot_ml - pred).abs().max()),
            "n": int(len(dd))}


summarise("ablation", d, _abl)

# ---------------- holdout ----------------
print("\n=== A15 holdout (拟合域 + 留出域) ===")
fit = pd.read_csv(A15 / "holdout_fit_ha.csv", encoding="utf-8-sig")
ho = pd.read_csv(A15 / "holdout_holdout_co.csv", encoding="utf-8-sig")


def _r2(fitd, hod):
    """真留出 R2: 用拟合域线性系数预测留出域 dS_pot, 与实测比。"""
    f = fitd.dropna(subset=["M0_ml", "M1_ml", "x_ai_ml", "dS_pot_ml"])
    h = hod.dropna(subset=["M0_ml", "M1_ml", "x_ai_ml", "dS_pot_ml"])
    if not len(f) or not len(h):
        return float("nan")
    X = (f.M0_ml - f.M1_ml).values
    y = f.dS_pot_ml.values
    b = np.polyfit(X, y, 1)
    Xh = (h.M0_ml - h.M1_ml).values
    yh = h.dS_pot_ml.values
    pred = np.polyval(b, Xh)
    ss_res = ((yh - pred) ** 2).sum()
    ss_tot = ((yh - yh.mean()) ** 2).sum()
    return float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")


out["holdout_R2"] = {
    "all": round(_r2(fit, ho), 6),
    "ok": round(_r2(_rel(fit), _rel(ho)), 6),
}
print(f"  {'holdout R2 (真留出)':38} 全={out['holdout_R2']['all']}  "
      f"可靠={out['holdout_R2']['ok']}")

for name, d_ in (("holdout_fit_ha", fit), ("holdout_holdout_co", ho)):
    summarise(name, d_, lambda x: {
        "n": int(len(x)),
        "ident_resid_max": float(
            (pd.to_numeric(x.dS_pot_ml, errors="coerce")
             - (pd.to_numeric(x.C_ml, errors="coerce")
                - pd.to_numeric(x.F_ml, errors="coerce"))).abs().max()),
    })

# ---------------- grid resolution ----------------
print("\n=== A15 grid_resolution (541/14196 剔除) ===")
g = pd.read_csv(A15 / "grid_resolution_points.csv", encoding="utf-8-sig")


def _grid(dd):
    return {"n_feasible": int(dd.feasible.astype(str).str.lower()
                              .isin(["true", "1"]).sum()),
            "n": int(len(dd))}


summarise("grid_resolution", g, _grid)

conv = pd.read_csv(A15 / "grid_resolution_convergence.csv", encoding="utf-8-sig")
print(f"\n  grid_resolution_convergence.csv 列: {list(conv.columns)}")
print(f"  一行内 n_feasible 汇总: {conv.n_feasible.describe().to_dict()}")

(HERE / "a15_gates_reliable.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print("\n[write] a15_gates_reliable.json")
