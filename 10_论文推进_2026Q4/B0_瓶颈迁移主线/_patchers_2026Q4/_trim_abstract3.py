# -*- coding: utf-8 -*-
"""摘要再减 13 词至 <=250。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("We show that a closed-form threshold exists above which a higher ratio increases total "
     "cooling make-up demand.",
     "We show a closed-form threshold above which a higher ratio increases total make-up demand."),
    ("Placing $C^{*}=L/\\mathrm{CoC}_d$ relative to the two source salinities partitions cities into "
     "four regimes, two reproduced.",
     "Placing $C^{*}=L/\\mathrm{CoC}_d$ against the two source salinities partitions cities into four "
     "regimes, two reproduced."),
    ("The criterion reduces to two numbers: with data centres taking 6% and 26% of potable and "
     "reclaimed supply, cities whose potable-to-reclaimed ratio falls below 3.50 necessarily exceed "
     "$r^{*}$ (13.6% of 169 California systems do); under equal shares the boundary falls to 0.81 "
     "and three systems remain below it.",
     "The criterion reduces to two numbers: with data centres taking 6% and 26% of potable and "
     "reclaimed supply, cities whose potable-to-reclaimed ratio falls below 3.50 exceed $r^{*}$ "
     "(13.6% of 169 California systems do); under equal shares the boundary falls to 0.81, and "
     "three systems remain below it."),
    ("Under a purely physical constraint set the water-scarce endpoint loses about 100 MW as $r$ "
     "rises from 0.5 to 0.9 while its grid constraint is unchanged; the cool endpoint loses none "
     "because its bottleneck is electrical.",
     "Under a purely physical constraint set the water-scarce endpoint loses about 100 MW as $r$ "
     "rises from 0.5 to 0.9 while its grid constraint holds; the cool endpoint loses none because "
     "its bottleneck is electrical."),
    ("Current policy ranges produce no capacity consequence, a falsifiable prediction rather than a "
     "limitation.",
     "Current policy ranges produce no capacity consequence, a falsifiable prediction not a "
     "limitation."),
]


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    for old, new in PAIRS:
        if old in t:
            t = t.replace(old, new, 1)
        else:
            print("未匹配:", old[:55])
    MS.write_text(t, encoding="utf-8")
    m = re.search(r"^##\s+Abstract\s*$(.*?)^##\s+", t, re.M | re.S)
    ab = re.sub(r"\$[^$]*\$", " MATH ", m.group(1))
    s = re.sub(r"\$[^$]*\$", " MATH ", t)
    print("摘要:", len(ab.split()), "| 全文:", len(s.split()))


if __name__ == "__main__":
    main()
