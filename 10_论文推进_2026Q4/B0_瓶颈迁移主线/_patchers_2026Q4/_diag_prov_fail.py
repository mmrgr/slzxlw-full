# -*- coding: utf-8 -*-
"""诊断来源链核验的 5 项失败。"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PDF = Path(r"C:/Users/mmrgr/Desktop/000/Item 7 Post Meeting Material.pdf")
EN = Path(__file__).resolve().parent / "04_wr_manuscript_en.md"

doc = fitz.open(PDF)
print("=== 各页是否含 'Independent community report' ===")
hits = [i + 1 for i in range(doc.page_count)
        if "Independent community report" in doc[i].get_text()]
print("  页码:", hits[:10])

print("\n=== p.53 原文（含 6%/26% 那段）===")
p53 = doc[52].get_text()
i = p53.find("6%")
print(repr(p53[max(0, i - 400):i + 700]))

print("\n=== 全文中 'disclosure' / 'Supporting' 出现处 ===")
for i in range(doc.page_count):
    t = doc[i].get_text()
    if "disclosure" in t.lower() or "Supporting" in t:
        j = max(t.lower().find("disclosure"), t.find("Supporting"))
        print(f"  p{i+1}: …{t[max(0,j-250):j+250]}…".replace("\n", " ")[:520])

print("\n=== 英文稿是否含这些表述 ===")
en = EN.read_text(encoding="utf-8")
for kw in ("transcribed", "not in our possession", "not held",
           "government statement", "Water Usage"):
    print(f"  {kw!r}: {en.count(kw)}")
