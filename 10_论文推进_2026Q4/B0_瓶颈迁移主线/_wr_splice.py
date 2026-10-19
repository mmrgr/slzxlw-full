# -*- coding: utf-8 -*-
"""拼接 WR 英文稿分块：删除截断尾部后追加新块。"""
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
PART = HERE / "_wr_part2_intro_methods.md"


def main() -> None:
    text = MS.read_text(encoding="utf-8")
    # 删除上次 here-doc 截断留下的不完整 §1/§2 段：从第一个 "## 1. Introduction" 起到文件末尾全部砍掉
    idx = text.find("## 1. Introduction")
    if idx != -1:
        text = text[:idx].rstrip() + "\n\n"
    part = PART.read_text(encoding="utf-8").strip() + "\n"
    MS.write_text(text + part, encoding="utf-8")

    # 统计
    t = MS.read_text(encoding="utf-8")
    def wc(s: str) -> int:
        s = re.sub(r"\$[^$]*\$", " MATH ", s)
        return len(s.split())
    parts = re.split(r"^(##\s+.+)$", t, flags=re.M)
    print(f"{'节':<46}{'words':>8}")
    print("-" * 56)
    tot = 0
    for i in range(1, len(parts), 2):
        n = wc(parts[i + 1] if i + 1 < len(parts) else "")
        tot += n
        print(f"{parts[i].strip()[:44]:<46}{n:>8}")
    print("-" * 56)
    print(f"{'合计':<46}{tot:>8}")


if __name__ == "__main__":
    main()
