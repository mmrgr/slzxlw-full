"""找出所有残留的硬编码绝对路径 (2026-10-17).

上一轮只替换了"引擎路径"与"外部数据路径"两种模式,
漏掉了 `Path(r"C:\\Users\\mmrgr\\...\\10_论文推进_2026Q4")` 这类**项目根路径**。
本脚本用更宽的匹配找出全部残留。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
PAT = re.compile(r'["\']C:[\\/]+Users[\\/]+mmrgr[^"\']*["\']')

hits = []
for p in sorted(ROOT.glob("**/*.py")):
    s = str(p)
    if "__pycache__" in s or "_archive" in s:
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    for m in PAT.finditer(t):
        line = t[:m.start()].count("\n") + 1
        hits.append((str(p.relative_to(ROOT)), line, m.group(0)[:100]))

print("=" * 78)
print("残留硬编码绝对路径")
print("=" * 78)
print(f"  共 {len(hits)} 处\n")
for f, l, c in hits:
    print(f"  {f}:{l}")
    print(f"      {c}")

# 分类
eng = sum(1 for _f, _l, c in hits if "07_代码" in c)
ext = sum(1 for _f, _l, c in hits if "_ext_data" in c)
proj = sum(1 for _f, _l, c in hits if "10_论文推进" in c and "07_代码" not in c and "_ext_data" not in c)
print(f"\n  引擎路径 {eng} · 外部数据 {ext} · 项目根 {proj}")
sys.exit(0 if not hits else 1)
