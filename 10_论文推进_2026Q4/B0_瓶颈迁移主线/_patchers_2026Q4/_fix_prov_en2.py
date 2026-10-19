# -*- coding: utf-8 -*-
"""用实际存在的锚点，在英文正文 §3.4 补入 6%/26% 来源链说明。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
EN = HERE / "04_wr_manuscript_en.md"

t = EN.read_text(encoding="utf-8")

# 找到 "The screen" 附近实际文本
i = t.find("The screen")
print("锚点上下文:", repr(t[i:i + 320]) if i >= 0 else "NF")

ADD = (" The two shares that calibrate $\\rho$ are a transcribed government statement rather than a "
       "first-hand measurement: the originating City report (File 26-1037) is not in our possession, "
       "and the figures reach us through an independent community report whose page 53 reproduces "
       "them in text, with its own warning that the denominators are not additive and that the "
       "supporting period needs disclosure (SI S7.2).")

# 插在 "This is a transferable screening procedure" 之前
ANCHOR = "This is a transferable screening procedure"
if ANCHOR in t and ADD.strip() not in t:
    t = t.replace(ANCHOR, ADD.strip() + " " + ANCHOR, 1)
    EN.write_text(t, encoding="utf-8")
    print("OK 已插入来源链说明")
else:
    print("锚点未匹配或已存在")

m = re.search(r"^##\s+Abstract\s*$(.*?)^##\s+", t, re.M | re.S)
ab = re.sub(r"\$[^$]*\$", " MATH ", m.group(1))
s = re.sub(r"\$[^$]*\$", " MATH ", t)
print(f"摘要 {len(ab.split())} | 全文 {len(s.split())}")
