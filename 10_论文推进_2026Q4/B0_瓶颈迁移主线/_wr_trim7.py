# -*- coding: utf-8 -*-
"""第七批精简：最后 ~35 词，压到 7700 以内。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS: list[tuple[str, str]] = [
    (
        "The data-centre component resolves information-technology load, cooling (evaporative, dry and hybrid), make-up demand and blowdown. Potable and reclaimed water are blended to a target substitution ratio $r$, and water quality is tracked for two species, total dissolved solids (TDS) and chloride. The cooling constraint is the tighter of the two species. The parameter set configures exactly these two species: the quality-limit table contains TDS (2200 mg L$^{-1}$) and chloride (500 mg L$^{-1}$) and the source-water records carry the same two.",
        "The data-centre component resolves information-technology load, cooling (evaporative, dry and hybrid), make-up demand and blowdown. Potable and reclaimed water are blended to a target substitution ratio $r$, and water quality is tracked for two species, total dissolved solids (TDS) and chloride, both configured with limits and source concentrations: TDS at 2200 and chloride at 500 mg L$^{-1}$. The cooling constraint is the tighter of the two.",
    ),
    (
        "Two endpoints represent corners of the parameter domain rather than real cities. The water-scarce, high-cooling-load endpoint (D-HA) combines a high wet-bulb climate with a tight abstraction cap, treatment works of 370 ML d$^{-1}$, wastewater works of 270 ML d$^{-1}$ and a reclaimed facility of 40 ML d$^{-1}$. The cool-climate endpoint (D-CO) combines a low cooling load with a generous abstraction cap, 380, 270 and 36 ML d$^{-1}$ respectively.",
        "Two endpoints represent corners of the parameter domain, not real cities. The water-scarce, high-cooling-load endpoint (D-HA) combines a high wet-bulb climate with a tight abstraction cap, treatment works of 370 ML d$^{-1}$, wastewater works of 270 ML d$^{-1}$ and a reclaimed facility of 40 ML d$^{-1}$. The cool-climate endpoint (D-CO) combines a low cooling load with a generous cap and 380, 270 and 36 ML d$^{-1}$ respectively.",
    ),
    (
        "The migration sequence differs in more than its starting point. The water-scarce endpoint passes through six distinct failure capacities spanning 650 MW, moving from the water side to the grid and ending at peak capacity and domestic supply; the cool endpoint passes through three spanning 300 MW, beginning at the grid and reaching source abstraction only at the end. Because the endpoints share everything except climate and facility parameters, this divergence in starting point, length and ordering is what a residual-margin explanation predicts and a scale explanation cannot produce.",
        "The migration sequence differs in more than its starting point. The water-scarce endpoint passes through six distinct failure capacities spanning 650 MW, moving from the water side to the grid and ending at peak capacity and domestic supply; the cool endpoint passes through three spanning 300 MW, beginning at the grid and reaching source abstraction only at the end. Because the endpoints share everything except climate and facility parameters, this divergence is what a residual-margin explanation predicts and a scale explanation cannot produce.",
    ),
]


def main() -> None:
    text = MS.read_text(encoding="utf-8")
    applied, missed = 0, []
    for old, new in PAIRS:
        if old in text:
            text = text.replace(old, new, 1)
            applied += 1
        else:
            missed.append(old[:70])
    MS.write_text(text, encoding="utf-8")
    print(f"已替换 {applied}/{len(PAIRS)}")
    for m in missed:
        print("  未匹配:", m, "…")
    s = re.sub(r"\$[^$]*\$", " MATH ", text)
    print("当前总词数:", len(s.split()))


if __name__ == "__main__":
    main()
