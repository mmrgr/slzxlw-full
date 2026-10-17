"""修正分支统计数字 (2026-10-17). 用原始字符串避免 \\r 转义。"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"
t = P.read_text(encoding="utf-8")

PAIRS = [
    ("| 232 cases; both signs occur |", "| 234 cases; both signs occur |"),
    ("| negative in **369 of 372** cases |", "| negative in **380 of 391** cases |"),
]

n = 0
for a, b in PAIRS:
    if a in t:
        t = t.replace(a, b, 1)
        n += 1
    else:
        print(f"  MISS: {a[:50]}")

P.write_text(t, encoding="utf-8")
print(f"替换 {n}/{len(PAIRS)}")

import re
for i, l in enumerate(t.split("\n"), 1):
    if re.search(r"\d+ cases|negative in \*\*", l):
        print(f"  {i}: {l.strip()[:110]}")
