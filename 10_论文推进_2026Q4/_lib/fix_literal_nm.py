r"""清理 LaTeX 中的字面 "\n" 与 "\r" 残留 (2026-10-17).

现象: `$x_{\nm AI}$` —— 这里 `\n` 是**两个字符**反斜杠+n(不是换行),
      修复方式是把 `\nm` 换成 `\rm`。

同时全局扫描所有 `_{` 或 `^{` 后紧跟字母的位置, 检查是否为合法 LaTeX 命令。
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MS = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"
t = MS.read_text(encoding="utf-8")

# 把字面的 "\nm " 还原为 "\rm "
before = t.count("\\nm ")
t = t.replace("\\nm ", "\\rm ")
# 也处理 "\rm" 前后异常
t = t.replace("\\\\rm", "\\rm")

MS.write_text(t, encoding="utf-8")
print(f"  修复 '\\nm ' 残留: {before} 处")

# 复验: 检查所有 _ { 后的首命令
bad = []
for m in re.finditer(r"[_^]\{([a-zA-Z\\]+)", t):
    cmd = m.group(1)
    if not cmd.startswith("\\"):
        bad.append((m.start(), cmd[:12]))
print(f"  `_{{`/`^{{` 后直接跟字母(缺反斜杠)的位置: {len(bad)}")
for p, c in bad[:5]:
    print(f"    pos {p}: {c!r}")

i = t.find("The 11 exceptions in branch C")
print("\n复验:")
print(repr(t[i:i + 240]))
