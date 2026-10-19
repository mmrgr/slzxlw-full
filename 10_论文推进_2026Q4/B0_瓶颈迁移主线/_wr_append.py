# -*- coding: utf-8 -*-
"""通用拼接：把 _wr_partN_*.md 依次追加到英文稿，并统计各节词数。

用法:
    python _wr_append.py _wr_part3_results.md
"""
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


def wc(s: str) -> int:
    s = re.sub(r"\$[^$]*\$", " MATH ", s)
    return len(s.split())


def report(text: str) -> int:
    parts = re.split(r"^(##\s+.+)$", text, flags=re.M)
    print(f"{'节':<46}{'words':>8}")
    print("-" * 56)
    tot = 0
    for i in range(1, len(parts), 2):
        n = wc(parts[i + 1] if i + 1 < len(parts) else "")
        tot += n
        print(f"{parts[i].strip()[:44]:<46}{n:>8}")
    print("-" * 56)
    print(f"{'合计（含 Abstract）':<46}{tot:>8}")
    return tot


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python _wr_append.py <part.md> [...]")
        return
    text = MS.read_text(encoding="utf-8").rstrip() + "\n\n"
    for arg in sys.argv[1:]:
        p = HERE / arg
        if not p.exists():
            print("MISSING", p)
            continue
        text += p.read_text(encoding="utf-8").strip() + "\n\n"
    MS.write_text(text, encoding="utf-8")
    report(MS.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
