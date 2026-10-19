# -*- coding: utf-8 -*-
"""最后 7 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("The migration sequence differs beyond its starting point.",
     "The migration sequence differs beyond its start."),
    ("Zero gain is not zero cost. The unit costs differ by a factor of 32.5, but as only one cost "
     "input has an official source we read that ratio as an order of magnitude only.",
     "Zero gain is not zero cost. The unit costs differ 32.5-fold, but as only one input has an "
     "official source we read that ratio as an order of magnitude only."),
    ("A non-informative constraint is not evidence of safety: the scan never reached it.",
     "A non-informative constraint is not evidence of safety: the scan never reached it."),
    ("The two regimes differ qualitatively.", "The regimes differ qualitatively."),
]


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    before = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    for old, new in PAIRS:
        if old in t and old != new:
            t = t.replace(old, new, 1)
        elif old not in t:
            print("未匹配:", old[:55])
    MS.write_text(t, encoding="utf-8")
    after = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    print(f"{before} -> {after}（减 {before-after}）")


if __name__ == "__main__":
    main()
