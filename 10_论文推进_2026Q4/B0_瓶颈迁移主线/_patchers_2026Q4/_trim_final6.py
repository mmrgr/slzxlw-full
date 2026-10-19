# -*- coding: utf-8 -*-
"""最后 5 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("The cooling constraint is the tighter of the two.",
     "The cooling constraint is the tighter."),
    ("Roughly one recycled-water system in seven would cross the threshold if it hosted data centres "
     "with Santa Clara's 6%/26% shares.",
     "Roughly one recycled-water system in seven would cross it if it hosted data centres with "
     "Santa Clara's 6%/26% shares."),
]


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    before = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    for old, new in PAIRS:
        if old in t:
            t = t.replace(old, new, 1)
        else:
            print("未匹配:", old[:50])
    MS.write_text(t, encoding="utf-8")
    after = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    print(f"{before} -> {after}（减 {before-after}）")


if __name__ == "__main__":
    main()
