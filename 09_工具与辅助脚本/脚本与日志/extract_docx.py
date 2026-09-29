import sys
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

src = r"C:\Users\mmrgr\Desktop\开题\开题报告3.3.docx"
out = r"C:\Users\mmrgr\WorkBuddy\2026-09-15-10-49-54\kaoti_text.txt"

doc = Document(src)
lines = []

def iter_block_items(parent):
    from docx.oxml.ns import qn
    body = parent.element.body
    for child in body.iterchildren():
        if child.tag == qn('w:p'):
            yield Paragraph(child, parent)
        elif child.tag == qn('w:tbl'):
            yield Table(child, parent)

for block in iter_block_items(doc):
    if isinstance(block, Paragraph):
        t = block.text.strip()
        if not t:
            continue
        st = block.style.name if block.style else ""
        prefix = ""
        if st and st.lower().startswith("heading"):
            prefix = f"[{st}] "
        elif "Title" in st:
            prefix = "[TITLE] "
        lines.append(prefix + t)
    elif isinstance(block, Table):
        lines.append("<<TABLE>>")
        for row in block.rows:
            cells = [c.text.strip().replace("\n", " ") for c in row.cells]
            lines.append(" | ".join(cells))
        lines.append("<</TABLE>>")

with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("WROTE", len(lines), "lines")
