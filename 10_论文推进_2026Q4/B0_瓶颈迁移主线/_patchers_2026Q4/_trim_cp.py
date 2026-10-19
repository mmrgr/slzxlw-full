# -*- coding: utf-8 -*-
"""补入 C_p 锚定后回补词数：7812 -> <=7700（需减 ~115）。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    # §4.4 自我压缩（保留关键数字，删赘语）
    ("Of these, $C_p$ decides the case-city verdict. Locating it against 10,090 measured Californian "
     "groundwater TDS determinations puts the assumed 180 mg L$^{-1}$ at the 14th percentile, with a "
     "statewide median of 420 mg L$^{-1}$; raising $C_p$ to that median drives $r^{*}$ from 0.5532 to "
     "0.0870, and to −1.01 at the neighbouring county median, which moves the case city from clearly "
     "below the threshold to clearly above it and then into Regime I. The plausible range of an "
     "unmeasured parameter straddles the decision boundary, which is why the verdict is nominal "
     "rather than robust. Details and caveats are in SI S7.10; that comparison uses groundwater "
     "monitoring rather than finished water and does not replace the project value.",
     "Of these, $C_p$ decides the case-city verdict: against 10,090 measured Californian groundwater "
     "TDS values the assumed 180 mg L$^{-1}$ sits at the 14th percentile against a median of "
     "420 mg L$^{-1}$, and raising it to that median drives $r^{*}$ from 0.5532 to 0.0870 and to "
     "−1.01 at the neighbouring county median, moving the case city from clearly below the threshold "
     "to clearly above it and then into Regime I. The plausible range of an unmeasured parameter "
     "straddles the decision boundary. SI S7.10 gives the caveats; the comparison uses groundwater "
     "monitoring, not finished water, and does not replace the project value."),
    # §4.4 其他段落压缩
    ("The bottleneck attribution rests on a single deterministic scan with no random source, so no "
     "sampling error estimate exists for the dominant constraint. A $\\pm2\\%$ perturbation of all "
     "thresholds moves daily capacity by up to 250 MW at the water-scarce endpoint, roughly 75 MW per "
     "1% of threshold, so absolute capacities are unreliable; what survives is the migration "
     "structure, with first failures in 1000 to 1350 MW and 1450 to 1500 MW, two non-overlapping "
     "intervals. Grid quantisation is why only the zero-effect region and the endpoint decline are "
     "cited as numbers, and intervention interactions were not tested since the nine interventions "
     "were applied one at a time.",
     "Bottleneck attribution rests on a single deterministic scan with no random source, so no "
     "sampling error estimate exists. A $\\pm2\\%$ perturbation moves daily capacity by up to 250 MW "
     "at the water-scarce endpoint, so absolute capacities are unreliable; what survives is the "
     "migration structure, with first failures in 1000–1350 and 1450–1500 MW, two non-overlapping "
     "intervals. Quantisation is why only the zero-effect region and the endpoint decline are cited "
     "as numbers, and interactions were not tested since the nine interventions were applied singly."),
    ("The semantics of the grid constraint are unresolved: the model does not distinguish "
     "campus-connection capacity from node-available capacity in the urban grid, which governs how "
     "the electrical bottleneck should be read. It may represent an engineering constraint on campus "
     "interconnection rather than physical headroom, and is the element most likely to be challenged.",
     "The grid constraint's semantics are unresolved: the model does not distinguish "
     "campus-connection from node-available capacity, which governs how the electrical bottleneck is "
     "read. It may be an engineering constraint on campus interconnection rather than physical "
     "headroom, and is the element most likely to be challenged."),
    ("The threshold value is not a universal constant but the value at the endpoint water-quality "
     "parameters; any city's value must be computed from its own. The classification boundaries are "
     "thin: when $C^{*}$ approaches either source salinity a small parameter error changes the regime "
     "assignment, so we claim a method rather than any city's classification. Regime I was verified "
     "with a design value of 15, which is engineeringly unrealistic since real towers rarely exceed "
     "8, and that construction serves logical verification rather than description. The regime "
     "validation used one endpoint, one capacity and five ratios, so its universality rests on the "
     "derivation rather than on exhaustive simulation.",
     "The threshold is not a universal constant but the value at the endpoint parameters; any city's "
     "value must be computed from its own. Classification boundaries are thin: when $C^{*}$ "
     "approaches either source salinity a small error changes the regime, so we claim a method rather "
     "than any city's assignment. Regime I was verified at a design value of 15, engineeringly "
     "unrealistic since real towers rarely exceed 8, so that construction serves logical verification "
     "rather than description. Validation used one endpoint, one capacity and five ratios, so "
     "universality rests on the derivation."),
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
