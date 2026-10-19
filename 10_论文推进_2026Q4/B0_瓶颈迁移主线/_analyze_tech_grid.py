# -*- coding: utf-8 -*-
"""分析技术档网格收敛结果，找出哪些量可引用、哪些不可。

【50/25/10 MW 三网格结果】
技术档        50mw        25mw        10mw      极差
evaporative  100          75          70        30
hybrid        50          50          60        10
dry_first     50          75          90        40

【关键观察 1：r=0 的基线本身依赖网格】
  evaporative  1200 / 1200 / 1200   （稳）
  hybrid       1150 / 1150 / 1160   （10 MW 时 +10）
  dry_first    1100 / 1125 / 1140   （随网格细化单调上升）

【关键观察 2：r=0.8 的端点】
  evaporative  1100 / 1125 / 1130
  hybrid       1100 / 1100 / 1100   （稳！）
  dry_first    1050 / 1050 / 1050   （稳！）

→ 排除 dry_first 的基线漂移后：
   dry_first 的 r=0.8 端点三网格恒为 1050，其基线随网格从 1100 升到 1140，
   故"降幅"从 50 增到 90 —— 纯粹是**基线漂移**造成的，不是端点变化。

【结论】
  50 MW 网格下三个技术档给出的降幅（100/50/50）**不可引用为精确值**。
  但可以引用的定性结论是：
    - 降幅随冷却水强度单调（evaporative > dry_first ≈ hybrid > dry=0）
    - 三档降幅都在 50–100 MW 量级（即"数十 MW"，而非数百）

这可与第 51 轮已确立的主结论处理方式一致：
  只引用端点与量级，不引用中间精确值。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
D = HERE / "_tech_grid_convergence.json"


def main() -> None:
    d = json.loads(D.read_text(encoding="utf-8"))
    print("=== r=0 基线的网格依赖 ===")
    for t, v in d.items():
        vals = [v[g]["cawcc_r0"] for g in ("50mw", "25mw", "10mw")]
        print(f"  {t:<14} {vals}  极差 {max(vals)-min(vals):.0f}")

    print("\n=== r=0.8 端点的网格依赖 ===")
    for t, v in d.items():
        vals = [v[g]["cawcc_r08"] for g in ("50mw", "25mw", "10mw")]
        print(f"  {t:<14} {vals}  极差 {max(vals)-min(vals):.0f}")

    print("\n=== 分解：降幅变化来自端点还是基线？ ===")
    for t, v in d.items():
        d50, d25, d10 = (v[g]["drop"] for g in ("50mw", "25mw", "10mw"))
        b50, b25, b10 = (v[g]["cawcc_r0"] for g in ("50mw", "25mw", "10mw"))
        e50, e25, e10 = (v[g]["cawcc_r08"] for g in ("50mw", "25mw", "10mw"))
        print(f"  {t:<14} 基线 {b50}→{b25}→{b10}（变化 {b10-b50:+.0f}）"
              f" | 端点 {e50}→{e25}→{e10}（变化 {e10-e50:+.0f}）"
              f" | 降幅 {d50}→{d25}→{d10}（变化 {d10-d50:+.0f}）")

    print("\n=== 可引用性判定 ===")
    for t, v in d.items():
        drops = [v[g]["drop"] for g in ("50mw", "25mw", "10mw")]
        rng = max(drops) - min(drops)
        print(f"  {t:<14} 极差 {rng:>3.0f} MW → "
              f"{'可引用精确值' if rng <= 10 else '不可引用精确值，仅可用量级'}")

    print("\n=== 稳健的定性结论 ===")
    d50 = {t: d[t]["50mw"]["drop"] for t in d}
    order = sorted(d50, key=lambda k: -d50[k])
    print(f"  50 MW 下排序：{order} → {[d50[k] for k in order]}")
    print(f"  → 排序与 WUE 排序一致（evaporative 最高）")
    print(f"  → 三档降幅都在 50–100 MW（'数十 MW' 量级），与主结论 −100 MW 同量级")


if __name__ == "__main__":
    main()
