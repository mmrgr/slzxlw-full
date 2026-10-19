# -*- coding: utf-8 -*-
"""用极细网格（1 MW）确定 r=0.9 处 CAWCC 的真值，判断解析残差是否源于量化。

【现状】
10 MW 网格：r=0.9 实测 CAWCC = 1110，解析预测 1088.9，差 21.1 MW。
10 MW 网格的量化误差最多 ±10 MW，故 21 MW 的差值**超出单次量化能解释的范围**。
但这可能是因为 1110 本身是 10 MW 网格上的离散点，真值可能更接近 1100。

【做法】
在 1080–1120 区间用 1 MW 步长扫描，找到精确的首个越界容量。
那样就能判断：CAWCC 真值是 1089（支持解析式）还是 1110（否定解析式）。
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
CAP1 = list(np.arange(1060, 1141, 1, dtype=float))


def main() -> None:
    proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")
    r = 0.9
    t = json.loads(json.dumps(proj))
    t["components"]["AI_DC1"]["water_sources"]["reclaimed"]["target_fraction"] = r
    t["components"]["AI_DC1"]["water_sources"]["potable"]["target_fraction"] = 1 - r
    scan = scan_with_mean(t, ts, CAP1)

    print(f"=== r={r}，1 MW 网格（{CAP1[0]:.0f}–{CAP1[-1]:.0f} MW）===")
    print(scan[["ai_capacity_mw", "max_source_abstraction_ratio"]].to_string(index=False))

    col = "max_source_abstraction_ratio"
    over = scan[scan[col] > 0.95]
    if over.empty:
        print("\n该区间内未越界")
        return
    first_bad = float(over["ai_capacity_mw"].iloc[0])
    prev = scan[scan["ai_capacity_mw"] < first_bad]
    last_ok = float(prev["ai_capacity_mw"].iloc[-1])
    print(f"\n首个越界 = {first_bad:.0f} MW（取水比 {over[col].iloc[0]:.6f}）")
    print(f"最后一个合规 = {last_ok:.0f} MW（取水比 {prev[col].iloc[-1]:.6f}）")
    print(f"→ 真 CAWCC 落在 ({last_ok:.0f}, {first_bad:.0f}] 区间")

    # 用两点线性外推精确交点
    x1, y1 = last_ok, float(prev[col].iloc[-1])
    x2, y2 = first_bad, float(over[col].iloc[0])
    if y2 != y1:
        xc = x1 + (0.95 - y1) * (x2 - x1) / (y2 - y1)
        print(f"\n线性插值交点: {xc:.2f} MW")
        print(f"解析预测（A/f, A=1500）: 1088.9 MW")
        print(f"差: {xc-1088.9:+.2f} MW")

    (HERE / "_fine_r09.json").write_text(json.dumps({
        "r": r, "last_ok_mw": last_ok, "first_bad_mw": first_bad,
        "ratio_last_ok": float(prev[col].iloc[-1]),
        "ratio_first_bad": float(over[col].iloc[0]),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n产物：_fine_r09.json")


if __name__ == "__main__":
    main()
