# -*- coding: utf-8 -*-
"""摘要回到 <=250 词；全文回到 <=7700 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

# 摘要：压缩前中段，为末句腾出空间
AB_PAIRS = [
    ("Embedded in a daily urban water metabolism model with ten carrying-capacity constraints and "
     "forty capacity points at two synthetic endpoints, the mechanism yields $r^{*}=0.5532$, "
     "matching model output to $8.9\\times10^{-16}$.",
     "In a daily urban water metabolism model with ten carrying-capacity constraints and forty "
     "capacity points at two synthetic endpoints, the mechanism yields $r^{*}=0.5532$, matching "
     "model output to $8.9\\times10^{-16}$."),
    ("Placing $C^{*}=L/\\mathrm{CoC}_d$ relative to the two source salinities partitions cities into "
     "four regimes, two of which are reproduced.",
     "Placing $C^{*}=L/\\mathrm{CoC}_d$ relative to the two source salinities partitions cities into "
     "four regimes, two reproduced."),
    ("Under a purely physical constraint set the water-scarce endpoint loses about 100 MW of feasible "
     "capacity as $r$ rises from 0.5 to 0.9 while its grid constraint is unchanged; the cool "
     "endpoint loses none because its bottleneck is electrical.",
     "Under a purely physical constraint set the water-scarce endpoint loses about 100 MW as $r$ "
     "rises from 0.5 to 0.9 while its grid constraint is unchanged; the cool endpoint loses none "
     "because its bottleneck is electrical."),
    ("The criterion reduces to two numbers: with data centres taking 6% and 26% of potable and "
     "reclaimed supply respectively, cities whose potable-to-reclaimed ratio falls below 3.50 "
     "necessarily exceed $r^{*}$, and 13.6% of 169 California systems do; under equal shares the "
     "boundary drops to 0.81 and three systems remain below it.",
     "The criterion reduces to two numbers: with data centres taking 6% and 26% of potable and "
     "reclaimed supply, cities whose potable-to-reclaimed ratio falls below 3.50 necessarily exceed "
     "$r^{*}$ (13.6% of 169 California systems do); under equal shares the boundary falls to 0.81 "
     "and three systems remain below it."),
    ("These assessments treat the reclaimed-water substitution ratio as a free policy variable and "
     "never test whether raising it carries a cost.",
     "These assessments treat the reclaimed-water substitution ratio as a free policy variable and "
     "never test whether raising it costs anything."),
]

# 正文：回收 ~13 词
BODY_PAIRS = [
    ("The migration sequence differs in more than its starting point.",
     "The migration sequence differs beyond its starting point."),
    ("For a city far below $r^{*}$ it supplies an executable planning ceiling, since the ratio can "
     "be raised to $r^{*}$ without cost — stronger than saying a higher ratio happens to be harmless.",
     "Far below $r^{*}$ it supplies an executable planning ceiling: the ratio can be raised to "
     "$r^{*}$ without cost, stronger than saying a higher ratio happens to be harmless."),
]


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    for old, new in AB_PAIRS:
        if old in t:
            t = t.replace(old, new, 1)
        else:
            print("摘要未匹配:", old[:50])
    for old, new in BODY_PAIRS:
        if old in t:
            t = t.replace(old, new, 1)
        else:
            print("正文未匹配:", old[:50])
    MS.write_text(t, encoding="utf-8")

    m = re.search(r"^##\s+Abstract\s*$(.*?)^##\s+", t, re.M | re.S)
    ab = re.sub(r"\$[^$]*\$", " MATH ", m.group(1))
    s = re.sub(r"\$[^$]*\$", " MATH ", t)
    print("摘要词数:", len(ab.split()), "| 全文词数:", len(s.split()))


if __name__ == "__main__":
    main()
