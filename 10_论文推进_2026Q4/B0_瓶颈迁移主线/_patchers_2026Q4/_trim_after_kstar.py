# -*- coding: utf-8 -*-
"""插入 k* 敏感性后回补词数至 <=7700。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    (
        "The value 3.50 must be reported together with $\\rho$, because $k^{*}$ is strongly sensitive to it and the screen is only as sharp as the shares it is fed. Holding $r^{*}$ at its nominal value, $\\rho=0.10$ gives $k^{*}=8.08$ and $\\rho=1.0$ gives $k^{*}=0.81$; across that range the Californian population falling below the boundary falls from 57 to 3 systems. $k^{*}$ is equally sensitive to $r^{*}$, which carries the $\\pm10\\%$ parameter uncertainty noted below: at $\\rho=0.2308$, moving $r^{*}$ from 0.50 to 0.61 moves $k^{*}$ from 4.33 to 2.77. We therefore report a conservative boundary as well. Setting $\\rho=1$, which assumes data centres take the same share of both supplies and is the least favourable assumption for crossing, yields $k^{*}=0.81$, and 3 of the 169 systems still fall below it. The claim that survives every assumption we examined is thus narrower than the Santa Clara-calibrated figure, and we state both.",
        "The value 3.50 must be reported with $\\rho$, because $k^{*}$ is strongly sensitive to it and the screen is only as sharp as the shares it is fed. Holding $r^{*}$ nominal, $\\rho=0.10$ gives $k^{*}=8.08$ and $\\rho=1.0$ gives $k^{*}=0.81$; across that range the Californian population below the boundary falls from 57 to 3 systems. $k^{*}$ is equally sensitive to $r^{*}$, which carries the $\\pm10\\%$ uncertainty noted below: at $\\rho=0.2308$, moving $r^{*}$ from 0.50 to 0.61 moves $k^{*}$ from 4.33 to 2.77. We therefore also report a conservative boundary. Setting $\\rho=1$, which assumes equal data-centre shares in both supplies and is least favourable to crossing, yields $k^{*}=0.81$, and 3 of the 169 systems still fall below it. The claim surviving every assumption we examined is narrower than the Santa-Clara-calibrated figure, and we state both.",
    ),
    (
        "Applied across a state, the screen identifies a non-trivial population. From the full 2022 California Electronic Annual Report we extracted every public water system reporting both potable and recycled production and computed $k$, retaining systems with potable production of at least 100 acre-feet per year, $k\\ge0.2$ and a recycled share no greater than 90%. That leaves 169 systems with a median $k$ of 13.54, of which 13.6% (23 systems) fall below $k^{*}=3.50$; among the 93 large systems serving 50,000 or more people the share is 8.6%.",
        "Applied across a state, the screen identifies a non-trivial population. From the full 2022 California Electronic Annual Report we extracted every public water system reporting both potable and recycled production and computed $k$, retaining systems with potable production of at least 100 acre-feet per year, $k\\ge0.2$ and a recycled share no greater than 90%. That leaves 169 systems with a median $k$ of 13.54, of which 13.6% (23) fall below $k^{*}=3.50$; among the 93 large systems serving 50,000 or more the share is 8.6%.",
    ),
]


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    n = 0
    for old, new in PAIRS:
        if old in t:
            t = t.replace(old, new, 1)
            n += 1
    MS.write_text(t, encoding="utf-8")
    s = re.sub(r"\$[^$]*\$", " MATH ", t)
    print(f"替换 {n}/{len(PAIRS)}；总词数 {len(s.split())}")


if __name__ == "__main__":
    main()
