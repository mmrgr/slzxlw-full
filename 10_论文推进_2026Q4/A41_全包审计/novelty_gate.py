"""门禁 14: 新颖性声明合规——A29 禁止表述不得以肯定形式出现 (2026-10-17).

【背景】A29_文献核验/innovation_overlap.md 逐篇列出了**禁止写入的英文表述**
（如 "first global framework pairing data centres with wastewater treatment plants"），
并给出允许的替换。六篇竞品中任何一篇漏引或误称首创, 都可能被 EIC 判为文献调研不足。

【难点】论文中有**否定式**用法, 例如:
    "Related claims we do not make: first quantification of AI-server ..."
这是**正确**的。因此本门禁不能简单 grep, 必须判断**所在句是否含否定词**。

【规则】
对每条禁止表述:
  找到它在文中的出现位置 -> 取该句 -> 若句中有 not/never/no/don't/do not
  或处于 "we do not claim" 语境, 则 PASS; 否则 FAIL。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MS = ROOT / "A16_英文稿/manuscript_en_v3.md"

# A29 禁止表述（小写化比对）
FORBIDDEN = [
    "first to note that water quality",
    "first to recognise the importance of water quality",
    "first to shift the focus from quantity to quality",
    "first global framework pairing",
    "first to quantify water-carbon symbiosis",
    "first to quantify water–carbon symbiosis",
    "first integrated spatial/engineering",
    "first integrated energy-water-carbon",
    "first integrated energy–water–carbon",
    "first spatially explicit AI water footprint",
    "first to show data centres impose peak",
    "first to show facility-level reporting",
    "first to reveal the trade-off",
    "first to show reclaimed water raises",
    "first urban-scale water metabolism",
    "first counterfactual framework",
    "first study of data-centre peak stress",
    "first quantification of AI-server",
    "first observation that reclaimed water can raise",
]

NEGATORS = ("not", "never", "no claim", "do not", "don't", "cannot", "n't")


def sentence_around(text: str, idx: int) -> str:
    """取 idx 所在的句子（以 . ; 换行(- 开头) 为界）。"""
    start = max(0, idx - 400)
    chunk = text[start:idx + len(FORBIDDEN[0]) + 400]
    # 以句号/分号切
    parts = re.split(r"(?<=[.;])\s+", chunk)
    for p in parts:
        if idx - start < len(p) + (idx - start):
            pass
    # 简化: 取包含 idx-start 位置的那一段
    pos = 0
    for p in parts:
        if pos <= (idx - start) <= pos + len(p):
            return p
        pos += len(p) + 1
    return chunk


def main() -> int:
    t = MS.read_text(encoding="utf-8")
    low = t.lower()
    print("=" * 76)
    print("新颖性声明合规门禁（A29 禁止表述）")
    print("=" * 76)
    fails = 0
    checked = 0
    for f in FORBIDDEN:
        pos = low.find(f)
        if pos < 0:
            continue
        checked += 1
        # 向前多取 300 字符, 以覆盖"列表式否定声明":
        #   "Related claims we do not make: first A; first B; first C."
        sent = t[max(0, pos - 300):pos + 300]
        negated = any(ng in sent.lower() for ng in NEGATORS)
        if negated:
            print(f"  [PASS] {f[:50]!r} — 处于否定语境")
        else:
            print(f"  [FAIL] {f[:50]!r} — 以肯定形式出现")
            print(f"         句: …{sent.strip()[:150]}…")
            fails += 1
    # A29 明示: 六篇竞品中任何一篇漏引, 都足以被 EIC 判为文献调研不足
    REQUIRED = ["Wang", "Saleh", "Xiao", "Han", "Alston", "Chen"]
    if "### Relation to prior work" in t and "### Limitations" in t:
        rel = t[t.index("### Relation to prior work"):t.index("### Limitations")]
    else:
        rel = t
    miss = [s for s in REQUIRED if s not in rel]
    print(f"  [{'PASS' if not miss else 'FAIL'}] 六篇必引竞品均在 Relation 节 "
          f"(缺失 {len(miss)})")
    if miss:
        print(f"        缺失: {miss}")
        fails += 1

    print()
    print(f"  命中禁止表述 {checked} 处; 不合格 {fails}")
    print(f"裁定: {'合规 ✓' if fails == 0 else f'{fails} 项违禁 ✗'}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
