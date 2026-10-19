# -*- coding: utf-8 -*-
"""统一 Alameda 中位的写法（545.5）与英文正文的 r* 值（−1.0096，保持 4 位）。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
SI = HERE / "05_wr_supplementary_en.md"
MS = HERE / "04_wr_manuscript_en.md"

# SI 正文句
t = SI.read_text(encoding="utf-8")
OLD = "and the neighbouring Alameda county\nmedian is 546 mg L⁻¹."
NEW = "and the neighbouring Alameda county\nmedian is 545.5 mg L⁻¹."
if OLD in t:
    SI.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK SI 正文 546 -> 545.5")
else:
    print("SI 正文未匹配")

# 英文正文：−1.01 -> −1.0096（与表一致，避免读者对不上）
u = MS.read_text(encoding="utf-8")
OLDU = "r^{*}$ from 0.5532 to 0.0870 and to −1.01 at the neighbouring county median"
NEWU = "r^{*}$ from 0.5532 to 0.0870 and to −1.0096 at the neighbouring county median"
if OLDU in u:
    MS.write_text(u.replace(OLDU, NEWU, 1), encoding="utf-8")
    print("OK 英文 −1.01 -> −1.0096")
else:
    print("英文未匹配")
