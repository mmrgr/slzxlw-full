# -*- coding: utf-8 -*-
"""留 10 词余量。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("Because $r^{*}$ is easily mistaken for a city constant, note that its sign and magnitude are "
     "themselves classificatory.",
     "Because $r^{*}$ is easily mistaken for a city constant, its sign and magnitude are themselves "
     "classificatory."),
    ("Roughly one recycled-water system in seven would cross it if it hosted data centres with Santa "
     "Clara's 6%/26% shares.",
     "Roughly one recycled-water system in seven would cross it given Santa Clara's 6%/26% shares."),
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
