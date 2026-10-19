# -*- coding: utf-8 -*-
"""摘要最后 1 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("The criterion reduces to two numbers: with data centres taking 6% and 26% of potable and "
     "reclaimed supply, cities whose potable-to-reclaimed ratio falls below 3.50 exceed $r^{*}$ "
     "(13.6% of 169 California systems do); under equal shares the boundary falls to 0.81 and "
     "three systems remain below it.",
     "The criterion reduces to two numbers: with data centres taking 6% and 26% of potable and "
     "reclaimed supply, cities whose potable-to-reclaimed ratio falls below 3.50 exceed $r^{*}$ "
     "(13.6% of 169 California systems do); with equal shares the boundary falls to 0.81 and three "
     "systems remain below it."),
]


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    hit = False
    for old, new in PAIRS:
        if old in t:
            t = t.replace(old, new, 1)
            hit = True
    if not hit:
        print("未匹配，改用逐字替换")
        t = t.replace("under equal shares the boundary", "with equal shares the boundary", 1)
    MS.write_text(t, encoding="utf-8")
    m = re.search(r"^##\s+Abstract\s*$(.*?)^##\s+", t, re.M | re.S)
    ab = re.sub(r"\$[^$]*\$", " MATH ", m.group(1))
    s = re.sub(r"\$[^$]*\$", " MATH ", t)
    print(f"摘要 {len(ab.split())} | 全文 {len(s.split())}")


if __name__ == "__main__":
    main()
