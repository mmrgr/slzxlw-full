# -*- coding: utf-8 -*-
"""诊断 Cal Water 水质报告页的动态数据接口。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
b = Path(r"C:/Users/mmrgr/AppData/Local/Temp/_cwr.html").read_text(encoding="utf-8", errors="replace")
print("页面长度", len(b))
print("含 'Santa Clara':", "Santa Clara" in b, "| 小写 santa 计数:", b.lower().count("santa"))

for pat in (r"wp-json[^\"' ]*", r"admin-ajax\.php[^\"' ]*", r"wpv_view_count[^\"' ]*"):
    hits = list(set(re.findall(pat, b)))[:6]
    print(f"\n[{pat}]")
    for h in hits:
        print("  ", h[:130])

# 找 data-* 属性里可能带地区 id 的
attrs = re.findall(r'(data-[a-z0-9-]+)="([^"]{0,80})"', b)
seen = set()
print("\n[data-* 属性（去重前 20）]")
for k, v in attrs:
    key = (k, v[:30])
    if key in seen:
        continue
    seen.add(key)
    if any(x in k for x in ("district", "office", "region", "location", "report")):
        print(f"   {k}={v[:60]}")
    if len(seen) > 40:
        break

# 找页面里出现的地区名
names = re.findall(r">([A-Z][A-Za-z .]{3,28})</(?:option|a|li|td)>", b)
print("\n[可能的地区名（前 20，去重）]")
for n in list(dict.fromkeys(names))[:20]:
    print("  ", n)
