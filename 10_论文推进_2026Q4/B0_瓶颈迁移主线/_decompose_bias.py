# -*- coding: utf-8 -*-
"""分解 CAWCC 解析残差：城市源取水 = 非 AI 部分 + AI 部分？

【上一轮结论】
CAWCC(r) = A/f(r) 在 r=0.9 处偏低 22.86 MW，偏差随 r 单调增大。
候选解释（我列了三条但未分解）：
  (a) 再生水交付比例 < 目标 r（园区储水/产能限制）
  (b) 园区储水调蓄
  (c) 多物种取紧耦合

【本条思路：直接看"城市源取水"的组成】
在固定容量 MW 下，随 r 增大：
  - AI 补水 M(r) 上升（因 CoC 下降）
  - 但 AI 取用的**自来水部分** = (1−r)·M(r)
若城市源取水 ≈ 非AI基础 + (1−r)·M(r)，则 (1−r) 项会部分抵消 M 的上升。
用 1 MW 网格在 CAWCC 附近测这三项，即可判断哪一项主导。
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
OUT = HERE / "_bias_decompose.txt"
lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(str(s))


def main() -> None:
    proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")

    # 先看 scan 有哪些可用列
    t0 = json.loads(json.dumps(proj))
    t0["components"]["AI_DC1"]["water_sources"]["reclaimed"]["target_fraction"] = 0.9
    t0["components"]["AI_DC1"]["water_sources"]["potable"]["target_fraction"] = 0.1
    s0 = scan_with_mean(t0, ts, [1100.0])
    w("=== scan 可用列 ===")
    for c in s0.columns:
        w("  " + c)

    caps = [1100.0, 1111.0, 1120.0]
    w("\n\n=== 三个容量点 × 五个 r ===")
    for mw in caps:
        w(f"\n--- {mw:.0f} MW ---")
        w(f"{'r':>5}{'取水比':>10}{'总取水':>11}{'自来水':>10}{'再生水':>10}"
          f"{'AI补水':>10}{'(1-r)M':>10}{'非AI':>10}")
        for r in (0.5, 0.7, 0.8, 0.9):
            t = json.loads(json.dumps(proj))
            t["components"]["AI_DC1"]["water_sources"]["reclaimed"]["target_fraction"] = r
            t["components"]["AI_DC1"]["water_sources"]["potable"]["target_fraction"] = 1 - r
            d = scan_with_mean(t, ts, [mw])
            x = d.iloc[0]
            ratio = float(x.get("max_source_abstraction_ratio", float("nan")))
            tot = float(x.get("total_withdrawal_ml", float("nan"))) / 730.0
            fw = float(x.get("freshwater_withdrawal_ml", float("nan"))) / 730.0
            rw = float(x.get("reclaimed_water_use_ml", float("nan"))) / 730.0
            mk_col = next((c for c in d.columns if "makeup" in c.lower()
                           and "external" in c.lower()), None)
            mk = float(x[mk_col]) / 730.0 if mk_col else float("nan")
            w(f"{r:>5.1f}{ratio:>10.6f}{tot:>11.2f}{fw:>10.2f}{rw:>10.2f}"
              f"{mk:>10.2f}{(1-r)*mk:>10.2f}{tot-(1-r)*mk:>10.2f}")

    OUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
