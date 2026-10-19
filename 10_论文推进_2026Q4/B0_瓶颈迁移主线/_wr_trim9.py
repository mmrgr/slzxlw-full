# -*- coding: utf-8 -*-
"""引用插入后回补词数：压回 7700 以内。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS: list[tuple[str, str]] = [
    (
        "Schwabe et al. describe supply-side self-consumption: indoor conservation reduces wastewater collection and shrinks the reclaimed pool downstream. Tran et al. describe quality-side deterioration: drought combined with conservation raises influent concentration and degrades effluent quality. Both mechanisms are now established reference points for adverse reuse outcomes.",
        "Schwabe et al. describe supply-side self-consumption: indoor conservation reduces wastewater collection and shrinks the reclaimed pool downstream. Tran et al. describe quality-side deterioration: drought combined with conservation raises influent concentration and degrades effluent quality.",
    ),
    (
        "This is more useful than asking whether reclaimed-water cooling is beneficial, because that answer depends on the city while the criterion makes the dependence explicit. What it does not supply is advice: reading this paper as a recommendation that a particular city set its target at 55% would exceed evidence resting on synthetic endpoints.",
        "This is more useful than asking whether reclaimed-water cooling is beneficial, because that answer depends on the city while the criterion makes the dependence explicit. What it does not supply is advice: reading this paper as a recommendation that a city set its target at 55% would exceed evidence resting on synthetic endpoints.",
    ),
    (
        "One methodological consequence deserves separate mention, because it is where volume-based policy indicators lose information [6,12]. City-wide utilisation has total wastewater throughput as its denominator, so a city can report 25% while a single campus consumes that entire 25% at a ratio near 100%, fully triggering the penalty; if the same volume is spread across a hundred small users, every ratio stays low and no penalty occurs.",
        "One methodological consequence deserves separate mention, because it is where volume-based policy indicators lose information [6,12]: city-wide utilisation has total wastewater throughput as its denominator, so a city can report 25% while a single campus consumes that entire 25% at a ratio near 100%, fully triggering the penalty, whereas the same volume spread across a hundred small users leaves every ratio low.",
    ),
]


def main() -> None:
    text = MS.read_text(encoding="utf-8")
    applied, missed = 0, []
    for old, new in PAIRS:
        if old in text:
            text = text.replace(old, new, 1)
            applied += 1
        else:
            missed.append(old[:70])
    MS.write_text(text, encoding="utf-8")
    print(f"已替换 {applied}/{len(PAIRS)}")
    for m in missed:
        print("  未匹配:", m, "…")
    s = re.sub(r"\$[^$]*\$", " MATH ", text)
    print("当前总词数:", len(s.split()))


if __name__ == "__main__":
    main()
