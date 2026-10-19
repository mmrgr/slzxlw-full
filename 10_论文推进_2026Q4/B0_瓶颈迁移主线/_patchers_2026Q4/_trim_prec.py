# -*- coding: utf-8 -*-
"""压回 7700 以内（需减 ~27）。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("One methodological consequence deserves separate mention [6,12]: city-wide utilisation has "
     "wastewater throughput as its denominator, so a city can report 25% while a single campus "
     "consumes that entire 25% at a ratio near 100%, fully triggering the penalty, whereas the same "
     "volume spread over a hundred users leaves every ratio low.",
     "One consequence deserves separate mention [6,12]: city-wide utilisation has wastewater "
     "throughput as its denominator, so a city can report 25% while a single campus consumes that "
     "entire 25% at a ratio near 100%, fully triggering the penalty, whereas the same volume spread "
     "over a hundred users leaves every ratio low."),
    ("At the modelled 1000 MW scale the ratio of wastewater throughput to campus make-up is 5.28, so "
     "city-wide utilisation of 20% already permits a campus ratio above 1.0.",
     "At 1000 MW the ratio of wastewater throughput to campus make-up is 5.28, so city-wide "
     "utilisation of 20% already permits a campus ratio above 1.0."),
    ("Aggregate utilisation therefore conceals the very heterogeneity the mechanism depends on, "
     "consistent with the broader point that bottleneck location is governed by structure rather "
     "than total volume.",
     "Aggregate utilisation therefore conceals the heterogeneity the mechanism depends on, "
     "consistent with bottleneck location being governed by structure rather than total volume."),
    ("A practical corollary follows from separating the effect of the substitution ratio from the "
     "effects of capacity and production, because all three are commonly described as expanding "
     "reclaimed-water use and they point in different directions.",
     "A corollary follows from separating the substitution ratio from capacity and production, "
     "because all three are described as expanding reclaimed-water use and they point in different "
     "directions."),
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
