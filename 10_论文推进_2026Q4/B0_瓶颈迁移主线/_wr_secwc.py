# -*- coding: utf-8 -*-
"""按 ### 小节统计词数，定位可压缩段落。"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
MS = Path(__file__).resolve().parent / "04_wr_manuscript_en.md"
t = MS.read_text(encoding="utf-8")


def wc(s: str) -> int:
    s = re.sub(r"\$[^$]*\$", " MATH ", s)
    return len(s.split())


parts = re.split(r"^(#{2,3}\s+.+)$", t, flags=re.M)
rows = []
for i in range(1, len(parts), 2):
    head = parts[i].strip()
    body = parts[i + 1] if i + 1 < len(parts) else ""
    rows.append((head, wc(body)))
rows.sort(key=lambda r: -r[1])
print(f"{'小节':<58}{'words':>7}")
print("-" * 66)
for h, n in rows:
    if n > 60:
        print(f"{h[:56]:<58}{n:>7}")
print("-" * 66)
print(f"{'合计':<58}{sum(n for _, n in rows):>7}")
