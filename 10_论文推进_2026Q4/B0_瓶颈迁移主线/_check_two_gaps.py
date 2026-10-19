# -*- coding: utf-8 -*-
"""核查两处疑似遗漏：

A. rstar_grid_convergence_table.csv 全部数值列未被引用
   → 论文的 −100/−100/−90 与零效应区数字从哪来？是否与这张表一致？

B. rstar_physical_cawcc_by_r.csv 的 physical_first_failed_mw 从未被引用
   → 而"首失效容量"是论文核心概念。论文报的是 CAWCC（最大安全容量），
     first_failed 是否 = CAWCC + 一个网格步？若是，则两者等价、无需另报。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"


def main() -> None:
    # ---------- A. 网格收敛表 ----------
    print("=" * 90)
    print("A. rstar_grid_convergence_table.csv")
    print("=" * 90)
    f = R2 / "rstar_grid_convergence_table.csv"
    d = pd.read_csv(f, encoding="utf-8-sig")
    print(d.to_string(index=False))

    print("\n=== 推算降幅（相对 r=0）===")
    for dom in d["domain"].unique():
        sub = d[d["domain"] == dom].copy()
        base = {g: float(sub[sub["target_r"] == 0][f"cawcc_{g}"].iloc[0])
                for g in ("50mw", "25mw", "10mw")}
        print(f"\n  {dom.upper()}  基线: 50mw={base['50mw']:.0f} 25mw={base['25mw']:.0f} 10mw={base['10mw']:.0f}")
        for _, x in sub.iterrows():
            drops = [float(x[f"cawcc_{g}"]) - base[g] for g in ("50mw", "25mw", "10mw")]
            print(f"    r={x['target_r']:.1f}  降幅 50/25/10 = "
                  f"{drops[0]:+.0f} / {drops[1]:+.0f} / {drops[2]:+.0f}")

    # ---------- B. first_failed vs CAWCC ----------
    print("\n" + "=" * 90)
    print("B. physical_first_failed_mw 与 physical_cawcc_mw 的关系")
    print("=" * 90)
    g = pd.read_csv(R2 / "rstar_physical_cawcc_by_r.csv", encoding="utf-8-sig")
    g["diff"] = g["physical_first_failed_mw"] - g["physical_cawcc_mw"]
    print(g[["domain", "target_r", "physical_cawcc_mw",
             "physical_first_failed_mw", "diff"]].to_string(index=False))
    print(f"\n  差值集合: {sorted(g['diff'].unique())}")
    print("  → 若差值恒为一个网格步（50 MW），则两者等价，无需另报。")


if __name__ == "__main__":
    main()
