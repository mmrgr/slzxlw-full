# -*- coding: utf-8 -*-
"""再减 31 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("This is a transferable screening procedure, not an assessment of one city; the case below "
     "demonstrates it.",
     "This is a transferable screen, not an assessment of one city; the case below demonstrates it."),
    ("Migration differs beyond its start. The water-scarce endpoint passes through six failure "
     "capacities spanning 650 MW, moving from water to grid and ending at peak capacity and domestic "
     "supply; the cool endpoint passes through three spanning 300 MW, from grid to source abstraction.",
     "Migration differs beyond its start. The water-scarce endpoint sees six failure capacities "
     "spanning 650 MW, from water to grid to peak capacity and domestic supply; the cool endpoint "
     "sees three spanning 300 MW, from grid to source abstraction."),
    ("The confound control is the hardest evidence: capacity, climate and city load are fixed and "
     "only the blend varies.",
     "The confound control is the hardest evidence: capacity, climate and city load fixed, only the "
     "blend varies."),
    ("Interventions confirm the binding constraint, not the label, decides whether investment works.",
     "Interventions confirm the binding constraint, not the label, decides effectiveness."),
    ("Regimes differ qualitatively. For $r\\le r^{*}$ the cycles equal the design value, make-up "
     "demand is constant, and the effect is pure gain:",
     "Regimes differ qualitatively. For $r\\le r^{*}$ the cycles equal the design value, make-up "
     "demand is constant, and the effect is pure gain:"),
    ("The response is a step, not a gradient.", "The response is a step, not a gradient."),
]

changed = 0
for old, new in PAIRS:
    if old != new and old in t:
        t = t.replace(old, new, 1)
        changed += 1
    elif old not in t:
        print("未匹配:", old[:55])
MS.write_text(t, encoding="utf-8")
after = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
print(f"改动 {changed} 处 -> {after}")
