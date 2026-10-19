# -*- coding: utf-8 -*-
"""最后 11 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

t = MS.read_text(encoding="utf-8")
before = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())

REPL = [
    ("Migration differs beyond its start. The water-scarce endpoint passes through six failure "
     "capacities spanning 650 MW, moving from the water side to the grid and ending at peak capacity "
     "and domestic supply; the cool endpoint passes through three spanning 300 MW, beginning at the "
     "grid and reaching source abstraction last.",
     "Migration differs beyond its start. The water-scarce endpoint passes through six failure "
     "capacities spanning 650 MW, moving from water to grid and ending at peak capacity and domestic "
     "supply; the cool endpoint passes through three spanning 300 MW, from grid to source abstraction."),
    ("Regimes differ qualitatively. For $r\\le r^{*}$ the cycles equal the design value, make-up "
     "demand is constant, and the effect is a pure gain:",
     "Regimes differ qualitatively. For $r\\le r^{*}$ the cycles equal the design value, make-up "
     "demand is constant, and the effect is pure gain:"),
    ("This is more useful than asking whether reclaimed-water cooling is beneficial, because that "
     "answer depends on the city while the criterion makes the dependence explicit.",
     "This beats asking whether reclaimed-water cooling is beneficial, because that answer depends "
     "on the city while the criterion makes the dependence explicit."),
]

changed = 0
for old, new in REPL:
    if old in t:
        t = t.replace(old, new, 1)
        changed += 1
    else:
        print("未匹配:", old[:55])
MS.write_text(t, encoding="utf-8")
after = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
print(f"{before} -> {after}（减 {before-after}，改动 {changed}）")
