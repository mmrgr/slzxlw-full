# -*- coding: utf-8 -*-
"""最后 1 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

t = MS.read_text(encoding="utf-8")
before = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
OLD = "The criterion becomes usable in quantities cities publish."
NEW = "The criterion becomes usable in quantities cities publish."
# 删一个 'the'：找到 "the relative tightness of the recycled subsystem"
OLD2 = "what constrains the blend is the relative tightness of the recycled subsystem rather than total volume."
NEW2 = "what constrains the blend is the tightness of the recycled subsystem rather than total volume."
if OLD2 in t:
    t = t.replace(OLD2, NEW2, 1)
    MS.write_text(t, encoding="utf-8")
    print("OK")
else:
    print("未匹配，尝试备选")
    for cand in ("in the current policy range", "at the water-scarce endpoint and 1600 MW"):
        if cand in t:
            print("  可用候选:", cand)
after = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
print(f"{before} -> {after}")
