# -*- coding: utf-8 -*-
"""在英文正文 §4.4 补上 C_p 的锚定尝试与后果（这是四个缺口中最关键的一个）。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

OLD = ("And the threshold rests on four unverified inputs, not one: no parameter among $L$, "
       "$\\mathrm{CoC}_d$, $C_p$ and $C_r$ carries a measured anchor.")
NEW = ("And the threshold rests on four unverified inputs, not one: no parameter among $L$, "
       "$\\mathrm{CoC}_d$, $C_p$ and $C_r$ carries a measured anchor. Of these, $C_p$ decides the "
       "case-city verdict. Locating it against 10,090 measured Californian groundwater TDS "
       "determinations puts the assumed 180 mg L$^{-1}$ at the 14th percentile, with a statewide "
       "median of 420 mg L$^{-1}$; raising $C_p$ to that median drives $r^{*}$ from 0.5532 to "
       "0.0870, and to −1.01 at the neighbouring county median, which moves the case city from "
       "clearly below the threshold to clearly above it and then into Regime I. The plausible range "
       "of an unmeasured parameter straddles the decision boundary, which is why the verdict is "
       "nominal rather than robust. Details and caveats are in SI S7.10; that comparison uses "
       "groundwater monitoring rather than finished water and does not replace the project value.")

t = MS.read_text(encoding="utf-8")
if OLD not in t:
    print("未匹配")
else:
    t = t.replace(OLD, NEW, 1)
    MS.write_text(t, encoding="utf-8")
    print("OK 英文 §4.4 已补充")
    print("词数:", len(re.sub(r"\$[^$]*\$", " MATH ", t).split()))
