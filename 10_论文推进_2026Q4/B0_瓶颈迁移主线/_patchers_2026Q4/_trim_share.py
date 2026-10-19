# -*- coding: utf-8 -*-
"""英文稿 7718 -> <=7700（需减 ~19）。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("Those two shares are a transcribed government statement rather than a first-hand measurement, "
     "as SI S7.2 sets out.",
     "Those two shares are a transcribed government statement, not a first-hand measurement "
     "(SI S7.2)."),
    ("A non-informative constraint is not evidence of safety: the scan never reached it. Two "
     "negative results matter.",
     "A non-informative constraint is not evidence of safety: the scan never reached it. Two "
     "negative results count."),
    ("The criterion becomes usable in quantities cities publish. With city potable use $P$ and "
     "reclaimed use $R$;",
     "The criterion becomes usable in quantities cities publish. With potable use $P$ and "
     "reclaimed use $R$;"),
    ("Interventions confirm the binding constraint, not the label, decides whether an investment "
     "works.",
     "Interventions confirm the binding constraint, not the label, decides whether investment "
     "works."),
    ("The confound control is the hardest evidence: capacity, climate driver and city load are fixed "
     "and only the blend varies.",
     "The confound control is the hardest evidence: capacity, climate and city load are fixed and "
     "only the blend varies."),
]


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    before = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    for old, new in PAIRS:
        if old in t:
            t = t.replace(old, new, 1)
        else:
            print("未匹配:", old[:60])
    MS.write_text(t, encoding="utf-8")
    after = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    print(f"{before} -> {after}（减 {before-after}）")


if __name__ == "__main__":
    main()
