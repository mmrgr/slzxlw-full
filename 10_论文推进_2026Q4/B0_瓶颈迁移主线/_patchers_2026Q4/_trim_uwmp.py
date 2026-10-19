# -*- coding: utf-8 -*-
"""压回 7700 以内（需减 ~23）。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("On supply capacity the plan gives the four components as SFPUC 5041, Valley Water 4560, "
     "groundwater 23,048 and recycled 6017 acre-feet per year, described in the source as \"about "
     "38,700\" in total; the 38,666 used here and the potable subtotal of 32,649 are our summations, "
     "not quoted figures. They give $k=5.43$ and $r=0.444$, 10.9 points below $r^{*}$.",
     "On supply capacity the plan gives SFPUC 5041, Valley Water 4560, groundwater 23,048 and "
     "recycled 6017 acre-feet per year, described as \"about 38,700\" in total; the 38,666 used here "
     "and the potable subtotal 32,649 are our summations, not quoted figures. They give $k=5.43$ and "
     "$r=0.444$, 10.9 points below $r^{*}$."),
    ("For Santa Clara the 2025 Urban Water Management Plan gives two calibers. On supply capacity "
     "the plan gives",
     "For Santa Clara the 2025 Urban Water Management Plan gives two calibers. On supply capacity it gives"),
    ("An independent source corroborates the ratio: the California Electronic Annual Report for 2022 "
     "gives potable 16,913 and recycled 3450 acre-feet, hence $k=4.90$, differing by 0.3% on potable "
     "and 11% on recycled.",
     "An independent source corroborates the ratio: the California Electronic Annual Report for 2022 "
     "gives potable 16,913 and recycled 3450 acre-feet, hence $k=4.90$, differing 0.3% on potable and "
     "11% on recycled."),
    ("The screen requires only two published numbers: a city whose ratio of potable to reclaimed use "
     "falls below 3.50 has a data-centre substitution ratio that necessarily exceeds $r^{*}$.",
     "The screen needs only two published numbers: a city whose ratio of potable to reclaimed use "
     "falls below 3.50 has a substitution ratio that necessarily exceeds $r^{*}$."),
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
