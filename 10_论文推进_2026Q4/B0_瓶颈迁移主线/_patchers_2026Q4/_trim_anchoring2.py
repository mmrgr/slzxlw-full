# -*- coding: utf-8 -*-
"""最后 12 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("Physical experiments were not performed; all evidence is computational, and the comparison "
     "against field measurement is directional only.",
     "No physical experiments were performed; all evidence is computational and the comparison "
     "against field measurement is directional."),
    ("Two decisions must be stated. Intervention counterfactuals were originally generated on a "
     "100 MW grid while the main results use 50 MW, so a gain may only be differenced against a "
     "baseline from the same grid; we therefore re-ran every intervention on the 50 MW grid.",
     "Two decisions must be stated. Intervention counterfactuals originally used a 100 MW grid while "
     "the main results use 50 MW, so a gain may only be differenced against a same-grid baseline; we "
     "therefore re-ran every intervention on the 50 MW grid."),
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
