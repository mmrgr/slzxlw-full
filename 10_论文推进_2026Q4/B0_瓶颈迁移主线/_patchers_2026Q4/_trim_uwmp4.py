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
    ("A corollary follows from separating the substitution ratio from capacity and production, "
     "because all three are described as expanding reclaimed-water use and they point in different "
     "directions.",
     "A corollary follows from separating the substitution ratio from capacity and production, all "
     "three described as expanding reclaimed-water use yet pointing in different directions."),
    ("This is a transferable screening procedure, not an assessment of any one city; the case below "
     "demonstrates it.",
     "This is a transferable screening procedure, not an assessment of one city; the case below "
     "demonstrates it."),
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
