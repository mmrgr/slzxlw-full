"""A28: 精确检测 LaTeX/文本中被打字机误转义破坏的片段.

破坏模式: Python 字符串里写 "\\varphi" 时若只写 "\v" 会变成垂直制表符,
同理 \\rho->\r(回车), \\theta->\t(制表), \\frac->\f(换页), \\beta->\b(退格)。
特征: 出现**裸控制字符** (不是可见的 '\' + 字母)。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CTRL = {"\t": "TAB(\\t)", "\r": "CR(\\r)", "\x0b": "VT(\\v)",
        "\x0c": "FF(\\f)", "\x08": "BS(\\b)", "\x07": "BEL(\\a)"}

hits = []
for f in sorted(ROOT.rglob("*.md")):
    if "OBSOLETE" in f.name or "_cleanup_backup" in str(f):
        continue
    try:
        s = f.read_text(encoding="utf-8")
    except Exception:
        continue
    for i, line in enumerate(s.splitlines(), 1):
        for ch, name in CTRL.items():
            if ch in line:
                hits.append((str(f.relative_to(ROOT)), i, name, line.strip()[:90]))

print(f"发现含裸控制字符的行: {len(hits)}")
for f, i, name, txt in hits[:40]:
    print(f"  {f}:{i}  [{name}]  {txt}")
if not hits:
    print("  (无损坏)")
