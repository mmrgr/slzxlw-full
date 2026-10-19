# -*- coding: utf-8 -*-
"""摘要最后 3 词：删 'and' + 两处赘词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("under equal shares the boundary falls to 0.81, and three systems remain below it.",
     "under equal shares the boundary falls to 0.81 and three systems remain below it."),
    ("Both a water-quality penalty and a water-side bottleneck are needed.",
     "Both a water-quality penalty and a water-side bottleneck are needed."),
    ("Current policy ranges produce no capacity consequence, a falsifiable prediction not a "
     "limitation.",
     "Current policy ranges produce no capacity consequence, a falsifiable prediction not a "
     "limitation."),
    ("The response is threshold-typed: the penalty is exactly zero for $r\\le r^{*}$ and beyond it "
     "independent of capacity (+6.47 to +6.48% across 200–1600 MW).",
     "The response is threshold-typed: the penalty is exactly zero for $r\\le r^{*}$ and beyond it "
     "independent of capacity (+6.47 to +6.48%, 200–1600 MW)."),
]


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    before = len(re.sub(r"\$[^$]*\$", " MATH ", re.search(
        r"^##\s+Abstract\s*$(.*?)^##\s+", t, re.M | re.S).group(1)).split())
    for old, new in PAIRS:
        if old in t:
            t = t.replace(old, new, 1)
        else:
            print("未匹配:", old[:55])
    MS.write_text(t, encoding="utf-8")
    m = re.search(r"^##\s+Abstract\s*$(.*?)^##\s+", t, re.M | re.S)
    ab = re.sub(r"\$[^$]*\$", " MATH ", m.group(1))
    s = re.sub(r"\$[^$]*\$", " MATH ", t)
    print(f"摘要 {before} -> {len(ab.split())} | 全文 {len(s.split())}")


if __name__ == "__main__":
    main()
