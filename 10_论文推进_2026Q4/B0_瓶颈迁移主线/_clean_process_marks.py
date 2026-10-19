# -*- coding: utf-8 -*-
"""清理主稿中的过程性标记（"本轮新增""v2 新增"等），使其成为定稿文本。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
V2 = HERE / "03_主稿_v2.md"

# 具体替换（精确匹配，避免误伤）
REPLACEMENTS = [
    ("（**本轮新增，论证重心之一**）", ""),
    ("（v2 新增）", ""),
    ("（本章重组：从两杠杆到三杠杆（v2 新增））", "（本章重组：从两杠杆到三杠杆）"),
    ("### 7.0 本章重组：从两杠杆到三杠杆", "### 7.0 本章的结构：从两杠杆到三杠杆"),
    ("### 8.6 政策意义：判据的价值在于界定安全区间", "### 8.6 政策意义：判据的价值在于界定安全区间"),
    ("### 8.5 与水质兼容性文献的对接", "### 8.5 与水质兼容性文献的对接"),
]

# 全部已知过程性标记
PATTERNS = [
    r"（\*\*本轮新增，论证重心之一\*\*）",
    r"（v2 新增）",
    r"（本轮新增）",
    r"\(v2 新增\)",
]


def main() -> None:
    t = V2.read_text(encoding="utf-8")
    orig = t

    # 先做精确替换
    for old, new in REPLACEMENTS:
        if old in t and old != new:
            t = t.replace(old, new)
            print(f"[OK  ] 替换：{old[:40]} → {new[:40] if new else '（删除）'}")

    # 再用正则清理残留
    for pat in PATTERNS:
        n = len(re.findall(pat, t))
        if n:
            t = re.sub(pat, "", t)
            print(f"[OK  ] 正则清理 {n} 处：{pat}")

    # 清理可能产生的双空格/空括号
    t = re.sub(r"（）", "", t)
    t = re.sub(r"[ \t]+\n", "\n", t)

    if t == orig:
        print("[SKIP] 无需修改")
        return

    V2.write_text(t, encoding="utf-8")
    print("-" * 60)
    print(f"字数 {len(orig):,} → {len(t):,}；行数 {t.count(chr(10)) + 1}")


if __name__ == "__main__":
    main()
