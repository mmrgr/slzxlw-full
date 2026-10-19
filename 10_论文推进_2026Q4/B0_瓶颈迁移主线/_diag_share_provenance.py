# -*- coding: utf-8 -*-
"""深查市府原创材料（26-1037 本体）中 6%/26% 的表述，区分"市府原文"与"第三方引述"。

已知：
  - Item 7 p.53 有 "Data centers: about 6% of potable use and 26% of recycled use"，
    但该页是**第三方评论文档**（含 "October staff water figures [1]" 这种引用口吻、
    "Supporting period and volumes need disclosure" 这种审阅批注）
  - 证据包摘录卡声称的英文原句 "approximately 6% of the City's total potable water use"
    在两个 PDF 中都搜不到

需要确定：
  1. 市府自己的 staff presentation（26-1037 本体）在哪几页？里面怎么表述？
  2. 6%/26% 在市府本体中是否只以图形形式存在（论文原主张）？
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PDF = Path(r"C:/Users/mmrgr/Desktop/000/Item 7 Post Meeting Material.pdf")
doc = fitz.open(PDF)


def main() -> None:
    # 打印 p.53 前后各一页的开头，判断文档性质
    for pno in (51, 52, 53, 54):
        print(f"\n{'='*78}\nPDF p.{pno+1}\n{'='*78}")
        print(doc[pno].get_text()[:900])

    # 找 6%/26% 是否在含 "Staff Presentation" 的页面出现
    print(f"\n{'='*78}\n扫描含 'Staff Presentation' 的页\n{'='*78}")
    for i in range(doc.page_count):
        t = doc[i].get_text()
        if "Staff Presentation" in t:
            has6 = "6%" in t
            has26 = "26%" in t
            print(f"  p{i+1}: 6%={'Y' if has6 else 'n'} 26%={'Y' if has26 else 'n'}  "
                  f"{t[:90].replace(chr(10),' ')}")

    # 全文里 "of potable use" / "of recycled use" 的所有出现
    print(f"\n{'='*78}\n'potable use' / 'recycled use' 全部出现\n{'='*78}")
    for i in range(doc.page_count):
        t = doc[i].get_text()
        for kw in ("of potable use", "of recycled use", "potable water use", "recycled water use"):
            if kw in t:
                idx = t.find(kw)
                print(f"  p{i+1} [{kw}]: …{t[max(0,idx-130):idx+130]}…".replace("\n", " "))


if __name__ == "__main__":
    main()
