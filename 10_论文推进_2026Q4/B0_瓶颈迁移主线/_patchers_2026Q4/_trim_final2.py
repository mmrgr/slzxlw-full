# -*- coding: utf-8 -*-
"""再压 ~110 词至 7700 以内。只做真实删减，不靠改写后变长。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    # §4.4 局限：合并两句
    (
        "The real-city section is an application, not a verification, and the distinction is not rhetorical. We have not observed make-up demand rising as a city crossed $r^{*}$; that would require facility-level time series we do not hold, and treating that section as confirmation would exceed the evidence. The two documented shares have different denominators, cannot be summed, and have an undisclosed reporting period. The city-wide ratio is an average over 56 facilities rather than a property of any one, and $k$ is sensitive to caliber: the two calibers differ by 5.5 percentage points in $r$, the same magnitude as the 5.4-point margin to the threshold, so the direction of the conclusion is determined while its size is not. The state-wide distribution is drawn from a selected subsample and cannot be extrapolated to the state's water systems.",
        "The real-city section is an application, not a verification. We have not observed make-up demand rising as a city crossed $r^{*}$; that needs facility-level time series we do not hold, and treating the section as confirmation would exceed the evidence. The two shares have different denominators, cannot be summed, and have an undisclosed reporting period. The city-wide ratio averages over 56 facilities rather than describing any one, and $k$ is caliber-sensitive: the two calibers differ by 5.5 points in $r$, the same magnitude as the 5.4-point margin, so the direction is determined while its size is not. The state-wide distribution comes from a selected subsample and cannot be extrapolated.",
    ),
    # §4.4 时间尺度
    (
        "Finally, the time-scale results are demoted rather than argued. Annual boundaries exceed daily ones by 500 and 250 MW and the hourly proxy falls below by 50 and 100 MW, but the proxy is built from a synthesised intraday load curve with assumed training, inference and peak factors, not measured hourly load; we report its direction and do not use it as evidence for the main claim.",
        "Finally, the time-scale results are demoted rather than argued. Annual boundaries exceed daily ones by 500 and 250 MW and the hourly proxy falls below by 50 and 100 MW, but the proxy rests on a synthesised intraday curve with assumed training, inference and peak factors, not measured load; we report its direction only.",
    ),
    # §3.2 四情形叙述
    (
        "Both endpoints fall in Regime II, since $C^{*}=2200/5=440$ lies between 180 and 650; their difference is not two mechanisms but one mechanism under two policy targets, the water-scarce 0.70 exceeding $r^{*}$ while the cool 0.45 does not. We verified that the regimes are behaviourally distinct by holding the endpoint at 800 MW and varying only $\\mathrm{CoC}_d$.",
        "Both endpoints fall in Regime II, since $C^{*}=2200/5=440$ lies between 180 and 650; their difference is one mechanism under two policy targets, the water-scarce 0.70 exceeding $r^{*}$ while the cool 0.45 does not. We verified behavioural distinctness by holding the endpoint at 800 MW and varying only $\\mathrm{CoC}_d$.",
    ),
    # §3.3
    (
        "Quantisation constrains what may be cited. Because the effect is roughly two grid steps and the first-failure boundary need not fall on a grid point, we recomputed at 25 MW and 10 MW. The zero-effect region is identical on all three grids, the strongest form of the result and the one our falsifiability claim rests on.",
        "Quantisation constrains what may be cited. Because the effect is roughly two grid steps and the first-failure boundary need not fall on a grid point, we recomputed at 25 and 10 MW. The zero-effect region is identical on all three grids — the strongest form of the result, and the one our falsifiability claim rests on.",
    ),
    # §1
    (
        "Three further gaps follow from the same framing. First, facility-scale metrics do not map onto system bottlenecks: a technology that halves water use per unit of power may deliver zero additional feasible capacity where the binding constraint is the grid. Second, distinct estimands are routinely reported as a single number; the physical carrying boundary, the policy-compliance threshold, the annual- and daily-scale boundaries and the hourly proxy are five different quantities, and conflating them invites a policy target to be read as a physical limit. Third, interventions are rarely tested counterfactually: where the reclaimed pool is already committed, the effect of a data centre drawing reclaimed water depends on whether it takes new supply or reallocated stock, and those two have opposite signs in the city water ledger.",
        "Three further gaps follow. First, facility-scale metrics do not map onto system bottlenecks: a technology that halves water use per unit of power may deliver zero additional feasible capacity where the binding constraint is the grid. Second, distinct estimands are reported as one number; the physical boundary, the policy threshold, the annual and daily boundaries and the hourly proxy are five quantities, and conflating them invites a policy target to be read as a physical limit. Third, interventions are rarely tested counterfactually: where the reclaimed pool is already committed, the effect depends on whether a data centre takes new supply or reallocated stock, and those have opposite signs in the city ledger.",
    ),
]


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    before = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    n = 0
    for old, new in PAIRS:
        if old in t:
            t = t.replace(old, new, 1)
            n += 1
        else:
            print("未匹配:", old[:55])
    MS.write_text(t, encoding="utf-8")
    after = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    print(f"替换 {n}/{len(PAIRS)}；{before} -> {after}（减 {before-after}）")


if __name__ == "__main__":
    main()
