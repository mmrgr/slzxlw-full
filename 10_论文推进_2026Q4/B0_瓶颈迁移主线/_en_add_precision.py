# -*- coding: utf-8 -*-
"""在英文 §4.4 补一句精度要求，并压缩其他处以保住 7700 词上限。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

ADD_OLD = ("The plausible range of an unmeasured parameter straddles the decision boundary. "
           "SI S7.10 gives the caveats; the comparison uses groundwater monitoring, not finished "
           "water, and does not replace the project value.")
ADD_NEW = ("The plausible range of an unmeasured parameter straddles the decision boundary. "
           "Inverting the closed form puts the requirement precisely: the verdict is \"not crossed\" "
           "if and only if the true $C_p$ is below 230.8 mg L$^{-1}$, so a measurement to ±25 "
           "mg L$^{-1}$ would settle it — the obstacle is availability, not precision. SI S7.10 "
           "gives the caveats; the comparison uses groundwater monitoring, not finished water, and "
           "does not replace the project value.")

TRIMS = [
    ("The endpoints are corners of a parameter domain, and a 25-city gradient scan checked "
     "continuity only.",
     "The endpoints are parameter-domain corners, and a 25-city gradient scan checked continuity "
     "only."),
    ("A 10% change in one parameter moves $r^{*}$ by 0.018 ($C_p$), 0.089 ($C_r$), 0.094 ($L$) or "
     "0.104 ($\\mathrm{CoC}_d$), with a two-endpoint span reaching 0.19 — enough to move the "
     "threshold across the case city's value.",
     "A 10% change in one parameter moves $r^{*}$ by 0.018 ($C_p$), 0.089 ($C_r$), 0.094 ($L$) or "
     "0.104 ($\\mathrm{CoC}_d$), with a span reaching 0.19 — enough to cross the case city's value."),
    ("Inverting the closed form puts the requirement precisely: the verdict is \"not crossed\" if "
     "and only if the true $C_p$ is below 230.8 mg L$^{-1}$, so a measurement to ±25 mg L$^{-1}$ "
     "would settle it — the obstacle is availability, not precision.",
     "Inverting the closed form gives the requirement: the verdict is \"not crossed\" iff the true "
     "$C_p$ is below 230.8 mg L$^{-1}$, so ±25 mg L$^{-1}$ would settle it; the obstacle is "
     "availability, not precision."),
    ("The migration sequence differs beyond its start. The water-scarce endpoint passes through six "
     "distinct failure capacities spanning 650 MW, moving from the water side to the grid and "
     "ending at peak capacity and domestic supply; the cool endpoint passes through three spanning "
     "300 MW, beginning at the grid and reaching source abstraction only at the end.",
     "The migration sequence differs beyond its start. The water-scarce endpoint passes through six "
     "failure capacities spanning 650 MW, moving from the water side to the grid and ending at peak "
     "capacity and domestic supply; the cool endpoint passes through three spanning 300 MW, "
     "beginning at the grid and reaching source abstraction last."),
]


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    before = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    if ADD_OLD in t:
        t = t.replace(ADD_OLD, ADD_NEW, 1)
        print("OK 补入精度要求")
    else:
        print("未匹配 精度要求锚点")
    for old, new in TRIMS:
        if old in t:
            t = t.replace(old, new, 1)
        else:
            print("未匹配 trim:", old[:55])
    MS.write_text(t, encoding="utf-8")
    after = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    print(f"{before} -> {after}")


if __name__ == "__main__":
    main()
