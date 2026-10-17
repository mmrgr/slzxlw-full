"""同步 make_fig4.py 内 E3 数字 (2026-10-17)."""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = Path(__file__).resolve().parent.parent / "A37_六主图_v4/make_fig4.py"
t = P.read_text(encoding="utf-8")

PAIRS = [
    ("结论: 仅化学 (q>0) 失败 (0.671 < 基线 0.861); 化学+分配联合判据 C4 全样本 0.906。",
     "结论: 仅化学 (q>0) 失败 (0.675 < 基线 0.809); 化学+分配联合判据 C4 全样本 0.914。"),
    ("⚠ 折外 (leave-one-composition-out) 均值 0.901 vs 基线 0.859 —— **该均值不是可靠摘要,",
     "⚠ 折外 (leave-one-composition-out) 均值 0.917 vs 基线 0.815 —— 中位增益 +0.092,"),
    ('"LIMITATION: the apparent out-of-sample gain (0.901 vs 0.859) is WITHDRAWN as evidence of "',
     '"LIMITATION: the out-of-sample gain (median +0.092; 0.917 vs 0.815) rests on only two "'),
    ("0.861", "0.809"),
    ("0.671", "0.675"),
    ("0.906", "0.914"),
]
n = 0
for a, b in PAIRS:
    if a in t:
        t = t.replace(a, b)
        n += 1
    else:
        print(f"  MISS: {a[:60]}")
P.write_text(t, encoding="utf-8")
print(f"替换 {n}/{len(PAIRS)}")
left = [x for x in ("0.861", "0.671", "0.906", "0.901", "0.859") if x in t]
print("残留:", left if left else "无")
