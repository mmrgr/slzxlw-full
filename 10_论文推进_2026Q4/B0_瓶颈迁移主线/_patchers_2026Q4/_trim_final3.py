# -*- coding: utf-8 -*-
"""最后 ~55 词：压引言第三段（含引用编号）与 §3.4 末段。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

OLD1 = ("Three further gaps follow from the same framing. First, facility-scale metrics do not map "
        "onto system bottlenecks: a technology that halves water use per unit of power may deliver "
        "zero additional feasible capacity where the binding constraint is the grid. Second, distinct "
        "estimands are routinely reported as a single number; the physical carrying boundary, the "
        "policy-compliance threshold, the annual- and daily-scale boundaries and the hourly proxy are "
        "five different quantities, and conflating them invites a policy target to be read as a "
        "physical limit [2,7,15]. Third, interventions are rarely tested counterfactually: where the "
        "reclaimed pool is already committed, the effect of a data centre drawing reclaimed water "
        "depends on whether it takes new supply or reallocated stock, and those two have opposite "
        "signs in the city water ledger [14].")
NEW1 = ("Three further gaps follow. First, facility-scale metrics do not map onto system bottlenecks: "
        "a technology that halves water use per unit of power may add zero feasible capacity where the "
        "binding constraint is the grid. Second, distinct estimands are reported as one number; the "
        "physical boundary, the policy threshold, the annual and daily boundaries and the hourly proxy "
        "are five quantities, and conflating them invites a policy target to be read as a physical "
        "limit [2,7,15]. Third, interventions are rarely tested counterfactually: where the pool is "
        "committed, the effect depends on whether a data centre takes new supply or reallocated stock, "
        "and those have opposite signs in the city ledger [14].")

OLD2 = ("Three limits on this section must travel with it. It is an application, not a verification: "
        "we have not observed make-up demand rising after a city's ratio crossed $r^{*}$, which would "
        "require facility-level time series that we do not hold. The 6% and 26% shares have different "
        "denominators and cannot be summed to 32%, and the reporting period behind them is undisclosed. "
        "And $r=0.499$ is a city-wide average over 56 data centres, not a property of any individual "
        "facility. Because $r^{*}$ carries roughly $\\pm10\\%$ parameter uncertainty, a true value near "
        "0.51 would place Santa Clara at or beyond the threshold, so \"not crossed\" is a conclusion "
        "under nominal parameters rather than a robust one.")
NEW2 = ("Three limits travel with this section. It is an application, not a verification: we have not "
        "observed make-up demand rising after a city's ratio crossed $r^{*}$, which would need "
        "facility-level time series we do not hold. The 6% and 26% shares have different denominators, "
        "cannot be summed to 32%, and have an undisclosed reporting period. And $r=0.499$ averages over "
        "56 data centres rather than describing any one. Because $r^{*}$ carries $\\pm10\\%$ uncertainty, "
        "a true value near 0.51 would put Santa Clara at or beyond the threshold, so \"not crossed\" "
        "holds under nominal parameters only.")


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    before = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    for old, new in ((OLD1, NEW1), (OLD2, NEW2)):
        if old in t:
            t = t.replace(old, new, 1)
        else:
            print("未匹配:", old[:55])
    MS.write_text(t, encoding="utf-8")
    after = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    print(f"{before} -> {after}（减 {before-after}）")


if __name__ == "__main__":
    main()
