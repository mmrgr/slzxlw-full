# -*- coding: utf-8 -*-
"""第五批精简：最后 ~80 词，压到 7700 以下。"""
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
        "Data-centre water use has become a new variable in urban water management. Most existing assessments operate at the facility scale: water use effectiveness per unit of information-technology power, comparisons between evaporative and dry cooling, and site-level water-risk scoring. Such accounting answers how much water a given facility withdraws, but it cannot answer the planning question that a city actually faces. When compute capacity grows from 100 MW to 1000 MW, does water quantity, water-treatment capacity, wastewater capacity or grid connection fail first? And which investment would genuinely raise the feasible scale? Neither answer follows from the absolute size of the facility; both follow from the city's own residual-margin structure. A water-rich city with a thin grid and a water-scarce city with a generous grid fail in entirely different places.",
        "Data-centre water use has become a new variable in urban water management. Most assessments operate at the facility scale: water use effectiveness per unit of information-technology power, comparisons between evaporative and dry cooling, and site-level water-risk scoring. Such accounting answers how much water a facility withdraws, but not the planning question a city faces. When compute capacity grows from 100 MW to 1000 MW, does water quantity, treatment capacity, wastewater capacity or grid connection fail first, and which investment would genuinely raise the feasible scale? Neither answer follows from facility size; both follow from the city's residual-margin structure. A water-rich city with a thin grid and a water-scarce city with a generous grid fail in entirely different places.",
    ),
    (
        "Three further gaps follow from the same facility-level framing. First, facility-scale metrics do not map onto system bottlenecks: a technology that halves water use per unit of power may deliver zero additional feasible capacity in a city whose binding constraint is the grid. Second, distinct estimands are routinely reported as a single number. The physical carrying boundary, the policy-compliance threshold, the annual-scale boundary, the daily-scale boundary and the hourly proxy boundary are five different quantities, and conflating them invites a policy target to be read as a physical limit. Third, interventions are rarely subjected to a counterfactual test. In a city whose reclaimed pool is already committed to incumbent users, the effect of a data centre drawing reclaimed water depends on whether it takes new supply or reallocated stock, and those two have opposite signs in the city water ledger.",
        "Three further gaps follow from the same framing. First, facility-scale metrics do not map onto system bottlenecks: a technology that halves water use per unit of power may deliver zero additional feasible capacity where the binding constraint is the grid. Second, distinct estimands are routinely reported as a single number; the physical carrying boundary, the policy-compliance threshold, the annual- and daily-scale boundaries and the hourly proxy are five different quantities, and conflating them invites a policy target to be read as a physical limit. Third, interventions are rarely tested counterfactually: where the reclaimed pool is already committed, the effect of a data centre drawing reclaimed water depends on whether it takes new supply or reallocated stock, and those two have opposite signs in the city water ledger.",
    ),
    (
        "Two scope statements belong here rather than in the limitations. We claim no capacity loss under current policy. In the range $r\\le0.35$, which contains current Chinese reclaimed-water utilisation targets, the carrying capacity of both endpoints does not vary with $r$ at all, and this exact zero is identical on all three capacity grids we tested. A linear mechanism cannot produce an exact zero; a threshold mechanism can, and that zero is falsifiable by any non-zero observation. The policy value of the criterion therefore lies in delimiting a safe interval rather than in forecasting any city's present condition. Second, the ratio used here is the campus substitution ratio, whose denominator is campus cooling make-up; it is not the city-wide reclaimed-water utilisation rate, whose denominator is municipal wastewater throughput. The two are not interchangeable, and the bridge between them is $r_{\\max}=u\\,(W/D)$.",
        "Two scope statements belong here rather than in the limitations. We claim no capacity loss under current policy. In the range $r\\le0.35$, which contains current Chinese reclaimed-water utilisation targets, the carrying capacity of both endpoints does not vary with $r$ at all, and this exact zero is identical on all three capacity grids tested. A linear mechanism cannot produce an exact zero; a threshold mechanism can, and that zero is falsifiable by any non-zero observation. The criterion's policy value therefore lies in delimiting a safe interval rather than forecasting any city's present condition. Second, the ratio used here is the campus substitution ratio, whose denominator is campus cooling make-up, not the city-wide utilisation rate whose denominator is municipal wastewater throughput; the bridge between them is $r_{\\max}=u\\,(W/D)$.",
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
