# -*- coding: utf-8 -*-
"""用 25/10 MW 细网格数据复核 CAWCC(r) = A/f(r) 解析形式。

【为什么必须做】
50 MW 网格下，所有预测值差都 ≤ 1 个网格步 —— 但这**部分是因为粗网格本身就模糊**。
一个错误的解析式在粗网格上也可能"看起来对"（因为容差宽达 50 MW）。

细网格把容差缩小到 10 MW，才能真正检验解析式。

【做法】
从 rstar_grid_convergence_table.csv 取 25/10 MW 的 CAWCC(r)（已在前几轮算好），
用各自网格的 r=0.5 点定标 A，再预测 r>r* 各点，看误差是否 ≤ 该网格的一个步长。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"

L, CD, CP, CR = 2200.0, 5.0, 180.0, 650.0


def f_of_r(r: float) -> float:
    c = min(CD, L / (r * CR + (1 - r) * CP))
    return c / (c - 1.0)


def main() -> None:
    d = pd.read_csv(R2 / "rstar_grid_convergence_table.csv", encoding="utf-8-sig")
    ha = d[d["domain"] == "ha"].sort_values("target_r")

    grids = {"50mw": 50.0, "25mw": 25.0, "10mw": 10.0}
    results = {}

    for g, step in grids.items():
        col = f"cawcc_{g}"
        obs = {float(x["target_r"]): float(x[col]) for _, x in ha.iterrows()}
        A = obs[0.5] * f_of_r(0.5)
        print(f"\n{'='*72}")
        print(f"[{g}] 步长 {step:.0f} MW；定标 A = CAWCC(0.5)×f(0.5) = "
              f"{obs[0.5]:.0f}×{f_of_r(0.5):.4f} = {A:.1f}")
        print("=" * 72)
        print(f"{'r':>5}{'f':>8}{'预测':>10}{'实测':>8}{'差MW':>8}{'差/步长':>9}")
        print("-" * 48)
        maxrel = 0.0
        all_ok = True
        rows = []
        for r in sorted(obs):
            pred = A / f_of_r(r)
            o = obs[r]
            diff = o - pred
            rel = abs(diff) / step
            maxrel = max(maxrel, rel)
            if rel > 1.0:
                all_ok = False
            print(f"{r:>5.1f}{f_of_r(r):>8.4f}{pred:>10.1f}{o:>8.0f}{diff:>8.1f}{rel:>9.2f}")
            rows.append({"r": r, "pred": round(pred, 2), "obs": o,
                         "diff": round(diff, 2), "rel_steps": round(rel, 3)})
        print(f"\n  最大相对误差 {maxrel:.2f} 步 → "
              f"{'✅ 解析式成立' if all_ok else '❌ 解析式不成立'}")
        results[g] = {"A": round(A, 2), "max_rel_steps": round(maxrel, 3),
                      "all_within_one_step": all_ok, "rows": rows}

    print(f"\n{'='*72}")
    print("总结：解析预测 CAWCC(r)=A/f(r) 在三网格下的最大相对误差")
    print("=" * 72)
    for g, v in results.items():
        print(f"  {g:<6} max {v['max_rel_steps']:.2f} 步  "
              f"{'✅' if v['all_within_one_step'] else '❌'}")

    import json
    (HERE / "_analytic_cawcc_multigrid.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n产物：_analytic_cawcc_multigrid.json")


if __name__ == "__main__":
    main()
