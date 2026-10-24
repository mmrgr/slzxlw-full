# -*- coding: utf-8 -*-
"""最小实验：验证 python-docx 插入的 OMML 公式能否被 Word 识别为公式对象。

生成 3 种形态，用 Word COM 打开检查 Document.OMaths.Count 与 Range.Text，
并导出 PDF 供目检。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from docx import Document
from docx.oxml import parse_xml
from docx.shared import Pt

HERE = Path(__file__).resolve().parent
OUT = HERE / "10_论文推进_2026Q4" if False else HERE
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

NSDECL = 'xmlns:m="%s" xmlns:w="%s"' % (M, W)


def omml_linear(text: str) -> str:
    """线性公式：整段文本一个 run，Word 显示为线性 UnicodeMath。"""
    esc = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
           .replace('"', "&quot;"))
    return (
        "<m:oMath %s>"
        '<m:r><m:rPr><m:sty m:val="p"/></m:rPr>'
        '<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr>'
        '<m:t xml:space="preserve">%s</m:t></m:r>'
        "</m:oMath>" % (NSDECL, esc)
    )


def omml_professional() -> str:
    """专业公式：m:f 分式结构。"""
    return (
        "<m:oMath %s>"
        "<m:f><m:num><m:r><m:t>L</m:t></m:r></m:num>"
        "<m:den><m:r><m:t>CoC</m:t></m:r></m:den></m:f>"
        "</m:oMath>" % NSDECL
    )


def omml_sub_sup() -> str:
    """带上下标结构。"""
    return (
        "<m:oMath %s>"
        "<m:sSup><m:e><m:r><m:t>C</m:t></m:r></m:e>"
        "<m:sup><m:r><m:t>*</m:t></m:r></m:sup></m:sSup>"
        "<m:r><m:t>=</m:t></m:r>"
        "<m:sSub><m:e><m:r><m:t>r</m:t></m:r></m:e>"
        "<m:sub><m:r><m:t>max</m:t></m:r></m:sub></m:sSub>"
        "</m:oMath>" % NSDECL
    )


def main() -> int:
    doc = Document()

    doc.add_paragraph("A. 线性公式（单 run 纯文本）:")
    p = doc.add_paragraph()
    p.add_run("前文 ")
    p._p.append(parse_xml(omml_linear("r^*=(L/CoC_d -C_p)/(C_r-C_p)")))
    p.add_run(" 后文")

    doc.add_paragraph("B. 专业公式（m:f 分式）:")
    p = doc.add_paragraph()
    p._p.append(parse_xml(omml_professional()))

    doc.add_paragraph("C. 上下标结构:")
    p = doc.add_paragraph()
    p._p.append(parse_xml(omml_sub_sup()))

    doc.add_paragraph("D. 线性含特殊符号:")
    p = doc.add_paragraph()
    p._p.append(parse_xml(omml_linear(
        "3.45×10^(-13)%,  r≤r^*,  C_mix<L,  ρ≡α/β,  k^*=(1/r^* -1)/ρ,  ∓10%,  r∈[0,1]")))

    out = HERE / "_tmp_omml_test.docx"
    doc.save(out)
    print("saved", out.name, out.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
