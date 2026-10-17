r"""按字符编码精确修复 LaTeX 中的换行断裂 (2026-10-17).

实测损坏形态: `$x_{` + LF(U+000A) + `m AI}$`
（不是 CR, 也不是字面 \n，是真正的换行符）
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

# 模式: `_{` 或 `^{` 后面紧跟 换行 + "m "  → 还原为 `_{\rm `
pat = re.compile(r"([_^])\{\nm ")
n = len(pat.findall(t))
t = pat.sub(r"\1{\\rm ", t)
MS.write_text(t, encoding="utf-8")
print(f"  修复 `_{{<LF>m ` -> `_{{\\\\rm `: {n} 处")

# 复验: 全文不得再有 `_{` 或 `^{` 直接跟换行
rest = re.findall(r"[_^]\{\n", t)
print(f"  剩余 `_{{<换行>` 形态: {len(rest)}")

i = t.find("The 11 exceptions in branch C")
print("\n复验:")
print(repr(t[i:i + 230]))
