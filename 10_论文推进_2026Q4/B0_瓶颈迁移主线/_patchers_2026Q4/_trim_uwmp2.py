# -*- coding: utf-8 -*-
"""最后 12 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

t = MS.read_text(encoding="utf-8")
before = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())

REPL = [
    ("A non-informative constraint is not evidence of safety: the scan never reached it. Two "
     "negative results are substantive.",
     "A non-informative constraint is not evidence of safety: the scan never reached it. Two "
     "negative results matter."),
    ("Zero gain is not zero cost. The unit costs differ by a factor of 32.5, but as only one cost "
     "input has an official source we read that ratio as an order of magnitude only.",
     "Zero gain is not zero cost. Unit costs differ 32.5-fold, but as only one input has an official "
     "source we read that ratio as an order of magnitude only."),
    ("The criterion becomes usable in quantities cities publish. Let city potable use be $P$ and "
     "reclaimed use be $R$;",
     "The criterion becomes usable in quantities cities publish. With city potable use $P$ and "
     "reclaimed use $R$;"),
    ("Regimes differ qualitatively. For $r\\le r^{*}$ the cycles equal the design value, make-up "
     "demand is constant, and the policy effect is a pure gain:",
     "Regimes differ qualitatively. For $r\\le r^{*}$ the cycles equal the design value, make-up "
     "demand is constant, and the effect is a pure gain:"),
]

changed = 0
for old, new in REPL:
    if old in t:
        t = t.replace(old, new, 1)
        changed += 1
    else:
        print("未匹配:", old[:55])
MS.write_text(t, encoding="utf-8")
after = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
print(f"{before} -> {after}（减 {before-after}，改动 {changed}）")
