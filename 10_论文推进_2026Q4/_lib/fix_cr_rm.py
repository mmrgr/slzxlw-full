r"""按字符编码精确修复 `\rm` 被吃 (2026-10-17).

损坏形态: `$|dS_{` + CR(U+000D) + `m pot}|<10^{-11}$`
（前一次写入时普通字符串的 \r 变成了真正的回车符）
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MS = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"
t = MS.read_text(encoding="utf-8")

CR = chr(13)
n = t.count("dS_{" + CR + "m pot}")
t = t.replace("dS_{" + CR + "m pot}", r"dS_{\rm pot}")
# 兜底: 任何 "_{<CR>m " 形态
n2 = t.count("_{" + CR + "m ")
t = t.replace("_{" + CR + "m ", r"_{\rm ")
MS.write_text(t, encoding="utf-8")

print(f"  修复 dS_{{<CR>m pot}}: {n} 处")
print(f"  兜底修复 _{{<CR>m : {n2} 处")
print(f"  剩余 CR 字符: {t.count(CR)}")

i = t.find("to machine precision")
print("\n复验:")
print(repr(t[max(0, i - 60):i + 130]))
