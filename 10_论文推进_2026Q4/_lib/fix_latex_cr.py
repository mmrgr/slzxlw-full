r"""修复主稿中因 Python 字符串转义被破坏的 LaTeX (2026-10-17).

问题: `$x_{\rm AI}$` 在写入时, `\r` 被解释为回车符,
      变成 `$x_{` + CR + `m AI}$`。
解决: 使用**原始字符串** r"..." 并在写入前做校验。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MS = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"
t = MS.read_text(encoding="utf-8")

# 目标: 把 "($x_{<CR>m AI}$ exceeds" 还原为 "($x_{\rm AI}$ exceeds"
import re
before = t.count("\r")
t2 = re.sub(r"\$x_\{\rm AI\}\$ exceeds", r"$x_{\\rm AI}$ exceeds", t)  # 幂等
t2 = re.sub(r"\$x_\{\x0dm AI\}\$", r"$x_{\\rm AI}$", t2)
t2 = re.sub(r"\$x_\{\rm AI\}\$", r"$x_{\\rm AI}$", t2)

# 更稳妥: 直接按字节替换 CR
lines = t2.split("\n")
fixed = []
n_fix = 0
for ln in lines:
    if "x_{" in ln and "m AI}" in ln and "$x_{\\rm AI}$" not in ln:
        ln = ln.replace("x_{" + chr(13) + "m AI}", r"x_{\rm AI}")
        n_fix += 1
    fixed.append(ln)
t2 = "\n".join(fixed)

MS.write_text(t2, encoding="utf-8")
print(f"  修复 {n_fix} 处")
print(f"  剩余 CR 字符: {t2.count(chr(13))}")

# 复验
i = t2.find("The 11 exceptions in branch C")
seg = t2[i:i + 300]
print("\n复验 (以 repr 显示, 便于看不可见字符):")
print(repr(seg))
