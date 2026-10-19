# -*- coding: utf-8 -*-
"""细查 UWMP 的 Water Quality 相关页（p.61-75, p.111, p.231），找可锚定 C_p/C_r 的数值。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PDF = Path(r"C:/Users/mmrgr/Desktop/000/2025 Urban Water Management Plan_Final.pdf")

PAGES = [5, 61, 62, 67, 68, 71, 72, 74, 75, 111, 231]


def main() -> None:
    doc = fitz.open(PDF)
    for p in PAGES:
        t = doc[p - 1].get_text()
        flat = " ".join(t.split())
        print(f"\n{'='*78}\nPDF p.{p}  (len {len(flat)})\n{'='*78}")
        # 找 water quality / recycled 相关句子
        found = False
        for kw in ("water quality", "Water Quality", "recycled water quality",
                   "recycled water", "salinity", "salt", "mineral"):
            for m in re.finditer(kw, flat):
                seg = flat[max(0, m.start() - 200):m.start() + 380]
                print(f"  [{kw}] …{seg}…")
                found = True
                break
            if found and kw in ("water quality", "Water Quality"):
                break
        if not found:
            print("  （无相关关键词）")
            print("  前 300 字:", flat[:300])

    # 全文中查找 recycled water 出厂水质描述
    print(f"\n{'='*78}\n全文含 'recycled' 且含 'quality' 的页\n{'='*78}")
    for i in range(doc.page_count):
        t = doc[i].get_text()
        tl = t.lower()
        if "recycled" in tl and "quality" in tl:
            flat = " ".join(t.split())
            j = tl.find("quality")
            print(f"\n  p.{i+1}: …{flat[max(0,j-260):j+340]}…")


if __name__ == "__main__":
    main()
