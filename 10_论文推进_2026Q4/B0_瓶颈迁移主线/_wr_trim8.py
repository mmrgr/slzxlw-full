# -*- coding: utf-8 -*-
"""第八批：最后 10 词。"""
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
        "Integrated cost is not part of this comparison beyond order of magnitude.",
        "",
    ),
    (
        "A non-informative constraint is not evidence of safety; it means the scan never reached it.",
        "A non-informative constraint is not evidence of safety: the scan never reached it.",
    ),
    (
        "Zero gain is therefore not zero cost. The unit costs of the two effective interventions differ by a factor of 32.5, but because only one of the two cost inputs has an official source we read that ratio only as an order of magnitude.",
        "Zero gain is therefore not zero cost. The unit costs of the two effective interventions differ by a factor of 32.5, but as only one cost input has an official source we read that ratio only as an order of magnitude.",
    ),
    (
        "The two regimes differ qualitatively. For $r\\le r^{*}$ the cycles of concentration equal the design value, make-up demand is constant, and the policy effect is a pure gain: potable abstraction falls by the substituted volume and total withdrawal does not move. For $r>r^{*}$ the cycles fall with $r$, make-up demand per unit of heat rejected rises through $M=E\\,\\mathrm{CoC}/(\\mathrm{CoC}-1)$, and the gain is partly eroded: the penalty relative to the constant-CoC baseline is $+1.27\\%$ at $r=0.60$, $+4.08\\%$ at $r=0.70$, $+7.06\\%$ at $r=0.80$ and $+10.21\\%$ at $r=0.90$.",
        "The two regimes differ qualitatively. For $r\\le r^{*}$ the cycles equal the design value, make-up demand is constant, and the policy effect is a pure gain: potable abstraction falls by the substituted volume and total withdrawal does not move. For $r>r^{*}$ the cycles fall with $r$, make-up demand per unit of heat rejected rises through $M=E\\,\\mathrm{CoC}/(\\mathrm{CoC}-1)$, and the gain is partly eroded: the penalty is $+1.27\\%$ at $r=0.60$, $+4.08\\%$ at $r=0.70$, $+7.06\\%$ at $r=0.80$ and $+10.21\\%$ at $r=0.90$.",
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
