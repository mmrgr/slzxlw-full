# -*- coding: utf-8 -*-
"""修正母稿 §3.6 第 4 点的过时陈述。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"

OLD = ("4. 要得到 50 MW 网格上的干预增益，必须重跑干预扫描于 50 MW 网格。"
       "**本文未做**，列为待办（见 §9.2 第 7 条）。")
NEW = ("4. ~~要得到 50 MW 网格上的干预增益，必须重跑干预扫描于 50 MW 网格。本文未做。~~ "
       "**已完成（2026-10-18）**：9 项干预已在 50 MW 网格重跑，基线 1150 / 1450 MW，"
       "增益 HA `leakage_minus_30pct` +150 MW、CO `grid_plus_50pct` +100 MW"
       "（见 §3.6 末段与 §9.2 第 8 条）。")

t = MS.read_text(encoding="utf-8")
if OLD in t:
    t = t.replace(OLD, NEW, 1)
    MS.write_text(t, encoding="utf-8")
    print("OK 修正 §3.6 第 4 点")
else:
    print("未匹配")
print("母稿", len(t), "字符")
