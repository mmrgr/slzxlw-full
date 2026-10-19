# -*- coding: utf-8 -*-
"""在手上两个市府 PDF 中核验 6% / 26% 的文字来源。

论文 §5.9.2 声称：这两个百分比「只存在于图形中，PDF 文本层没有」，是通过渲染 p.27
为 200 dpi 图像后读图获得的。

但证据包的摘录卡（中文）声称它引自「正式市议会报告正文的 Water Usage 段落」，
并给出英文原句 "approximately 6% of the City's total potable water use"。

两者说法不同，必须核实：文本层里到底有没有这句话？

扫描对象：
  - Item 7 Post Meeting Material.pdf (73 页)
  - 030 Request from Councilmember Jain...pdf (1 页)
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = Path(r"C:/Users/mmrgr/Desktop/000")
FILES = [
    "Item 7 Post Meeting Material.pdf",
    "030 Request from Councilmember Jain on data center water usage and demand side support program.pdf",
]

PATTERNS = [
    "6%", "26%", "potable", "recycled", "approximately",
    "total potable water use", "total recycled water use", "Water Usage",
    "26-1037",
]


def main() -> None:
    for fname in FILES:
        p = BASE / fname
        if not p.exists():
            print(f"缺失 {fname}")
            continue
        doc = fitz.open(p)
        print(f"\n{'='*78}\n{fname}  ({doc.page_count} 页)\n{'='*78}")
        for pat in PATTERNS:
            hits = []
            for i in range(doc.page_count):
                if pat.lower() in doc[i].get_text().lower():
                    hits.append(i + 1)
            print(f"  {pat!r:36} 命中页: {hits[:12] if hits else '（无）'}")

        # 单独看 26-1037 与 6%/26% 同页的情况
        print("\n  --- 同时含 '6%' 与 '26%' 的页 ---")
        for i in range(doc.page_count):
            t = doc[i].get_text()
            if "6%" in t and "26%" in t:
                print(f"    p{i+1}")
                # 打印上下文
                for k in ("6%", "26%"):
                    idx = t.find(k)
                    print(f"      [{k}] …{t[max(0,idx-160):idx+120]}…".replace("\n", " "))

        # 单独看 26-1037
        print("\n  --- 含 '26-1037' 的页及其上下文 ---")
        for i in range(doc.page_count):
            t = doc[i].get_text()
            if "26-1037" in t:
                idx = t.find("26-1037")
                print(f"    p{i+1}: …{t[max(0,idx-200):idx+260]}…".replace("\n", " "))


if __name__ == "__main__":
    main()
