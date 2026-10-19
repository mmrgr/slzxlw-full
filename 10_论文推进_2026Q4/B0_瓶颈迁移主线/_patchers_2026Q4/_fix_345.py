# -*- coding: utf-8 -*-
"""修正：50/1450 = 3.45%，正文写的 3.4% 略低。统一改为 3.45%。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"
G = HERE / "_verify_co_grid.py"

print(f"准确值: 50/1450 = {100*50/1450:.4f}%")

n = 0
for p, pairs, tag in (
        (MS, [("相对基线 ≤ 3.4%", "相对基线 3.45%")], "母稿"),
        (EN, [("never exceeding 3.4% of its baseline", "never exceeding 3.45% of its baseline")], "英文"),
        (SI, [("3.4% of the baseline", "3.45% of the baseline")], "SI")):
    t = p.read_text(encoding="utf-8")
    ok = 0
    for old, new in pairs:
        if old in t:
            t = t.replace(old, new, 1)
            ok += 1
        else:
            print(f"  {tag} 未匹配: {old}")
    if ok:
        p.write_text(t, encoding="utf-8")
        print(f"OK {tag}")
        n += 1

# 门禁也同步
t = G.read_text(encoding="utf-8")
OLD = '''    pct = 100.0 * max(drops.values()) / base["50mw"]
    ck("CO 相对基线 ≤ 3.4%", pct <= 3.41, f"{pct:.2f}%")'''
NEW = '''    pct = 100.0 * max(drops.values()) / base["50mw"]
    ck("CO 相对基线 = 3.45%", abs(pct - 3.448) < 0.01, f"{pct:.2f}%")'''
if OLD in t:
    G.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK 门禁已改为精确断言")
else:
    print("门禁未匹配")
print(f"完成 {n}/3")
