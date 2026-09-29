# -*- coding: utf-8 -*-
import os, glob, re
SRC = r"C:/Users/mmrgr/Desktop/论文/算力中心/.lit_extract/docx_txt"
OUT = os.path.join(SRC, "_deep_sections.txt")
blocks = []
for f in sorted(glob.glob(os.path.join(SRC, "*.txt"))):
    base = os.path.basename(f)
    if base.startswith("_"): continue
    txt = open(f, encoding='utf-8').read()
    # split into translation body and deep-review
    idx = txt.find("论文深度解读")
    if idx < 0:
        blocks.append(f"\n\n########## {base}  [无深度解读段] ##########\n" + txt[:1500])
        continue
    head = txt[:idx]
    deep = txt[idx:]
    blocks.append(f"\n\n########## {base} ##########\n[HEAD_LEN={len(head)} DEEP_LEN={len(deep)}]\n{deep}")
    # also record length of each section header in head
with open(OUT, 'w', encoding='utf-8') as fh:
    fh.write(''.join(blocks))
print("written", OUT, os.path.getsize(OUT))
