# Supplementary Information

**Manuscript:** A closed-form water-quality compatibility threshold governs where AI data-centre expansion binds an urban water system
**Journal:** *Water Research*

This file carries the material that the main text compresses: full estimand definitions and counterfactuals (S1), the metabolic-response results and time-scale results that the main text demotes (S2–S3), the complete three-lever analysis (S4), the full limitation register (S5), methodological detail on grids, sensitivity and verification (S6), the derivation detail behind the city screen (S7), and the data-reliability register (S8).

---

## S1 Estimands, counterfactuals and the no-calibration premise

### S1.1 Three counterfactuals

The sign of the city water ledger depends on where the AI facility's water comes from. Define three states: **B0**, the baseline city without AI; **B1**, a city with AI using reclaimed water at substitution ratio $\varphi>0$; **B2**, a city with the same AI load but using potable water only ($\varphi=0$). These support three different questions: B0→B1 gives the overall impact of AI connection including the added-load effect; B2→B1 gives the net effect of switching that same load to reclaimed water; and a city source-water increment proxy links B0 and B1 withdrawals but is **not** the B2→B1 difference. The three are not interchangeable, and every city withdrawal figure in the main text is tagged with the counterfactual it belongs to.

### S1.2 Six estimands

The same model under different constraint sets and time aggregations yields six distinct boundary values:

| Estimand | Constraint set | Time aggregation | Meaning |
|---|---|---|---|
| `daily` | physical + policy | daily (daily maximum) | joint feasible boundary, daily |
| `annual` | physical + policy | annual (annual mean) | joint feasible boundary, annual |
| `physical_daily` | physical only | daily | physical-only daily boundary |
| `physical_annual` | physical only | annual | physical-only annual boundary |
| `physical_hourly` | physical only | hourly proxy | peak-hour boundary (synthetic intraday curve) |
| `reclaimed_target` | policy only | daily | policy-compliance threshold |

"Physical" means the constraint set with the reclaimed-substitution policy constraint removed. This is not "stricter" or "looser": the joint annual estimand answers what is feasible when policy and physics must both hold, whereas the physical annual estimand answers where the physical system would bind if the policy target were not a constraint.

### S1.3 No-measurement premise

The positioning premise is that real-city calibration data (the E1 gate in S5) is unavailable. The two endpoints are synthetic parameter-domain corners built on one model skeleton with different climate drivers and facility parameters; drivers are synthetic 730-day series rather than observed hydrology; the ten constraint thresholds take engineering convention values and are calibrated against no city. Every capacity number is therefore internally consistent under its parameter set, not an estimate of reality.

---

## S2 Metabolic response and structural transition (demoted from the main text)

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

---

## S3 Time-scale effects (demoted from the main text)

### S3.1 Three boundaries

| Endpoint | Physical daily | Physical annual | Physical hourly proxy |
|---|---:|---:|---:|
| D-HA | 1150 MW | 1650 MW | 1100 MW |
| D-CO | 1450 MW | 1700 MW | 1350 MW |

Annual boundaries sit above daily ones (by 500 MW and 250 MW) and the hourly proxy sits below (by 50 MW and 100 MW). The directions are intuitive, since annual averaging smooths peaks and hourly aggregation amplifies them, but the magnitudes are not extrapolable.

### S3.2 Reservoir sustainability boundary

A joint gate over 10 years × 20 synthetic sequences (requiring end storage of at least 100% of initial and resident reliability of at least 99%) gives:

| Endpoint | Joint-gate median | Physical daily CAWCC | Ratio | Sequences with ratio ≥3 |
|---|---:|---:|---:|---:|
| D-HA | 200 MW | 1150 MW | 5.75 | 20/20 |
| D-CO | 900 MW | 1450 MW | 1.61 | 0/20 |

The statement must be split in two. At the water-scarce endpoint the reservoir sustainability boundary and the facility throughput boundary differ by a factor of about six (200 versus 1150 MW, median ratio 5.75, all 20 sequences ≥3), so treating "how much the facilities can process" as "how much the city can supply" is a common but wrong conversion. At the cool endpoint the two are of the same order (900 versus 1450 MW, ratio 1.61, none of 20 sequences ≥3), and the original hypothesis of an order-of-magnitude gap is **falsified at this endpoint**. That negative result is retained as a formal boundary condition rather than hidden as an outlier.

Four qualifications travel with S3.2. First, `hydrology_validation = NONE`: the products state that different seeds of one synthetic generator are not observed hydrology, and that adding sequences raises sampling precision without raising evidential grade, because the generator itself is validated against no external observation. Second, the boundary represents sampling stability across sequences and does not represent real hydrological uncertainty. Third, the cool endpoint's 20 sequences all give exactly 900 MW, so its reservoir conclusion carries almost no uncertainty information and must not be read as a robustness check. Fourth, censored sequences are zero at both endpoints, so the joint-gate values are true values rather than grid upper bounds.

### S3.3 Why the hour-scale result is demoted

The hourly proxy multiplies daily KPIs by a normalised 24-hour load curve built with assumed training fraction 0.65, inference fraction 0.35, peak factor 1.35 and peak hours 10 to 21, yielding an intraday peak factor of 1.0577. That is not measured hourly load: the real intraday profile of an AI data centre depends on training and inference mix, batch scheduling, cooling inertia and demand-response contracts, all unobserved. The hourly numbers therefore state only what the boundary would be if the peak factor were 1.0577. We do not report them in the abstract, do not use them to argue a general proposition that annual averaging overestimates carrying capacity, and report only their existence and direction.

---

## S4 The three levers of reclaimed water (full version)

### S4.1 Structure of the chapter

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
region where it does not.

### S4.2 Two mechanisms that must not be conflated

Policy-constraint failure has two causes, reported separately:

| Mechanism | Meaning | Evidence | Belongs to |
|---|---|---|---|
| (a) reclaimed pool capacity-limited | Hard supply ceiling, reclaimed use saturates | D-HA 1600 MW: after $r\ge0.7$ reclaimed use moves 25,157→25,567, only +1.6% | The "capacity-only expansion is ineffective" mechanism |
| (b) water-quality penalty dilutes the denominator | Falling CoC raises make-up demand, so the same pool corresponds to a larger denominator | Total withdrawal +5.4% over the same range (46,447→48,965) | The $r^{*}$ mechanism of the main text |

Both operate, but (b) dominates at the margin. (a) is an ordinary supply ceiling; (b) is the new mechanism. Conflating them would either overstate or misplace the conclusion.

### S4.3 Facility-level view

Across the 1027 converged unique scenarios of the A17 main grid (excluding 16 `no_convergence` and 9 `non_unique`), external make-up demand falls ($M_1<M_0$) in 263 scenarios, or 25.6%; the median $M_1-M_0$ is 0.0, with median $M_0$ of 31,264.8 ML and median $M_1$ of 33,559.9 ML. In most scenarios, switching the facility to reclaimed water raises its external make-up demand slightly, because blending depresses the cycles of concentration and the resulting make-up penalty offsets or exceeds the substituted volume. The 263 scenarios with falling make-up are exactly the subset with $q>0$, where $q=(M_0-M_1)/M_1$.

This is the empirical projection of the mechanism derived in the main text onto a parameter sample, not incidental scatter across scenarios. One qualification is mandatory: the sign of $q$ is set by water chemistry, and the `AI-UWM assumption` water sample, which carries two of the intended five species, is excluded from all sign claims, because missing species are zero-filled on the analysis path and make the sample look cleaner than it is, biasing toward "reuse is beneficial".

### S4.4 City-level view

Splitting scenarios by the state of the reclaimed pool gives two branches. The A branch (pool exhausted) holds 308 scenarios: displaced incumbent users must be replaced with the same volume of potable water, and city withdrawal does not fall. The C branch (pool has surplus) holds 391 scenarios: city withdrawal genuinely falls. The A branch's identity degenerates to $dS_{pot}=M_1-M_0$ with an absolute residual of $2.63\times10^{-6}$ ML.

### S4.5 City withdrawal falling is not carrying capacity rising

In the C branch city withdrawal does fall. But carrying capacity is defined by the first-failing constraint, not by withdrawal volume. Reducing the abstraction ratio only postpones the failure point of the abstraction constraint and leaves every other constraint in place. At the water-scarce endpoint, treatment utilisation and the abstraction ratio first fail at the same 1200 MW, and they do not separate when the ratio falls. At the cool endpoint the abstraction ratio first fails at 1800 MW, far later than the grid at 1500 MW, so abstraction is not a bottleneck there at all.

### S4.6 The decisive comparison

| Lever | Operation | D-HA result | D-CO result |
|---|---|---|---|
| Treatment capacity only | `treatment_capacity_ml_day` 40→160 (HA) / 36→160 (CO), production unchanged | CAWCC fixed at 1150, marginal gain identically 0 at every point | CAWCC fixed at 1450, marginal gain identically 0 at every point |
| Production | `central_reuse_fraction` 0.16→0.60 (HA) / 0.15→0.60 (CO) | CAWCC 1150→1400 (+250), bottleneck moves from source abstraction to grid connection | CAWCC fixed at 1450 throughout |

The code documents this distinction directly: the engine's own comments record that the two reclaimed-water levers must be scanned separately, that expanding treatment capacity while holding production fixed is ineffective investment with an identically zero marginal gain, and that the genuinely effective lever is the WWTW diversion ratio that determines production, with capacity following at 1.25 times production as a daily peak margin. The dataset exporter labels the two products "ineffective lever" and "true lever" respectively.

Detail for the water-scarce endpoint's bottleneck migration:

| `central_reuse_fraction` | Estimated production (ML/d) | Paired capacity (ML/d) | CAWCC (MW) | Limiting constraint |
|---:|---:|---:|---:|---|
| 0.16 (baseline) | 32.2 | 40.3 | **1150** | Source abstraction ratio |
| 0.25 | 50.4 | 62.9 | **1400** | Daily-average grid connection |
| 0.35 | 70.5 | 88.1 | 1400 | as above |
| 0.45 | 90.6 | 113.3 | 1400 | as above |
| 0.60 | 120.8 | 151.1 | 1400 | as above |

Raising the diversion fraction from 0.16 to 0.25 raises CAWCC from 1150 to 1400 MW (+250 MW) and migrates the bottleneck from source abstraction to grid connection, which is the second positive instance of the main proposition. These values sit on the 50 MW grid shared with the main results; the corresponding 100 MW-grid run gave 1100 to 1400 MW, and the difference between +300 and +250 MW is a baseline difference, not a disagreement about the mechanism.

Three construction assumptions must be declared. `treatment_capacity_ml_day` is set to the fraction times baseline sewage times 1.25, so production and capacity are set jointly rather than as independent levers. Estimated production is derived from the diversion fraction rather than accumulated daily by the engine. The curve is nevertheless a genuine model-run product, obtained by running the capacity scan and the carrying-capacity search at each fraction, not an inference. Both the 100 MW and the 50 MW versions are archived, the latter under the `_50mw` suffix, so the two grids can be compared directly.

### S4.7 Full limitation register for this chapter

- The volume-only quality path is internally inconsistent: it applies the loop limit to make-up concentration, and if loop concentration equalled make-up concentration the CoC should be identically 1, yet that path reports 1.8 to 5.0. Under the $r^{*}$ framework this is readable as a deliberate first-order approximation equivalent to assuming $\mathrm{CoC}=L/C_{mix}$ with no design ceiling; the full path takes the minimum. The two agree for $r>r^{*}$ and the approximation overestimates the CoC decline for $r\le r^{*}$, which is why its deviation is largest at low substitution ratios.
- Path dependence is real: under `coc_design = 5.0`, 12 of 16 scenarios have opposite signs across solver paths. We therefore keep the direction of the conclusions with the direction only, and treat the mechanism's magnitude as convention-dependent. The frequently quoted "800×" path discrepancy is **not** used as a quantity.
- The species-incompleteness bias described in S4.3 applies here: the two-species assumption sample is excluded from all sign claims.
- The chapter's statistics rest on 1027 converged unique solutions.

---

## S5 Full limitation register

### S5.1 Data and positioning

1. **No measurement calibration.** All capacity numbers are model values on synthetic endpoints, not any city's carrying capacity (the E1 gate is closed).
2. **Synthetic drivers.** The 730-day series is synthetic, not observed hydrology; the reservoir ensemble uses different seeds of one generator, and `hydrology_validation = NONE`.
3. **Single parameter set.** Each endpoint has one parameter set; no joint parameter-distribution sampling was done except the probability batches of S5.3.

### S5.1b Range-dependence of the non-informative constraints

The main text reports that three constraints at the water-scarce endpoint and six at the cool one
never fail within the 0–2000 MW scan, and states explicitly that this is not evidence of safety.
The obvious follow-up question, which had not been tested, is whether those constraints fail once
the scan is extended. Doubling the ceiling to 4000 MW gives:

| Constraint | D-HA first failure | D-CO first failure |
|---|---:|---:|
| `max_wwtw_utilization` | **never** (max 0.8992) | **never** (max 0.8755) |
| `system_reliability_fraction` | 2050 | 2550 |
| `unmet_cooling_water_ml` | 2300 | 3000 |
| `domestic_unmet_ml` | 1850 | 2350 |
| `peak_capacity_ratio` | 1750 | 2300 |
| `reclaimed_water_substitution_ratio` | 1350 | 2100 |

At 0 MW the reclaimed substitution ratio is zero because no data centre exists, so that point is
excluded as a domain artefact rather than a failure.

The result cuts both ways. It strengthens one claim and limits five others. The strengthened claim
is that wastewater treatment capacity is not a bottleneck: with the scan ceiling doubled to 4000 MW
its utilisation reaches only 0.8992 and 0.8755 against a 0.95 threshold, so the conclusion does not
depend on where the scan stopped. The five limited claims are the other non-informative statements,
which hold only inside 0–2000 MW and would fail between 1350 and 3000 MW if the scan were extended.
The main text keeps the 0–2000 MW wording, since the paper's conclusions are drawn in that range,
but reports the extended boundaries so that a reader can tell which negative results are robust and
which are range-dependent.

**Evidence:** `{ha,co}/capacity_scan_4000mw.csv`, `_noninformative_extended.json`,
`_noninformative_recheck.json`, `_test_noninformative_extended.py`.

---

### S5.2 Method gaps, registered honestly

4. **No repeated runs for bottleneck attribution.** Neither the constraint-binding diagnostic nor the capacity scan contains a random source, so the dominant-constraint determination is a deterministic single scan with no sampling error estimate. This was raised explicitly in external review and is accepted here.
5. **Threshold-perturbation sensitivity: done, and the conclusion is "absolute values sensitive, structure robust".** All constraints were perturbed by ±2%, classified by threshold dimension (zero-tolerance constraints unperturbed; `system_reliability_fraction` perturbed downward only because its 0.99 threshold is close to the physical bound; the rest two-sided). At the water-scarce endpoint the daily capacity range is 250 MW (1000 to 1250 MW), roughly 75 MW per 1% of threshold, and the dominant constraint flips at the ×1.02 relaxation level from source abstraction to the substitution ratio. At the cool endpoint the range is 50 MW and the dominant constraint remains the grid at all five perturbation levels. The meaning is that absolute capacities are unreliable, since a 1% threshold error moves them 75 MW, so we claim no absolute capacity; what is robust is the migration structure, with first failures in 1000 to 1350 MW and 1450 to 1500 MW, two non-overlapping intervals.
6. **Intervention interactions: tested, and the result is near-perfect additivity.** All 36
pairwise combinations of the nine interventions were re-run on the 50 MW grid, at both endpoints
and under both constraint sets. At each endpoint, 35 of 36 pairs are exactly additive, the
interaction being zero to numerical precision. The single exception at the water-scarce endpoint
pairs `leakage_minus_30pct` with `combined_upgrade`, and its interaction equals minus the leakage
gain exactly (−250 MW physical, −150 MW joint). This is redundancy rather than antagonism: the
specification of `combined_upgrade` already contains the leakage-reduction path, so applying both
counts that measure twice. The cool endpoint is fully additive, 36 of 36.

Three consequences are worth recording. First, effective interventions are independent of the
ineffective ones, so planning gains can be summed without worrying that combination erodes the
marginal benefit. Second, no pair shows the qualitatively important pattern of two individually
ineffective measures becoming effective together, consistent with the paper's claim that an
intervention off the binding constraint does nothing however many others accompany it. Third, the
gain itself is caliber-dependent: leakage reduction at the water-scarce endpoint is +150 MW under
the joint constraint set and +250 MW under the purely physical one, because under the joint set the
policy constraint fails before 1400 MW and truncates what leakage reduction can realise. This is
the same structure as the paper's main result — an intervention's value depends on which constraint
set defines carrying capacity — so the two calibers must never be mixed.

**Not done:** interactions of order three and above, and a full-factorial design. Given that every
first-order interaction is zero, higher-order terms have little prior support, and there are no
remaining effective interventions to combine.

**Evidence:** `{ha,co}/interaction_pairs_50mw.csv`, `interaction_pairs_50mw_summary.json`;
`_verify_interactions.py` (20/20).
7. **Grid resolution.** A 50 MW step means ±50 MW quantisation on all boundary values.
8. **Intervention gains were not originally on the 50 MW grid.** The main text's gains come from the re-run on that grid; the earlier 100 MW-grid values, including a +200 MW figure, are superseded, the +200 having been a baseline grid artefact since the 100 MW grid never evaluated 1150 MW.
9. **The "physical daily caliber gain" column of `intervention_baseline_alignment.csv` is unusable.** It is produced by cross-grid subtraction and gives a spurious −50 MW for zero-gain interventions. It is not cited.

### S5.3 Convergence status of probability results

10. **Water-scarce endpoint: `CONVERGED_PARTIAL`.** P05 and P95 are identical at sample sizes 256, 1024 and 1699, but P50 moves by one grid step between 1050 and 1100 MW and must not be locked to a single number. The largest batch is partially complete, so the statement is limited to "stable over completed sample sizes".
11. **Cool endpoint: `INSUFFICIENT_BATCHES`.** Only two sample sizes exist, so it must not be written as having passed a convergence test; the correct statement is that quantiles agree at two independent sample sizes and support stability in direction, conditional on existing batches.
12. **The cool endpoint's 0/1024 is not zero risk.** The correct wording is that zero exceedances were observed, with an exact binomial (Clopper–Pearson) one-sided 95% upper bound of 0.29%, i.e. a detection limit near 0.3%.

### S5.4 Data-reliability register

13. **The "limiting constraint" column of `intervention_cost_benefit.csv` is not citable.** The file predates the scale-free determination (2026-09-23), and 8 of 20 rows conflict with `intervention_marginal.csv` (2026-09-28). Only its gain, investment and Pareto columns are used.
14. **The "physical daily caliber gain" column of `intervention_baseline_alignment.csv` is not citable** (see item 9).
15. **`city_gradient_cawcc.csv` label errors were fixed on 2026-10-18.** In the original, 19 of 25 rows mislabelled the limiting constraint as the substitution ratio. The root cause was not a stale product but that `run_r2_city_gradient.py` passed the complete scan including 0 MW to the carrying-capacity search, whereas the main pipeline filters at 50 MW or above; 0 MW is the no-AI baseline where the substitution ratio is 0, so the policy constraint seized the first-failure position although it does not apply. After the fix the endpoints match one-for-one and the annual caliber is usable again.
16. **`constraint_binding_diagnosis.csv` was extended to 50–2000 MW on 2026-10-18.** The original covered only 900–1500 MW (52 rows) and missed the failure points at 1550, 1750 and 1850 MW; it now has 160 rows covering the full range.
17. **The numeric columns of the R5 argument map are out of date.** Its R1/R2 values, including an exceedance count of 122/1024 that does not exist in current products, must not be cited; all numbers are taken from `capacity_threshold_corrected.json` and `probabilistic_corrected_summary.json`.

### S5.4c Grid convergence at the cool endpoint

The main text's grid-convergence box reports the water-scarce endpoint's three-grid behaviour. The
cool endpoint carries the paper's central negative result — that its capacity barely responds
because its bottleneck is electrical — and a negative result deserves the same scrutiny as a
positive one. Checked on the same three grids:

| $r$ | 50 MW | 25 MW | 10 MW |
|---:|---:|---:|---:|
| 0.0 – 0.8 | 1450 | 1450 | 1460 |
| 0.9 | 1400 | 1425 | 1440 |
| **decline, $r$=0 → 0.9** | **50** | **25** | **20** |

The negative result holds: the decline never exceeds 50 MW, or 3.45% of the baseline, on any grid.
Two details are worth recording. First, the decline shrinks monotonically as the grid is refined
(50 → 25 → 20 MW), so the coarse grid slightly overstates the cool endpoint's response while
preserving its direction. Second, the 10 MW baseline is 1460 rather than 1450, a 10 MW difference
that the main text's single 1450 figure does not show; the absolute value carries the same
0–25 MW systematic underestimation documented for the water-scarce endpoint.

**Evidence:** `rstar_grid_convergence_table.csv`, `_check_co_grid.py`.

---

### S5.4b Joint-versus-physical gap is larger at the cool endpoint

The main text states the joint-versus-physical gap at the water-scarce endpoint (300 MW at
$r=0.9$). The cool endpoint's gap is larger still, and the reason is instructive.

| $r$ | D-HA joint | D-HA physical | gap | D-CO joint | D-CO physical | gap |
|---:|---:|---:|---:|---:|---:|---:|
| 0.6 | 1150 | 1150 | 0 | 1200 | 1450 | −250 |
| 0.7 | 1100 | 1150 | −50 | 1000 | 1450 | −450 |
| 0.8 | 900 | 1100 | −200 | 850 | 1450 | −600 |
| 0.9 | 800 | 1100 | −300 | 700 | 1400 | −700 |

The two endpoints have similar policy-constraint failure capacities, so the difference is not in
the policy constraint but in **where the physical bottleneck sits**. At the water-scarce endpoint
the physical bottleneck is source abstraction at 1200 MW, close to the policy constraint's failure
point (850 MW at $r=0.9$); the two are comparable, so the policy constraint can hardly displace the
physical one. At the cool endpoint the physical bottleneck is grid connection at 1500 MW, far later
than the policy constraint's failure point, so the policy constraint takes over readily and the
joint estimate collapses.

This matters for how the paper's numbers should be read. Reported jointly, the cool endpoint would
appear to lose 750 MW of carrying capacity as $r$ rises to 0.9; under the purely physical set it
loses 50 MW. The 15-fold discrepancy is entirely an artefact of leaving the policy constraint in the
criterion set, which is the self-reference the main text warns against. It also shows that the
caliber separation is not a technicality that happens to matter at one endpoint — it matters most
where the physical bottleneck is electrical, which is precisely where a naive joint estimate looks
most alarming.

**Evidence:** `rstar_physical_cawcc_by_r.csv` (20 rows), `_audit_co_joint.py`.

---

### S5.5 Limitations specific to the threshold chapter

18. **$r^{*}=0.5532$ is not a universal constant.** It is the value at the endpoint water-quality parameters, and any city's value follows from its own four parameters.
19. **The −100 MW physical effect is subject to quantisation.** With a 50 MW step the true decline lies between −50 and −150 MW; no precise value is claimed.
20. **The joint-versus-physical gap must not be mixed into the headline.** At $r=0.9$ the water-scarce endpoint shows 800 MW joint against 1100 MW physical, a 300 MW gap that is mainly "policy target not met" rather than physical capability loss. We claim only the 100 MW physical effect and **actively reject the larger 400 MW figure**.
21. **The cool endpoint's negative result must be reported.** The penalty occurs there too, with CoC falling from 5.0 to 3.648, but capacity barely moves because the bottleneck is electrical. This is precisely the counter-evidence that establishes the mechanism's second condition and is not hidden.
22. **A penalty percentage cannot be converted into a megawatt decline.** The response is threshold crossing plus quantisation; no "penalty % to MW" formula is established.
23. **The criterion should be applied to delivered rather than target substitution ratios.** When the reclaimed pool limits delivery the two differ; the 2e−3 to 6e−3 discrepancies in cross-validation arise here, because CoC is a daily non-linear function of a min operation and its time mean is not the value computed from the time-mean ratio, since min and averaging do not commute.
24. **Multi-species tightening is complete for this configuration.** With only TDS and chloride configured and both carrying full source concentrations, $r^{*}=\min(0.5532, 0.6842)=0.5532$ is the true minimum over configured species. The general form is $r^{*}=\min_s[(L_s/\mathrm{CoC}_d-C_{p,s})/(C_{r,s}-C_{p,s})]$; extending the species set later could lower it and would advance the onset of the penalty.
25. **Classification boundaries are not empirically validated, and the anchor gap is wider than one parameter.** The regime boundaries depend on the position of $C^{*}=L/\mathrm{CoC}_d$ relative to the two source salinities, so they inherit the uncertainty of all four threshold parameters. Auditing these four against `parameter_envelope_R7.csv` (54 rows) gives:

| Parameter | Value | In envelope table | Anchor status |
|---|---:|---|---|
| $L$ (loop TDS limit) | 2200 mg L⁻¹ | **no** | never audited |
| $\mathrm{CoC}_d$ | 5.0 | yes | **no anchor** |
| $C_p$ (potable TDS) | 180 mg L⁻¹ | **no** | never audited |
| $C_r$ (reclaimed TDS) | 650 mg L⁻¹ | **no** | never audited |

Only one of the four appears in the envelope table, and that one is itself unanchored; the three water-quality parameters have never been entered into it. An earlier internal description treated $\mathrm{CoC}_d$ alone as the weakest link, which understated the gap: the weakness is not one parameter but all four.

Sensitivity to a single ±10% perturbation, expressed as the offset from the nominal $r^{*}=0.5532$ and the two-endpoint span: $L$ 0.0936 / 0.1872; $\mathrm{CoC}_d$ 0.1040 / 0.1891; $C_r$ 0.0888 / 0.1560; $C_p$ 0.0178 / 0.0343. Any one of the first three can push $r^{*}$ into 0.46–0.66, an interval that spans both "the case city has not crossed" and "it has". This is the most consequential quantitative limitation in the paper.

**Evidence:** `_rstar_param_anchoring.json`, `_rstar_sens_exact.py`. The four values above were read directly from `examples/cawcc_r2/ha/project.json`.
26. **Regime boundaries are thin.** When $C^{*}$ approaches either source salinity, a small parameter error changes the assignment. We claim a classification method, not any city's classification.
27. **Regime I's verification construction is engineeringly unrealistic.** A design value of 15 is far above real cooling towers, which rarely exceed 8; it serves logical verification of the taxonomy's self-consistency, not description. Regime III's design value of 2.5 is within normal engineering range.
28. **Regime validation used two endpoints, one capacity and five ratios each.** Universality still rests on the derivation rather than on simulation: the empirical work is a sampling check, not a full-grid confirmation, and the capacity dimension was not varied. The dual-endpoint replication (S6.5) removes the earlier single-baseline limitation but does not make the check exhaustive.
29. **The campus ratio is not the city-wide utilisation rate.** The bridge is $r_{\max}=u\,(W/D)$, and under the modelled parameters $W/D$ runs from 3.59 at 1500 MW to 10.59 at 500 MW with a median of 5.33, so a city-wide utilisation of 20–25% can correspond to a campus ratio above 100%. We claim no specific policy target has triggered the penalty.
30. **$W/D$ is itself a model product, not a measurement.** Both $W$ and $D$ come from synthetic endpoints, and a real city's ratio depends on city size, industrial structure and campus capacity and may differ substantially. It is an order-of-magnitude reference only.
31. **Grid quantisation has been quantified (2026-10-18).** The zero-effect region's zero decline is identical on all three grids and is not subject to quantisation, which directly supports the "exactly zero" argument. Absolute CAWCC approaches the upper bound monotonically as the grid is refined (1150, 1175, 1190 at $r=0.6$), so the 50 MW grid systematically underestimates by 0 to 25 MW. The effect is robust at the endpoint (−100/−100/−90, range 10 MW) but unstable in the middle (−50/−25/−10 at $r=0.6$, range 40 MW; −100/−75/−70 at $r=0.8$, range 30 MW). Only the endpoint decline is cited.
32. **Grid inconsistency is caused by subtracting two rounding errors, not by instability.** If the true boundary is 1187 MW the three grids report 1150, 1175 and 1180, so declines relative to each grid's baseline are −50/−25/−20. The fluctuation in decline is a quantisation artefact while the monotone approach of absolute values is the real model behaviour. This distinction governs citability.

### S5.6 Limitations specific to the real-city application

33. **The real-city section is an application, not a verification.** The prediction $r=0.44$ to $0.50<r^{*}=0.55$ follows from substituting official data, but we have not observed whether make-up demand rises when $r$ crosses $r^{*}$; that requires facility-level, month-by-month withdrawal and make-up time series that we do not hold. Reading that section as confirming the mechanism in Santa Clara exceeds the evidence.
34. **The reporting period behind the 6% and 26% shares is undisclosed.** The city's third-party evidence register states explicitly that supporting period and volumes need disclosure. We use 2025 UWMP data but cannot assume the shares correspond to 2025.
35. **$r=0.499$ is a city-wide average, not any specific facility.** Santa Clara has 56 data centres and we hold no per-facility water data; technologies, cooling types and reclaimed connection status differ widely.
36. **$k=P/R$ is sensitive to caliber.** The supply-capacity caliber gives $k=5.43$ and $r=0.444$; the actual-use caliber gives $k=4.35$ and $r=0.499$. The two differ by 5.5 percentage points in $r$, the same magnitude as the 5.4-point margin to the threshold, so while the direction of "not crossed" is determined, its magnitude is not.
37. **The California $k$ distribution has selection bias.** The 169 systems are only those reporting both potable and recycled; most of the state's 7,000-plus recycled-reporting systems are wholesalers and cannot yield a $k$. The distribution cannot be extrapolated to the state.
38. **Parameter uncertainty in $r^{*}$ could change the verdict, and it has four independent sources.** A 10% error in a single threshold parameter moves $r^{*}$ by 0.018 ($C_p$), 0.089 ($C_r$), 0.094 ($L$) or 0.104 ($\mathrm{CoC}_d$); the two-endpoint span reaches 0.19, so $r^{*}$ can sit anywhere in roughly 0.46–0.66. A true value near 0.51 would put Santa Clara at or beyond the threshold, and one near 0.46 would put it clearly below. Because none of the four parameters carries a measured anchor (item 25), "not crossed" is a nominal-parameter conclusion rather than a robust one — and the uncertainty is not dominated by a single parameter that could be tightened first.
39. **The two documented shares cannot be added.** They have different denominators, so 6% and 26% do not sum to 32% of combined use.
40. **The 56-facility count was cross-checked independently.** The city's 2026 report gives 56 operating or under-construction facilities, and an independent OpenStreetMap count over the city bounding box (2 nodes plus 54 ways) gives the same 56.

### S5.7 Interaction with the literature

41. **Literature coordinates were initially missing and have been added.** The reused-water rebound literature includes Schwabe et al. (supply-side self-consumption) and Tran et al. (quality-side deterioration), with which this chapter shares an intellectual lineage. They were absent from the original library and appeared only as independent rediscovery; they are now cited.
42. **Our evidence grade is lower than the global symbiosis assessment.** That study uses a global inventory with life-cycle assessment and optimisation; ours uses two synthetic endpoints. Nothing here corrects it.
43. **We omit bidirectional heat recovery.** That study returns data-centre waste heat to sludge drying and anaerobic digestion; our model treats data-centre heat as waste. This is a dimension we lack.
44. **Directional agreement with field measurement is not agreement with measurement.** The 4.2 MW tower measurement is a single facility in the oil and gas sector; our model is city-scale.

---

### S5.8 Analytic reach: the threshold is exact, the effect size is not

Section 5.7 establishes that the threshold location is exactly analytic. It is natural to ask
whether the effect size beyond the threshold is analytic too. Take the water-scarce endpoint's
binding constraint, an abstraction ratio of at most 0.95. If city source abstraction can be written
as a constant plus a term proportional to $MW\,f(r)$ with $f(r)=\mathrm{CoC}(r)/(\mathrm{CoC}(r)-1)$,
then setting it equal to $0.95\,CAP$ gives $\mathrm{CAWCC}(r)=A/f(r)$ for a constant $A$ calibrated
in the region $r\le r^{*}$ where CoC is pinned at its design value.

Tested across resolutions, the form appears to hold on coarse grids and fails on fine ones:

| Grid | Maximum deviation | Verdict |
|---|---:|---|
| 50 MW | 0.70 grid steps | appears to hold |
| 25 MW | 0.45 steps | appears to hold |
| 10 MW | **2.11 steps (21 MW)** | fails |

A 1 MW scan then fixes the true value at $r=0.9$: the last compliant capacity is 1111 MW (ratio
0.949889) and the first failing is 1112 MW (ratio 0.950034), giving an interpolated CAWCC of
1111.76 MW against the analytic 1088.9 MW. The discrepancy is **22.86 MW**, and at 1 MW resolution
the quantisation tolerance is ±1 MW, so this cannot be explained as rounding. The bias also grows
monotonically with $r$ — roughly +5 MW at $r=0.6$, +9 MW at $r=0.8$ and +23 MW at $r=0.9$ — which
means the closed form is missing a term that rises with $r$. We did not decompose that term; the
candidates include the delivered-versus-target reclaimed fraction, storage buffering in the reuse
pond, and coupling through the multi-species minimum.

This establishes a boundary that the paper should state explicitly rather than leave implicit.
Analytic reach covers the threshold, not the effect size: $r^{*}$ is exact to machine precision,
whereas the −100 MW figure is a model output that no closed form reproduces to better than about 2%
at the high end. The paper's self-description as a criterion rather than a prediction is therefore
not merely a framing choice; it is the honest description of what the analysis can and cannot
deliver.

**Evidence:** `_analytic_cawcc_test.json`, `_analytic_cawcc_multigrid.json`, `_fine_r09.json`,
`_test_analytic_cawcc.py`, `_test_analytic_multigrid.py`, `_fine_r09.py`.

---

### S5.9 CoC is computed from the target mix, not the delivered one

Section S5.8 attributes the analytic residual to a term rising with $r$ without decomposing it. The
decomposition follows.

At the water-scarce endpoint, 1100 MW and the full 730-day driver, raising the target substitution
ratio yields:

| $r$ target | $r_{\mathrm{eff}}$ delivered | days short | CoC model | CoC at target $r$ | CoC at $r_{\mathrm{eff}}$ |
|---:|---:|---:|---:|---:|---:|
| 0.70 | 0.700000 | **0 / 730** | 4.3222 | 4.3222 | 4.3222 |
| 0.75 | 0.740217 | 262 / 730 | 4.1315 | 4.1315 | 4.1674 |
| 0.80 | 0.755645 | 620 / 730 | 3.9568 | 3.9568 | 4.1110 |
| 0.85 | 0.751428 | 724 / 730 | 3.7964 | 3.7964 | 4.1263 |
| 0.90 | 0.743997 | 724 / 730 | 3.6484 | 3.6484 | 4.1535 |

Two facts stand out. First, delivery falls short from $r=0.75$ onward and settles on a plateau near
0.74–0.76, set by the 40 ML d⁻¹ reclaimed capacity and the 300 ML pond; by $r=0.9$ only 6 of 730
days meet the target. Second, the model's CoC always equals the value computed from the **target**
mix, agreeing with it to 1e-15, while differing from the delivered-mix value by up to 0.505
(3.6484 against 4.1535).

When delivery falls short the real blend is fresher than the target, so the true cycles would be
higher and the penalty smaller. The model therefore understates CoC and overstates the
water-quality penalty above $r\approx0.70$. Three consequences follow. The declines reported at
$r=0.8$ and $0.9$ in the main results table are upper bounds under this modelling convention rather
than point estimates. The analytic residual of S5.8 is explained: the closed form uses the target
ratio, consistently with the model, and the discrepancy originates in the model's simplification,
not in the algebra. And the threshold is untouched, because $r^{*}=0.5532$ lies in the region where
delivery is complete.

This also clarifies how capacity limitation enters the model despite `max_reuse_utilization` being
excluded (item (b) of the constraint discussion, S4.2). That indicator was excluded because a
300 ML pond makes nameplate daily throughput normal buffering rather than failure. The capacity
limit has not vanished on that account: it propagates through the delivered-fraction shortfall while
CoC remains target-based, and the direction of that propagation is conservative, overstating
water-side pressure.

**Evidence:** `_reff_shortfall.json`, `_reff_shortfall.txt`, `_coc_reff_tension.json`,
`_quantify_reff_shortfall.py`, `_verify_coc_reff.py`.

---

### S5.10 The legacy volume-only path, and what changes under dynamic salt tracking

Tracing the delivered-fraction residual of S5.9 one level further exposes a setting that the paper
must declare.

Neither `examples/cawcc_r2/{ha,co}/project.json` sets `quality_state_enabled`, whose default is
false (`full_engine.py:160`). All 730 days therefore report
`quality_state_status = DISABLED_LEGACY_VOLUME_ONLY` and `quality_solver_status = not_applicable`.
On that path CoC is taken directly from $\min(\mathrm{CoC}_d, L/C_{\mathrm{mix}}(r))$ with no
day-by-day solute balance, which is why model CoC matches the closed form to 1e-15.

Setting `quality_state_enabled = true` changes the result materially. At the water-scarce endpoint
and 1100 MW:

| $r$ | CoC, legacy | CoC, dynamic | Annual make-up ML, legacy | Annual make-up ML, dynamic |
|---:|---:|---:|---:|---:|
| 0.0 | 5.0000 | 5.0000 | 30,770.8 | 30,770.8 |
| 0.5 | 5.0000 | 4.9999 | 30,770.8 | 30,771.0 |
| 0.7 | 4.3222 | **4.3709** | 31,923.9 | **31,825.6** |
| 0.8 | 3.9568 | **4.1490** | 32,764.8 | **32,284.5** |
| 0.9 | 3.6484 | **4.1364** | 33,655.1 | **32,312.9** |

Both paths show a threshold-type backlash: relative to $r=0$ the dynamic make-up rises **+5.012%** at
$r=0.9$ against **+9.373%** for the legacy path. The dynamic effect is about half, not zero.

Under dynamic tracking CoC stays essentially at its design value and annual make-up varies by less
than 0.02% across the whole range, so the threshold-typed penalty largely disappears.

Two implementation defects, not a physical mechanism, produced the earlier reading. Neither
endpoint project declares a TDS or chloride load for municipal wastewater: the sanitary load is
`{BOD: 0.06, TSS: 0.07} kg capita⁻¹ d⁻¹` with no salt species. That fixture gap exposed two code paths.
First, `_reuse_output_quality` trusted the wastewater ledger's mass-to-volume ratio even when the
resulting concentration fell *below* the potable concentration, which is physically impossible for
treated effluent; it now rejects such a value as incomplete and retains the declared 650 mg L⁻¹.
Second, and decisively, `data_center.py` treated the quality override as a wholesale *replacement*
rather than a merge. With TDS absent from the override, TDS dropped out of the mixed make-up
concentration entirely, leaving only the potable contribution ($0.3\times180=54$ mg L⁻¹);
$L/C_{\mathrm{mix}}=2200/54=40.7$ then exceeded the design cycles of 5.0 and `min()` clamped CoC to its
design value. That clamp is what made annual make-up look invariant and the backlash appear to vanish.
The override is now merged: species declared by the source are retained unless the ledger supplies a
physical value for them.

A 2 × 2 design separates the two explanations at the water-scarce endpoint, 1100 MW, 730 days:

| Path | Municipal TDS load | $C_r$ median mg L⁻¹ | Make-up $r$=0.5 ML | Make-up $r$=0.9 ML | Change |
|---|---|---:|---:|---:|---:|
| legacy | absent | 650 (declared; path bypasses the ledger) | 30,770.8 | 33,655.1 | **+9.373%** |
| legacy | declared | 650 (same) | 30,770.8 | 33,655.1 | +9.373% |
| dynamic | absent | 650 (declared; ledger rejected as incomplete) | 30,771.0 | 32,312.9 | **+5.011%** |
| dynamic | declared | **650.30** | 30,876.4 | 33,149.8 | **+7.363%** |

With the defects fixed the dynamic path reproduces the backlash instead of cancelling it: the effect
is **+5.011%** absent the salt load and **+7.363%** once it is back-calibrated, against **+9.373%** on
the legacy path. The dynamic effect is roughly half the legacy one, not zero. Salt-free make-up was
never a pathway property; it was the signature of the override bug.

Three consequences. First, the closed form for $r^{*}$ is unaffected in either case: it describes
where the quality ceiling begins to bind, which is path-independent. Second, the −100 MW and +6.48%
figures are legacy-path values; with the salt balance correctly closed the same mechanism produces
about half that effect (see S5.11). Third, the mechanism's **direction** is robust across paths —
raising $r$ always increases withdrawal and lowers CAWCC — while its **magnitude** is not.

The legacy path is retained as the main scenario for two reasons. It shares the CoC expression used
in the analytic derivation of §5.7.2, which is what allows the closed form to agree with the model
to 1e-15; under dynamic tracking the closed form retains only qualitative value. And it needs no
back-calibration of the wastewater salt load, which the endpoint projects do not declare. The price
of that choice is the upper-end magnitude, which is stated explicitly in the main text.

**Evidence:** `_quality_state_sensitivity.json`, `_quality_state_sensitivity.txt`,
`_quality_storage_diag.txt`, `_test_quality_state.py`, `_diag_quality_storage.py`.

---

### S5.11 Both paths with aligned water quality, and what the halving means

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

Total withdrawal over the same sweep is reported in the 2 × 2 table above; the legacy path rises from
30,770.8 ML at $r=0$ to 33,655.1 ML at $r=0.9$, the dynamic path from 30,770.8 to 32,312.9 ML
(absent-TDS-load caliber). We do not tabulate a withdrawal-to-demand ratio here because the two
calibers use different denominators and quoting a single ratio would invite the same caliber mixing
that this section is written to avoid.

The capacity effect is halved, not eliminated: 100 MW under the legacy path against 50 MW under
dynamic tracking. In withdrawal the same comparison is **+9.373% against +5.012%** (absent-TDS-load
caliber) or **+7.363%** once the salt load is back-calibrated — either way a factor of roughly two,
never zero. We therefore withdraw the earlier claim that
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
`_reuse_tds_aligned.txt`.

---

## S6 Methodological detail compressed from the main text

### S6.1 Why the intervention grid mattered

Intervention scans use a 100 MW grid (`capacities_mw = [0, 100, …, 2000]`) while the main results use a 50 MW grid. The intervention baseline is therefore 1100 MW (water-scarce) and 1400 MW (cool) while the main physical daily CAWCC is 1150 and 1450 MW. Three consequences follow. First, all gains are reported on the 50 MW grid so that they share the main results' grid. Second, the main CAWCC values are never arithmetically combined with post-intervention values, because they are different estimands on different grids; doing so produces artefacts, as when the alignment file reports −50 MW for every zero-gain intervention, which is the direct difference between a 100 MW-grid post-intervention value and the 50 MW-grid 1150 MW baseline. No intervention that changed nothing can cause a 50 MW loss. Third, the +150 and +50 entries in that file are cross-grid interpolations and were unverified before the re-run; the re-run in this paper supersedes them.

### S6.2 Cross-validation against an independent product

The earlier `reclaimed_fraction_sweep_R8.csv` product (generated 2026-09-28, independent of this round) records CoC values identical to this round's digit for digit: at target ratios 0.5, 0.6 and 0.7 the mean CoC is 5.000000, 4.761905 and 4.322200, and make-up per unit of heat rejected is 0.001800, 0.001821 and 0.001867. That product's independent verdict was that CoC is monotonically non-increasing, make-up per unit heat is monotonically non-decreasing, and the mechanism holds. The mechanism was therefore independently verified on 2026-09-28, but at that time only as a compatibility check; this paper promotes it to a criterion.

One deviation must be recorded: at $r=0.8$ and 0.9 the R8 CoC differs from this round's by 2e−3 to 6e−3. The cause is not model inconsistency but that R8's delivered fraction is a period mean (0.7938 and 0.8232) whereas CoC is a daily non-linear function subject to a min operation, and min and averaging do not commute. This is item 23 of S5.5.

### S6.3 Water-balance closure and variant consistency

Closure passes for all 45 scenarios on both identities with a maximum relative error of $3.45\times10^{-13}\%$ (column `相对闭合误差_科学计数`; an earlier draft quoted $2.5\times10^{-13}\%$, which could not be checked against the CSV because its numeric column applied `round(..., 9)` and flattened machine-precision residuals to zero; the scientific-notation column was added on 2026-10-19 and the value corrected to the measured maximum). After propagating the D1/D2 joint repair to 23 derived variants, the maximum deviation across the ten daily constraints is $0.00\times10^{0}$ and the carrying thresholds and bottleneck constraints match one-for-one. This conclusion is limited to three field classes (off-site electricity water intensity, WWTW process emissions and WWTW specific electricity use) and must not be extrapolated to changes in flow or capacity parameters.

### S6.4 Consistency of the city-gradient scan

A 25-city linear-mixing gradient along the two parameter axes was rerun and repaired on 2026-10-18, adding seven annual KPI columns and correcting the limiting-constraint labels. The daily CAWCC and limiting constraints at theta=(0,0) and theta=(1,1) match the main results one-for-one: 1150 MW with source abstraction and 1450 MW with grid connection. The scan tests continuity along the parameter axes and supports no multi-city conclusion.

---

### S6.5 Dual-baseline replication of the regime taxonomy

The regime taxonomy was initially validated on the water-scarce baseline only, a limitation
recorded as item 28. Because both endpoints carry identical water-quality parameters
($L=2200$ mg L$^{-1}$ and chloride $500$ mg L$^{-1}$; $C_p=180$, $C_r=650$ mg L$^{-1}$;
$\mathrm{CoC}_d=5.0$), their analytic $r^{*}$ is the same, but their climate drivers and
facility parameters differ. Replicating on both therefore tests whether the taxonomy's
qualitative behaviour is a property of the water chemistry alone or of the full model
configuration.

| Regime | $\mathrm{CoC}_d$ | $r^{*}$ | Baseline | CoC at $r=0$ | Change in withdrawal, $r=0\to0.8$ | CoC equal to design |
|---|---:|---:|---|---:|---:|---|
| II | 5.0 | 0.5532 | D-HA | 5.0000 | +6.48% | 3/5 points |
| II | 5.0 | 0.5532 | D-CO | 5.0000 | +6.48% | 3/5 points |
| I | 15.0 | −0.0709 | D-HA | 12.2222 | +20.74% | 0/5 points |
| I | 15.0 | −0.0709 | D-CO | 12.2222 | +20.74% | 0/5 points |
| III | 2.5 | 1.4894 | D-HA | 2.5000 | 0.00e+00% | 5/5 points |
| III | 2.5 | 1.4894 | D-CO | 2.5000 | 0.00e+00% | 5/5 points |

All six combinations confirm their predictions. The absolute withdrawals differ between
baselines — at $r=0$ under Regime II, 22,390.8 ML at the water-scarce endpoint versus
22,126.7 ML at the cool endpoint — but the **relative** changes agree to every digit
reported here (Regime II: +6.476503% versus +6.476462%; Regime I: +20.741175% versus
+20.741024%).

This near-identity is expected rather than surprising, and it is worth stating why, because
a near-identical result invites the suspicion that the baseline switch did not take effect.
The relative change in make-up demand depends only on the ratio of
$\mathrm{CoC}/(\mathrm{CoC}-1)$ between the two substitution ratios, and the CoC trajectory
is set by the water-quality parameters alone through
$\mathrm{CoC}=\min(\mathrm{CoC}_d, L/C_{\mathrm{mix}}(r))$. Since both baselines share
those parameters, they share the CoC trajectory, so any quantity proportional to it must
scale almost identically. What the dual replication establishes is therefore that the
taxonomy's behaviour is not an artefact of one city's climate or facility sizing — which is
precisely the part of the configuration that differs, and which is what changes the absolute
withdrawals by 230 to 345 ML between baselines. The agreement is close but not exact: the
residual at the fifth and sixth significant figure reflects small differences in the daily
delivered-ratio path, on which the min operation acts before averaging, and it is two orders
of magnitude below the evaporation drift discussed next.

One quantitative check ties the taxonomy back to the derivation. The closed form predicts a
$+7.056\%$ rise in make-up demand from $r=0$ to $0.8$ at $\mathrm{CoC}_d=5$, computed as the
ratio of $\mathrm{CoC}/(\mathrm{CoC}-1)$ at the two points; the model returns $+6.477\%$ for
total withdrawal. The 0.58-point shortfall is the same evaporation drift recorded in the main
text: evaporation is not perfectly constant, falling $0.76\%$ over the range, so the closed
form slightly over-predicts. The agreement is therefore close but not exact, and the residual
is attributed rather than left unexplained.

**Evidence:** `rstar_regime_validation_dualbase.csv` (with a `base` column) and
`rstar_regime_validation_dualbase.json` (`per_base` object). The single-baseline
`rstar_regime_validation.csv` and `.json` are retained unchanged in the archive so that
downstream checks written against those products continue to resolve; both pairs were
regenerated on 2026-10-18, the dual-baseline pair with `--bases ha,co`.

---

## S7 Derivation detail for the two-number city screen

### S7.1 From shares to the campus ratio

Let city potable use be $P$ and city reclaimed use be $R$. If data centres take share $\alpha$ of potable and share $\beta$ of reclaimed, campus make-up is $D=\alpha P+\beta R$ and

$$r=\frac{\beta R}{\alpha P+\beta R}=\frac{1}{1+(\alpha/\beta)k},\qquad k\equiv\frac{P}{R}.$$

Setting $r=r^{*}$ gives

$$k^{*}=\frac{1/r^{*}-1}{\alpha/\beta}.$$

With $\alpha=0.06$ and $\beta=0.26$ and $r^{*}=0.5532$, $k^{*}=(1/0.5532-1)/(6/26)=3.50$.

### S7.2 The Santa Clara source data

The 6% and 26% shares carry a provenance chain that must be stated exactly, and it is weaker
than a first-hand reading.

| Link | Content | Verifiable here |
|---|---|---|
| Origin | City of Santa Clara, File 26-1037, 2026-10-06, "Water Usage" section | **no** — original not held |
| Transcription | *Santa Clara data centers — Independent community report*, October 2026, **p.53** table, citing the above as `[1]` | yes — present in the text layer |
| Use here | share ratio $\rho=6/26$ for the $k^{*}$ screen | — |

The verifiable line (p.53, text layer, not read from any graphic) reads:

> "October staff water figures [1] Data centers: about 6% of potable use and 26% of recycled use.
> Separate water-system denominators; not 32% of combined use. Supporting period and volumes need
> disclosure."

Three qualifications follow. First, the shares are a **transcribed government statement rather
than a first-hand measurement**: we hold the community report, not the City's original, so we
cannot independently confirm its "Water Usage" section or any graphic in it. An earlier version of
this manuscript described the figures as existing only inside two pie charts on page 27 and as
recoverable only by rendering that page at 200 dpi; the evidence available to us does not support
that description, and it has been corrected. Second, the two denominators differ and are not
additive, as the source itself warns. Third, the reporting period is undisclosed, again as the
source states.

$\rho=6/26$ should therefore be read as a **government-stated but independently unverified
scenario anchor**, not as reproducible measurement. That evidential grade carries into the
sensitivity analysis of S7.7 and into the limitation register.

### S7.3 The two UWMP calibers

On supply capacity the plan states, on p.65, that the four sources together yield "about 38,700 AFY", itemised as SFPUC 5041, Valley Water 4560, groundwater wells 23,048 and recycled 6017 acre-feet per year. The 38,666 used here and the potable subtotal of 32,649 are our summations of those components, not figures printed in the plan; the components themselves appear on p.65 and in Table 6-11 on p.66. They give $k=5.43$ and $r=0.444$, 10.9 points below $r^{*}$. On 2025 actual use (p.35) potable is 16,857 AF and recycled 3871 AF, giving $k=4.35$ and $r=0.499$, 5.4 percentage points below, a margin of 9.8%.

### S7.4 The eAR cross-check

The California Electronic Annual Report for 2022 independently gives City of Santa Clara (PWSID CA4310012) potable production of 16,913 AF and recycled production of 3450 AF, hence $k=4.90$. The two independent official sources give 16,857 versus 16,913 AF on potable (0.3% apart) and 3871 versus 3450 AF on recycled (11% apart).

### S7.5 The structural observation

City-wide use is 20,728 of 38,666 AFY, or 53.6% of supply capacity, while recycled-system utilisation is 3871 of 6017, or 64.3%. The city is lightly loaded as a whole while its recycled subsystem is heavily loaded, which is why the actual-use caliber sits closer to the threshold: when total water is abundant, what constrains the campus blend is the relative tightness of the recycled subsystem.

### S7.6 The testable prediction

From $r=0.499$ and $r^{*}=0.5532$, crossing the threshold requires one of three changes:

| Change | Threshold condition |
|---|---|
| Recycled use | rise from 3871 to 4816 AF (+24%) |
| Potable use | fall from 16,857 to 13,548 AF (−20%) |
| $k$ | fall from 4.35 to 3.50 (−19.6%) |

If Santa Clara's data centres raise recycled use by about 24% over the present base, the campus ratio would cross $r^{*}$. This is a prediction open to future observation.

### S7.7 Sensitivity of the critical ratio $k^{*}$

The critical city ratio is $k^{*}=(1/r^{*}-1)/\rho$ with $\rho\equiv\alpha/\beta$. Because both
inputs are uncertain for any city other than the one documented case, we tabulated the
sensitivity rather than reporting a single number.

Against $\rho$, holding $r^{*}=0.5532$:

| $\rho$ | $k^{*}$ | Californian systems with $k<k^{*}$ | Share | Interpretation |
|---:|---:|---:|---:|---|
| 0.10 | 8.08 | 57 | 33.7% | data centres almost exclusively on reclaimed water |
| 0.20 | 4.04 | 29 | 17.2% | |
| **0.2308** | **3.50** | **23** | **13.6%** | Santa Clara 6%/26% |
| 0.30 | 2.69 | 14 | 8.3% | |
| 0.50 | 1.62 | 4 | 2.4% | |
| **1.00** | **0.81** | **3** | **1.8%** | conservative: equal shares in both supplies |
| 2.00 | 0.40 | 1 | 0.6% | data centres mostly on potable water |

Against $r^{*}$, holding $\rho=0.2308$:

| $r^{*}$ | $k^{*}$ | Systems with $k<k^{*}$ | Share |
|---:|---:|---:|---:|
| 0.50 | 4.33 | 34 | 20.1% |
| 0.52 | 4.00 | 29 | 17.2% |
| **0.5532** | **3.50** | **23** | **13.6%** |
| 0.58 | 3.14 | 20 | 11.8% |
| 0.61 | 2.77 | 15 | 8.9% |

Two conclusions follow. First, the headline figures of 3.50 and 13.6% are conditional on the
Santa Clara share ratio; they are not properties of the criterion itself, and reporting them
without $\rho$ would overstate the sharpness of the screen. Second, even under the least
favourable assumption we examined — equal shares in both supplies, $\rho=1$ — three systems
remain below the boundary, so the qualitative claim survives while the population it identifies
shrinks by an order of magnitude. The honest reading is that the screen is a way of asking a
well-posed question of a city's two published numbers, not a fixed threshold applicable
everywhere.

Counts in both tables are computed against the **exact** root of $k^{*}=(1/r^{*}-1)/\rho$, not
against the rounded value displayed in the first column. The distinction matters in exactly one
cell: at $\rho=0.10$ the exact boundary is 8.0766 while the display reads 8.08, and one system
sits at $k=8.0787$ between them, so rounding the boundary first would report 58 systems instead
of 57. We report the exact-boundary count throughout.

**Evidence:** `_ca_kstar_sensitivity.json`, computed from `_ca_k_clean.json` (169 systems).

---

### S7.8 The California $k$ distribution

Using the full 2022 eAR (about 1.32 million rows), we extracted every public water system reporting both potable and recycled production and computed $k$. After removing obvious recycled-water wholesalers and micro-systems ($P\ge100$ AF, $k\ge0.2$, recycled share no more than 90%):

| Sample | n | Median $k$ | Share with $k<k^{*}=3.50$ |
|---|---:|---:|---:|
| All valid systems | 169 | 13.54 | 13.6% (23) |
| Large (population ≥ 50,000) | 93 | 16.95 | 8.6% (8) |
| Medium (5,000–50,000) | 66 | 10.29 | 19.7% |

Roughly one recycled-water system in seven has a $k$ below 3.50, so **if** such a city hosted data centres with Santa Clara's 6%/26% shares its campus ratio would cross $r^{*}$. The distribution indicates the criterion's reach; it does not show that any of these cities has crossed, because the shares are city-specific and we hold documented shares for one city only.

### S7.9 Cleaning rules and their effect

The raw extraction yields 188 systems. Applying the three rules above leaves 169, so 19 systems (10.1%) are removed as wholesalers or micro-systems. The median moves from the raw set to 13.54 on the cleaned set, and the below-threshold share is computed on the cleaned set only.

---

### S7.10 An attempted external anchor for $C_p$, and why it matters

Item 25 established that none of the four threshold parameters carries a measured anchor. We
attempted to close part of that gap for $C_p$, the potable-water TDS, using the only multi-county
public dataset we could reach that reports measured total dissolved solids: the California GAMA
Division of Drinking Water compilation (2020–present), obtained from the state open-data portal.

**What the dataset is and is not.** It reports groundwater monitoring results, not finished
drinking water at a treatment plant outlet, and the release we obtained covers 19 counties and
does **not** include Santa Clara. It therefore cannot replace the project value of 180 mg L⁻¹, and
we do not use it that way.

**What it can establish.** It locates the assumed value within the state's measured distribution.
Across 10,090 TDS determinations the percentiles are 120 (p5), 239 (p25), 420 (p50), 650 (p75)
and 2,100 mg L⁻¹ (p95); the assumed 180 mg L⁻¹ sits at the **14th percentile**, i.e. the project
assumes markedly fresher potable water than the Californian groundwater median. County medians
range from 210 mg L⁻¹ (Fresno) to 1,200 mg L⁻¹ (Imperial), and the neighbouring Alameda county
median is 545.5 mg L⁻¹.

**Why this is the most consequential of the four gaps.** $C_p$ enters the threshold twice, in the
numerator with a negative sign and in the denominator with a negative sign, and the numerator is
$L/\mathrm{CoC}_d-C_p$. When $C_p$ approaches $L/\mathrm{CoC}_d=440$ mg L⁻¹ the numerator
collapses and $r^{*}\to0$; beyond it $r^{*}<0$ and the system enters Regime I, where any
substitution carries a cost. Evaluating the closed form at the observed values:

| $C_p$ source | $C_p$ (mg L⁻¹) | $r^{*}$ | Verdict for the case city ($r=0.444$ / $0.499$) |
|---|---:|---:|---|
| Project assumption (unanchored) | 180 | 0.5532 | not crossed / not crossed |
| Fresno county median | 210 | 0.5227 | not crossed / not crossed |
| GAMA statewide median | 420 | 0.0870 | **crossed / crossed** |
| Alameda county median | 545.5 | −1.0096 | **crossed / crossed** (Regime I) |
| Los Angeles county median | 550 | −1.1000 | **crossed / crossed** (Regime I) |

A shift of $C_p$ from 180 to the statewide median is enough to move the case city from clearly
below the threshold to clearly above it, and a further shift drives $r^{*}$ negative, which is a
categorical change rather than a numerical one. This is why we describe the case-city verdict as
nominal rather than robust: the verdict is decided by a parameter that has never been measured,
and the plausible range of that parameter straddles the decision boundary.

The same sensitivity applies to $C_r$: holding $C_p$ at 180, $C_r$ of 500, 650, 800 and
1,000 mg L⁻¹ give $r^{*}$ of 0.8125, 0.5532, 0.4194 and 0.3171 respectively. Reclaimed-water TDS
in practice varies by an order of magnitude with source and treatment, so this range is not
exotic.

**How precisely must $C_p$ be measured before the verdict is settled?** Inverting the closed
form for $C_p$ answers this directly. Setting $r^{*}$ equal to the case city's observed ratio gives
$C_p=(L/\mathrm{CoC}_d-r^{*}C_r)/(1-r^{*})$: the verdict is "not crossed" if and only if the true
$C_p$ lies below 230.8 mg L⁻¹ under the actual-use caliber ($r=0.499$), or below 272.3 mg L⁻¹ under
the supply-capacity caliber ($r=0.444$). The project assumes 180 mg L⁻¹, which leaves a margin of
50.8 mg L⁻¹ against the tighter of the two. A measurement precise to **±25 mg L⁻¹** would therefore
settle the question; typical laboratory TDS determinations are far more precise than that. The
obstacle is availability, not precision.

The requirement becomes much sharper if $C_r$ is also treated as unknown, because the two enter
the same expression. Holding $r=0.499$, the critical $C_p$ is 380.2 mg L⁻¹ at $C_r=500$, 230.8 at
$C_r=650$, 81.4 at $C_r=800$, and negative beyond about $C_r=1{,}000$ — at which point no positive
$C_p$ can keep the city below the threshold. Measuring the potable and reclaimed salinities
together therefore matters more than measuring either alone.

**What would close the gap.** Facility-level finished-water TDS or electrical conductivity for
one city's potable supply and its recycled supply, from consumer confidence reports or plant
operating records. Such values are routinely published in the United States and would replace
both unanchored parameters at once; the loop salinity limit $L$ is the harder one, because it
depends on heat-exchanger metallurgy and operating practice rather than on water source alone.

**Evidence:** `_gama_tds_statewide.json`, `_c_p_anchor_impact.json`, `_gama_tds.py`,
`_cp_anchor_impact.py`.

---

### S7.11 First-hand documentary support for the mechanism's premise

The main text's mechanism assumes that campus cooling make-up is a blend of sources and that the
binding property is salinity. That premise had rested on model construction alone; the city's
statutory water plan supplies documentary support that we had not previously drawn on.

From the 2025 Urban Water Management Plan, page 62:

> "In areas of the City served by groundwater, industrial customers will find the quality of
> treated recycled water to be more consistent than groundwater for cooling towers. Those cooling
> towers that receive groundwater could also receive a blend of multiple water sources based on
> system demand (e.g., groundwater blended with imported surface water) with slight variations in
> water quality, whereas those that receive recycled water would receive one consistent water
> source."

> "The enhanced blend of water will help industrial users reduce operating costs, and it can be
> used on a wider variety of landscapes, due to a much lower level of salinity."

And from page 86:

> "In contrast to other areas adjacent to San Francisco Bay where saltwater intrusion has been an
> issue, total dissolved solids (TDS) is not a concern for the City."

These support three things respectively: that cooling towers in this city do receive blended
make-up water whose quality varies with the mix, which is precisely the object of
$C_{\mathrm{mix}}(r)=rC_r+(1-r)C_p$; that the utility frames the relevant water-quality attribute
as salinity, which is the variable our criterion uses; and that the city's potable supply is not
TDS-stressed, which makes the assumed $C_p=180$ mg L⁻¹ plausible or even conservative rather than
arbitrary. The last point is consistent with the statewide groundwater median of 420 mg L⁻¹: that
figure is a state-wide median, and the plan states this city is not among the TDS-affected areas.

**A limit that must be stated in the same breath.** The plan contains no numerical TDS,
conductivity, chloride or hardness values at all — across 282 pages these terms appear only in the
abbreviation list, in the qualitative passages quoted above, and in a regulatory appendix. The
quotations therefore support the premise and the direction of the parameter choice; they cannot
anchor $C_p$ or $C_r$. Item 44 of the limitation register, on the four unanchored threshold
parameters, is unaffected.

**Evidence:** `_verify_uwmp_quality.py` (11/11), reading `2025 Urban Water Management Plan_Final.pdf`
pp. 62 and 86 directly.

---

### S7.12 External check on the water-side implementation: cooling tiers against a project design value

The model's water-side parameters — WUE and the cooling-technology settings — previously had no
external comparison; the parameter envelope marks most of them unanchored. An independent official
figure is available. The city's community report reproduces a project-level environmental design
estimate for the Bowers project (Final EIR, October 2023, printed pp. 3-14 and 4.18-2): rooftop
air-cooled chillers with adiabatic assistance, with cooling water of at most 0.5 acre-feet per year,
equal to 616.7 m³.

Running the model's seven cooling tiers at an IT capacity of 10 MW gives:

| Tier | WUE (L kWh⁻¹) | Annual make-up (m³) |
|---|---:|---:|
| `dry` | **0.000** | 0 |
| `dry_first` | **0.398** | 56.9 |
| `hybrid` | **0.606** | 86.1 |
| `liquid_to_water` | 1.912 | 251.7 |
| `efficient_evaporative` | 2.117 | 278.7 |
| `evaporative` | **2.205** | 290.2 |
| `liquid_to_air` | 0.000 | 0 |

The design figure implies a WUE that depends on the facility's IT capacity. At 10 MW it is
0.0070 L kWh⁻¹, which lies between the `dry` tier and the `dry_first` tier. Crucially, this holds
across the whole plausible capacity range: from 1 to 72 MW the implied WUE moves from 0.0704 to
0.0010 L kWh⁻¹, never leaving that interval. The conclusion therefore does not depend on the one
quantity the document does not disclose. It also agrees with the document's own description of the
design as air-cooled with adiabatic assistance.

Two inferences follow. First, the tier gradient is monotone and of the right magnitude, and the
evaporative tier at 2.205 L kWh⁻¹ sits inside the conventional 2–4 band, so the water-side
implementation carries no order-of-magnitude error. Second, Santa Clara is not uniformly
evaporatively cooled: the Bowers design implies a WUE about 315 times below the model's evaporative
tier. Since the main text models every facility with a single evaporative setting, its water-side
results are biased upward rather than downward, which makes the paper's account of water-side
pressure conservative.

**Limit, stated with the result.** The Bowers IT capacity is not public. The community report
explicitly warns that the 72 MW designation belongs to backup generation and must not be read as
measured annual grid demand. This check therefore establishes tier and order-of-magnitude
consistency only; it cannot anchor a WUE value, and it supports no inference about the technology
mix or total water use of the city's data centres.

**Evidence:** `_tech_wue_benchmark.json`, `_verify_bowers_benchmark.py` (9/9), reading
`2025 Urban Water Management Plan` and `Item 7 Post Meeting Material.pdf` pp. 60–61.

---

### S7.13 Cooling-technology sensitivity

The main text models both endpoints with a single evaporative cooling tier. Section S7.12 shows
that Santa Clara is not uniformly evaporatively cooled: one documented project uses air-cooled
chillers with adiabatic assistance at a WUE some 315 times below the evaporative tier. The claim
that a uniform evaporative assumption is conservative had not been tested. This section tests it.

Switching the water-scarce endpoint among four tiers while holding all other parameters fixed:

| Tier | WUE (L kWh⁻¹) | $\mathrm{CoC}_d$ | Make-up increase, $r$ 0.5→0.8 at 1200 MW | Physical CAWCC drop, 50/25/10 MW grids |
|---|---:|---:|---:|---|
| `evaporative` | 2.125 | 5.0 | **+6.478%** | 100 / 75 / 70 |
| `hybrid` | 0.558 | 5.0 | **+6.472%** | 50 / 50 / 60 |
| `dry_first` | 0.327 | **6.0** | **+7.851%** | 50 / 75 / 90 |
| `dry` | 0.000 | 5.0 | **not applicable** (external withdrawal identically zero) | 0 / 0 / 0 |

The capacity drop is grid-limited, with ranges of 10 to 40 MW across the three resolutions, and —
more importantly — the **ordering of the tiers does not survive refinement**. At 50 MW the ordering
is `evaporative` (100) > `hybrid` (50) = `dry_first` (50); at 25 MW it is `evaporative` (75) =
`dry_first` (75) > `hybrid` (50); at 10 MW it reverses to `dry_first` (90) > `evaporative` (70) >
`hybrid` (60). Decomposing the variation explains why. For `evaporative` the baseline is stable at
1200 MW on all three grids while the $r=0.8$ endpoint rises from 1100 to 1125 to 1130, so the drop
converges downward, 100 → 75 → 70. For `dry_first` the endpoint is stable at 1050 MW while the
baseline rises from 1100 to 1125 to 1140, so the drop diverges upward, 50 → 75 → 90. The two
depend on the grid in opposite directions, so a crossing is unavoidable and neither the individual
values nor their ranking is citable.

Three claims survive. First, all three tiers that use cooling water produce drops in the 50–90 MW
range, the same order of magnitude as the −100 MW main result. Second, `dry` is zero on all three
grids because its external withdrawal is identically zero — the criterion is inapplicable there,
not robust. Third, statements of the form "the effect decreases monotonically with cooling-water
intensity" or "uniform evaporative modelling bounds the effect from above" hold only on the 50 MW
grid and are refuted by the finer ones; we therefore do not make them.

Four readings. First, the threshold-typed response does not depend on the cooling technology: all
three tiers that use any cooling water retain it, between +6.47% and +7.85%. The mechanism result
of the main text is therefore not an artefact of the evaporative assumption. Second, the effect
size does scale with water intensity, falling −100 → −50 → −50 → 0 MW. This gives quantitative
content to the conservatism claim: a city with half its facilities on hybrid cooling would show
roughly −50 MW rather than −100 MW. Third, the `dry` tier must be described separately, because its
external withdrawal is identically zero and the criterion is inapplicable rather than robust — left
unsaid, the zero capacity drop would read as the mechanism failing there. Fourth, `dry_first`
produces a larger make-up increase because its design cycles of concentration are 6.0 rather than
5.0, which lowers $r^{*}$ to 0.3972 and so crosses the threshold earlier; this is another concrete
instance of the high elasticity of $r^{*}$ with respect to $\mathrm{CoC}_d$ (−1.69).

The implication for external validity is that the mechanism conclusion is robust to cooling
technology while the effect size is conditional on it. Because the technology mix of a real city is
unknown — only one project's design value is public here — the −100 MW figure should be read as the
evaporatively-cooled upper bound.

**Evidence:** `_tech_sensitivity.json`, `_verify_tech_sensitivity.py` (11/11).

---

## S8 Data-reliability warnings for reviewers

1. `intervention_cost_benefit.csv` — "limiting constraint" column not citable (S5.4 item 13).
2. `intervention_baseline_alignment.csv` — "physical daily caliber gain" column not citable (S5.4 item 14).
3. `city_gradient_cawcc.csv` — fixed 2026-10-18; earlier versions mislabel 19 of 25 rows (S5.4 item 15).
4. `constraint_binding_diagnosis.csv` — extended 2026-10-18 from 52 to 160 rows (S5.4 item 16).
5. `reclaimed_fraction_sweep_R8.csv` — differs from this round by 2e−3 to 6e−3 in CoC at high $r$, for the commutation reason in S6.2.
6. `parameter_envelope_R7.csv` — 10 inside envelope, 10 on boundary, 32 without anchor, 2 outside; the anchor source is a convenience sample, not a systematic review.
7. `volume-only` quality path — internally inconsistent by construction, readable as a first-order approximation (S4.7).
