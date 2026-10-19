# -*- coding: utf-8 -*-
"""摘要最后 3 词（按当前实际文本）。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("The cooling-tower salt balance and the design limit bound the cycles of concentration by "
     "make-up salinity, giving",
     "Cooling-tower salt balance and the design limit bound the cycles of concentration by make-up "
     "salinity, giving"),
    ("Placing $C^{*}=L/\\mathrm{CoC}_d$ against the two source salinities partitions cities into four "
     "regimes, two reproduced.",
     "Placing $C^{*}=L/\\mathrm{CoC}_d$ against the two source salinities partitions cities into four "
     "regimes; two are reproduced."),
]


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    for old, new in PAIRS:
        if old in t:
            t = t.replace(old, new, 1)
        else:
            print("未匹配:", old[:60])
    MS.write_text(t, encoding="utf-8")
    m = re.search(r"^##\s+Abstract\s*$(.*?)^##\s+", t, re.M | re.S)
    ab = re.sub(r"\$[^$]*\$", " MATH ", m.group(1))
    s = re.sub(r"\$[^$]*\$", " MATH ", t)
    print("摘要:", len(ab.split()), "| 全文:", len(s.split()))


if __name__ == "__main__":
    main()
