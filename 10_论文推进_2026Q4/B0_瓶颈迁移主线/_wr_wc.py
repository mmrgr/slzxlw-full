# -*- coding: utf-8 -*-
"""快速统计 WR 稿件各节词数。"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
MS = Path(__file__).resolve().parent / "04_wr_manuscript_en.md"
t = MS.read_text(encoding="utf-8")


def wc(s: str) -> int:
    s = re.sub(r"\$[^$]*\$", " MATH ", s)
    s = re.sub(r"\\\([^)]*\\\)", " MATH ", s)
    return len(s.split())


parts = re.split(r"^(##\s+.+)$", t, flags=re.M)
print(f"{'节':<44}{'words':>8}")
print("-" * 54)
tot = 0
for i in range(1, len(parts), 2):
    head = parts[i].strip()
    body = parts[i + 1] if i + 1 < len(parts) else ""
    n = wc(body)
    tot += n
    print(f"{head[:42]:<44}{n:>8}")
print("-" * 54)
print(f"{'合计（含 Nomenclature/Abstract）':<44}{tot:>8}")
