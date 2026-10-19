# -*- coding: utf-8 -*-
"""更新 SI：三情形验证从单基底升级为双基底，并新增一节记录该验证的结果。"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
SI = HERE / "05_wr_supplementary_en.md"

OLD_28 = ("28. **Regime validation used one endpoint, one capacity and five ratios.** "
          "Universality rests on the derivation; the empirical work is a sampling check, "
          "not a full-grid confirmation.")

NEW_28 = ("28. **Regime validation used two endpoints, one capacity and five ratios each.** "
          "Universality still rests on the derivation rather than on simulation: the empirical "
          "work is a sampling check, not a full-grid confirmation, and the capacity dimension "
          "was not varied. The dual-endpoint replication (S6.5) removes the earlier single-baseline "
          "limitation but does not make the check exhaustive.")

# 在 S6.4 之后追加 S6.5
ANCHOR = "## S7 Derivation detail for the two-number city screen"

NEW_S65 = """### S6.5 Dual-baseline replication of the regime taxonomy

The regime taxonomy was initially validated on the water-scarce baseline only, a limitation
recorded as item 28. Because both endpoints carry identical water-quality parameters
($L=2200$ mg L$^{-1}$ and chloride $500$ mg L$^{-1}$; $C_p=180$, $C_r=650$ mg L$^{-1}$;
$\\mathrm{CoC}_d=5.0$), their analytic $r^{*}$ is the same, but their climate drivers and
facility parameters differ. Replicating on both therefore tests whether the taxonomy's
qualitative behaviour is a property of the water chemistry alone or of the full model
configuration.

| Regime | $\\mathrm{CoC}_d$ | $r^{*}$ | Baseline | CoC at $r=0$ | Change in withdrawal, $r=0\\to0.8$ | CoC equal to design |
|---|---:|---:|---|---:|---:|---|
| II | 5.0 | 0.5532 | D-HA | 5.0000 | +6.48% | 3/5 points |
| II | 5.0 | 0.5532 | D-CO | 5.0000 | +6.48% | 3/5 points |
| I | 15.0 | −0.0709 | D-HA | 12.2222 | +20.74% | 0/5 points |
| I | 15.0 | −0.0709 | D-CO | 12.2222 | +20.74% | 0/5 points |
| III | 2.5 | 1.4894 | D-HA | 2.5000 | 0.00e+00% | 5/5 points |
| III | 2.5 | 1.4894 | D-CO | 2.5000 | 0.00e+00% | 5/5 points |

All six combinations confirm their predictions. The absolute withdrawals differ between
baselines — at $r=0$ under Regime II, 22,390.8 ML at the water-scarce endpoint versus
22,126.7 ML at the cool endpoint — but the **relative** changes are identical to the
printed digits.

This identity is expected rather than surprising, and it is worth stating why, because an
identical-looking result invites the suspicion that the baseline switch did not take effect.
The relative change in make-up demand depends only on the ratio of
$\\mathrm{CoC}/(\\mathrm{CoC}-1)$ between the two substitution ratios, and the CoC trajectory
is set by the water-quality parameters alone through $\\mathrm{CoC}=\\min(\\mathrm{CoC}_d, L/C_{\\mathrm{mix}}(r))$.
Since both baselines share those parameters, they share the CoC trajectory, so any quantity
proportional to it must scale identically. What the dual replication establishes is therefore
that the taxonomy's behaviour is not an artefact of one city's climate or facility sizing —
which is precisely the part of the configuration that differs. The identity of the
percentages is the evidence, not a defect.

One quantitative check ties the taxonomy back to the derivation. The closed form predicts a
$+7.056\\%$ rise in make-up demand from $r=0$ to $0.8$ at $\\mathrm{CoC}_d=5$, computed as the
ratio of $\\mathrm{CoC}/(\\mathrm{CoC}-1)$ at the two points; the model returns $+6.477\\%$ for
total withdrawal. The 0.58-point shortfall is the same evaporation drift recorded in the main
text: evaporation is not perfectly constant, falling $0.76\\%$ over the range, so the closed
form slightly over-predicts. The agreement is therefore close but not exact, and the residual
is attributed rather than left unexplained.

**Evidence:** `rstar_regime_validation.csv` (with a `base` column), `rstar_regime_validation.json`
(`per_base` object). Both were regenerated on 2026-10-18 with `--bases ha,co`.

"""


def main() -> None:
    text = SI.read_text(encoding="utf-8")
    if OLD_28 not in text:
        print("找不到第 28 条，中止")
        return
    text = text.replace(OLD_28, NEW_28, 1)
    if ANCHOR not in text:
        print("找不到 S7 锚点，中止")
        return
    text = text.replace(ANCHOR, NEW_S65 + "---\n\n" + ANCHOR, 1)
    SI.write_text(text, encoding="utf-8")
    print("OK 已更新第 28 条并新增 S6.5")
    print("新长度:", len(text))


if __name__ == "__main__":
    main()
