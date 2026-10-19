# -*- coding: utf-8 -*-
"""分析 CAWCC(r)=A/f(r) 在 r=0.9 处 22.9 MW 偏差的物理来源。

【已知（1 MW 网格，非量化误差）】
  r=0.9: 真 CAWCC = 1111.76 MW；解析 A/f(r) = 1088.9 MW；差 +22.86 MW
  r=0.6: 差约 +5；r=0.7 +7；r=0.8 +9（10 MW 网格）；r=0.9 +22.9

偏差随 r 单调增大 → 解析式缺一个随 r 增长的项。

【关键线索：多物种取紧】
解析式只用了 TDS 的 CoC。但模型取 TDS 与 chloride 的**较紧者**。
TDS: r*(TDS) = 0.5532；chloride: r*(Cl) = 0.6842。
当 r > 0.6842 时，**氯化物成为更紧的约束**！

r=0.9 > 0.6842 → CoC 由氯化物决定，而非 TDS。

验证：
  CoC_TDS(0.9)    = min(5, 2200/(0.9·650+0.1·180)) = 3.6484
  CoC_Cl(0.9)     = min(5, 500/(0.9·130+0.1·35))   = 500/120.5 = 4.1494
  取紧者 = min(3.6484, 4.1494) = 3.6484（TDS 更紧）

等等——TDS 更紧，所以取 TDS 是对的。那偏差不来自这里。

【第二个候选：园区储水】
园区有 300 ML 储池。r 高时再生水需求大，储池可能放空 → 实际交付比例 < 目标 r。
但主稿已说明交付比例影响。

【第三个候选：城市取水不只是 AI 补水】
若城市源取水还包含"因 AI 排水增加而减少的污水回用"等耦合项，则非线性。

【本脚本：直接测】
在 r=0.9、CAWCC 附近，读取各分量的精确值，反算「城市取水 − AI补水」的差额，
看这个差额是否随 r 变化。
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


def main() -> None:
    proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")
    caps = [1100.0, 1120.0]

    print(f"{'r':>5}{'MW':>7}{'CoC':>9}{'总取水ML/d':>12}{'AI补水ML/d':>12}"
          f"{'非AI部分':>11}{'取水比':>9}")
    print("-" * 76)
    for r in (0.5, 0.6, 0.7, 0.8, 0.9):
        t = json.loads(json.dumps(proj))
        t["components"]["AI_DC1"]["water_sources"]["reclaimed"]["target_fraction"] = r
        t["components"]["AI_DC1"]["water_sources"]["potable"]["target_fraction"] = 1 - r
        scan = scan_with_mean(t, ts, caps)
        for _, x in scan.iterrows():
            mw = float(x["ai_capacity_mw"])
            tot = float(x["total_withdrawal_ml"]) / 730.0
            coc = float(x["coc_mean"])
            ratio = float(x["max_source_abstraction_ratio"])
            fm = f"external_makeup_ml" if "external_makeup_ml" in scan.columns else None
            mk = float(x[fm]) / 730.0 if fm else float("nan")
            # 城市源取水（从比例反推）
            CAP_SRC = 300.0  # RES1 abstraction_capacity_ml_day（HA 为 380?）
            print(f"{r:>5.1f}{mw:>7.0f}{coc:>9.4f}{tot:>12.2f}{mk:>12.2f}"
                  f"{tot-mk:>11.2f}{ratio:>9.6f}")


if __name__ == "__main__":
    main()
