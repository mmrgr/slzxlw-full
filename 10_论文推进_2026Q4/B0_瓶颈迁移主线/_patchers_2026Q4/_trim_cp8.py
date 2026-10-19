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

OLD = "when it does not operate in the current policy range"
NEW = "when it does not operate in current policy ranges"
if OLD in t:
    t = t.replace(OLD, NEW, 1)
    MS.write_text(t, encoding="utf-8")
    print("OK 替换成功")
else:
    print("未匹配")

after = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
print(f"{before} -> {after}")
