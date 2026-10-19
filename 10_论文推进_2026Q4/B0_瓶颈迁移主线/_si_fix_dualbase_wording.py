# -*- coding: utf-8 -*-
"""收紧 SI S6.5 中关于"两基底一致"的措辞：说明一致到所报精度，并非严格相等。"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
SI = HERE / "05_wr_supplementary_en.md"

OLD = """All six combinations confirm their predictions. The absolute withdrawals differ between
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
percentages is the evidence, not a defect."""

NEW = """All six combinations confirm their predictions. The absolute withdrawals differ between
baselines — at $r=0$ under Regime II, 22,390.8 ML at the water-scarce endpoint versus
22,126.7 ML at the cool endpoint — but the **relative** changes agree to every digit
reported here (Regime II: +6.476503% versus +6.476462%; Regime I: +20.741175% versus
+20.741024%).

This near-identity is expected rather than surprising, and it is worth stating why, because
a near-identical result invites the suspicion that the baseline switch did not take effect.
The relative change in make-up demand depends only on the ratio of
$\\mathrm{CoC}/(\\mathrm{CoC}-1)$ between the two substitution ratios, and the CoC trajectory
is set by the water-quality parameters alone through
$\\mathrm{CoC}=\\min(\\mathrm{CoC}_d, L/C_{\\mathrm{mix}}(r))$. Since both baselines share
those parameters, they share the CoC trajectory, so any quantity proportional to it must
scale almost identically. What the dual replication establishes is therefore that the
taxonomy's behaviour is not an artefact of one city's climate or facility sizing — which is
precisely the part of the configuration that differs, and which is what changes the absolute
withdrawals by 230 to 345 ML between baselines. The agreement is close but not exact: the
residual at the fifth and sixth significant figure reflects small differences in the daily
delivered-ratio path, on which the min operation acts before averaging, and it is two orders
of magnitude below the evaporation drift discussed next."""


def main() -> None:
    text = SI.read_text(encoding="utf-8")
    if OLD not in text:
        print("未匹配，中止")
        return
    SI.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK 措辞已收紧")
    print("新长度:", len(text))


if __name__ == "__main__":
    main()
