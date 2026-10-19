# -*- coding: utf-8 -*-
"""最后 7 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

OLD = ("Two further decisions must be stated. Intervention counterfactuals were originally "
       "generated on a 100 MW grid while the main results use 50 MW, so a gain may only be "
       "differenced against a baseline from the same grid; we therefore re-ran every "
       "intervention on the 50 MW grid, and all gains reported here share the grid of the "
       "main results. Second, capacity grids introduce quantisation, so we re-ran the "
       "decisive comparisons at 25 MW and 10 MW resolution.")
NEW = ("Two further decisions must be stated. Intervention counterfactuals were originally "
       "generated on a 100 MW grid while the main results use 50 MW, so a gain may only be "
       "differenced against a baseline from the same grid; we therefore re-ran every "
       "intervention on the 50 MW grid. Second, capacity grids introduce quantisation, so we "
       "re-ran the decisive comparisons at 25 and 10 MW resolution.")

t = MS.read_text(encoding="utf-8")
if OLD in t:
    t = t.replace(OLD, NEW, 1)
    MS.write_text(t, encoding="utf-8")
    print("替换成功")
else:
    print("未匹配，尝试按行修复")
    print(OLD[:80])

s = re.sub(r"\$[^$]*\$", " MATH ", t)
print("words:", len(s.split()))
