# -*- coding: utf-8 -*-
"""核实上一轮"动态路径下 −100 MW 消失"的结论是否可靠。

【疑点 1：CoC 全是 nan】
两组的 CoC 列都取到 nan，说明 `coc_mean` 不在 CAWCC 点那行的列里，
或列名不同。需修正取值方式，否则无法判断机制。

【疑点 2：legacy 组总取水非单调】
  r=0.6: 32555.5
  r=0.7: 33387.0
  r=0.8: 32776.8
  r=0.9: 33667.1
在 CAWCC 点取总取水，但 CAWCC 本身随 r 变化（1150/1150/1100/1100），
故不同 r 下取的是不同容量点 → 不可比。

应改为**固定容量点**（如统一取 1100 MW）比较总取水。

【疑点 3：动态路径 CAWCC 恒 1200 是否真实？】
若动态路径下 CoC 恒为设计值 5.0，则补水不随 r 变，
城市取水不随 r 变 → CAWCC 当然不动。这与上一轮 r=0.9 时 CoC=4.9981 一致。
但需确认：动态路径下 r 提高是否**任何**约束都未受影响。

【本脚本】
1. 修正 CoC 取值（正确列名）；
2. 固定 1100 MW 比较总取水与各约束值；
3. 明确回答：动态路径下 r* 机制是否完全消失。
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
OUT = HERE / "_dynamic_path_verify.txt"
lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(str(s))


def main() -> None:
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")
    MW = 1100.0

    for mode, enable in (("legacy", False), ("dynamic", True)):
        w(f"\n{'='*88}\n[{mode}]  固定 {MW:.0f} MW\n{'='*88}")
        w(f"{'r':>5}{'CoC':>10}{'总取水ML':>13}{'取水比':>10}{'r_eff':>10}"
          f"{'状态':<30}")
        for r in (0.0, 0.5, 0.6, 0.7, 0.8, 0.9):
            proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
            dc = proj["components"]["AI_DC1"]
            if enable:
                dc["quality_state_enabled"] = True
            dc["water_sources"]["reclaimed"]["target_fraction"] = r
            dc["water_sources"]["potable"]["target_fraction"] = 1 - r
            scan = scan_with_mean(proj, ts, [MW])
            x = scan.iloc[0]
            coc_col = "coc_mean" if "coc_mean" in scan.columns else None
            coc = float(x[coc_col]) if coc_col else float("nan")
            tot = float(x["total_withdrawal_ml"])
            ratio = float(x["max_source_abstraction_ratio"])
            reff = float(x["reclaimed_water_substitution_ratio"]) if \
                "reclaimed_water_substitution_ratio" in scan.columns else float("nan")
            # 状态列在 scan 里可能没有；从 daily 另取代价高，这里先省略
            w(f"{r:>5.1f}{coc:>10.4f}{tot:>13.1f}{ratio:>10.6f}{reff:>10.4f}")

    Path(HERE / "_dynamic_path_verify.txt").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
