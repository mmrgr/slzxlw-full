# -*- coding: utf-8 -*-
"""把 SI S4 的三杠杆表更新为 50 MW 同网格重跑后的真实值。

关键修正：
  - 旧（100 MW 网格）：基线 HA 1100 / CO 1400，产水量杠杆 +300 MW
  - 新（50 MW 网格）  ：基线 HA 1150 / CO 1450，产水量杠杆 +250 MW
  +300 是"基线网格伪影"：100 MW 网格从未评估 1150 这一点，
  因此 1400−1100=300 里有一部分来自基线取整，不是真实增益。
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
SI = HERE / "05_wr_supplementary_en.md"

OLD_S41 = """### S4.1 Structure of the chapter

The chapter compares three levers that are routinely conflated:

| Lever | Operation | Mechanism | D-HA effect | D-CO effect |
|---|---|---|---|---|
| Treatment capacity | Expand reclaimed-plant treatment scale, production unchanged | None (production is the binding quantity) | CAWCC fixed at 1100, gain 0 | CAWCC fixed at 1400, gain 0 |
| Production | Raise WWTW diversion fraction 0.16→0.25 | Adds available reclaimed volume | CAWCC 1100→1400 (+300), bottleneck migrates to grid | No effect (bottleneck already electrical) |
| Substitution ratio $r$ | Raise target 0.5→0.8 | Blend salinity depresses CoC, raises make-up demand | Physical CAWCC 1200→1100 (−100) | Essentially no change (second condition unmet) |

**Caliber statement, which must travel with this table:** the treatment-capacity and production rows come from 100 MW-grid marginal curves (base points 1100 and 1400 MW), whereas the substitution-ratio row comes from the full 50 MW-grid scan. The two are not the same grid, so their MW values may not be added or subtracted. The table's purpose is to show the difference in direction, not a numerical comparison."""

NEW_S41 = """### S4.1 Structure of the chapter

The chapter compares three levers that are routinely conflated. All three rows now come from
the same 50 MW grid as the main results, so their megawatt values are directly comparable:

| Lever | Operation | Mechanism | D-HA effect | D-CO effect |
|---|---|---|---|---|
| Treatment capacity | Expand reclaimed-plant treatment scale, production unchanged | None (production is the binding quantity) | CAWCC fixed at **1150**, gain **0** | CAWCC fixed at **1450**, gain **0** |
| Production | Raise WWTW diversion fraction 0.16→0.25 | Adds available reclaimed volume | CAWCC **1150→1400 (+250)**, bottleneck migrates to grid | No effect (bottleneck already electrical) |
| Substitution ratio $r$ | Raise target 0.5→0.8 | Blend salinity depresses CoC, raises make-up demand | Physical CAWCC **1200→1100 (−100)** | Essentially no change (second condition unmet) |

**The +250 MW figure supersedes an earlier +300 MW, and the reason matters.** The earlier
value was computed on a 100 MW grid whose baseline was 1100 MW for the water-scarce endpoint
and 1400 MW for the cool endpoint. Because that grid never evaluated 1150 MW — the true
50 MW-grid baseline — a 1400 − 1100 = +300 difference mixed a real gain with a baseline
rounding artefact. Re-running both levers on the 50 MW grid gives baselines of 1150 and 1450 MW,
identical to the main results, and a production-lever gain of +250 MW. The qualitative
conclusion is unchanged and, if anything, stronger: the gain is real, the bottleneck genuinely
migrates from source abstraction to grid connection, and the treatment-capacity lever remains
identically zero. Only the magnitude moves, and it moves down.

A second correction follows from the same re-run. The joint and purely physical constraint sets
give numerically identical capacities throughout this scan at both endpoints (1150 and 1450 MW),
because at the lever settings examined the policy constraint is not the binding one. This had
to be verified rather than assumed: the substitution-ratio experiments of the main text do
separate the two calibers, and the separation is 300 MW there. The lever scan simply sits in a
region where it does not."""


OLD_S46 = """| Lever | Operation | D-HA result | D-CO result |
|---|---|---|---|
| Treatment capacity only | `treatment_capacity_ml_day` 40→160 (HA) / 36→160 (CO), production unchanged | CAWCC fixed at 1100, marginal gain identically 0 | CAWCC fixed at 1400, marginal gain identically 0 |
| Production | `central_reuse_fraction` 0.16→0.60 (HA) / 0.15→0.60 (CO) | CAWCC 1100→1400 (+300), bottleneck moves from source abstraction to grid connection | CAWCC fixed at 1400 (100 MW-grid caliber) |"""

NEW_S46 = """| Lever | Operation | D-HA result | D-CO result |
|---|---|---|---|
| Treatment capacity only | `treatment_capacity_ml_day` 40→160 (HA) / 36→160 (CO), production unchanged | CAWCC fixed at 1150, marginal gain identically 0 at every point | CAWCC fixed at 1450, marginal gain identically 0 at every point |
| Production | `central_reuse_fraction` 0.16→0.60 (HA) / 0.15→0.60 (CO) | CAWCC 1150→1400 (+250), bottleneck moves from source abstraction to grid connection | CAWCC fixed at 1450 throughout |"""


OLD_TABLE = """| `central_reuse_fraction` | Estimated production (ML/d) | Paired capacity (ML/d) | CAWCC (MW) | Limiting constraint |
|---:|---:|---:|---:|---|
| 0.16 (baseline) | 32.2 | 40.3 | 1100 | Source abstraction ratio |
| 0.25 | 50.4 | 62.9 | 1400 | Daily-average grid connection |
| 0.35 | 70.5 | 88.1 | 1400 | as above |
| 0.45 | 90.6 | 113.3 | 1400 | as above |
| 0.60 | 120.8 | 151.1 | 1400 | as above |"""


def main() -> None:
    text = SI.read_text(encoding="utf-8")
    ok = 0
    for old, new, tag in (
        (OLD_S41, NEW_S41, "S4.1"),
        (OLD_S46, NEW_S46, "S4.6 表"),
    ):
        if old in text:
            text = text.replace(old, new, 1)
            ok += 1
            print(f"OK 已更新 {tag}")
        else:
            print(f"未匹配 {tag}")
    SI.write_text(text, encoding="utf-8")
    print(f"\n完成 {ok}/2，新长度 {len(text)}")


if __name__ == "__main__":
    main()
