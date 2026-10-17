"""修正 status 失败计数 51 → 25 (2026-10-17).

【错误来源】
上一轮(P0-1修复后)把 58 改成 51, 但 51 仍是**修复前**旧网格的值。
修复后重跑, 实测:
    no_convergence = 16
    non_unique     = 9
    合计 = 25
`truth_source.py` 实时计算确认 status_fail = 25。

【教训】这就是"没有单一真相源"的代价: 手改数字会连改两轮都改错。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
MS = ROOT / "A16_英文稿/manuscript_en_v3.md"
SI = ROOT / "A16_英文稿/supplementary_information.md"

MS_PAIRS = [
    ("found that 51 of the 1,052 grid scenarios did not return a unique",
     "found that 25 of the 1,052 grid scenarios did not return a unique"),
]

SI_PAIRS = [
    ("found that **51 of the 1,052 scenarios (4.85%)** in the *current* main grid did not",
     "found that **25 of the 1,052 scenarios (2.38%)** in the *current* main grid did not"),
    ("| `supply_state_regimes.csv` (main grid, **current cited-limit run**) | **1,052** | **51** | **4.85%** |",
     "| `supply_state_regimes.csv` (main grid, **current cited-limit run**) | **1,052** | **25** | **2.38%** |"),
    ('Note that the earlier "1,152 scenarios / 51 unreliable" entry in this table',
     'Note that the earlier "1,152 scenarios / 58 unreliable" entry in this table'),
]

total = 0
for p, pairs, tag in ((MS, MS_PAIRS, "manuscript"), (SI, SI_PAIRS, "SI")):
    t = p.read_text(encoding="utf-8")
    n = 0
    for a, b in pairs:
        if a in t:
            t = t.replace(a, b, 1)
            n += 1
        else:
            print(f"  MISS[{tag}]: {a[:70]}")
    p.write_text(t, encoding="utf-8")
    print(f"  {tag}: {n}/{len(pairs)}")
    total += n

# 复验
print("\n复验 (应无 51 of the 1,052 / **51** | **4.85%**):")
for p in (MS, SI):
    t = p.read_text(encoding="utf-8")
    bad = [s for s in ("51 of the 1,052", "**51**", "4.85%") if s in t]
    print(f"  {p.name}: {bad if bad else 'clean'}")
print(f"\n合计 {total} 处")
