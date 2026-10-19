# -*- coding: utf-8 -*-
"""最后 19 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("One methodological consequence deserves separate mention, because it is where volume-based "
     "policy indicators lose information [6,12]: city-wide utilisation has total wastewater "
     "throughput as its denominator, so a city can report 25% while a single campus consumes that "
     "entire 25% at a ratio near 100%, fully triggering the penalty, whereas the same volume spread "
     "across a hundred small users leaves every ratio low.",
     "One methodological consequence deserves separate mention [6,12]: city-wide utilisation has "
     "wastewater throughput as its denominator, so a city can report 25% while a single campus "
     "consumes that entire 25% at a ratio near 100%, fully triggering the penalty, whereas the same "
     "volume spread over a hundred users leaves every ratio low."),
    ("A reviewer may reasonably ask what policy value a mechanism has when it does not operate in the "
     "current policy range. The criterion does not forecast any city's present state; it delimits an "
     "interval, which is useful at every stage.",
     "A reviewer may ask what policy value a mechanism has when it does not operate in the current "
     "policy range. The criterion forecasts no city's present state; it delimits an interval, useful "
     "at every stage."),
    ("This is more useful than asking whether reclaimed-water cooling is beneficial, because that "
     "answer depends on the city while the criterion makes the dependence explicit.",
     "This is more useful than asking whether reclaimed-water cooling is beneficial, because that "
     "answer depends on the city while the criterion makes the dependence explicit."),
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
