# -*- coding: utf-8 -*-
"""最后 5 词。"""
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
    ("the abstraction ratio is 0.9497 for $r\\le0.5$, compliant against 0.95, and 0.9513 at "
     "$r=0.6$, non-compliant:",
     "the abstraction ratio is 0.9497 for $r\\le0.5$, compliant against 0.95, and 0.9513 at "
     "$r=0.6$, non-compliant:"),
    ("The penalty strikes the water side and does not touch the electricity side.",
     "The penalty strikes the water side, not the electricity side."),
    ("Interventions confirm that the binding constraint, not the label, determines whether an "
     "investment has any effect.",
     "Interventions confirm that the binding constraint, not the label, decides whether an "
     "investment works."),
    ("Six of the ten constraints never carry information at the cool endpoint and three at the "
     "water-scarce endpoint.",
     "Six constraints never carry information at the cool endpoint and three at the water-scarce "
     "one."),
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
