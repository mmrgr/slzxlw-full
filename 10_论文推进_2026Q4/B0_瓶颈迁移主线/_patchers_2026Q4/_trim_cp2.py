# -*- coding: utf-8 -*-
"""再减 56 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("The real-city section is an application, not a verification. We have not observed make-up "
     "demand rising as a city crossed $r^{*}$; that needs facility-level time series we do not hold, "
     "and treating the section as confirmation would exceed the evidence. The two shares have "
     "different denominators, cannot be summed, and have an undisclosed reporting period. The "
     "city-wide ratio averages over 56 facilities rather than describing any one, and $k$ is "
     "caliber-sensitive: the two calibers differ by 5.5 points in $r$, the same magnitude as the "
     "5.4-point margin, so the direction is determined while its size is not. The state-wide "
     "distribution comes from a selected subsample and cannot be extrapolated.",
     "The real-city section is an application, not a verification. We have not observed make-up "
     "demand rising as a city crossed $r^{*}$; that needs facility-level time series we do not hold. "
     "The two shares have different denominators, cannot be summed, and have an undisclosed period. "
     "The city-wide ratio averages over 56 facilities rather than describing any one, and $k$ is "
     "caliber-sensitive: the calibers differ by 5.5 points in $r$, the same magnitude as the "
     "5.4-point margin, so the direction is determined while its size is not. The state-wide "
     "distribution comes from a selected subsample and cannot be extrapolated."),
    ("Finally, the time-scale results are demoted rather than argued. Annual boundaries exceed daily "
     "ones by 500 and 250 MW and the hourly proxy falls below by 50 and 100 MW, but the proxy rests "
     "on a synthesised intraday curve with assumed training, inference and peak factors, not measured "
     "load; we report its direction only.",
     "Finally, the time-scale results are demoted rather than argued. Annual boundaries exceed daily "
     "ones by 500 and 250 MW and the hourly proxy falls below by 50 and 100 MW, but the proxy rests "
     "on a synthesised intraday curve with assumed training, inference and peak factors; we report "
     "its direction only."),
    ("Interventions confirm that the binding constraint, not the intervention label, determines "
     "whether an investment has any effect. Of nine one-to-one interventions at the water-scarce "
     "endpoint, only 30% leakage reduction yields a gain, raising capacity from 1150 to 1300 MW by "
     "relaxing the water side; expanding grid connection by 50% yields exactly zero, at a median "
     "investment of 44,921 ten-thousand yuan.",
     "Interventions confirm that the binding constraint, not the label, determines whether an "
     "investment has any effect. Of nine one-to-one interventions at the water-scarce endpoint, only "
     "30% leakage reduction yields a gain, raising capacity from 1150 to 1300 MW by relaxing the "
     "water side; 50% grid expansion yields exactly zero, at a median investment of 44,921 "
     "ten-thousand yuan."),
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
