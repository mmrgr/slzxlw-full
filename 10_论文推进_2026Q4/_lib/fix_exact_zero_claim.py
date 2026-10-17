r"""修复 exact-zero 表述 + LaTeX 转义 (2026-10-17).

【两个问题】
1. 主稿 "0.000000 ML exactly (80/80)" 不准确: 严格 0.0 只有 36/80,
   其余 44 个是 |dS| < 1e-11 的机器精度残差。应改为 "to machine precision"。
2. 上一版用普通字符串写入, `\rm` 的 `\r` 被解释成回车, 变成 `dS_{m pot}`。
   **必须用原始字符串 r"..."**。

【实测】
branch-A (limit_scale=1e6, 纯挤占): n=80
  · 恰好 0.0 : 36
  · |dS|<1e-11: 44 (机器精度)
  · 全部 80 个 |dS| < 1e-11
"""
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MS = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"
SI = Path(__file__).resolve().parent.parent / "A16_英文稿/supplementary_information.md"

# 1) 先修主稿里被破坏的 LaTeX
t = MS.read_text(encoding="utf-8")
bad = "$|dS_{m pot}|<10^{-11}$"
if bad in t:
    t = t.replace(bad, r"$|dS_{\rm pot}|<10^{-11}$")
    MS.write_text(t, encoding="utf-8")
    print("主稿: 已修复被吃掉的 \\rm")

# 2) 修 SI
t2 = SI.read_text(encoding="utf-8")
OLD2 = r"$dS_{\rm pot}=$ **0.000000 ML exactly** in the committed branch (80/80); ≤ 0 in the surplus"
NEW2 = (r"$dS_{\rm pot}=0$ **to machine precision** in the committed branch "
        r"($|dS_{\rm pot}|<10^{-11}$ ML in all 80/80 cases; 36 are exactly 0.0); "
        r"≤ 0 in the surplus")
if OLD2 in t2:
    SI.write_text(t2.replace(OLD2, NEW2, 1), encoding="utf-8")
    print("SI: 已修正 exact-zero 表述")
else:
    print("SI 锚点未匹配，尝试正则定位…")
    m = re.search(r"\$dS_\{\\rm pot\}=\$ \*\*0\.000000 ML exactly\*\*", t2)
    if m:
        SI.write_text(t2[:m.start()] + NEW2 + t2[m.end():], encoding="utf-8")
        print("SI: 已用正则替换")
    else:
        i = t2.find("0.000000 ML exactly")
        print("上下文:", repr(t2[max(0, i - 90):i + 90]))

# 复验
for p in (MS, SI):
    tt = p.read_text(encoding="utf-8")
    print(f"\n{p.name}:")
    print(f"  CR 字符数: {tt.count(chr(13))}")
    for m in re.finditer(r"\$[^$]*dS_\{[^}]*\}[^$]*\$", tt):
        if "m pot" in m.group(0) and "rm pot" not in m.group(0):
            print(f"  ⚠ 仍有损坏: {m.group(0)[:60]}")
