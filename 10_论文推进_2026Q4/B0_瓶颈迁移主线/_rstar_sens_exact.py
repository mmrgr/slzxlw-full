# -*- coding: utf-8 -*-
"""精确复算 r* 四参数各 ±10% 的移动量，用于核对论文"0.05–0.09"的说法。"""
from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

L, CD, CP, CR = 2200.0, 5.0, 180.0, 650.0


def rstar(l=L, cd=CD, cp=CP, cr=CR):
    return (l / cd - cp) / (cr - cp)


base = rstar()
print(f"标称 r* = {base:.4f}\n")
print(f"{'参数':<8}{'-10% 时 r*':>12}{'+10% 时 r*':>12}{'跨度':>10}{'相对标称最大偏移':>18}")
print("-" * 64)
rows = []
for name, kw in (("L", "l"), ("CoC_d", "cd"), ("C_r", "cr"), ("C_p", "cp")):
    vals = {}
    for s, tag in ((0.9, "-10%"), (1.1, "+10%")):
        args = {"l": L, "cd": CD, "cp": CP, "cr": CR}
        args[kw] = args[kw] * s
        vals[tag] = rstar(**args)
    span = abs(vals["+10%"] - vals["-10%"])
    maxdev = max(abs(vals["-10%"] - base), abs(vals["+10%"] - base))
    print(f"{name:<8}{vals['-10%']:>12.4f}{vals['+10%']:>12.4f}{span:>10.4f}{maxdev:>18.4f}")
    rows.append((name, vals["-10%"], vals["+10%"], span, maxdev))

print("\n论文现有表述：'参数 ±10% 即移动 r* 约 0.05–0.09'")
mx = max(r[4] for r in rows)
print(f"实测：单参数 ±10% 使 r* 相对标称最大偏移 = {mx:.4f}（{rows[0][0]} 与 {rows[1][0]}）")
print(f"→ 论文数值约为实测的 1/{mx/0.09:.1f} ~ 1/{mx/0.05:.1f}，属低估。")
