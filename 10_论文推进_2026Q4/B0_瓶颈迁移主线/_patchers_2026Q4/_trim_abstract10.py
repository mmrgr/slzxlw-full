# -*- coding: utf-8 -*-
"""摘要最后 1 词：删 'the'。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

t = MS.read_text(encoding="utf-8")
OLD = "with equal shares the boundary falls to 0.81 and three systems remain below it."
NEW = "with equal shares the boundary falls to 0.81 and three systems remain below."
if OLD in t:
    t = t.replace(OLD, NEW, 1)
    MS.write_text(t, encoding="utf-8")
    print("OK")
else:
    print("未匹配")

m = re.search(r"^##\s+Abstract\s*$(.*?)^##\s+", t, re.M | re.S)
ab = re.sub(r"\$[^$]*\$", " MATH ", m.group(1))
s = re.sub(r"\$[^$]*\$", " MATH ", t)
print(f"摘要 {len(ab.split())} | 全文 {len(s.split())}")
