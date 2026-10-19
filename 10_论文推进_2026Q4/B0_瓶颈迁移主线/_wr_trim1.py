# -*- coding: utf-8 -*-
"""逐处精简 WR 英文稿，把 8418 词压到 <=7700 词。只做删减，不改任何数字。"""
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

# (old, new) —— old 必须唯一匹配
PAIRS: list[tuple[str, str]] = [
    # ---- 2.1 ----
    (
        "We report two species because that is what the current parameter set configures: the quality-limit table contains TDS (2200 mg L$^{-1}$) and chloride (500 mg L$^{-1}$) and the source-water records carry the same two. Earlier project documentation described five species; the present configuration does not, and we report the configuration that exists.",
        "The parameter set configures exactly these two species: the quality-limit table contains TDS (2200 mg L$^{-1}$) and chloride (500 mg L$^{-1}$) and the source-water records carry the same two.",
    ),
    # ---- 2.2 ----
    (
        "Their policy substitution targets differ (0.65 and 0.40), which is a property of the city rather than of the model, and this is precisely why the joint and purely physical constraint sets diverge at the two endpoints.",
        "Their policy substitution targets differ (0.65 and 0.40), a property of the city rather than of the model, and this is why the joint and purely physical constraint sets diverge at the two endpoints.",
    ),
    # ---- 2.3 ----
    (
        "Ten constraints are evaluated at every capacity point (Table 1). Capacity-type constraints are written against a planning-margin threshold of 0.95 rather than 1.0. This is deliberate: the engine hard-truncates treatment utilisation, so a threshold of 1.0 would make the constraint vacuously true and unable to serve as a bottleneck criterion. The 0.95 threshold asks how much margin remains, not whether the plant physically overflows. One candidate indicator, the reclaimed-plant utilisation ratio, is excluded: the facility carries a 300 ML storage pond, roughly seven to nine days of production, so reaching nameplate treatment rate on a daily step is normal buffering rather than failure, and the indicator is identically 1.0 across the whole capacity range, which would drive every carrying capacity to zero.",
        "Ten constraints are evaluated at every capacity point (Table 1). Capacity-type constraints use a planning-margin threshold of 0.95 rather than 1.0, because the engine hard-truncates treatment utilisation and a threshold of 1.0 would be vacuously true; 0.95 asks how much margin remains. One candidate indicator, the reclaimed-plant utilisation ratio, is excluded: a 300 ML storage pond, roughly seven to nine days of production, makes nameplate treatment rate on a daily step normal buffering rather than failure, and the indicator is identically 1.0 across the capacity range.",
    ),
    (
        "The distinction is not a technical detail but a premise of the argument. Our independent variable is the substitution target $r$ itself; were we to leave the condition that delivered ratio must meet target ratio inside the criterion set, raising $r$ would necessarily make failure more likely, which is self-reference rather than physical evidence. All conclusions about whether $r$ changes carrying capacity therefore rest on the purely physical set. The joint set appears only as a contrast, and the gap between the two must always be stated with it; at the water-scarce endpoint the gap reaches 300 MW at $r=0.9$.",
        "The distinction is a premise, not a detail. Our independent variable is the substitution target $r$; leaving the condition that delivered ratio must meet target ratio inside the criterion set would make raising $r$ necessarily raise the chance of failure, which is self-reference rather than physical evidence. All conclusions about whether $r$ changes carrying capacity therefore rest on the purely physical set; the joint set appears only as a contrast, and the gap reaches 300 MW at $r=0.9$.",
    ),
    (
        "Because the same model yields several distinct boundary values, every capacity number in this paper is tagged with its estimand: daily or annual aggregation, joint or purely physical constraint set, and a separate hourly proxy. The annual estimand answers what is feasible when policy and physics must both hold; the physical annual estimand answers where the physical system would bind if the policy target were not a constraint. These are not stricter and looser versions of one number; they answer different questions. Full definitions of all six estimands and of the three counterfactuals they serve are given in SI Section S1.",
        "Because the same model yields several boundary values, every capacity number is tagged with its estimand: daily or annual aggregation, joint or purely physical constraint set, and a separate hourly proxy. These are not stricter and looser versions of one number; they answer different questions. Definitions of all six estimands and the three counterfactuals they serve are in SI Section S1.",
    ),
    # ---- 2.4 ----
    (
        "Capacity is scanned from 0 to 2000 MW in 50 MW steps, 41 points in total, with the full 730-day model re-run at every point. The first-failure capacity is the first point at which at least one constraint is violated; the maximum safe capacity is the last point before it. The 0 MW point serves as the no-AI baseline for counterfactual differencing.",
        "Capacity is scanned from 0 to 2000 MW in 50 MW steps, 41 points, with the full 730-day model re-run at every point. The first-failure capacity is the first point at which any constraint is violated; the maximum safe capacity is the last point before it. The 0 MW point is the no-AI baseline for counterfactual differencing.",
    ),
    (
        "When several constraints fail at the same capacity point, the dominant constraint is the one with the largest dimensionless violation, computed as violation divided by the absolute target, with ties broken by constraint name. The scale-free measure is required because constraints carry different units: at the water-scarce endpoint the domestic-unmet constraint first fails at 1850 MW with a margin of 167.78 ML, whereas the abstraction ratio first fails at 1200 MW with a margin of only 0.00495 in dimensionless terms. Ranking by raw margin would place domestic supply ahead of the true bottleneck. The rule also makes the reported bottleneck independent of the insertion order of the constraint dictionary, which is a precondition for reproducibility.",
        "When several constraints fail at the same point, the dominant one has the largest dimensionless violation, violation divided by the absolute target, ties broken by name. The scale-free measure is required because constraints carry different units: the domestic-unmet constraint first fails at 1850 MW with a margin of 167.78 ML, whereas the abstraction ratio first fails at 1200 MW with a margin of 0.00495 in dimensionless terms, so ranking by raw margin would place domestic supply ahead of the true bottleneck. The rule also makes the result independent of the insertion order of the constraint dictionary.",
    ),
    (
        "Two further protocol decisions must be stated. First, intervention counterfactuals were generated on a 100 MW grid while the main results use 50 MW, so an intervention gain may only be differenced against a baseline from the same grid. We therefore re-ran every intervention on the 50 MW grid, and all gains reported here share the grid of the main results; the earlier 100 MW values differed by up to one grid step and are superseded. Second, capacity grids introduce quantisation. We re-ran the decisive comparisons at 25 MW and 10 MW resolution, and the outcome of that test governs which numbers may be cited and with what tolerance.",
        "Two further decisions must be stated. Intervention counterfactuals were originally generated on a 100 MW grid while the main results use 50 MW, so a gain may only be differenced against a baseline from the same grid; we therefore re-ran every intervention on the 50 MW grid, and all gains reported here share the grid of the main results. Second, capacity grids introduce quantisation, so we re-ran the decisive comparisons at 25 MW and 10 MW resolution.",
    ),
    # ---- 2.5 ----
    (
        "External anchoring covers parameter ranges and orders of magnitude only; it is never used as a calibration target. Of 54 model parameters, 10 fall inside a documented envelope, 10 sit on an envelope boundary, 32 carry no anchor at all and 2 fall outside it. The anchors themselves come from a convenience sample of the local literature library rather than a formal systematic review with a search protocol. The design cycles of concentration, which is the parameter that controls the threshold, carries no anchor in that envelope, and it is the weakest link in the classification developed below. Driver series are synthetic 730-day sequences, not observed hydrology, and no constraint threshold has been calibrated against any city.",
        "External anchoring covers parameter ranges and orders of magnitude only and is never a calibration target. Of 54 model parameters, 10 fall inside a documented envelope, 10 sit on a boundary, 32 carry no anchor and 2 fall outside; the anchors come from a convenience sample of the local literature library, not a formal systematic review. The design cycles of concentration, which controls the threshold, carries no anchor, making it the weakest link in the classification below. Drivers are synthetic 730-day sequences, and no constraint threshold has been calibrated against any city.",
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
            missed.append(old[:60])
    MS.write_text(text, encoding="utf-8")
    print(f"已替换 {applied}/{len(PAIRS)}")
    for m in missed:
        print("  未匹配:", m, "…")
    s = re.sub(r"\$[^$]*\$", " MATH ", text)
    print("当前总词数:", len(s.split()))


if __name__ == "__main__":
    main()
