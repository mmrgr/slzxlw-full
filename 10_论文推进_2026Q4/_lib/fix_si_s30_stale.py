"""修正 SI S3.0 中剩余的陈旧值 (2026-10-17).

用 truth_source 的实测值一次性对齐:
    no_convergence 16, non_unique 9  (原写 18/33)
    nodisp 391                        (原写 372)
    resid 4.37e-11 / 3.55e-16         (原写 2.55e-11 / 2.9e-16)
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
SI = ROOT / "A16_英文稿/supplementary_information.md"

PAIRS = [
    ("`: `no_convergence` (18) and `non_unique` (33), which exhaust the status",
     "`: `no_convergence` (16) and `non_unique` (9), which exhaust the status"),
    ("| zero-displacement | — | 372 |",
     "| zero-displacement | — | 391 |"),
    ("| identity residual (ML, relative) | — | **2.55e−11 (2.9e−16)** |",
     "| identity residual (ML, relative) | — | **4.37e−11 (3.55e−16)** |"),
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

for s in ("(18) and `non_unique` (33)", "| — | 372 |", "2.55e−11 (2.9e−16)"):
    print(f"  残留 {s!r}: {s in t}")
