# -*- coding: utf-8 -*-
"""探查：CAWCC 的 r 依赖能否用解析方法预测？

【动机】
论文已证明 r* 的**阈值位置**是解析的（8.9e-16 精度）。
但**效应量 −100 MW** 完全来自引擎输出，没有解析解释。

若能解析预测 CAWCC(r) 并复现 −100 MW，则论证从"模型演示"升级为"解析可预测"。

【思路】
D-HA 的首失效约束是 max_source_abstraction_ratio ≤ 0.95：
    city_source_abstraction(MW, r) / source_capacity = 0.95
故 CAWCC(r) 是使该等式成立的最大 MW。

若源取水可分解为：
    city_source_abstraction = 城市基础取水(与 MW 无关) + 园区补水(MW, r)
其中园区补水 = E(MW) × CoC(r)/(CoC(r)−1)，E ∝ MW

则：
    base + k·MW·f(r) = 0.95 · CAP
    → MW*(r) = (0.95·CAP − base) / (k·f(r))

即 **CAWCC(r) 应与 1/f(r) 成正比**，f(r) = CoC/(CoC−1)。
这是一个可直接检验的解析预测。

【本脚本】
1. 从 rstar_scan_ha.csv 提取各 r 下 CAWCC 与 CoC；
2. 检验 CAWCC(r)·f(r) 是否为常数（解析预测）；
3. 若成立，用两个 r 点定标预测其余点，比较误差。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"


def main() -> None:
    # ---- 读扫描与 CAWCC ----
    scan_f = R2 / "rstar_scan_ha.csv"
    caw_f = R2 / "rstar_physical_cawcc_by_r.csv"
    if not scan_f.exists() or not caw_f.exists():
        print("缺产物")
        for p in (scan_f, caw_f):
            print("  ", p, p.exists())
        return

    scan = pd.read_csv(scan_f, encoding="utf-8-sig")
    caw = pd.read_csv(caw_f, encoding="utf-8-sig")
    caw = caw[caw["domain"] == "ha"].sort_values("target_r")
    print("=== D-HA 纯物理 CAWCC 与 CoC ===")
    print(caw[["target_r", "physical_cawcc_mw", "physical_limiting_constraint"]].to_string(index=False))

    print(f"\n=== scan 列（{len(scan.columns)}）===")
    cols = [c for c in scan.columns if any(k in c.lower() for k in
            ("withdraw", "abstract", "makeup", "coc", "capacity", "total"))]
    print(cols)

    print(f"\n=== scan 中 r 取值 ===")
    if "target_r" in scan.columns:
        print(sorted(scan["target_r"].unique()))

    # ---- 在 CAWCC 容量点上取该约束的实际值 ----
    print(f"\n=== 在各自 CAWCC 点上，水源取水比的实测值 ===")
    print(f"{'r':>5}{'CAWCC':>8}{'该点取水比':>12}{'上一网格点取水比':>16}")
    for _, row in caw.iterrows():
        r = float(row["target_r"])
        mw = float(row["physical_cawcc_mw"])
        sub = scan[(scan["target_r"] == r)]
        if sub.empty:
            continue
        # 找 CAWCC 点与下一点
        col = next((c for c in sub.columns if "mean_source_abstraction" in c), None)
        if col is None:
            col = next((c for c in sub.columns
                        if "source" in c.lower() and "ratio" in c.lower()), None)
        if col is None:
            print(f"  找不到取水比列，候选: "
                  f"{[c for c in sub.columns if 'ratio' in c.lower()][:8]}")
            break
        at = sub[np.isclose(sub["ai_capacity_mw"], mw)]
        prev = sub[np.isclose(sub["ai_capacity_mw"], mw - 50)]
        v_at = float(at[col].iloc[0]) if len(at) else float("nan")
        v_prev = float(prev[col].iloc[0]) if len(prev) else float("nan")
        print(f"{r:>5.1f}{mw:>8.0f}{v_at:>12.6f}{v_prev:>16.6f}")


if __name__ == "__main__":
    main()
