# -*- coding: utf-8 -*-
import os, glob
SRC = r"C:/Users/mmrgr/Desktop/论文/算力中心/.lit_extract/docx_txt"
OUT = os.path.join(SRC, "_digest.txt")
KEEP = ["核心结论","研究问题与真正贡献","关键证据与实验结果","论文没有证明什么","可复现性清单","价值、适用条件与下一步","最终记忆卡"]
blocks=[]
for f in sorted(glob.glob(os.path.join(SRC,"*.txt"))):
    b=os.path.basename(f)
    if b.startswith("_") or b.startswith("Global data"): continue
    t=open(f,encoding='utf-8').read()
    i=t.find("论文深度解读")
    if i<0: continue
    t=t[i:]
    # split by headings
    import re
    parts=re.split(r'(?m)^\s*(' + '|'.join(map(re.escape,KEEP)) + r')\s*$', t)
    picks=[]
    for k in range(1,len(parts),2):
        picks.append(parts[k]+"\n"+parts[k+1])
    head=None
    blocks.append("\n\n================ "+b+" ================\n"+"\n".join(picks))
r=''.join(blocks)
open(OUT,'w',encoding='utf-8').write(r)
print("chars:",len(r))
