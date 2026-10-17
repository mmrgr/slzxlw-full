"""Lead 终审 v2: 主稿 v2 数字 -> 产物 溯源审计 (修正版口径).

检查主稿 v2 中每个关键数字能否在**现行**产物中找到, 且恒等式/符号一致。
已作废的产物不再作为来源。
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


def main() -> None:
    ok_all = True
    print("=" * 76)
    print("Lead 终审 v2: 主稿数字溯源 + 一致性")
    print("=" * 76)

    pf = pd.read_csv(A13 / "potable_flows.csv", encoding="utf-8-sig")
    ab = pd.read_csv(A15 / "ablation_matrix.csv", encoding="utf-8-sig")
    hs = json.loads((A15 / "holdout_summary.json").read_text(encoding="utf-8"))
    asum = json.loads((A15 / "ablation_summary.json").read_text(encoding="utf-8"))
    pb = json.loads((A15 / "prior_bounds.json").read_text(encoding="utf-8"))
    gr = json.loads((A15 / "grid_resolution_summary.json").read_text(encoding="utf-8"))
    ar = json.loads((A13 / "allocation_rule_summary.json").read_text(encoding="utf-8"))

    ident = (pf["dS_pot_ml"] - (pf["M1_ml"] - pf["M0_ml"])).abs().max()
    disp = (pf["x_ai_ml"] - (pf["pool_ml"] - pf["inc_recl_ml"])).abs().max()
    d0 = ab[ab["dp_scale"] == 0.0]

    checks = [
        ("情景数 408", len(pf), 408, 0),
        ("恒等式残差 3.3e-11", ident, 3.3e-11, 1e-11),
        ("纯挤占残差 5.5e-12", disp, 5.5e-12, 1e-11),
        ("负值数 0", int((pf["dS_pot_ml"] < -1e-6).sum()), 0, 0),
        ("正值数 384", int((pf["dS_pot_ml"] > 1e-6).sum()), 384, 0),
        ("零值数 24", int((pf["dS_pot_ml"].abs() <= 1e-6).sum()), 24, 0),
        ("max dS_pot 29103", pf["dS_pot_ml"].max(), 29103.0, 1.0),
        ("消融格点 64", asum["n_rows"], 64, 0),
        ("G1 无水质 dS=0.000", hs["H3_no_quality_constraint_max_abs_dS"], 0.0, 1e-9),
        ("H2 真留出 R2 0.599", hs["H2_true_holdout"]["co_R2_phi_eff"], 0.5985, 0.002),
        ("H2 基线 -0.034", hs["H2_true_holdout"]["trivial_baseline_R2"], -0.0338, 0.002),
        ("dp=0 max 2741.1", d0["dS_pot_ml"].max(), 2741.1, 1.0),
    ]

    for name, got, want, tol in checks:
        good = abs(float(got) - float(want)) <= max(tol, 1e-12)
        ok_all &= good
        print(f"  [{'OK  ' if good else 'FAIL'}] {name:28} got={float(got):>16.6g}  want={want}")

    print()
    print("=" * 76)
    print("一致性 / 纪律检查")
    print("=" * 76)

    logic = [
        ("dS_pot >= 0 在份额口径恒成立", bool(pf["dS_pot_ml"].min() >= -1e-6)),
        ("份额口径恒等式成立 (dp=0)", bool(
            (d0["dS_pot_ml"] - d0["dS_pot_ident_ml"]).abs().max() < 1e-6)),
        ("含容量扩张口径恒等式不成立 (预期)",
         bool((ab[ab["dp_scale"] > 0]["dS_pot_ml"]
               - ab[ab["dp_scale"] > 0]["dS_pot_ident_ml"]).abs().max() > 1e3)),
        ("消融 5/5 gates 通过", bool(asum["all_gates_pass"])),
        ("留出 5/5 gates 通过", bool(hs["all_gates_pass"])),
        ("份额口径概率约 0 (先验稳健)",
         bool(pb["drift_dp0"]["max"] < 0.01)),
        ("含容量扩张概率对先验敏感 (跨度>0.2)",
         bool(pb["drift_dp1"]["span"] > 0.2)),
        ("先验组合数 = 27", bool(pb["n_configs"] == 27)),
        ("网格边界位置 100% 收敛",
         bool(all(v["share_within_1_step"] == 1.0
                  for v in gr["convergence"].values()))),
        ("无非单调可行域 (0/39)",
         bool(gr["nonmonotone_at_193"]["n_nonmonotone"] == 0)),
        ("规则敏感性: 实质情景 48",
         bool(ar["n_effective"] == 48)),
        ("规则敏感性: 纯挤占精确成立",
         bool(ar["pure_displacement_max_abs_ml"] < 1e-9)),
        ("H3 无水质约束 => 恰好 0",
         bool(hs["H3_no_quality_constraint_max_abs_dS"] == 0.0)),
        ("chi 单调 (水质越差惩罚越大)", bool(hs["H4_chi_monotone"])),
    ]
    for name, good in logic:
        ok_all &= bool(good)
        print(f"  [{'OK  ' if good else 'FAIL'}] {name}")

    print()
    print("=" * 76)
    print("结论:", "全部通过 —— 主稿 v2 数字可溯源, 逻辑一致"
          if ok_all else "存在失败项 —— 需修正")
    print("=" * 76)
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
