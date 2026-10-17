"""修正 SI S10 取代表 (2026-10-17)."""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SI = Path(__file__).resolve().parent.parent / "A16_英文稿/supplementary_information.md"

PAIRS = [
    ("cited limits and the dual gate the authoritative figures are **369 of 372, with 3\n   exceptions**.",
     "cited limits and the dual gate the authoritative figures are **380 of 391, with 11\n   exceptions**."),
    ("**−0.0733** under the cited limit set; the old figures came from the pre-A27 placeholder",
     "**−0.0682** under the cited limit set; the old figures came from the pre-A27 placeholder"),
]

t = SI.read_text(encoding="utf-8")
n = 0
for a, b in PAIRS:
    if a in t:
        t = t.replace(a, b, 1)
        n += 1
    else:
        print(f"  MISS: {a[:70]}")
SI.write_text(t, encoding="utf-8")
print(f"替换 {n}/{len(PAIRS)}")
for s in ("369 of 372", "−0.0733**"):
    print(f"  残留 {s!r}: {s in t}")
