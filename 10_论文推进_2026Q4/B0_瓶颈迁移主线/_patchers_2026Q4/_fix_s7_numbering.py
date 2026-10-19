# -*- coding: utf-8 -*-
"""修正 SI S7 节内重复编号：第二个 S7.8 改为 S7.9。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
SI = HERE / "05_wr_supplementary_en.md"

t = SI.read_text(encoding="utf-8")
old = "### S7.8 Cleaning rules and their effect"
new = "### S7.9 Cleaning rules and their effect"
if old in t:
    t = t.replace(old, new, 1)
    SI.write_text(t, encoding="utf-8")
    print("OK S7.8(第二处) -> S7.9")
else:
    print("未匹配")

import re
heads = re.findall(r"^### (S\d+\.\d+)", t, flags=re.M)
print("S7 系列:", [h for h in heads if h.startswith("S7")])
