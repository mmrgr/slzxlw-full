# -*- coding: utf-8 -*-
"""再减 38 词至 7700 以内。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("Against assessments of the global potential of data–water symbiosis our result is "
     "complementary, not corrective. Wang et al. quantified, across 4775 data centres and 57,547 "
     "wastewater plants, savings of roughly 1.3 billion m³ of water and 84 million tonnes of "
     "CO₂-equivalent per year, plus bidirectional heat recovery. We do not dispute that estimate; we "
     "identify the ratio at which its marginal saving begins to be eroded. Their question is how much "
     "can be saved, ours is when saving stops being saving.",
     "Against global assessments of data–water symbiosis our result is complementary, not "
     "corrective. Wang et al. quantified, across 4775 data centres and 57,547 wastewater plants, "
     "savings of roughly 1.3 billion m³ of water and 84 million tonnes of CO₂-equivalent per year "
     "plus bidirectional heat recovery. We do not dispute that estimate; we identify the ratio at "
     "which its marginal saving begins to erode. Their question is how much can be saved, ours when "
     "saving stops being saving."),
    ("Against facility-scale accounting the relation is one of level, not disagreement. Reviews of "
     "data-centre water use conclude that no single formula applies, and national inventories have "
     "established the magnitude of the demand, including the concentration of Chinese compute in "
     "water-scarce regions.",
     "Against facility-scale accounting the relation is one of level, not disagreement. Reviews of "
     "data-centre water use conclude that no single formula applies [8], and national inventories "
     "have established the demand's magnitude, including the concentration of Chinese compute in "
     "water-scarce regions [2,5,15]."),
    ("The value added lies in a mechanism facility-scale accounting cannot express: water-footprint "
     "accounting treats water as a homogeneous commodity, so the effect of blend salinity on the "
     "cycles of concentration is summed away.",
     "The value added lies in a mechanism facility accounting cannot express: footprint accounting "
     "treats water as homogeneous, so the effect of blend salinity on the cycles of concentration is "
     "summed away."),
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
