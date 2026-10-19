# -*- coding: utf-8 -*-
"""最后 15 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

OLD = ("The confound control is the hardest evidence available, holding capacity, climate driver "
       "and city load fixed and varying only the blend.")
NEW = ("The confound control is the hardest evidence available: capacity, climate driver and city "
       "load are fixed and only the blend varies.")

OLD2 = ("The mechanism is thus stated completely as two conditions, $r>r^{*}$ and a water-side "
        "bottleneck. It is not a general claim that water saving is harmful; the cool endpoint is "
        "the negative result that establishes the second condition.")
NEW2 = ("The mechanism is thus stated completely as two conditions, $r>r^{*}$ and a water-side "
        "bottleneck. It is not a claim that water saving is harmful; the cool endpoint is the "
        "negative result establishing the second condition.")

OLD3 = ("The response is a step rather than a gradient. Constraint margins at a carrying boundary "
        "are small by construction:")
NEW3 = ("The response is a step, not a gradient. Constraint margins at a carrying boundary are "
        "small by construction:")


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    before = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    for old, new in ((OLD, NEW), (OLD2, NEW2), (OLD3, NEW3)):
        if old in t:
            t = t.replace(old, new, 1)
        else:
            print("未匹配:", old[:50])
    MS.write_text(t, encoding="utf-8")
    after = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    print(f"{before} -> {after}（减 {before-after}）")


if __name__ == "__main__":
    main()
