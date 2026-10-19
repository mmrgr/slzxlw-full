# -*- coding: utf-8 -*-
"""核查：CO 端 10 MW 网格的基线是 1460，而不是 1450。

【发现】
rstar_grid_convergence_table.csv 中：
  ha r=0: 50mw=1200, 25mw=1200, 10mw=1200   （基线不随网格变）
  co r=0: 50mw=1450, 25mw=1450, 10mw=1460   （基线随网格 +10）

而主稿 §5.8.2 表把 CO 的纯物理 CAWCC 写成 **1450**（50 MW 网格值），
并称"基本不动"。

但若 10 MW 网格下基线是 1460，则：
  - 绝对值的网格依赖同样存在于 CO 端（+10 MW）
  - CO 端 r=0.9 的降幅在 10 MW 下为 −20 MW（不是 −50）

【为什么要紧】
主稿 §5.8.2 的网格框只讨论了 D-HA 的三网格（−100/−100/−90），
**从未给出 D-CO 的三网格数字**。而 CO 端恰恰是"负结果"的承载体，
其"基本不动"这一结论是否也经过三网格检验，论文没说。

本脚本回答：CO 的"基本不动"在三网格下是否成立。
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
    d = pd.read_csv(R2 / "rstar_grid_convergence_table.csv", encoding="utf-8-sig")
    co = d[d["domain"] == "co"]
    print("=== D-CO 三网格纯物理 CAWCC ===")
    print(co[["target_r", "cawcc_50mw", "cawcc_25mw", "cawcc_10mw"]].to_string(index=False))

    print("\n=== D-CO 端'基本不动'是否成立 ===")
    for g in ("50mw", "25mw", "10mw"):
        vals = co[f"cawcc_{g}"].tolist()
        rng = max(vals) - min(vals)
        base = vals[0]
        end = vals[-1]
        print(f"  {g:<6} 范围 {min(vals):.0f}–{max(vals):.0f}（极差 {rng:.0f}）"
              f"  r=0:{base:.0f} → r=0.9:{end:.0f}（降 {base-end:.0f}）")

    print("\n=== 与主结论（HA）对比 ===")
    ha = d[d["domain"] == "ha"]
    for g in ("50mw", "25mw", "10mw"):
        ha_drop = float(ha[f"cawcc_{g}"].iloc[0]) - float(ha[f"cawcc_{g}"].iloc[-1])
        co_drop = float(co[f"cawcc_{g}"].iloc[0]) - float(co[f"cawcc_{g}"].iloc[-1])
        print(f"  {g:<6} HA 降 {ha_drop:.0f} MW | CO 降 {co_drop:.0f} MW")

    print("\n=== 判定 ===")
    co_ranges = [float(co[f"cawcc_{g}"].max() - co[f"cawcc_{g}"].min())
                 for g in ("50mw", "25mw", "10mw")]
    print(f"  CO 端在三网格下极差 {max(co_ranges):.0f} MW，"
          f"相对于 1450 的基线为 {100*max(co_ranges)/1450:.1f}%")
    print(f"  → '基本不动' 在三网格下{'成立' if max(co_ranges) <= 100 else '不成立'}")
    print(f"\n  注意：CO 的 10 MW 基线为 {co['cawcc_10mw'].iloc[0]:.0f}，"
          f"与 50 MW 的 {co['cawcc_50mw'].iloc[0]:.0f} 差 "
          f"{co['cawcc_10mw'].iloc[0]-co['cawcc_50mw'].iloc[0]:.0f} MW。")
    print("  主稿只给了 CO 的 50 MW 值 1450，未说明其 10 MW 值为 1460。")


if __name__ == "__main__":
    main()
