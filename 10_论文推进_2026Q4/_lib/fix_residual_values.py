"""修正残留的旧恒等式残差值 (2026-10-17).

【背景】P0-1 修复后主网格重跑, 恒等式残差从 2.55e-11 变为 4.37e-11 (相对 2.9e-16→3.55e-16)。
但主稿/SI 中仍有 6 处残留旧值 —— 它们不在我此前 grep 的范围里, 属漏网。

【实测】4.365575e-11 ML, 相对 3.5496e-16 (n=839)。
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
OLD_ABS = "2.55 × 10⁻¹¹"
NEW_ABS = "4.37 × 10⁻¹¹"
OLD_REL = "2.9 × 10⁻¹⁶"
NEW_REL = "3.55 × 10⁻¹⁶"
OLD_SHORT = "2.5 × 10⁻¹¹"
NEW_SHORT = "4.4 × 10⁻¹¹"

TARGETS = [
    ROOT / "A16_英文稿/manuscript_en_v3.md",
    ROOT / "A16_英文稿/supplementary_information.md",
]

total = 0
for p in TARGETS:
    t = p.read_text(encoding="utf-8")
    n0 = t.count(OLD_ABS) + t.count(OLD_REL) + t.count(OLD_SHORT)
    t = t.replace(OLD_ABS, NEW_ABS)
    t = t.replace(OLD_REL, NEW_REL)
    t = t.replace(OLD_SHORT, NEW_SHORT)
    p.write_text(t, encoding="utf-8")
    left = t.count(OLD_ABS) + t.count(OLD_REL) + t.count(OLD_SHORT)
    print(f"  {p.name}: 替换 {n0} 处, 残留 {left}")
    total += n0

print(f"\n合计 {total} 处")
print("复验:")
for p in TARGETS:
    t = p.read_text(encoding="utf-8")
    hits = re.findall(r"[\d.]+ × 10⁻¹[¹⁶]", t)
    from collections import Counter
    print(f"  {p.name}: {dict(Counter(hits))}")
