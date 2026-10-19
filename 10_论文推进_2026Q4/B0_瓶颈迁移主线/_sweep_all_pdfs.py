# -*- coding: utf-8 -*-
"""对全部 5 份一手 PDF 做"水质 + 水量 + 能耗"三维度穷举检索。

【为什么】
上一轮的教训是：UWMP 282 页在手上，却只查过水量维度，漏掉了水质维度里
支撑机制前提的三段关键陈述。

因此本轮对**全部**一手材料做同样的事：
  1. 每份文档 × 每个维度关键词，统计命中页；
  2. 对命中页打印上下文；
  3. 特别关注此前从未用过的两份：
       - Item 7 Post Meeting Material.pdf (73 页，独立社区报告)
       - Estimated Makeup of Computing Workload Purposes...pdf
"""
from __future__ import annotations

import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = Path(r"C:/Users/mmrgr/Desktop/000")

DOCS = [
    "Item 7 Post Meeting Material.pdf",
    "Estimated Makeup of Computing Workload Purposes in Santa Clara Data Centers.pdf",
    "Data Center Location Map Oct 2026.pdf",
    "030 Request from Councilmember Jain on data center water usage and demand side support program.pdf",
]

# 维度分组：水质 / 水量 / 冷却与浓缩倍数 / 能耗与容量
DIMS = {
    "水质": ["TDS", "dissolved solids", "salinity", "conductivity", "chloride",
             "hardness", "cycles of concentration", "concentration cycle", "blowdown"],
    "水量": ["water use", "potable", "recycled", "AF", "acre-feet", "gallons",
             "makeup", "make-up", "million gallons"],
    "冷却系统": ["cooling tower", "cooling tower", "evaporative", "dry cooler",
                 "liquid cooling", "WUE", "water usage effectiveness"],
    "能耗容量": ["MW", "megawatt", "GWh", "PUE", "power", "energy"],
}


def main() -> None:
    for fname in DOCS:
        p = BASE / fname
        if not p.exists():
            print(f"\n缺失: {fname}")
            continue
        doc = fitz.open(p)
        n = doc.page_count
        print(f"\n{'='*80}\n{fname}\n({n} 页)\n{'='*80}")
        texts = [" ".join(doc[i].get_text().split()) for i in range(n)]

        for dim, kws in DIMS.items():
            print(f"\n  [{dim}]")
            for kw in kws:
                pages = [i + 1 for i, t in enumerate(texts) if kw.lower() in t.lower()]
                if pages:
                    print(f"    {kw:<26} {len(pages):>4} 页  {pages[:12]}")


if __name__ == "__main__":
    main()
