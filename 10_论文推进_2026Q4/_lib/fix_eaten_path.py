"""修复主稿中被 shell 反引号吞掉的路径 (2026-10-17).

【事故】我用 heredoc 写入含反引号的 Markdown 时, bash 把反引号内容当作命令执行,
导致 `point (\`A41_全包审计/run_all_gates.py\`)` 变成 `point ()`。
【修正】用脚本文件写回正确文本, 避免任何 shell 解释。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"
t = P.read_text(encoding="utf-8")

OLD = "point () runs all eleven and returns"
NEW = ("point (`A41_全包审计/run_all_gates.py`) runs all eleven and returns")

if OLD in t:
    P.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("已修复路径")
else:
    print("未找到损坏处, 当前上下文:")
    i = t.find("A single entry")
    print(repr(t[max(0, i - 60):i + 220]))
