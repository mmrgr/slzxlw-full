# -*- coding: utf-8 -*-
"""查清 38,666 与 32,649 在 UWMP 里是否真的不存在，以及它们是怎么来的。

论文 §5.9.4 把这两个数写成 p.65 的内容。若 PDF 无此文字，则属
"把推算值当作引用值"，必须改口径。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PDF = Path(r"C:/Users/mmrgr/Desktop/000/2025 Urban Water Management Plan_Final.pdf")

doc = fitz.open(PDF)
# 全文去逗号拼接，用于搜索
pages = [(i, doc[i].get_text()) for i in range(doc.page_count)]
decomma = [(i, t.replace(",", "")) for i, t in pages]

print("=== 搜索 38666 / 32649 ===")
for target in ("38666", "32649"):
    hits = [i + 1 for i, t in decomma if target in t]
    print(f"  {target}: 出现在 PDF 页码 {hits if hits else '（无）'}")

print("\n=== 搜索 5,041 / 4,560 / 23,048 / 6,017 / 16,857 / 3,871 / 20,728 ===")
for target in ("5041", "4560", "23048", "6017", "16857", "3871", "20728"):
    hits = [i + 1 for i, t in decomma if target in t]
    print(f"  {'{:,}'.format(int(target)):>7}: PDF 页 {hits[:6] if hits else '（无）'}")

# p.65 完整文本，看它到底给出什么
print("\n=== PDF p.65 全文 ===")
print(doc[64].get_text()[:1800])

# 看 p.64/66 是否有 supply 表
print("\n=== PDF p.64 末 600 字 ===")
print(doc[63].get_text()[-600:])
