# -*- coding: utf-8 -*-
"""修正论文中 38,666 / 32,649 的口径标注。

【事实（经 PDF 逐页核对）】
  p.65 原文：「all four of its supply sources will have a total average yield of about 38,700 AFY」
        并列出 5,041 / 4,560 / 23,048 / 6,017 —— 均确切出现在 p.65
  → 38,666 是四项之和的**推算值**，原文口径是「约 38,700」
  → 32,649 是 potable 三项之和（5,041+4,560+23,048）的**推算值**，
    且其成分出现在 p.66 的表 6-11，不是 p.65

【问题】正文把 38,666 与 32,649 当作 p.65 的原值引用，属"推算值冒充引用值"。
虽不影响 r 与 k 的计算（因为 k 用的是 32,649/6,017，r 用 k 推），但口径必须说清。

【修法】把两个数标注为"sum of the four components"，并注明原文写 about 38,700。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

MS_OLD = "（供给能力口径的构成：SFPUC 5,041 + Valley Water 4,560 + 地下水井 23,048 + 再生水 6,017 = 38,666 AFY。）"
MS_NEW = ("（供给能力口径的构成：SFPUC 5,041 + Valley Water 4,560 + 地下水井 23,048 + 再生水 6,017，"
          "四项**均见于 UWMP p.65**。UWMP 原文称四源合计「about 38,700 AFY」；本文用的 **38,666** 是四项之和，"
          "属**推算值而非原文数字**。同理 **potable 32,649** 为 5,041+4,560+23,048 之和，"
          "其成分载于 p.66 表 6-11 而非 p.65。两处口径须与原文区分。）")

EN_OLD = ("On supply capacity (SFPUC 5041, Valley Water 4560, groundwater 23,048 and recycled 6017, "
          "totalling 38,666 acre-feet per year) potable is 32,649 and reclaimed 6017, giving "
          "$k=5.43$ and $r=0.444$, 10.9 points below $r^{*}$.")
EN_NEW = ("On supply capacity the plan gives the four components as SFPUC 5041, Valley Water 4560, "
          "groundwater 23,048 and recycled 6017 acre-feet per year, described in the source as "
          "\"about 38,700\" in total; the 38,666 used here and the potable subtotal of 32,649 are "
          "our summations, not quoted figures. They give $k=5.43$ and $r=0.444$, 10.9 points below "
          "$r^{*}$.")

SI_OLD = ("On supply capacity (normal year, p.65) the components are SFPUC 5041, Valley Water 4560, "
          "groundwater wells 23,048 and recycled 6017, totalling 38,666 acre-feet per year; potable "
          "capacity is 32,649 AFY, giving $k=5.43$ and $r=0.444$, which is 10.9 percentage points "
          "below $r^{*}$.")
SI_NEW = ("On supply capacity the plan states, on p.65, that the four sources together yield \"about "
          "38,700 AFY\", itemised as SFPUC 5041, Valley Water 4560, groundwater wells 23,048 and "
          "recycled 6017 acre-feet per year. The 38,666 used here and the potable subtotal of 32,649 "
          "are our summations of those components, not figures printed in the plan; the components "
          "themselves appear on p.65 and in Table 6-11 on p.66. They give $k=5.43$ and $r=0.444$, "
          "10.9 points below $r^{*}$.")

n = 0
for path, old, new, tag in ((MS, MS_OLD, MS_NEW, "母稿"),
                            (EN, EN_OLD, EN_NEW, "英文"),
                            (SI, SI_OLD, SI_NEW, "SI")):
    t = path.read_text(encoding="utf-8")
    if old in t:
        path.write_text(t.replace(old, new, 1), encoding="utf-8")
        print(f"OK {tag}")
        n += 1
    else:
        print(f"未匹配 {tag}")
print(f"完成 {n}/3")
