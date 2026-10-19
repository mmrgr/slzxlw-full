# -*- coding: utf-8 -*-
"""按实际文本再减 36 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("Against assessments of the global potential of data–water symbiosis [14] our result is "
     "complementary, not corrective. That assessment quantified, across 4775 data centres and 57,547 "
     "wastewater plants, savings of roughly 1.3 billion m³ of water and 84 million tonnes of "
     "CO₂-equivalent per year, plus bidirectional heat recovery. We do not dispute that estimate; we "
     "identify the ratio at which its marginal saving begins to be eroded. Their question is how much "
     "can be saved, ours is when saving stops being saving.",
     "Against global assessments of data–water symbiosis [14] our result is complementary, not "
     "corrective. That assessment quantified, across 4775 data centres and 57,547 wastewater plants, "
     "savings of roughly 1.3 billion m³ of water and 84 million tonnes of CO₂-equivalent per year "
     "plus bidirectional heat recovery. We do not dispute it; we identify the ratio at which its "
     "marginal saving begins to erode. Their question is how much can be saved, ours when saving "
     "stops being saving."),
    ("Those studies answer how much water is used; ours answers which constraint fails first and how "
     "raising the reclaimed ratio reorders that sequence.",
     "Those studies answer how much water is used; ours which constraint fails first and how raising "
     "the reclaimed ratio reorders that sequence."),
    ("Two asymmetries must be stated. Their evidence base, a global inventory with life-cycle "
     "assessment and optimisation, is stronger than ours, so nothing here corrects it. And they "
     "include bidirectional heat recovery, returning data-centre waste heat to sludge drying and "
     "anaerobic digestion, a coupling our model omits by treating that heat as waste.",
     "Two asymmetries must be stated. Their evidence base, a global inventory with life-cycle "
     "assessment and optimisation, is stronger than ours, so nothing here corrects it. And they "
     "return data-centre waste heat to sludge drying and anaerobic digestion, a coupling our model "
     "omits by treating that heat as waste."),
    ("Two mechanisms can make the policy constraint fail. The reclaimed pool may be capacity-limited, "
     "in which case reclaimed use saturates and the constraint fails against a hard supply ceiling. "
     "Or the water-quality penalty may dilute the denominator, so the same pool corresponds to a "
     "larger make-up demand: at the water-scarce endpoint and 1600 MW reclaimed use rises only from "
     "25,157 to 25,567, or 1.6%, while total withdrawal rises 5.4%. Both operate, but the second "
     "dominates at the margin and is the new mechanism; treating the first as the whole story would "
     "misplace the conclusion.",
     "Two mechanisms can make the policy constraint fail. The reclaimed pool may be capacity-limited, "
     "so reclaimed use saturates against a hard supply ceiling. Or the water-quality penalty may "
     "dilute the denominator, so the same pool corresponds to a larger make-up demand: at the "
     "water-scarce endpoint and 1600 MW reclaimed use rises only from 25,157 to 25,567, or 1.6%, "
     "while total withdrawal rises 5.4%. Both operate, but the second dominates at the margin and is "
     "the new mechanism; treating the first as the whole story would misplace the conclusion."),
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
