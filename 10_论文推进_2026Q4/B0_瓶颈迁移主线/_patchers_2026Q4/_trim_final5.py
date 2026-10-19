# -*- coding: utf-8 -*-
"""最后 12 词：删一句冗余限定。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

OLD = ("The unit costs of the two effective interventions differ by a factor of 32.5, but as only "
       "one cost input has an official source we read that ratio only as an order of magnitude.")
NEW = ("The unit costs differ by a factor of 32.5, but as only one cost input has an official "
       "source we read that ratio as an order of magnitude only.")

OLD2 = ("Zero gain is therefore not zero cost.")
NEW2 = "Zero gain is not zero cost."

OLD3 = ("A non-informative constraint is not evidence of safety: the scan never reached it.")
NEW3 = "A non-informative constraint is not evidence of safety: the scan never reached it."

OLD4 = ("The sample is also selected, since California has more than 7,000 systems reporting "
        "recycled production but most are wholesalers reporting no potable production and cannot "
        "yield a $k$.")
NEW4 = ("The sample is also selected: California has more than 7,000 systems reporting recycled "
        "production, but most are wholesalers reporting no potable production and cannot yield a $k$.")


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    before = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    for old, new in ((OLD, NEW), (OLD2, NEW2), (OLD4, NEW4)):
        if old in t:
            t = t.replace(old, new, 1)
        else:
            print("未匹配:", old[:50])
    MS.write_text(t, encoding="utf-8")
    after = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    print(f"{before} -> {after}（减 {before-after}）")


if __name__ == "__main__":
    main()
