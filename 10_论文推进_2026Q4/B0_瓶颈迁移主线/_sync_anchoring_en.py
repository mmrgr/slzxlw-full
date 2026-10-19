# -*- coding: utf-8 -*-
"""把"r* 四参数中三个从未锚定"同步到英文正文与 SI。

实测（_rstar_param_anchoring.py）：
  parameter_envelope_R7.csv 共 54 行，r* 的四个参数中
    CoC_d  在表内，标"无锚点"
    L      不在表内
    C_p    不在表内
    C_r    不在表内
  ⇒ 四个参数中 1 个在表内且无锚点，3 个从未核查。
敏感性：单参数 ±10% 相对标称的最大偏移 L 0.0936 / CoC_d 0.1040 / C_r 0.0888 / C_p 0.0178；
两端跨度 0.1872 / 0.1891 / 0.1560 / 0.0343。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

OLD_MS_METHOD = ("The design cycles of concentration, which controls the threshold, carries no "
                 "anchor, making it the weakest link in the classification below. Drivers are "
                 "synthetic 730-day sequences, and no constraint threshold has been calibrated "
                 "against any city.")
NEW_MS_METHOD = ("None of the four parameters that set the threshold carries a measured anchor: the "
                 "design cycles of concentration is listed in the envelope without an anchor, and "
                 "the three water-quality parameters — the loop salinity limit and the two source "
                 "salinities — are not in the envelope table at all and have never been checked "
                 "against external data. Drivers are synthetic 730-day sequences, and no constraint "
                 "threshold has been calibrated against any city.")

OLD_MS_LIM = ("The design cycles of concentration, which controls the threshold, carries no anchor, "
              "making the classification boundary the weakest link.")
NEW_MS_LIM = ("None of the four parameters that set the threshold carries a measured anchor — the "
              "design cycles of concentration is listed without one, and the three water-quality "
              "parameters were never entered into the envelope table — so the threshold value rests "
              "on four unverified inputs rather than one.")

OLD_MS_SENS = ("the near-equality of the first two reflects that both enter only through "
               "$C^{*}$, and a 10% change in either moves $r^{*}$ by roughly 0.05 to 0.09.")
NEW_MS_SENS = ("the near-equality of the first two reflects that both enter only through "
               "$C^{*}$. A 10% change in a single parameter moves $r^{*}$ by 0.018 ($C_p$), 0.089 "
               "($C_r$), 0.094 ($L$) or 0.104 ($\\mathrm{CoC}_d$) relative to nominal, and the "
               "two-endpoint span reaches 0.19 for the last two — enough to move the threshold "
               "across the value observed for the case city.")

OLD_SI_25 = ("25. **Classification boundaries are not empirically validated.** The regime boundaries "
             "depend on the position of $C^{*}=L/\\mathrm{CoC}_d$ relative to the two source "
             "salinities, and $\\mathrm{CoC}_d$ carries no anchor in the parameter envelope. This is "
             "the weakest link.")
NEW_SI_25 = ("""25. **Classification boundaries are not empirically validated, and the anchor gap is wider than one parameter.** The regime boundaries depend on the position of $C^{*}=L/\\mathrm{CoC}_d$ relative to the two source salinities, so they inherit the uncertainty of all four threshold parameters. Auditing these four against `parameter_envelope_R7.csv` (54 rows) gives:

| Parameter | Value | In envelope table | Anchor status |
|---|---:|---|---|
| $L$ (loop TDS limit) | 2200 mg L⁻¹ | **no** | never audited |
| $\\mathrm{CoC}_d$ | 5.0 | yes | **no anchor** |
| $C_p$ (potable TDS) | 180 mg L⁻¹ | **no** | never audited |
| $C_r$ (reclaimed TDS) | 650 mg L⁻¹ | **no** | never audited |

Only one of the four appears in the envelope table, and that one is itself unanchored; the three water-quality parameters have never been entered into it. An earlier internal description treated $\\mathrm{CoC}_d$ alone as the weakest link, which understated the gap: the weakness is not one parameter but all four.

Sensitivity to a single ±10% perturbation, expressed as the offset from the nominal $r^{*}=0.5532$ and the two-endpoint span: $L$ 0.0936 / 0.1872; $\\mathrm{CoC}_d$ 0.1040 / 0.1891; $C_r$ 0.0888 / 0.1560; $C_p$ 0.0178 / 0.0343. Any one of the first three can push $r^{*}$ into 0.46–0.66, an interval that spans both "the case city has not crossed" and "it has". This is the most consequential quantitative limitation in the paper.

**Evidence:** `_rstar_param_anchoring.json`, `_rstar_sens_exact.py`. The four values above were read directly from `examples/cawcc_r2/ha/project.json`.""")

t = MS.read_text(encoding="utf-8")
n = 0
for old, new, tag in ((OLD_MS_METHOD, NEW_MS_METHOD, "英文 §2.5"),
                      (OLD_MS_LIM, NEW_MS_LIM, "英文 §4.4"),
                      (OLD_MS_SENS, NEW_MS_SENS, "英文 §3.2")):
    if old in t:
        t = t.replace(old, new, 1)
        n += 1
        print(f"OK {tag}")
    else:
        print(f"未匹配 {tag}")
MS.write_text(t, encoding="utf-8")

s = SI.read_text(encoding="utf-8")
if OLD_SI_25 in s:
    s = s.replace(OLD_SI_25, NEW_SI_25, 1)
    SI.write_text(s, encoding="utf-8")
    print("OK SI 第 25 条")
else:
    print("未匹配 SI 第 25 条")

import re
print("\n英文稿词数:", len(re.sub(r"\$[^$]*\$", " MATH ", t).split()))
