# -*- coding: utf-8 -*-
"""最后 8 词。"""
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
    ("Interventions confirm that the binding constraint, not the label, decides whether an "
     "investment works.",
     "Interventions confirm the binding constraint, not the label, decides whether an investment "
     "works."),
    ("The confound control is the hardest evidence available: capacity, climate driver and city load "
     "are fixed and only the blend varies.",
     "The confound control is the hardest evidence: capacity, climate driver and city load are fixed "
     "and only the blend varies."),
    ("The migration sequence differs beyond its start.",
     "Migration differs beyond its start."),
    ("The response is a step, not a gradient.", "The response is a step, not a gradient."),
    ("Why the water-scarce endpoint loses capacity while the cool endpoint does not requires a second "
     "condition.",
     "Why the water-scarce endpoint loses capacity but the cool one does not requires a second "
     "condition."),
]

changed = 0
for old, new in REPL:
    if old != new and old in t:
        t = t.replace(old, new, 1)
        changed += 1
    elif old not in t:
        print("未匹配:", old[:55])
MS.write_text(t, encoding="utf-8")
after = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
print(f"{before} -> {after}（减 {before-after}，改动 {changed}）")
