# -*- coding: utf-8 -*-
"""修正 SI S7.2，并在英文正文末段补上 6%/26% 的证据等级。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

SI_OLD = ("The 6% and 26% shares come from page 27 of the city council staff presentation of "
          "2026-10-06 (RTC #26-1037), which contains two pie charts: recycled water at 26% for data "
          "centres and 74% for the rest of the city, potable water at 6% for data centres and 94% "
          "for the rest. **These percentages exist only inside the graphics and are absent from the "
          "PDF text layer**; they were obtained by rendering page 27 at 200 dpi and reading the "
          "image. Any text-only extraction misses them. The two denominators differ and are not "
          "additive.")

SI_NEW = """The 6% and 26% shares carry a provenance chain that must be stated exactly, and it is weaker
than a first-hand reading.

| Link | Content | Verifiable here |
|---|---|---|
| Origin | City of Santa Clara, File 26-1037, 2026-10-06, "Water Usage" section | **no** — original not held |
| Transcription | *Santa Clara data centers — Independent community report*, October 2026, **p.53** table, citing the above as `[1]` | yes — present in the text layer |
| Use here | share ratio $\\rho=6/26$ for the $k^{*}$ screen | — |

The verifiable line (p.53, text layer, not read from any graphic) reads:

> "October staff water figures [1] Data centers: about 6% of potable use and 26% of recycled use.
> Separate water-system denominators; not 32% of combined use. Supporting period and volumes need
> disclosure."

Three qualifications follow. First, the shares are a **transcribed government statement rather
than a first-hand measurement**: we hold the community report, not the City's original, so we
cannot independently confirm its "Water Usage" section or any graphic in it. An earlier version of
this manuscript described the figures as existing only inside two pie charts on page 27 and as
recoverable only by rendering that page at 200 dpi; the evidence available to us does not support
that description, and it has been corrected. Second, the two denominators differ and are not
additive, as the source itself warns. Third, the reporting period is undisclosed, again as the
source states.

$\\rho=6/26$ should therefore be read as a **government-stated but independently unverified
scenario anchor**, not as reproducible measurement. That evidential grade carries into the
sensitivity analysis of S7.7 and into the limitation register."""

# 英文正文：补一句证据等级
EN_OLD = ("The criterion reduces to two numbers: with data centres taking 6% and 26% of potable and "
          "reclaimed supply, cities whose potable-to-reclaimed ratio falls below 3.50 exceed "
          "$r^{*}$ (13.6% of 169 California systems do); with equal shares the boundary falls to "
          "0.81 and three systems remain below.")
EN_NEW = ("The criterion reduces to two numbers: with data centres taking 6% and 26% of potable and "
          "reclaimed supply, cities whose potable-to-reclaimed ratio falls below 3.50 exceed "
          "$r^{*}$ (13.6% of 169 California systems do); with equal shares the boundary falls to "
          "0.81 and three systems remain below. Those two shares are a transcribed government "
          "statement rather than a first-hand measurement, as SI S7.2 sets out.")

n = 0
for path, old, new, tag in ((SI, SI_OLD, SI_NEW, "SI S7.2"), (EN, EN_OLD, EN_NEW, "英文末段")):
    t = path.read_text(encoding="utf-8")
    if old in t:
        path.write_text(t.replace(old, new, 1), encoding="utf-8")
        print(f"OK {tag}")
        n += 1
    else:
        print(f"未匹配 {tag}")

import re
t = EN.read_text(encoding="utf-8")
print("\n英文词数:", len(re.sub(r"\$[^$]*\$", " MATH ", t).split()))
