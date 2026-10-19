# -*- coding: utf-8 -*-
"""最后 3 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("A non-informative constraint is not evidence of safety: the scan never reached it.",
     "A non-informative constraint is not evidence of safety: the scan never reached it."),
    ("Zero gain is not zero cost.", "Zero gain is not zero cost."),
    ("The regimes differ qualitatively.", "Regimes differ qualitatively."),
    ("Roughly one recycled-water system in seven would cross it given Santa Clara's 6%/26% shares.",
     "About one recycled-water system in seven would cross it given Santa Clara's 6%/26% shares."),
    ("Two gaps follow.", "Two gaps follow."),
    ("The criterion becomes usable in quantities cities already publish.",
     "The criterion becomes usable in quantities cities publish."),
]


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    before = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    changed = 0
    for old, new in PAIRS:
        if old != new and old in t:
            t = t.replace(old, new, 1)
            changed += 1
    MS.write_text(t, encoding="utf-8")
    after = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    print(f"{before} -> {after}（减 {before-after}，改动 {changed} 处）")


if __name__ == "__main__":
    main()
