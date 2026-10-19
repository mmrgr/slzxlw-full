# -*- coding: utf-8 -*-
"""把干预交互结果同步到英文正文与 SI。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

# ---------- 英文正文 §4.4 ----------
EN_OLD = ("Quantisation is why only the zero-effect region and the endpoint decline are cited as "
          "numbers, and interactions were not tested since the nine interventions were applied "
          "singly.")
EN_NEW = ("Quantisation is why only the zero-effect region and the endpoint decline are cited as "
          "numbers. All 36 pairwise intervention combinations were subsequently run on the same grid "
          "in both calibers: 35 of 36 are exactly additive at each endpoint, and the sole "
          "non-additive pair — leakage reduction with the combined upgrade — is redundant by "
          "construction, since the upgrade already contains leakage reduction, so its interaction "
          "equals minus the leakage gain exactly. No pair showed the pattern that would matter for "
          "the argument, namely two individually ineffective interventions becoming effective "
          "together.")

# ---------- SI 第 6 条 ----------
SI_OLD = ("6. **No intervention interactions.** Nine interventions were applied one at a time; no "
          "full-factorial or pairwise interaction test was run.")
SI_NEW = """6. **Intervention interactions: tested, and the result is near-perfect additivity.** All 36
pairwise combinations of the nine interventions were re-run on the 50 MW grid, at both endpoints
and under both constraint sets. At each endpoint, 35 of 36 pairs are exactly additive, the
interaction being zero to numerical precision. The single exception at the water-scarce endpoint
pairs `leakage_minus_30pct` with `combined_upgrade`, and its interaction equals minus the leakage
gain exactly (−250 MW physical, −150 MW joint). This is redundancy rather than antagonism: the
specification of `combined_upgrade` already contains the leakage-reduction path, so applying both
counts that measure twice. The cool endpoint is fully additive, 36 of 36.

Three consequences are worth recording. First, effective interventions are independent of the
ineffective ones, so planning gains can be summed without worrying that combination erodes the
marginal benefit. Second, no pair shows the qualitatively important pattern of two individually
ineffective measures becoming effective together, consistent with the paper's claim that an
intervention off the binding constraint does nothing however many others accompany it. Third, the
gain itself is caliber-dependent: leakage reduction at the water-scarce endpoint is +150 MW under
the joint constraint set and +250 MW under the purely physical one, because under the joint set the
policy constraint fails before 1400 MW and truncates what leakage reduction can realise. This is
the same structure as the paper's main result — an intervention's value depends on which constraint
set defines carrying capacity — so the two calibers must never be mixed.

**Not done:** interactions of order three and above, and a full-factorial design. Given that every
first-order interaction is zero, higher-order terms have little prior support, and there are no
remaining effective interventions to combine.

**Evidence:** `{ha,co}/interaction_pairs_50mw.csv`, `interaction_pairs_50mw_summary.json`;
`_verify_interactions.py` (20/20)."""

n = 0
for path, old, new, tag in ((EN, EN_OLD, EN_NEW, "英文 §4.4"), (SI, SI_OLD, SI_NEW, "SI 第 6 条")):
    t = path.read_text(encoding="utf-8")
    if old in t:
        path.write_text(t.replace(old, new, 1), encoding="utf-8")
        print(f"OK {tag}")
        n += 1
    else:
        print(f"未匹配 {tag}")

import re
t = EN.read_text(encoding="utf-8")
print("英文词数:", len(re.sub(r"\$[^$]*\$", " MATH ", t).split()))
