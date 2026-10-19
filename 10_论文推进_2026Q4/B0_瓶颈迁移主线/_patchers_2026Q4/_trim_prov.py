# -*- coding: utf-8 -*-
"""英文 7749 -> <=7700（需减 ~50）。压缩来源链句本身 + 其他冗处。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("The two shares that calibrate $\\rho$ are a transcribed government statement rather than a "
     "first-hand measurement: the originating City report (File 26-1037) is not in our possession, "
     "and the figures reach us through an independent community report whose page 53 reproduces "
     "them in text, with its own warning that the denominators are not additive and that the "
     "supporting period needs disclosure (SI S7.2).",
     "The two shares calibrating $\\rho$ are transcribed, not first-hand: the originating City "
     "report (File 26-1037) is not in our possession, and the figures reach us through an "
     "independent community report whose page 53 reproduces them in text, warning itself that the "
     "denominators are not additive and the period undisclosed (SI S7.2)."),
    ("A non-informative constraint is not evidence of safety: the scan never reached it. Two "
     "negative results count.",
     "A non-informative constraint is not evidence of safety: the scan never reached it. Two "
     "negative results matter."),
    ("The value 3.50 must be reported with $\\rho$, because $k^{*}$ is strongly sensitive to it and "
     "the screen is only as sharp as the shares it is fed.",
     "The value 3.50 must be reported with $\\rho$: $k^{*}$ is strongly sensitive to it, and the "
     "screen is only as sharp as the shares it is fed."),
    ("We therefore also report a conservative boundary. Setting $\\rho=1$, which assumes equal "
     "data-centre shares in both supplies and is least favourable to crossing, yields $k^{*}=0.81$, "
     "and 3 of the 169 systems still fall below it.",
     "We therefore report a conservative boundary too: $\\rho=1$, assuming equal data-centre shares "
     "in both supplies and least favourable to crossing, yields $k^{*}=0.81$, with 3 of 169 systems "
     "still below it."),
    ("The claim surviving every assumption we examined is narrower than the Santa-Clara-calibrated "
     "figure, and we state both.",
     "The claim surviving every assumption we examined is narrower than the Santa-Clara figure; we "
     "state both."),
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
