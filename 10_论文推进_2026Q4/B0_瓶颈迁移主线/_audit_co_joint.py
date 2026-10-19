# -*- coding: utf-8 -*-
"""核查：D-CO 端联合口径 CAWCC 随 r 大幅下降，但主稿只报纯物理。

【产物显示（rstar_physical_cawcc_by_r.csv）】
  co, r=0.0–0.5: joint=1450   physical=1450
  co, r=0.6    : joint=1200   physical=1450
  co, r=0.7    : joint=1000   physical=1450
  co, r=0.8    : joint=850    physical=1450
  co, r=0.9    : joint=700    physical=1400

【问题】
主稿 §5.8.2 表只报 CO 的 physical（1450 恒定），并称"诚实负结果"。
但联合口径在 CO 端从 1450 骤降到 700（r=0.9），降幅 750 MW —— 远大于 HA 端的 300 MW。
而主稿 §5.8.2 读数 3 只提到 "D-HA 在 r=0.9 时联合 800 vs 纯物理 1100，差 300 MW"，
**从未提到 CO 端的联合口径下降更大**。

这是一个实质性遗漏：读者会以为"CO 端政策口径影响小"，实际恰恰相反。
必须量化并写入。
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
    d = pd.read_csv(R2 / "rstar_physical_cawcc_by_r.csv", encoding="utf-8-sig")
    print("列名:", list(d.columns))
    print()

    # 识别列
    jc = next(c for c in d.columns if "joint" in c.lower() and "mw" in c.lower())
    pc = next(c for c in d.columns if "physical" in c.lower() and "mw" in c.lower())

    print(f"{'域':<6}{'r':>5}{'联合':>8}{'纯物理':>9}{'差':>8}")
    print("-" * 40)
    rows = []
    for _, x in d.iterrows():
        j, p = float(x[jc]), float(x[pc])
        print(f"{x['domain']:<6}{x['target_r']:>5.1f}{j:>8.0f}{p:>9.0f}{j-p:>8.0f}")
        rows.append({"domain": x["domain"], "r": float(x["target_r"]),
                     "joint": j, "physical": p, "gap": j - p})

    print("\n=== 各域联合口径的降幅（相对 r=0）===")
    for dom in ("ha", "co"):
        sub = [x for x in rows if x["domain"] == dom]
        base_j = sub[0]["joint"]
        base_p = sub[0]["physical"]
        print(f"\n  {dom.upper()}:")
        for x in sub:
            print(f"    r={x['r']:.1f}  联合 {x['joint']:>6.0f}（降 {base_j-x['joint']:>4.0f}）"
                  f"  纯物理 {x['physical']:>6.0f}（降 {base_p-x['physical']:>3.0f}）")

    # 关键对比
    ha_end = [x for x in rows if x["domain"] == "ha" and x["r"] == 0.9][0]
    co_end = [x for x in rows if x["domain"] == "co" and x["r"] == 0.9][0]
    print(f"\n=== 关键对比（r=0.9）===")
    print(f"  HA: 联合 {ha_end['joint']:.0f} vs 纯物理 {ha_end['physical']:.0f}，差 {ha_end['gap']:.0f} MW")
    print(f"  CO: 联合 {co_end['joint']:.0f} vs 纯物理 {co_end['physical']:.0f}，差 {co_end['gap']:.0f} MW")
    print(f"  → CO 端的联合-纯物理差距（{co_end['gap']:.0f}）比 HA 端（{ha_end['gap']:.0f}）"
          f"{'更大' if co_end['gap'] > ha_end['gap'] else '更小'}")
    print(f"\n  主稿 §5.8.2 读数 3 只提 HA 的 300 MW，未提 CO 的 {co_end['gap']:.0f} MW。")


if __name__ == "__main__":
    main()
