"""系统性数字核对: 把主稿中的整数与产物中的整数做交集比对 (2026-10-17).

【目的】此前用 grep 追特定数字, 漏掉了表格内的计数(232/369/372)。
本脚本换个方向: 从产物算出**权威计数集合**, 再扫主稿里所有整数,
列出"主稿出现但不在权威集合中"的可疑整数, 供人工判断。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
MS = ROOT / "A16_英文稿/manuscript_en_v3.md"

import numpy as np
import pandas as pd

d = pd.read_csv(ROOT / "A13_可靠性机制/supply_state_regimes.csv")
rel = d[(d.status == "converged_unique") & (~d.coc_floor_degenerate.astype(bool))].copy()
C = rel.inc_B2_ml - rel.inc_B1_ml
x = rel.x_ai_B1_ml
pure = np.isclose(x, C, rtol=1e-9)
nodisp = np.isclose(C, 0, atol=1e-9)
q = (rel.M0_ml - rel.M1_ml) / rel.M1_ml

AUTHORITATIVE = {
    len(d), len(rel), int((d.status != "converged_unique").sum()),
    int((d.status == "no_convergence").sum()), int((d.status == "non_unique").sum()),
    int(d.coc_floor_degenerate.sum()),
    int((rel.dS_pot_ml < 0).sum()), int((rel.dS_pot_ml > 0).sum()),
    int((rel.dS_pot_ml == 0).sum()),
    int(pure.sum()), int(nodisp.sum()), int((rel[nodisp].dS_pot_ml < 0).sum()),
    int((q > 1e-9).sum()), int((q.abs() <= 1e-9).sum()), int((q < -1e-9).sum()),
    68, 839, 1052, 47, 60, 141, 597, 10826, 39, 61,
}

# 已知合法但不来自主网格的整数(图号/年份/条款号等) 白名单
WHITELIST = set(range(0, 25)) | {2025, 2026, 2012, 2017, 50050, 19923, 730, 95,
                                 10, 100, 1, 2, 3, 4, 5, 6, 7, 8, 9}

t = MS.read_text(encoding="utf-8")
# 只扫 Results/Discussion 正文(跳过 References/Declarations)
body = t[t.index("## Introduction"):t.index("## References")]
ints = {}
for m in re.finditer(r"(?<![\d.])(\d{2,6})(?![\d.])", body):
    v = int(m.group(1))
    start = max(0, m.start() - 55)
    ints.setdefault(v, []).append(body[start:m.end() + 25].replace("\n", " "))

sus = {v: ctx for v, ctx in ints.items()
       if v not in AUTHORITATIVE and v not in WHITELIST}

print("=" * 76)
print("主稿整数 vs 权威计数 比对")
print("=" * 76)
print(f"  权威计数集合: {sorted(AUTHORITATIVE)}")
print(f"\n  主稿中不在权威集合的整数: {len(sus)} 个\n")
for v in sorted(sus):
    print(f"  {v}:")
    for c in sus[v][:2]:
        print(f"      …{c}…")
