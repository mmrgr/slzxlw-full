# -*- coding: utf-8 -*-
"""修正摘要末句：3.50 须连同份额比 ρ 一起报，并给出保守边界。控制在 250 词内。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

OLD_TAIL = ("The criterion collapses to two numbers: cities with potable-to-reclaimed ratios below "
            "3.50 necessarily exceed $r^{*}$; 13.6% of 169 California systems do.")
NEW_TAIL = ("The criterion reduces to two numbers: with data centres taking 6% and 26% of potable "
            "and reclaimed supply respectively, cities whose potable-to-reclaimed ratio falls below "
            "3.50 necessarily exceed $r^{*}$, and 13.6% of 169 California systems do; under equal "
            "shares the boundary drops to 0.81 and three systems remain below it.")

t = MS.read_text(encoding="utf-8")
if OLD_TAIL not in t:
    print("未匹配")
else:
    t = t.replace(OLD_TAIL, NEW_TAIL, 1)
    MS.write_text(t, encoding="utf-8")
    print("OK 摘要末句已改")

m = re.search(r"^##\s+Abstract\s*$(.*?)^##\s+", t, re.M | re.S)
ab = re.sub(r"\$[^$]*\$", " MATH ", m.group(1))
print("摘要词数:", len(ab.split()))
s = re.sub(r"\$[^$]*\$", " MATH ", t)
print("全文词数:", len(s.split()))
