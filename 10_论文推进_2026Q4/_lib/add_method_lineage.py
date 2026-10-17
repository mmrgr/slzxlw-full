"""补入 A29 🟡中等级建议的文献定位 (2026-10-17).

A29 innovation_overlap.md 第 7、9 项建议:
  第7项: 可写 "Using an established urban water metabolism formulation
          (e.g., WaterMet^2; Renouf et al., 2018), we add ..."
          —— 即把本文放到既有城市水系统建模文献中定位, 不主张首创。
  第9项: 冷却 LCA 已是成熟领域 (含 Nature 正刊 Alissa 2025), 仅作参数来源引用。

当前主稿:**完全未引用**这些文献 ⇒ 学术定位缺口。
它们都在 references.bib 中已核验, 只是没进正文与文献表。

本脚本在 Relation to prior work 末尾补一段方法论定位。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MS = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"
t = MS.read_text(encoding="utf-8")

ANCHOR = "To our knowledge — with the caveat that our search"
BLOCK = """**Methodological lineage.** We do not present the urban-water *modelling* itself as a
contribution. The engine used here extends an established lineage of urban water-system
metabolism models — WaterMet² and related unit-process formulations (Behzadian & Kapelan, 2015;
Renouf et al., 2018) and more recent decentralisation analyses (Garrido-Baserba et al., 2024) —
and we take from that literature the convention that supply, use, wastewater and reuse are
accounted in a single balanced system. Likewise, cooling-side life-cycle assessment is a mature
field, including studies that compare cooling options in data centres (Isler-Kaya &
Karaosmanoğlu, 2023; Alissa et al., 2025), and we use such work only as a source of parameter
ranges rather than claiming novelty in impact assessment. What is new here is narrower and is
stated in the next paragraph.

"""

if ANCHOR in t and "Methodological lineage" not in t:
    t = t.replace(ANCHOR, BLOCK + ANCHOR, 1)
    MS.write_text(t, encoding="utf-8")
    print("已补入方法论定位段")
else:
    print("MISS 或已存在")
