"""A28: 精确检测 LaTeX/文本中被打字机误转义破坏的片段.

破坏模式: Python 字符串里写 "\\varphi" 时若只写 "\v" 会变成垂直制表符,
同理 \\rho->\r(回车), \\theta->\t(制表), \\frac->\f(换页), \\beta->\b(退格)。
特征: 出现**裸控制字符** (不是可见的 '\' + 字母)。
"""
from __future__ import annotations

import sys
from pathlib import Path

def _research_root() -> Path:
    """标记式定位研究目录根 (不依赖脚本所在层数)。

    2026-10-16 整理轮加入: 原写法 `Path(__file__).resolve().parent.parent`
    在脚本被移入子目录后会算错根, 导致所有相对路径断链。
    """
    import os
    _h = Path(__file__).resolve()
    for _b in (_h.parent, *_h.parent.parents):
        if (_b / "_lib").is_dir() or (_b / "_PROJECT_ROOT").exists():
            return _b
    _env = os.environ.get("AIUWM_RESEARCH_DIR")
    if _env and Path(_env).is_dir():
        return Path(_env)
    raise RuntimeError(
        "找不到研究目录根 (10_论文推进_2026Q4)。"
        "请确认该目录下存在 _lib/ 或 _PROJECT_ROOT 标记文件。")

ROOT = _research_root()
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