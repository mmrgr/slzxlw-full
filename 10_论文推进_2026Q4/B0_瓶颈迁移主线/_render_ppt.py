# -*- coding: utf-8 -*-
"""把 PPT 转出的 PDF 渲染成 PNG，供人工/模型目检。"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import pypdfium2 as pdfium

HERE = Path(__file__).resolve().parent
src = HERE / "_chk" / "62_导师汇报_10页_20261020.pdf"
out = HERE / "_chk"

pdf = pdfium.PdfDocument(str(src))
print("页数:", len(pdf))
for i in range(len(pdf)):
    pdf[i].render(scale=1.7).to_pil().save(str(out / ("s%02d.png" % (i + 1))))
print("已渲染到", out)
