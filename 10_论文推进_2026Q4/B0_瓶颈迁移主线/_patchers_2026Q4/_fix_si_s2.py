# -*- coding: utf-8 -*-
"""修正 SI 的 S2 节：按母稿 §4.1-§4.4 实况重写，删除我误写的"两端都不重合"。"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
SI = HERE / "05_wr_supplementary_en.md"

NEW_S2 = """## S2 Metabolic response and structural transition (demoted from the main text)

### S2.1 Aggregate indicators barely move at low capacity

At the water-scarce endpoint, from 50 MW to 1100 MW, the freshwater-dependence ratio is identically 0.3000, the urban water cycling rate identically 0.7000 and the consumption share identically 0.7867. An AI load growing 22-fold leaves every structural indicator of urban water metabolism unchanged. This is not a model defect but a geometric consequence of the constraint structure: in the low-capacity region the AI load is small relative to total city demand and draws its increment from the two sources in fixed proportion, so structural ratios cannot move. "Totals rise while structure holds" is exactly why facility-scale accounting sees no problem.

### S2.2 Structural transition and first-failure capacity: the relationship is endpoint-dependent

The two capacities do not relate in the same way at the two endpoints, and the asymmetry must be reported as found:

| Endpoint | Capacity at which the structural indicator first departs from baseline | Physical daily CAWCC | Relationship |
|---|---:|---:|---|
| D-HA | **1150 MW** (freshwater-dependence ratio 0.300000→0.302388) | **1150 MW** | **coincide** |
| D-CO | **1700 MW** (0.550000→0.550334) | **1450 MW** | **250 MW later** |

At the water-scarce endpoint the structural transition and the carrying boundary coincide, because that endpoint's first-failing constraint is the source abstraction ratio, which is itself the direct driver of the structural indicator: when abstraction hits its ceiling the structure must turn at the same point. This licenses the strong statement that structural transition coincides with constraint transition at the water-scarce endpoint. At the cool endpoint the structural transition comes 250 MW later than the carrying boundary, because that endpoint's first-failing constraint is grid connection, which is independent of water-side structure; the structural indicator only begins to reflect source pressure at 1700 MW, before the abstraction ratio's first failure at 1800 MW. The strong statement therefore cannot be made at the cool endpoint.

The resulting formulation is that whether structural transition coincides with constraint transition is itself endpoint-dependent — coinciding where the first-failing constraint drives the structural indicator directly, separating where the first-failing constraint lies on the electrical side. This is more precise, and more consistent with a mechanism-study positioning, than the original expectation that the structural transition point could be located internally by the model alone.

### S2.3 Quantitative response after the transition

At the water-scarce endpoint the structural indicators decay monotonically once the boundary is crossed:

| Capacity (MW) | Freshwater-dependence ratio | Water cycling rate | State |
|---:|---:|---:|---|
| ≤1100 | 0.3000 | 0.7000 | structure constant |
| 1150 | 0.3024 | 0.6976 | transition begins (= CAWCC) |
| 1200 | 0.3113 | 0.6887 | first failure (abstraction ratio 0.9550 > 0.95) |
| 1300 | 0.3444 | 0.6556 | |
| 1500 | 0.4249 | 0.5751 | |
| 2000 | 0.5630 | 0.4370 | |

From CAWCC (1150 MW) to 2000 MW the freshwater-dependence ratio rises from 0.30 to 0.56 (+87%) and the cycling rate falls from 0.70 to 0.44. Structure deteriorates at an accelerating rate once the boundary is crossed, which is the quantitative expression of "crossing is not a point but a process".

### S2.4 Qualification

All of S2 is a synthetic-endpoint result. The freshwater-dependence ratio is defined as potable divided by the sum of withdrawal and unmet demand, and its value is set directly by the substitution target (a target of 0.70 giving 0.30 at the water-scarce endpoint); it is not a measured structural indicator of any city. At the cool endpoint the structural indicators do not turn at all at its CAWCC of 1450 MW, which is the direct expression of "the grid binds first", but this must not be read as "cool cities are unaffected by water quantity": it states only that under this parameter set the water-side constraints have not become first-failing within 2000 MW.
"""


def main() -> None:
    text = SI.read_text(encoding="utf-8")
    start = text.index("## S2 Metabolic response")
    end = text.index("## S3 Time-scale effects")
    new = text[:start] + NEW_S2 + "\n---\n\n" + text[end:]
    SI.write_text(new, encoding="utf-8")
    print("OK S2 已按母稿 §4.1–§4.4 重写")
    print("新长度:", len(new), "字符")


if __name__ == "__main__":
    main()
