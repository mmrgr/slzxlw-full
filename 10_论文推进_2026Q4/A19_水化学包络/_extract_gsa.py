import re
import sys
import pymupdf

p = r"C:/Users/mmrgr/Desktop/论文/算力中心/07_代码_AI-UWM引擎/aiuwm_src/research_2026/external_evidence/gsa_blowdown_recovery_2023/GSA_Blowdown_Recovery_System_Full_Report.pdf"
d = pymupdf.open(p)
txt = "\n".join(pg.get_text() for pg in d)
out = r"C:/Users/mmrgr/Desktop/论文/算力中心/10_论文推进_2026Q4/A19_水化学包络/_gsa_extract.txt"
open(out, "w", encoding="utf-8").write(txt)
print("pages", len(d), "chars", len(txt))
for kw in ["cycle", "Cycle", "concentration", "Concentration", "LSI", "Langelier",
           "inhibit", "scale", "Scale", "silica", "blowdown", "antiscalant",
           "COC", "CoC", "conductivity", "alkalinity", "pH"]:
    print(f"{kw:16s} {len(re.findall(kw, txt))}")
