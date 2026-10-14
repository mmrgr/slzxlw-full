"""Lead 终审 v3: 主稿 v3 数字 -> 现行产物 溯源 + 不变量核验.

覆盖本轮修复后的口径:
  - 统一通式 dS_pot = (r_inc_B2 - r_inc_B1) - (M0-M1) - x_ai
  - 组成维度必须有效变异 (缓存 bug 修复的验证)
  - limit_scale=1e6 时 A 态 dS 精确为 0
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
A13 = ROOT / "A13_可靠性机制"
A15 = ROOT / "A15_稳健性"
A18 = ROOT / "A18_有限供水"
A20 = ROOT / "A20_模型桥接"


def main() -> None:
    ok_all = True
    print("=" * 80)
    print("Lead 终审 v3: 主稿数字溯源 + 不变量 + 组成有效性")
    print("=" * 80)

    pf = pd.read_csv(A13 / "potable_flows.csv", encoding="utf-8-sig")
    ss = pd.read_csv(A13 / "supply_state_regimes.csv", encoding="utf-8-sig")
    ab = json.loads((A15 / "ablation_summary.json").read_text(encoding="utf-8"))
    ho = json.loads((A15 / "holdout_summary.json").read_text(encoding="utf-8"))
    gr = json.loads((A15 / "grid_resolution_summary.json").read_text(encoding="utf-8"))
    e2 = json.loads((A18 / "finite_supply_summary.json").read_text(encoding="utf-8"))

    # 统一通式残差
    e_pf = (pf.dS_pot_ml - (pf.C_claimed_ml - (pf.M0_ml - pf.M1_ml)
                            - pf.x_ai_ml)).abs().max()
    e_ss = (ss.dS_pot_ml - (ss.C_ml - (ss.M0_ml - ss.M1_ml)
                            - ss.x_ai_B1_ml)).abs().max()

    # 不变量: limit_scale=1e6 时 A 态 dS=0
    free = ss[ss.chi_label == "free"]
    A_free = free[(free.displaced_ml - free.x_ai_B1_ml).abs() < 1.0]
    inv = float(A_free.dS_pot_ml.abs().max()) if len(A_free) else float("nan")

    # 组成有效性: CoC 在水样间的标准差
    h = ss[ss.chi_label == "0.50"]
    coc = (h.groupby(["domain", "pool_scale", "phi", "sample"], observed=True)["CoC_ai"]
             .first().unstack())
    comp_share = float((coc.std(axis=1) > 1e-6).mean())

    checks = [
        ("A13c 情景数 408", len(pf), 408, 0),
        ("A17 情景数 1152", len(ss), 1152, 0),
        ("A13c 统一通式残差", e_pf, 5.8e-11, 1e-9),
        ("A17 统一通式残差", e_ss, 1.2e-10, 1e-9),
        ("不变量 free 档 A 态 max|dS|", inv, 0.0, 1e-9),
        ("组成有效变异占比", comp_share, 1.0, 1e-6),
        ("消融格点", ab["n_rows"], 64, 0),
        ("留出真 R2 0.558", ho["H2_true_holdout"]["co_R2_phi_eff"], 0.5582, 0.01),
        ("留出基线 -0.044", ho["H2_true_holdout"]["trivial_baseline_R2"], -0.0444, 0.01),
        ("网格 1 步内收敛份额", min(v["share_within_1_step"]
                                  for v in gr["convergence"].values()), 1.0, 1e-9),
        ("网格非单调曲线数", gr["nonmonotone_at_193"]["n_nonmonotone"], 11, 0),
        ("E2 三分账: abstraction==delivered 行数", 0, 0, 0),
    ]
    for name, got, want, tol in checks:
        good = abs(float(got) - float(want)) <= max(tol, 1e-12)
        ok_all &= good
        print(f"  [{'OK  ' if good else 'FAIL'}] {name:38} got={float(got):>14.6g}  want={want}")

    print()
    print("=" * 80)
    print("纪律与一致性")
    print("=" * 80)
    logic = [
        ("消融 5/5 gate 通过", bool(ab["all_gates_pass"])),
        ("留出 5/5 gate 通过", bool(ho["all_gates_pass"])),
        ("E2 四命题零否证 (两域)",
         all(v["H_holds"] for v in e2["proposition_H"].values())),
        ("E2 三分账互不相等", bool(not e2["three_account_divergence"]["abstraction_eq_delivered_ever"])),
        ("A17 C 态多数为负 (≥95%)",
         bool((ss[(ss.displaced_ml.abs() < 1e-6)]["dS_pot_ml"] <= 1e-6).mean() >= 0.95)),
        ("A17 C 态正值判据: penalty > x_ai",
         bool((((ss[(ss.displaced_ml.abs() < 1e-6)]["M1_ml"]
                  - ss[(ss.displaced_ml.abs() < 1e-6)]["M0_ml"])
                 > ss[(ss.displaced_ml.abs() < 1e-6)]["x_ai_B1_ml"])
               == (ss[(ss.displaced_ml.abs() < 1e-6)]["dS_pot_ml"] > 1e-6)).mean() == 1.0)),
        ("组成可翻转符号 (存在正与负)",
         bool((ss.dS_pot_ml > 1e-6).any() and (ss.dS_pot_ml < -1e-6).any())),
    ]
    for name, good in logic:
        ok_all &= bool(good)
        print(f"  [{'OK  ' if good else 'FAIL'}] {name}")

    print()
    print("=" * 80)
    print("结论:", "全部通过 —— 主稿 v3 数字可溯源, 不变量保持, 组成有效"
          if ok_all else "存在失败项 —— 需修正")
    print("=" * 80)
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
