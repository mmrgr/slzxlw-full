"""同步 Fig3 图注数字 (2026-10-17). 用文件而非 heredoc, 避免转义。"""
import re
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "A37_六主图_v4" / "make_fig3.py"
t = P.read_text(encoding="utf-8")

# 逐条精确替换(顺序重要: 先长串)
PAIRS = [
    ("Across the 813 solver-reliable grid", "Across the 839 solver-reliable grid"),
    ("**643 negative (beneficial) /", "**626 negative (beneficial) /"),
    ("into **290 (q > 0) /", "into **263 (q > 0) /"),
    ("288 (q = 0) / 235 (q < 0)**", "288 (q = 0) / 288 (q < 0)**"),
    ("**0 of\n290**", "**0 of\n263**"),
    ("n_eff = **813** of 1 052", "n_eff = **839** of 1 052"),
    ("(0 / 290 harmful)", "(0 / 263 harmful)"),
    ("134 positive (harmful) / 36 zero", "177 positive (harmful) / 36 zero"),
]
n = 0
for a, b in PAIRS:
    if a in t:
        t = t.replace(a, b, 1)
        n += 1
P.write_text(t, encoding="utf-8")
print(f"替换 {n}/{len(PAIRS)}")

# 残检
left = [m for m in ("813", "643", "134 posit", "290", "235") if m in t]
print("脚本内残留:", left if left else "无")
