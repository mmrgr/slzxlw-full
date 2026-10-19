# -*- coding: utf-8 -*-
"""提取 Cal Water CCR 页面中被隐藏的 wq-city 块（含各城市的报告链接）。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
b = Path(r"C:/Users/mmrgr/AppData/Local/Temp/_bayq.html").read_text(encoding="utf-8", errors="replace")

# 找出所有 wq-city div 的 id 与 data-wq-district
ids = re.findall(r'class="wq-city"[^>]*data-wq-district="([^"]*)"[^>]*id="([^"]*)"', b)
if not ids:
    ids = re.findall(r'id="([^"]*)"[^>]*class="wq-city"[^>]*data-wq-district="([^"]*)"', b)
print(f"wq-city 块数: {len(ids)}")
for a, c in ids[:40]:
    print("  ", a, c)

# 直接搜 Santa Clara 相关（大小写/连字符变体）
print("\n[Santa Clara 变体搜索]")
for v in ("santa", "clara", "Santa", "Clara"):
    c = b.lower().count(v.lower())
    print(f"  {v}: {c}")

# 找 wq-city 的完整结构（第一个）
m = re.search(r'<div[^>]*class="wq-city"[^>]*>', b)
if m:
    print("\n[第一个 wq-city 起的 1200 字符]")
    print(b[m.start():m.start() + 1200])
