# -*- coding: utf-8 -*-
"""在 UWMP 全文中搜索水质数据（TDS / 电导率 / 氯化物 / 硬度）。

【为什么这是关键机会】
前几轮为了找 C_p（自来水 TDS）的锚点，反复去外部网站（santaclaraca.gov 403、
valleywater.org 403、calwater.com 无 Santa Clara），全部失败。

但 UWMP 是加州法定文件，**通常包含水源水质表**（DWR 要求描述水质以评估处理需求）。
若其中列出 Santa Clara 各水源的 TDS，就能**直接锚定 C_p**，无需任何外部数据。

UWMP 282 页一直在手上，但我只查过水量页（p.35/p.65），从未查过水质页。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PDF = Path(r"C:/Users/mmrgr/Desktop/000/2025 Urban Water Management Plan_Final.pdf")

KEYWORDS = [
    "TDS", "Total Dissolved Solids", "total dissolved solids",
    "Conductivity", "conductivity", "EC ", "µmhos", "umhos", "μS/cm",
    "Chloride", "chloride", "Hardness", "hardness",
    "Water Quality", "water quality",
]


def main() -> None:
    doc = fitz.open(PDF)
    n = doc.page_count
    print(f"页数 {n}")

    # 逐关键词统计命中页
    print(f"\n{'关键词':<28}{'命中页数':>8}   页码示例")
    print("-" * 78)
    hits_by_kw: dict[str, list[int]] = {}
    for kw in KEYWORDS:
        pages = [i + 1 for i in range(n) if kw in doc[i].get_text()]
        hits_by_kw[kw] = pages
        print(f"{kw:<28}{len(pages):>8}   {pages[:10]}")

    # 找同时含 TDS 与数值的页
    print(f"\n{'='*78}\n含 'TDS' 且含 3 位数字的页\n{'='*78}")
    for i in hits_by_kw.get("TDS", []):
        t = doc[i - 1].get_text()
        if re.search(r"\b\d{2,4}\b", t):
            print(f"\n--- PDF p.{i} ---")
            # 打印 TDS 附近上下文
            for m in re.finditer(r"TDS", t):
                seg = t[max(0, m.start() - 260):m.start() + 400]
                print("  …", " ".join(seg.split())[:620])
                break

    # 找含 conductivity 的页
    print(f"\n{'='*78}\n含 'onductivity' 的页\n{'='*78}")
    for i in hits_by_kw.get("Conductivity", []):
        t = doc[i - 1].get_text()
        print(f"\n--- PDF p.{i} ---")
        for m in re.finditer(r"[Cc]onductivity", t):
            seg = t[max(0, m.start() - 200):m.start() + 320]
            print("  …", " ".join(seg.split())[:520])
            break


if __name__ == "__main__":
    main()
