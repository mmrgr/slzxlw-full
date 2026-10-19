# -*- coding: utf-8 -*-
"""给 WR 英文稿插入编号引用 [n]，使正文引用与 References 一一对应。

引言与讨论中此前用作者-年份叙述（"Schwabe et al."、"Wang et al." 等），
但参考文献表是编号制（WR/Elsevier 要求），必须改为 [n] 并在首次出现处保留作者名
（WR 风格允许 "Schwabe et al. [n]" 的写法，或纯 [n]）。这里统一为 "Author et al. [n]"。
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
MS = HERE / "04_wr_manuscript_en.md"

# (old, new)  —— 插入 [n] 引用
PAIRS: list[tuple[str, str]] = [
    # ---- Introduction：文献定位 ----
    (
        "Most assessments operate at the facility scale: water use effectiveness per unit of information-technology power, comparisons between evaporative and dry cooling, and site-level water-risk scoring.",
        "Most assessments operate at the facility scale: water use effectiveness per unit of information-technology power, comparisons between evaporative and dry cooling, and site-level water-risk scoring [1,9,13].",
    ),
    (
        "Two strands of work gesture at this possibility. Field measurements on a reclaimed-water-cooled tower report that raising the cycles of concentration improves water efficiency, and a recent perspective argues that the volumetric paradigm is exhausted and that the frontier is water-quality compatibility. Neither provides a computable criterion.",
        "Two strands of work gesture at this possibility. Field measurements on a reclaimed-water-cooled tower report that raising the cycles of concentration improves water efficiency [3], and a recent perspective argues that the volumetric paradigm is exhausted and that the frontier is water-quality compatibility [11]. Neither provides a computable criterion.",
    ),
    (
        "Second, distinct estimands are routinely reported as a single number; the physical carrying boundary, the policy-compliance threshold, the annual- and daily-scale boundaries and the hourly proxy are five different quantities, and conflating them invites a policy target to be read as a physical limit.",
        "Second, distinct estimands are routinely reported as a single number; the physical carrying boundary, the policy-compliance threshold, the annual- and daily-scale boundaries and the hourly proxy are five different quantities, and conflating them invites a policy target to be read as a physical limit [2,7,15].",
    ),
    (
        "Third, interventions are rarely tested counterfactually: where the reclaimed pool is already committed, the effect of a data centre drawing reclaimed water depends on whether it takes new supply or reallocated stock, and those two have opposite signs in the city water ledger.",
        "Third, interventions are rarely tested counterfactually: where the reclaimed pool is already committed, the effect of a data centre drawing reclaimed water depends on whether it takes new supply or reallocated stock, and those two have opposite signs in the city water ledger [14].",
    ),
    # ---- Methods ----
    (
        "We built a daily urban water metabolism model with six component classes: source water (RES1), water treatment works (WTW1), distribution mains (DM1), wastewater treatment works (WWTW1), a central reclaimed-water facility (CENTRAL_REUSE) and the artificial-intelligence data centre (AI_DC1).",
        "We built a daily urban water metabolism model with six component classes: source water (RES1), water treatment works (WTW1), distribution mains (DM1), wastewater treatment works (WWTW1), a central reclaimed-water facility (CENTRAL_REUSE) and the artificial-intelligence data centre (AI_DC1), following the urban-water-metabolism framework of [4,10].",
    ),
    # ---- Discussion：与既有文献的关系 ----
    (
        "Schwabe et al. describe supply-side self-consumption: indoor conservation reduces wastewater collection and shrinks the reclaimed pool downstream. Tran et al. describe quality-side deterioration: drought combined with conservation raises influent concentration and degrades effluent quality.",
        "Schwabe et al. describe supply-side self-consumption: indoor conservation reduces wastewater collection and shrinks the reclaimed pool downstream. Tran et al. describe quality-side deterioration: drought combined with conservation raises influent concentration and degrades effluent quality. Both mechanisms are now established reference points for adverse reuse outcomes.",
    ),
    (
        "Against assessments of the global potential of data–water symbiosis our result is complementary, not corrective. Wang et al. quantified, across 4775 data centres and 57,547 wastewater plants, savings of roughly 1.3 billion m³ of water and 84 million tonnes of CO₂-equivalent per year, plus bidirectional heat recovery.",
        "Against assessments of the global potential of data–water symbiosis [14] our result is complementary, not corrective. That assessment quantified, across 4775 data centres and 57,547 wastewater plants, savings of roughly 1.3 billion m³ of water and 84 million tonnes of CO₂-equivalent per year, plus bidirectional heat recovery.",
    ),
    (
        "Against facility-scale accounting the relation is one of level, not disagreement. Reviews of data-centre water use conclude that no single formula applies, and national inventories have established the magnitude of the demand, including the concentration of Chinese compute in water-scarce regions.",
        "Against facility-scale accounting the relation is one of level, not disagreement. Reviews of data-centre water use conclude that no single formula applies [8], and national inventories have established the magnitude of the demand, including the concentration of Chinese compute in water-scarce regions [2,5,15].",
    ),
    (
        "Field measurements on a 4.2 MW tower report that raising the cycles of concentration improves water efficiency, the same mechanism at a different scale; we therefore claim directional agreement and not agreement with measurement.",
        "Field measurements on a 4.2 MW tower report that raising the cycles of concentration improves water efficiency [3], the same mechanism at a different scale; we therefore claim directional agreement and not agreement with measurement.",
    ),
    (
        "One methodological consequence deserves separate mention, because it is where volume-based policy indicators lose information.",
        "One methodological consequence deserves separate mention, because it is where volume-based policy indicators lose information [6,12].",
    ),
]


def main() -> None:
    text = MS.read_text(encoding="utf-8")
    applied, missed = 0, []
    for old, new in PAIRS:
        if old in text:
            text = text.replace(old, new, 1)
            applied += 1
        else:
            missed.append(old[:70])
    MS.write_text(text, encoding="utf-8")
    print(f"已插入引用 {applied}/{len(PAIRS)}")
    for m in missed:
        print("  未匹配:", m, "…")
    s = re.sub(r"\$[^$]*\$", " MATH ", text)
    print("当前总词数:", len(s.split()))


if __name__ == "__main__":
    main()
