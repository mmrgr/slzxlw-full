# -*- coding: utf-8 -*-
"""最后 9 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("A non-informative constraint is not evidence of safety: the scan never reached it. Two of these "
     "negative results are substantive.",
     "A non-informative constraint is not evidence of safety: the scan never reached it. Two "
     "negative results are substantive."),
    ("Domestic unmet demand is identically zero and never informative at the cool endpoint, which is "
     "why we claim nothing about domestic supply there.",
     "Domestic unmet demand is zero and never informative at the cool endpoint, which is why we "
     "claim nothing about domestic supply there."),
    ("Cross-application is ineffective in both directions. Zero gain is not zero cost.",
     "Cross-application is ineffective both ways. Zero gain is not zero cost."),
    ("The same pattern reproduces at the cool endpoint and 1600 MW, where the abstraction ratio rises "
     "from 0.9306 to 0.9472 and treatment utilisation from 0.9503 to 0.9674 while the grid ratio "
     "remains at 1.0959.",
     "The pattern reproduces at the cool endpoint and 1600 MW, where the abstraction ratio rises from "
     "0.9306 to 0.9472 and treatment utilisation from 0.9503 to 0.9674 while the grid ratio stays at "
     "1.0959."),
]


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    before = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    for old, new in PAIRS:
        if old in t:
            t = t.replace(old, new, 1)
        else:
            print("未匹配:", old[:55])
    MS.write_text(t, encoding="utf-8")
    after = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    print(f"{before} -> {after}（减 {before-after}）")


if __name__ == "__main__":
    main()
