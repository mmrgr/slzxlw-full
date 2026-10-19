# -*- coding: utf-8 -*-
"""诊断带 dist=bay 的 CCR 页面，找真实数据接口。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
b = Path(r"C:/Users/mmrgr/AppData/Local/Temp/_bayq.html").read_text(encoding="utf-8", errors="replace")
print("len", len(b), "| Santa Clara:", "Santa Clara" in b)

# 找所有疑似 API / JSON / endpoint
pats = [
    r"https?://[^\"'\s]+\.json[^\"'\s]*",
    r"/wp-json/[^\"'\s]+",
    r"admin-ajax\.php[^\"'\s]*",
    r"api/[^\"'\s]+",
    r"fetch\([^)]{0,120}\)",
    r"axios\.[a-z]+\([^)]{0,120}\)",
    r"\$\.(?:get|post|ajax)\([^)]{0,120}\)",
]
for p in pats:
    hits = list(dict.fromkeys(re.findall(p, b)))[:8]
    if hits:
        print(f"\n[{p}]")
        for h in hits:
            print("  ", h[:150])

# 找 script src
print("\n[script src]")
for s in list(dict.fromkeys(re.findall(r'<script[^>]+src="([^"]+)"', b)))[:15]:
    print("  ", s[:150])

# 找内联 script 里含 ccr/district 的片段
print("\n[内联 script 含 ccr/district/report]")
for m in re.finditer(r"<(script)[^>]*>(.*?)</script>", b, re.S):
    body = m.group(2)
    if any(k in body.lower() for k in ("ccr", "district", "report", "pdf")):
        print("  ...", body.strip()[:400].replace("\n", " "))
        print("  ---")
