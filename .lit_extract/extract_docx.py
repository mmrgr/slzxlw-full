# -*- coding: utf-8 -*-
import os, glob, re
from docx import Document

SRC = r"C:/Users/mmrgr/Desktop/论文/算力中心/06_文献库/lw"
OUT = r"C:/Users/mmrgr/Desktop/论文/算力中心/.lit_extract/docx_txt"
os.makedirs(OUT, exist_ok=True)

def norm(s):
    s = s.replace('\u00a0', ' ')
    s = re.sub(r'[ \t]+', ' ', s)
    return s.strip()

def para_text(p):
    # join runs, keep inline breaks
    return norm(''.join(r.text for r in p.runs) or p.text)

def table_text(t):
    lines = []
    for row in t.rows:
        cells = [norm(c.text) for c in row.cells]
        # dedupe merged cells
        seen = []
        for c in cells:
            if not seen or seen[-1] != c:
                seen.append(c)
        lines.append(' | '.join(seen))
    return lines

for f in sorted(glob.glob(os.path.join(SRC, '*.docx'))):
    if os.path.basename(f).startswith('~$'):
        continue
    base = os.path.splitext(os.path.basename(f))[0]
    base = base.replace('_zh-CN', '')
    try:
        d = Document(f)
    except Exception as e:
        print('FAIL', base, e); continue
    body = d.element.body
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    from docx.oxml.ns import qn
    lines = []
    for child in body.iterchildren():
        if child.tag == qn('w:p'):
            p = Paragraph(child, d)
            t = para_text(p)
            if t:
                lines.append(t)
        elif child.tag == qn('w:tbl'):
            t = Table(child, d)
            lines.append('[TABLE]')
            lines.extend(table_text(t))
            lines.append('[/TABLE]')
    txt = '\n'.join(lines)
    op = os.path.join(OUT, re.sub(r'[\\/:*?"<>|]', '_', base)[:90] + '.txt')
    with open(op, 'w', encoding='utf-8') as fh:
        fh.write(txt)
    print(f'{len(txt):>8}  {os.path.basename(op)}')
