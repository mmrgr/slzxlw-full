# -*- coding: utf-8 -*-
"""诊断 GAMA 数据里的县名与化学名实际取值。"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SRC = Path(r"C:/Users/mmrgr/AppData/Local/Temp/_gama.csv")

counties = Counter()
chems = Counter()
n = 0
with SRC.open("r", encoding="utf-8", errors="replace", newline="") as f:
    import csv
    rd = csv.DictReader(f)
    for row in rd:
        n += 1
        c = (row.get("gm_county_name") or "").strip()
        if c:
            counties[c] += 1
        ch = (row.get("gm_chemical_name") or "").strip()
        if ch:
            chems[ch] += 1
        if n >= 1_836_529:
            break

print(f"扫描 {n:,} 行")
print(f"\n县名取值数 {len(counties)}，含 SANTA CLARA 的：")
for k, v in counties.items():
    if "SANTA" in k.upper() or "CLARA" in k.upper():
        print(f"  {k!r}: {v:,}")
print("\n前 20 个县名：")
for k, v in counties.most_common(20):
    print(f"  {k!r}: {v:,}")

print(f"\n化学名取值数 {len(chems)}，含 TDS/CONDUCT/CHLOR 的：")
for k, v in chems.items():
    ku = k.upper()
    if "TDS" in ku or "CONDUCT" in ku or "CHLOR" in ku or "DISSOLVED" in ku:
        print(f"  {k!r}: {v:,}")
print("\n前 25 个化学名：")
for k, v in chems.most_common(25):
    print(f"  {k!r}: {v:,}")
