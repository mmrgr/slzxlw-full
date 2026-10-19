# -*- coding: utf-8 -*-
"""修正 SI 的 S5.10 与 S5.11。

S5.10 现文本把成因判为「buffering, not a defect」，S5.11 整节建立在「上下界」上。
两者都须重写。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
SI = HERE / "05_wr_supplementary_en.md"

# ---------- S5.10：替换"成因是缓冲"那一段 ----------
S510_OLD = """The cause is buffering, not a defect. Day-by-day diagnostics show the 24 ML campus pond filling from
its 12 ML initial state on day one and remaining full, while blowdown TDS falls from 1998 to roughly
194 mg L⁻¹, close to the make-up concentration. Salt accumulates in the pond rather than in the
loop. This is the physical consequence of the storage specification (300 ML at the reuse facility,
about 7–9 days of production), not an implementation error.

Three consequences. First, the paper's r\\* results hold under the condition that cooling storage is
unsaturated or negligible — a boundary condition not previously stated. Second, the −100 MW and
+6.48% figures are legacy-path values and should be read as the effect in the limit of no dynamic
salt buffering. Third, the closed form for $r^{*}$ is itself unaffected, since it describes where the
quality ceiling begins to bind, which is path-independent; what depends on the path is the magnitude
of the response beyond that ceiling.

The legacy path is retained as the main scenario for two reasons. It shares the CoC expression used
in the analytic derivation of §5.7.2, which is what allows the closed form to agree with the model
to 1e-15; under dynamic tracking the closed form retains only qualitative value. And it yields an
upper bound, because assuming the full salt load acts on the loop immediately can only overstate,
never understate, the penalty. The mechanism's direction is therefore robust while its magnitude is
an upper bound."""

S510_NEW = """The cause is **not** buffering, and an earlier draft of this section said that it was. Day-by-day
diagnostics do show the 24 ML campus pond filling from its 12 ML initial state on day one and
remaining full, with blowdown TDS falling from 1998 to roughly 194 mg L⁻¹. That much is accurate.
What the plateau actually reflects, however, is that the make-up itself carries almost no salt.
Neither endpoint project declares a TDS or chloride load for municipal wastewater: the sanitary
load is `{BOD: 0.06, TSS: 0.07} kg capita⁻¹ d⁻¹` with no salt species, so `pollutant_storage` is
effectively empty for TDS, and `_reuse_output_quality` (`full_engine.py:195-229`) then overrides the
declared `water_sources.reclaimed.quality.TDS = 650` with that ledger's mass-to-volume ratio. The
dynamic path therefore ran with a reclaimed TDS of **8.27 mg L⁻¹**, 1.3% of the declared 650, and a
loop fed almost salt-free make-up cannot accumulate salt regardless of pond size. The 194 mg L⁻¹
blowdown is consistent with that, not evidence of storage buffering.

A 2 × 2 design separates the two explanations at the water-scarce endpoint, 1100 MW, 730 days:

| Path | Municipal TDS load | $C_r$ median mg L⁻¹ | Make-up $r$=0.5 ML | Make-up $r$=0.9 ML | Change |
|---|---|---:|---:|---:|---:|
| legacy | absent | 650 (declared; path bypasses the ledger) | 30,770.8 | 33,655.1 | **+9.373%** |
| legacy | declared | 650 (same) | 30,770.8 | 33,655.1 | +9.373% |
| dynamic | absent | **8.27** | 30,770.8 | 30,774.3 | **+0.011%** |
| dynamic | declared | **650.30** | 30,876.4 | 33,149.8 | **+7.363%** |

The lock-up appears only in the cell without a salt load and disappears once the load is
back-calibrated so that the reclaimed concentration returns to its declared 650 mg L⁻¹. Salt-free
make-up, not storage buffering, is therefore the cause.

Three consequences. First, the closed form for $r^{*}$ is unaffected in either case: it describes
where the quality ceiling begins to bind, which is path-independent. Second, the −100 MW and +6.48%
figures are legacy-path values; with the salt balance correctly closed the same mechanism produces
about half that effect (see S5.11). Third, the mechanism's **direction** is robust across paths —
raising $r$ always increases withdrawal and lowers CAWCC — while its **magnitude** is not.

The legacy path is retained as the main scenario for two reasons. It shares the CoC expression used
in the analytic derivation of §5.7.2, which is what allows the closed form to agree with the model
to 1e-15; under dynamic tracking the closed form retains only qualitative value. And it needs no
back-calibration of the wastewater salt load, which the endpoint projects do not declare. The price
of that choice is the upper-end magnitude, which is stated explicitly in the main text."""

# ---------- S5.11：整节替换 ----------
S511_OLD_START = "### S5.11 Both paths, and the bracket they define"
S511_OLD_END = ("**Evidence:** `_dynamic_path_cawcc.json`, `_dynamic_path_verify.txt`,\n"
                "`_test_dynamic_path_main.py`, `_verify_dynamic_result.py`.")

S511_NEW = """### S5.11 Both paths with aligned water quality, and what the halving means

S5.10 identifies salt-free make-up rather than storage as the reason the dynamic path looked
invariant. This section reports the same comparison once the water-quality inputs are aligned, which
is the only version of the comparison that can speak to the mechanism.

With the wastewater salt load back-calibrated so that the reclaimed TDS returns to 650 mg L⁻¹, at
the water-scarce endpoint and the same 50 MW grid and purely physical constraint set as the main
analysis:

| $r$ | legacy CAWCC MW | dynamic CAWCC MW |
|---:|---:|---:|
| 0.0 | 1200 | 1200 |
| 0.7 | 1150 | 1150 |
| 0.9 | 1100 | 1150 |

Total withdrawal over the same sweep:

| $r$ | legacy ML | legacy ratio | dynamic ML | dynamic ratio |
|---:|---:|---:|---:|---:|
| 0.0 | 30,770.8 | 0.936303 | 30,770.8 | 0.936303 |
| 0.5 | 30,770.8 | 0.936303 | 30,876.4 | 0.939518 |
| 0.9 | 33,655.1 | 0.948293 | 33,149.8 | 0.946157 |

The effect is halved, not eliminated: 100 MW under the legacy path against 50 MW under dynamic
tracking, and +9.373% against +7.363% in withdrawal. We therefore withdraw the earlier claim that
the 100 MW effect vanishes under dynamic tracking, and with it the bracket framing in which the
legacy path was an upper bound and dynamic tracking a lower bound near zero. That framing was built
on the miscoded water quality of S5.10 and does not survive the correction.

What remains is narrower but sound. The direction of the backlash is identical on both paths, so
raising the target ratio always increases withdrawal and lowers CAWCC; only the magnitude is
path-dependent, and the −100 MW and +6.48% reported in the main text are legacy-path values to be
read as an upper-end estimate under this modelling convention rather than as a robust point
estimate. The criterion is untouched: $r^{*}$ is an algebraic threshold fixed by four water-quality
parameters, so the derivation of S5.7.2, the four-regime taxonomy of S5.7.3b and the elasticities of
S5.7.3c all stand on either path.

**Evidence:** `_dynamic_path_cawcc.json`, `_dynamic_path_verify.txt`,
`_test_dynamic_path_main.py`, `_verify_dynamic_result.py`, `_twobytwo_attribution.txt`,
`_dynamic_aligned_cawcc.json`, `_dynamic_aligned_cawcc.txt`, `_reuse_tds_rootcause.txt`,
`_reuse_tds_aligned.txt`."""

t = SI.read_text(encoding="utf-8")
ok = 0

if S510_OLD in t:
    t = t.replace(S510_OLD, S510_NEW, 1)
    print("OK S5.10")
    ok += 1
else:
    print("❌ S5.10 锚点未匹配")

i0 = t.find(S511_OLD_START)
i1 = t.find(S511_OLD_END)
if i0 > 0 and i1 > i0:
    i1 += len(S511_OLD_END)
    t = t[:i0] + S511_NEW + t[i1:]
    print("OK S5.11")
    ok += 1
else:
    print(f"❌ S5.11 锚点未匹配 i0={i0} i1={i1}")

if ok:
    SI.write_text(t, encoding="utf-8")
print(f"完成 {ok}/2")
