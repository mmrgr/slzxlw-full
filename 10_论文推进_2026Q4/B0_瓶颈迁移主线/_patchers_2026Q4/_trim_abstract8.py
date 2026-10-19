# -*- coding: utf-8 -*-
"""摘要最后 2 词。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    ("Such assessments treat the substitution ratio as a free policy variable and never test "
     "whether raising it costs anything.",
     "Such assessments treat the substitution ratio as a free policy variable, never testing "
     "whether raising it costs anything."),
]


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    for old, new in PAIRS:
        if old in t:
            t = t.replace(old, new, 1)
        else:
            print("未匹配")
    MS.write_text(t, encoding="utf-8")
    m = re.search(r"^##\s+Abstract\s*$(.*?)^##\s+", t, re.M | re.S)
    ab = re.sub(r"\$[^$]*\$", " MATH ", m.group(1))
    s = re.sub(r"\$[^$]*\$", " MATH ", t)
    print(f"摘要 {len(ab.split())} | 全文 {len(s.split())}")


if __name__ == "__main__":
    main()
