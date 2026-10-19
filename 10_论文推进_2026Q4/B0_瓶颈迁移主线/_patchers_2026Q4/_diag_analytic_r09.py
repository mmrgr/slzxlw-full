# -*- coding: utf-8 -*-
"""诊断：为何 r=0.9 的解析误差最大（10 MW 网格下 21 MW）？

【观察】
10 MW 网格：预测 1088.9，实测 1110，差 +21.1（2.11 步）。
其余各点误差 ≤ 0.91 步。误差在 r=0.9 处突然放大。

【候选解释】
1. **r=0.9 时首失效约束可能改变**。
   主稿说 HA 的纯物理首失效始终是 max_source_abstraction_ratio。
   若在 10 MW 网格下 r=0.9 的首失效变成别的约束，则解析式（基于取水比）失效。

2. **弃水/回用反馈**：高 r 时再生水不够用，实际交付比例 < 目标，
   使有效 CoC 高于解析 CoC，从而取水偏少、CAWCC 偏高。

3. **storage 缓冲**：园区储水在低容量时未饱和，在高容量时饱和，非线性介入。

【检验方式】
直接读 10 MW 网格在 r=0.9 附近的逐点取水比，看它在哪个容量越过 0.95，
以及该点的实际 delivered r 与 CoC 是否偏离解析值。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:/Users/mmrgr/Desktop/论文/算力中心/07_代码_AI-UWM引擎/aiuwm_src")
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from run_r2 import scan_with_mean  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
HERE = Path(__file__).resolve().parent
CAP10 = list(np.arange(1000, 1250, 10, dtype=float))


def main() -> None:
    proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")

    for r in (0.8, 0.9):
        t = json.loads(json.dumps(proj))
        t["components"]["AI_DC1"]["water_sources"]["reclaimed"]["target_fraction"] = r
        t["components"]["AI_DC1"]["water_sources"]["potable"]["target_fraction"] = 1 - r
        scan = scan_with_mean(t, ts, CAP10)
        print(f"\n{'='*78}\n r = {r}   （10 MW 网格，1000–1240 MW）\n{'='*78}")
        cols = ["ai_capacity_mw", "coc_mean", "max_source_abstraction_ratio"]
        cols += [c for c in ("actual_reclaimed_fraction",) if c in scan.columns]
        print(scan[[c for c in cols if c in scan.columns]].to_string(index=False))

        # 找首次越过 0.95
        over = scan[scan["max_source_abstraction_ratio"] > 0.95]
        if not over.empty:
            print(f"\n  首次越过 0.95 的容量: {over['ai_capacity_mw'].iloc[0]:.0f} MW")
            prev = scan[scan["ai_capacity_mw"] < over["ai_capacity_mw"].iloc[0]]
            if not prev.empty:
                print(f"  上一点 ({prev['ai_capacity_mw'].iloc[-1]:.0f} MW) 取水比: "
                      f"{prev['max_source_abstraction_ratio'].iloc[-1]:.6f}")
            print(f"  该点取水比: {over['max_source_abstraction_ratio'].iloc[0]:.6f}")
        # 实际 delivered r
        if "actual_reclaimed_fraction" in scan.columns:
            print(f"\n  实际交付再生水比例（在 CAWCC 附近）: ")
            sub = scan[(scan["ai_capacity_mw"] >= 1080) & (scan["ai_capacity_mw"] <= 1200)]
            print(sub[["ai_capacity_mw", "actual_reclaimed_fraction",
                       "coc_mean"]].to_string(index=False))


if __name__ == "__main__":
    main()
