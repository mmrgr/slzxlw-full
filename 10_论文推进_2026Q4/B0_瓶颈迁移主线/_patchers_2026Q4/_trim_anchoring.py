# -*- coding: utf-8 -*-
"""同步锚点缺口后回补词数：7784 -> <=7700（需减 ~85）。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    # §2.5 精简（保留四参数事实，删冗余）
    ("External anchoring covers parameter ranges and orders of magnitude only and is never a "
     "calibration target. Of 54 model parameters, 10 fall inside a documented envelope, 10 sit on "
     "a boundary, 32 carry no anchor and 2 fall outside; the anchors come from a convenience sample "
     "of the local literature library, not a formal systematic review. None of the four parameters "
     "that set the threshold carries a measured anchor: the design cycles of concentration is listed "
     "in the envelope without an anchor, and the three water-quality parameters — the loop salinity "
     "limit and the two source salinities — are not in the envelope table at all and have never been "
     "checked against external data. Drivers are synthetic 730-day sequences, and no constraint "
     "threshold has been calibrated against any city.",
     "External anchoring covers parameter ranges and orders of magnitude only, never calibration. Of "
     "54 model parameters, 10 fall inside a documented envelope, 10 sit on a boundary, 32 carry no "
     "anchor and 2 fall outside; the anchors come from a convenience sample of the local literature "
     "library, not a systematic review. None of the four threshold parameters carries a measured "
     "anchor: the design cycles of concentration is listed without one, and the three water-quality "
     "parameters — the loop salinity limit and the two source salinities — are absent from the "
     "envelope table entirely. Drivers are synthetic, and no threshold has been calibrated against "
     "any city."),
    # §4.4 精简
    ("The dominant limitation is that nothing here is calibrated to a real city. All capacity numbers "
     "are conditional on synthetic 730-day drivers, one parameter set per endpoint and ten thresholds "
     "not calibrated against any city, so they demonstrate mechanism rather than estimate reality. "
     "The endpoints are corners of a parameter domain, and a 25-city gradient scan checked continuity "
     "only. None of the four parameters that set the threshold carries a measured anchor — the design "
     "cycles of concentration is listed without one, and the three water-quality parameters were never "
     "entered into the envelope table — so the threshold value rests on four unverified inputs rather "
     "than one.",
     "The dominant limitation is that nothing here is calibrated to a real city. All capacity numbers "
     "are conditional on synthetic drivers, one parameter set per endpoint and ten uncalibrated "
     "thresholds, so they demonstrate mechanism rather than estimate reality. The endpoints are "
     "corners of a parameter domain, and a 25-city gradient scan checked continuity only. And the "
     "threshold rests on four unverified inputs, not one: no parameter among $L$, $\\mathrm{CoC}_d$, "
     "$C_p$ and $C_r$ carries a measured anchor."),
    # §3.2 精简
    ("The threshold's form is structural and its value conditional. Elasticities at the nominal point "
     "are $+1.6923$ for $L$, $-1.6921$ for $\\mathrm{CoC}_d$, $-1.3828$ for $C_r$ and $-0.3093$ for "
     "$C_p$; the near-equality of the first two reflects that both enter only through $C^{*}$. A 10% "
     "change in a single parameter moves $r^{*}$ by 0.018 ($C_p$), 0.089 ($C_r$), 0.094 ($L$) or "
     "0.104 ($\\mathrm{CoC}_d$) relative to nominal, and the two-endpoint span reaches 0.19 for the "
     "last two — enough to move the threshold across the value observed for the case city.",
     "The threshold's form is structural and its value conditional. Elasticities are $+1.6923$ for "
     "$L$, $-1.6921$ for $\\mathrm{CoC}_d$, $-1.3828$ for $C_r$ and $-0.3093$ for $C_p$; the "
     "near-equality of the first two reflects that both enter only through $C^{*}$. A 10% change in "
     "one parameter moves $r^{*}$ by 0.018 ($C_p$), 0.089 ($C_r$), 0.094 ($L$) or 0.104 "
     "($\\mathrm{CoC}_d$), with a two-endpoint span reaching 0.19 — enough to move the threshold "
     "across the case city's value."),
    # §3.4
    ("This is a transferable screening procedure, not an assessment of any one city; the city below is "
     "the substitution that demonstrates it.",
     "This is a transferable screening procedure, not an assessment of any one city; the case below "
     "demonstrates it."),
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
