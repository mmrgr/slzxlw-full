"""把双路径对照写入 SI（S21 新节）+ 主稿边界声明 (2026-10-17).

路线 C: 主口径不变, 把 16 情景双路径对照作为敏感性分析呈现, 并给出精确边界声明。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
SI = ROOT / "A16_英文稿/supplementary_information.md"
MS = ROOT / "A16_英文稿/manuscript_en_v3.md"

SI_SECTION = """
---

## S21. Solver-path sensitivity: does the volume-only水质口径 drive the composition result?

**Why this section exists.** The engine offers two quality solvers. The main grid in this paper
uses the *volume-only* path throughout. A reviewer is entitled to ask whether the results —
particularly the composition effect — depend on that choice. We ran the comparison and report
it here in full, including the parts that are uncomfortable for our conclusions.

### S21.1 The two paths

| path | how loop concentration is obtained | key code |
|---|---|---|
| **volume-only** (main grid) | instantaneous mix of the make-up sources; no loop solute stock is carried between days | `concentrations[i] += fraction × value`, then `CoC = min(limit_i / concentration_i, design)` |
| **R10a dynamic** (opt-in) | a loop solute stock is integrated day by day | `loop_state = mix(withdrawn_state, prior_return_state)` |

### S21.2 An internal inconsistency in the volume-only path

In the volume-only path the value used against the concentration limits **is the make-up
concentration itself**, not a loop concentration. We verified this directly: the CoC it reports
is reproduced to 4 decimal places by the closed form `min_i(limit_i / C_makeup,i)` in **8 of 8**
tested conditions.

That is internally inconsistent. If the loop concentration equals the make-up concentration then,
by definition, CoC = 1; yet the same path reports CoC between 1.8 and 5.0. Put differently, the
path applies **circulating-water** limits to **make-up water**, and treats the resulting ratio as
a circulation ratio.

The dynamic path does not have this problem: for the same inputs its CoC rises from the initial
value and converges to a steady state consistent with a continuously stirred loop —
**5.0000** (s.d. 0.00 over the last 30 days) at φ = 0.6, and 4.98 at φ = 0.4, where the alkalinity
limit binds slightly. We also tested the naive mass-balance check
`M = E·CoC/(CoC−1)` and it **fails to discriminate**: the engine computes make-up water *from*
CoC, so any CoC satisfies it (deviation 2.8% vs 2.3%). That check is reported here only to record
that it was tried and is not evidence either way.

### S21.3 What changes if the dynamic path is used

Sixteen matched scenarios (4 compositions × 2 domains × 2 blending fractions). `dS_pot` is
assembled as `M1 − M0` for the pure-displacement branch, computed directly by the engine.

| domain | composition | φ | dS_pot, volume-only (ML) | dS_pot, R10a (ML) | sign |
|---|---|---:|---:|---:|---|
| ha | IEUA | 0.4 | **+1,967** | **−3,027** | **flips** |
| ha | IEUA | 0.6 | **+3,056** | **−3,075** | **flips** |
| ha | Figshare RW | 0.4 | **+7,423** | **−3,018** | **flips** |
| ha | Figshare RW | 0.6 | **+12,784** | **−3,063** | **flips** |
| ha | AI-UWM assumption | 0.4 | **+5,481** | **−3,021** | **flips** |
| ha | AI-UWM assumption | 0.6 | **+9,086** | **−3,068** | **flips** |
| ha | LADWP | 0.4 | −3,083 | −3,034 | same |
| ha | LADWP | 0.6 | −3,083 | −3,083 | same |
| co | IEUA | 0.4 | **+1,944** | **−2,986** | **flips** |
| co | IEUA | 0.6 | **+3,020** | **−3,039** | **flips** |
| co | Figshare RW | 0.4 | **+7,336** | **−2,978** | **flips** |
| co | Figshare RW | 0.6 | **+12,633** | **−3,027** | **flips** |
| co | AI-UWM assumption | 0.4 | **+5,416** | **−2,981** | **flips** |
| co | AI-UWM assumption | 0.6 | **+8,979** | **−3,032** | **flips** |
| co | LADWP | 0.4 | −3,046 | −2,994 | same |
| co | LADWP | 0.6 | −3,046 | −3,046 | same |

**Twelve of sixteen scenarios change sign.** The four that do not are all LADWP, whose
concentration limits barely bind in either path. Under the dynamic path the compositions become
almost indistinguishable (all ≈ −3,000 ML), because the loop reaches the design CoC and the
quality penalty is small in every case.

*(Magnitudes here are for a 1 GW facility over the 730-day window and are not comparable with the
main-grid values, which are produced under the shared-pool allocation problem; only the sign and
the ordering are comparable.)*

### S21.4 What we conclude, and what we do not

We do **not** switch the main results to the dynamic path, for three reasons that we state
plainly rather than hiding behind the word "sensitivity":

1. **The dynamic path is not externally validated either.** The test above is an *internal*
   physical-consistency argument, not a comparison with measured cooling-tower chemistry. The
   dynamic path also carries its own simplifications (it does not resolve the maintenance-loop
   volume explicitly and does not model scale-inhibitor dosing).
2. **Neither path is a controlled experiment on the mechanism.** The four compositions differ in
   salinity *and* in data completeness *and* in which species bind; the grid is not a salinity
   scan.
3. **Honesty about what the main results are.** The composition effect reported in the main text
   **is a property of the volume-only path**. Under a structurally different — and in one respect
   more defensible — solver, it largely disappears.

We therefore state the dependence explicitly in the main text rather than presenting the
composition result as solver-independent. Three readings remain open and we do not choose among
them: (H1) the volume-only path is wrong and the composition result should be withdrawn;
(H2) each path captures part of the physics — volume-only the direction that poorer make-up water
forces a lower circulation ratio, R10a the loop's salt accumulation; (H3) real cooling towers sit
between the two idealisations. Distinguishing them requires **measured** per-species circulating
water chemistry from operating towers, which this study does not have.

**Scripts.** `A38_模拟审稿/ne5b_path_physics.py` (inconsistency proof),
`ne5c_convergence.py` (steady-state convergence), `ne5d_direction.py` (16-scenario comparison).
"""

# ---- 写入 SI ----
t = SI.read_text(encoding="utf-8")
if "## S21. Solver-path sensitivity" in t:
    print("SI 已含 S21, 跳过")
else:
    t = t.rstrip() + "\n" + SI_SECTION
    SI.write_text(t, encoding="utf-8")
    print("SI 已新增 S21")

# ---- 主稿: 找到 Limitations 中路径相关条目并强化 ----
m = MS.read_text(encoding="utf-8")
OLD = "Our primary result"
import re

# 定位第 1 条 Limitations（路径依赖）
pat = re.compile(r"1\. \*\*The quality penalty is path-dependent.*?(?=\n2\. )", re.S)
m0 = pat.search(m)
if not m0:
    print("主稿未找到 Limitations#1, 跳过主稿修改")
else:
    new_lim = (
        "1. **The quality penalty is path-dependent, and the dependence is not cosmetic.** "
        "The engine offers two quality solvers. Our main results use the *volume-only* path, "
        "in which the quantity compared against the circulating-water limits is the make-up "
        "concentration itself; that path reports circulating-water CoC between 1.8 and 5.0 "
        "while, by its own construction, the loop concentration equals the make-up "
        "concentration (CoC = 1) — an internal inconsistency we document in SI S21.2. The "
        "opt-in dynamic path integrates a loop solute stock and converges to a steady state "
        "consistent with a stirred loop. On sixteen matched scenarios the two paths give "
        "**opposite signs in twelve** (SI S21.3). We keep the volume-only path as the primary "
        "estimand because changing it would require recomputing the entire grid, because "
        "neither path is validated against measured tower chemistry, and because the choice "
        "would not resolve the mechanism — but we state the consequence plainly: **the "
        "composition effect reported in the main text is a property of the volume-only path**, "
        "and under the dynamic path the compositions become nearly indistinguishable. Three "
        "readings remain open (SI S21.4) and we do not choose among them.\n\n"
    )
    m = m[:m0.start()] + new_lim + m[m0.end():]
    MS.write_text(m, encoding="utf-8")
    print("主稿 Limitations#1 已强化")
