# -*- coding: utf-8 -*-
"""1) 在英文正文 §3.4 补上 6%/26% 的来源链说明；
2) 修正 _verify_share_provenance.py 的换行处理与封面页码。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
EN = HERE / "04_wr_manuscript_en.md"
GATE = HERE / "_verify_share_provenance.py"

# ---------- 1) 英文正文补来源链 ----------
t = EN.read_text(encoding="utf-8")
ANCHOR = ("The screen needs only two published numbers: a city whose ratio of potable to reclaimed "
          "use falls below 3.50 has a substitution ratio that necessarily exceeds $r^{*}$.")
ADD = (" The two shares that calibrate $\\rho$ are a transcribed government statement rather than a "
       "first-hand measurement: the originating City report (File 26-1037) is not in our possession, "
       "and the figures reach us through an independent community report whose page 53 reproduces "
       "them in text, together with its own warning that the two denominators are not additive and "
       "that the supporting period needs disclosure (SI S7.2).")

if ANCHOR in t:
    t = t.replace(ANCHOR, ANCHOR + ADD, 1)
    EN.write_text(t, encoding="utf-8")
    print("OK 英文正文已补来源链")
else:
    print("未匹配英文锚点")

# 移除此前误加在摘要末尾的那句（若仍在）
OLD_AB = (" Those two shares are a transcribed government statement, not a first-hand measurement "
          "(SI S7.2).")
if OLD_AB in t:
    t = t.replace(OLD_AB, "", 1)
    EN.write_text(t, encoding="utf-8")
    print("OK 移除摘要中的重复句")

m = re.search(r"^##\s+Abstract\s*$(.*?)^##\s+", t, re.M | re.S)
ab = re.sub(r"\$[^$]*\$", " MATH ", m.group(1))
s = re.sub(r"\$[^$]*\$", " MATH ", t)
print(f"摘要 {len(ab.split())} | 全文 {len(s.split())}")

# ---------- 2) 修正门禁脚本 ----------
g = GATE.read_text(encoding="utf-8")
g = g.replace(
    '''        p1 = doc[0].get_text()
        ck("PDF 封面标明 Independent community report",
           "Independent community report" in p1, p1[:60].replace("\\n", " "))
        p53 = doc[52].get_text()
        ck("p.53 文本层含 6%",
           "6%" in p53, "6% found" if "6%" in p53 else "missing")
        ck("p.53 文本层含 26%", "26%" in p53, "")
        ck("p.53 含 'of potable use'", "of potable use" in p53, "")
        ck("p.53 含 'not 32% of combined use'", "not 32% of combined use" in p53, "")
        ck("p.53 含 'Supporting period and volumes need disclosure'",
           "Supporting period and volumes need disclosure" in p53, "")''',
    '''        # 封面页本身是市府议程页；社区报告的页眉出现在 p.48 起
        ck("PDF 含标明 Independent community report 的页",
           any("Independent community report" in doc[i].get_text()
               for i in range(doc.page_count)), "p.48+")
        # PDF 换行会把短语切断，比较前先把所有空白折叠成单空格
        p53 = " ".join(doc[52].get_text().split())
        ck("p.53 文本层含 6%", "6%" in p53, "6% found" if "6%" in p53 else "missing")
        ck("p.53 文本层含 26%", "26%" in p53, "")
        ck("p.53 含 'of potable use'", "of potable use" in p53, "")
        ck("p.53 含 'not 32% of combined use'", "not 32% of combined use" in p53, "")
        ck("p.53 含 'Supporting period and volumes need disclosure'",
           "Supporting period and volumes need disclosure" in p53, "")''')
g = g.replace(
    '''    ck("英文写明 'transcribed government statement'",
       "transcribed government statement" in en, "")
    ck("英文写明 'not in our possession' 或等价",
       "not held" in en or "not in our possession" in en, "")''',
    '''    ck("英文写明 'transcribed government statement'",
       "transcribed government statement" in en, "")
    ck("英文写明 'not in our possession' 或等价",
       "not in our possession" in en or "not held" in en, "")''')
GATE.write_text(g, encoding="utf-8")
print("OK 门禁脚本已修正（换行折叠 + 封面页改为任页匹配）")
