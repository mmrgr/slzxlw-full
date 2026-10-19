# -*- coding: utf-8 -*-
"""把 k* 的敏感性分析写入英文正文与 SI。

核心：k* = (1/r* − 1)/ρ，ρ = α/β。k* 对 ρ 极敏感：
  ρ=6/26=0.2308 → k*=3.50，加州 23/169（13.6%）低于此
  ρ=1（份额相同）→ k*=0.808，仅 3/169（1.8%）
故 3.50 不是普适常数，必须连同 ρ 一起报，并给出保守边界。
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

OLD_MS = """Setting $r=r^{*}$ gives the critical city ratio $k^{*}=(1/r^{*}-1)/(\\alpha/\\beta)$. With the shares documented for Santa Clara, California, of 6% of city potable water and 26% of city reclaimed water, $k^{*}=(1/0.5532-1)/(6/26)=3.50$. The screen requires only two published numbers: a city whose ratio of potable to reclaimed use falls below 3.50 has a data-centre substitution ratio that necessarily exceeds $r^{*}$ and enters the penalty region. This is a transferable screening procedure, not an assessment of any one city; the city below is the substitution that demonstrates it."""

NEW_MS = """Setting $r=r^{*}$ gives the critical city ratio $k^{*}=(1/r^{*}-1)/\\rho$, where $\\rho\\equiv\\alpha/\\beta$ is the ratio of the data-centre shares in the two supplies. For the shares documented in Santa Clara, California — 6% of city potable water and 26% of city reclaimed water, so $\\rho=6/26=0.2308$ — this gives $k^{*}=3.50$: a city whose ratio of potable to reclaimed use falls below 3.50 has a data-centre substitution ratio that necessarily exceeds $r^{*}$. This is a transferable screening procedure, not an assessment of any one city; the city below is the substitution that demonstrates it.

The value 3.50 must be reported together with $\\rho$, because $k^{*}$ is strongly sensitive to it and the screen is only as sharp as the shares it is fed. Holding $r^{*}$ at its nominal value, $\\rho=0.10$ gives $k^{*}=8.08$ and $\\rho=1.0$ gives $k^{*}=0.81$; across that range the Californian population falling below the boundary falls from 57 to 3 systems. $k^{*}$ is equally sensitive to $r^{*}$, which carries the $\\pm10\\%$ parameter uncertainty noted below: at $\\rho=0.2308$, moving $r^{*}$ from 0.50 to 0.61 moves $k^{*}$ from 4.33 to 2.77. We therefore report a conservative boundary as well. Setting $\\rho=1$, which assumes data centres take the same share of both supplies and is the least favourable assumption for crossing, yields $k^{*}=0.81$, and 3 of the 169 systems still fall below it. The claim that survives every assumption we examined is thus narrower than the Santa Clara-calibrated figure, and we state both."""

OLD_SI_ANCHOR = "### S7.7 The California $k$ distribution"

NEW_SI = """### S7.7 Sensitivity of the critical ratio $k^{*}$

The critical city ratio is $k^{*}=(1/r^{*}-1)/\\rho$ with $\\rho\\equiv\\alpha/\\beta$. Because both
inputs are uncertain for any city other than the one documented case, we tabulated the
sensitivity rather than reporting a single number.

Against $\\rho$, holding $r^{*}=0.5532$:

| $\\rho$ | $k^{*}$ | Californian systems with $k<k^{*}$ | Share | Interpretation |
|---:|---:|---:|---:|---|
| 0.10 | 8.08 | 57 | 33.7% | data centres almost exclusively on reclaimed water |
| 0.20 | 4.04 | 29 | 17.2% | |
| **0.2308** | **3.50** | **23** | **13.6%** | Santa Clara 6%/26% |
| 0.30 | 2.69 | 14 | 8.3% | |
| 0.50 | 1.62 | 4 | 2.4% | |
| **1.00** | **0.81** | **3** | **1.8%** | conservative: equal shares in both supplies |
| 2.00 | 0.40 | 1 | 0.6% | data centres mostly on potable water |

Against $r^{*}$, holding $\\rho=0.2308$:

| $r^{*}$ | $k^{*}$ | Systems with $k<k^{*}$ | Share |
|---:|---:|---:|---:|
| 0.50 | 4.33 | 34 | 20.1% |
| 0.52 | 4.00 | 29 | 17.2% |
| **0.5532** | **3.50** | **23** | **13.6%** |
| 0.58 | 3.14 | 20 | 11.8% |
| 0.61 | 2.77 | 15 | 8.9% |

Two conclusions follow. First, the headline figures of 3.50 and 13.6% are conditional on the
Santa Clara share ratio; they are not properties of the criterion itself, and reporting them
without $\\rho$ would overstate the sharpness of the screen. Second, even under the least
favourable assumption we examined — equal shares in both supplies, $\\rho=1$ — three systems
remain below the boundary, so the qualitative claim survives while the population it identifies
shrinks by an order of magnitude. The honest reading is that the screen is a way of asking a
well-posed question of a city's two published numbers, not a fixed threshold applicable
everywhere.

**Evidence:** `_ca_kstar_sensitivity.json`, computed from `_ca_k_clean.json` (169 systems).

---

### S7.8 The California $k$ distribution"""


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    if OLD_MS not in t:
        print("英文稿未匹配")
    else:
        t = t.replace(OLD_MS, NEW_MS, 1)
        MS.write_text(t, encoding="utf-8")
        print("OK 英文稿已插入 k* 敏感性")

    s = SI.read_text(encoding="utf-8")
    if OLD_SI_ANCHOR not in s:
        print("SI 锚点未匹配")
        return
    s = s.replace(OLD_SI_ANCHOR, NEW_SI, 1)
    SI.write_text(s, encoding="utf-8")
    print("OK SI 已新增 S7.7（原 S7.7 顺延为 S7.8）")


if __name__ == "__main__":
    main()
