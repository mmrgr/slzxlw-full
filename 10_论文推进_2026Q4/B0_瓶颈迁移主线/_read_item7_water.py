# -*- coding: utf-8 -*-
"""细读 Item 7 中与冷却技术/WUE/水量相关的页（59-62, 66, 68-69, 72-73）。

【目的】
论文的 WUE、冷却技术参数目前全为假设值（参数包络表标"无锚点"）。
若这份市议会材料给出**实测或官方估计的 WUE / 冷却方式分布 / 单位 MW 用水量**，
就能给水侧参数一个真实锚点——这是比 C_p 更贴近模型核心的参数。

Hits: water use [59,61], WUE [61,62,69,73], evaporative [59,68],
      liquid cooling [59], gallons [60,61,62,69,73], makeup [72]
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PDF = Path(r"C:/Users/mmrgr/Desktop/000/Item 7 Post Meeting Material.pdf")
PAGES = [59, 60, 61, 62, 66, 68, 69, 72, 73]


def main() -> None:
    doc = fitz.open(PDF)
    for p in PAGES:
        t = " ".join(doc[p - 1].get_text().split())
        print(f"\n{'='*80}\nPDF p.{p}\n{'='*80}")
        print(t[:2400])


if __name__ == "__main__":
    main()
