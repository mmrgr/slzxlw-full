# -*- coding: utf-8 -*-
"""留出余量：再压 ~25 词，避免正好压线。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("For a city far below $r^{*}$ it supplies an executable planning ceiling, since the ratio can "
     "be raised to $r^{*}$ without cost, a stronger statement than saying a higher ratio happens to "
     "be harmless for now. For a city near $r^{*}$ it supplies the threshold location and its "
     "parameter sensitivity. For a city beyond $r^{*}$ it supplies the direction and magnitude of "
     "the penalty. For a city planning a fully reclaimed campus it supplies the four-regime "
     "classification, which answers whether such a target is achievable at all from four parameters.",
     "For a city far below $r^{*}$ it supplies an executable planning ceiling, since the ratio can "
     "be raised to $r^{*}$ without cost — stronger than saying a higher ratio happens to be harmless. "
     "Near $r^{*}$ it gives the threshold location and its parameter sensitivity. Beyond it, the "
     "direction and magnitude of the penalty. For a fully reclaimed campus it gives the four-regime "
     "classification, which answers from four parameters whether such a target is achievable."),
    ("The result is a mechanism demonstration under synthetic parameters, and the calibration "
     "described above remains the step required to convert the criterion into a forecast.",
     "The result is a mechanism demonstration under synthetic parameters; calibration remains the "
     "step required to convert the criterion into a forecast."),
]


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    before = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    for old, new in PAIRS:
        if old in t:
            t = t.replace(old, new, 1)
        else:
            print("未匹配:", old[:55])
    MS.write_text(t, encoding="utf-8")
    after = len(re.sub(r"\$[^$]*\$", " MATH ", t).split())
    print(f"{before} -> {after}（减 {before-after}）")


if __name__ == "__main__":
    main()
