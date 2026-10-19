# -*- coding: utf-8 -*-
"""摘要再减 18 词至 <=250。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("Cooling AI data centres with reclaimed water is promoted as a water-saving measure whose "
     "potential is quantified. These assessments treat the reclaimed-water substitution ratio as a "
     "free policy variable and never test whether raising it costs anything.",
     "Cooling AI data centres with reclaimed water is promoted as a water-saving measure. Such "
     "assessments treat the reclaimed-water substitution ratio as a free policy variable and never "
     "test whether raising it costs anything."),
    ("Combining the cooling-tower salt balance with the design limit bounds the cycles of "
     "concentration by make-up salinity, giving",
     "The cooling-tower salt balance and the design limit bound the cycles of concentration by "
     "make-up salinity, giving"),
    ("The response is threshold-typed: the make-up penalty is exactly zero for $r\\le r^{*}$ and, "
     "beyond it, independent of capacity (+6.47 to +6.48% across 200–1600 MW).",
     "The response is threshold-typed: the make-up penalty is exactly zero for $r\\le r^{*}$ and "
     "beyond it independent of capacity (+6.47 to +6.48% across 200–1600 MW)."),
    ("Both a water-quality penalty and a water-side bottleneck are therefore required. Current policy "
     "ranges produce no capacity consequence, a falsifiable prediction, not a limitation.",
     "Both a water-quality penalty and a water-side bottleneck are required. Current policy ranges "
     "produce no capacity consequence, a falsifiable prediction rather than a limitation."),
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
