# -*- coding: utf-8 -*-
"""把词数压回 <=7700（当前 7837，需减 ~140）。重点压 §3.4 与 §4.4。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
MS = HERE / "04_wr_manuscript_en.md"

PAIRS = [
    # §3.4 首段
    (
        "The criterion becomes usable in quantities cities already publish. Let city potable use be $P$ and reclaimed use be $R$; if data centres take share $\\alpha$ of potable and $\\beta$ of reclaimed, campus make-up is $D=\\alpha P+\\beta R$ and the campus ratio is",
        "The criterion becomes usable in quantities cities already publish. Let city potable use be $P$ and reclaimed use be $R$; if data centres take share $\\alpha$ of potable and $\\beta$ of reclaimed, campus make-up is $D=\\alpha P+\\beta R$, so",
    ),
    # §3.4 Santa Clara 两口径
    (
        "For Santa Clara the 2025 Urban Water Management Plan gives two calibers. On supply capacity (SFPUC 5041, Valley Water 4560, groundwater 23,048 and recycled 6017, totalling 38,666 acre-feet per year) potable is 32,649 and reclaimed 6017, giving $k=5.43$ and $r=0.444$, 10.9 percentage points below $r^{*}$. On 2025 actual use potable is 16,857 and reclaimed 3871, giving $k=4.35$ and $r=0.499$, 5.4 points below. Both calibers agree the threshold has not been crossed, but the actual-use margin is only 9.8%. An independent source corroborates the ratio: the California Electronic Annual Report for 2022 gives potable 16,913 and recycled 3450 acre-feet, hence $k=4.90$, differing by 0.3% on potable and 11% on recycled. The actual-use caliber sits closer to the threshold because the city is lightly loaded overall, using 20,728 of 38,666 acre-feet per year or 53.6% of supply capacity, while its recycled subsystem is heavily loaded at 3871 of 6017, or 64.3%: when total water is abundant, what constrains the data-centre blend is the tightness of the recycled subsystem rather than total volume.",
        "For Santa Clara the 2025 Urban Water Management Plan gives two calibers. On supply capacity (SFPUC 5041, Valley Water 4560, groundwater 23,048 and recycled 6017, totalling 38,666 acre-feet per year) potable is 32,649 and reclaimed 6017, giving $k=5.43$ and $r=0.444$, 10.9 points below $r^{*}$. On 2025 actual use potable is 16,857 and reclaimed 3871, giving $k=4.35$ and $r=0.499$, 5.4 points below. Both agree the threshold is not crossed, but the actual-use margin is only 9.8%. An independent source corroborates the ratio: the California Electronic Annual Report for 2022 gives potable 16,913 and recycled 3450 acre-feet, hence $k=4.90$, differing by 0.3% on potable and 11% on recycled. The actual-use caliber sits closer because the city is lightly loaded overall, using 20,728 of 38,666 acre-feet per year or 53.6% of capacity, while its recycled subsystem is heavily loaded at 3871 of 6017, or 64.3%: when water is abundant, what constrains the blend is the tightness of the recycled subsystem rather than total volume.",
    ),
    # §4.4 局限
    (
        "The dominant limitation is that nothing here is calibrated to a real city. All capacity numbers are conditional on synthetic 730-day drivers, one parameter set per endpoint and ten in-model thresholds that have not been calibrated against any city, so they demonstrate mechanism rather than estimate reality. The two endpoints are corners of a parameter domain, and a 25-city gradient scan along the parameter axes checked continuity only. The design cycles of concentration, which controls the threshold, carries no anchor, making the classification boundary the weakest link in the argument.",
        "The dominant limitation is that nothing here is calibrated to a real city. All capacity numbers are conditional on synthetic 730-day drivers, one parameter set per endpoint and ten thresholds not calibrated against any city, so they demonstrate mechanism rather than estimate reality. The endpoints are corners of a parameter domain, and a 25-city gradient scan checked continuity only. The design cycles of concentration, which controls the threshold, carries no anchor, making the classification boundary the weakest link.",
    ),
    (
        "The semantics of the grid constraint are unresolved: the model does not distinguish campus-connection capacity from node-available capacity in the urban grid, which governs how the electrical bottleneck should be read. It may represent an engineering constraint on campus interconnection rather than physical headroom in the city grid, and is the element most likely to be challenged.",
        "The grid constraint's semantics are unresolved: the model does not distinguish campus-connection capacity from node-available capacity in the urban grid, which governs how the electrical bottleneck should be read. It may represent an engineering constraint on campus interconnection rather than physical headroom, and is the element most likely to be challenged.",
    ),
    # §1 引言末段
    (
        "Two scope statements belong here rather than in the limitations. We claim no capacity loss under current policy. In the range $r\\le0.35$, which contains current Chinese reclaimed-water utilisation targets, the carrying capacity of both endpoints does not vary with $r$ at all, and this exact zero is identical on all three capacity grids tested. A linear mechanism cannot produce an exact zero; a threshold mechanism can, and that zero is falsifiable by any non-zero observation. The criterion's policy value therefore lies in delimiting a safe interval rather than forecasting any city's present condition. Second, the ratio used here is the campus substitution ratio, whose denominator is campus cooling make-up, not the city-wide utilisation rate whose denominator is municipal wastewater throughput; the bridge between them is $r_{\\max}=u\\,(W/D)$.",
        "Two scope statements belong here rather than in the limitations. We claim no capacity loss under current policy. In the range $r\\le0.35$, which contains current Chinese reclaimed-water utilisation targets, the carrying capacity of both endpoints does not vary with $r$ at all, and this exact zero is identical on all three capacity grids tested. A linear mechanism cannot produce an exact zero; a threshold mechanism can, and that zero is falsifiable by any non-zero observation. The criterion's policy value therefore lies in delimiting a safe interval rather than forecasting any city's present condition. Second, the ratio used here is the campus substitution ratio, not the city-wide utilisation rate whose denominator is municipal wastewater throughput; the bridge between them is $r_{\\max}=u\\,(W/D)$.",
    ),
]


def main() -> None:
    t = MS.read_text(encoding="utf-8")
    n = 0
    for old, new in PAIRS:
        if old in t:
            t = t.replace(old, new, 1)
            n += 1
        else:
            print("未匹配:", old[:60])
    MS.write_text(t, encoding="utf-8")
    s = re.sub(r"\$[^$]*\$", " MATH ", t)
    print(f"替换 {n}/{len(PAIRS)}；总词数 {len(s.split())}")


if __name__ == "__main__":
    main()
