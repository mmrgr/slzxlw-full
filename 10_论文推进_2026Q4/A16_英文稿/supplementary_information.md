# Supplementary Information (A16, v3)

Companion to `manuscript_en_v3.md` — *Supply state, not cooling technology, governs the urban
water outcome of reclaimed-water cooling in AI data centres*.

> **Version note.** v3 supersedes v2. Between them, two material defects were found and
> fixed (see `19_缺陷报告_缓存与桥接_2026-10-15.md`); all numbers here are from corrected runs.

---

## S1. Symbol table

| Symbol | Meaning | Unit |
|---|---|---|
| $M_0,M_1$ | facility makeup in the all-potable and reclaimed counterfactuals (same scenario) | ML/period |
| $E$ | cooling-tower evaporation | ML/period |
| $\mathrm{CoC}$ | cycles of concentration | – |
| $\varphi,\varphi_{\rm eff}$ | requested / realised reclaimed fraction of makeup | – |
| $x_{\rm AI}$ | reclaimed volume allocated to the facility | ML/period |
| $r_{\rm inc}$ | reclaimed volume allocated to incumbents | ML/period |
| $P$ | nominal reclaimed pool | ML/period |
| $\Delta P$ | added reclaimed capacity | ML/period |
| $F$ | **discharge**: potable the facility stops withdrawing | ML/period |
| $C$ | **claim**: potable displaced incumbents must withdraw | ML/period |
| $dS_{\rm pot}$ | city potable-withdrawal change $=C-F$ | ML/period |
| `limit_scale` | **water-quality limit scaling factor** (not $\chi$) | – |
| `elig` | committed reclaimed demand $=P_0+\texttt{gap}$ | ML/period |
| `gap` | incumbents' *unmet reclaimed* demand (engine) | ML/period |

**Withdrawn symbols:** supply-stress $\psi$, unmet-demand gap $\Delta$, critical ratio
$\varphi^*$ (traced to two errors documented in S10).

---

## S2. The three accounts

Measured on the full daily engine (68 runs × 730 days, read-only instrumented subclass):

| account | relation |
|---|---|
| requested vs delivered | equal **only** while the supply path is unconstrained; otherwise difference = unmet demand |
| delivered vs abstracted | **never equal** — 0 of 68 runs agree |

Path efficiency $\eta_{\rm path} = 0.849$ (both domains); marginal wedge
$1/\eta_{\rm path} = 1.178$.

**Phantom abstraction** (withdrawal reported that the source cannot physically supply):
up to **6,713 ML** (D-HA) and **6,121 ML** (D-CO).

---

## S3. The identity and its branches

$$dS_{\rm pot} = C - F
= \bigl(r_{\rm inc}^{B_2}-r_{\rm inc}^{B_1}\bigr) - (M_0-M_1) - x_{\rm AI}$$

**Residual 5.8 × 10⁻¹¹ ML** across 1,152 scenarios.

- If the facility's draw is **entirely** displaced ($C=x_{\rm AI}$): collapses to $dS=M_1-M_0$.
  Holds for 2 of 4 compositions; **fails** for the other 2 (by up to 24,404 ML), which is why
  the general form is required.
- If there is **no** displacement ($C=0$): $dS=-(M_0-M_1)-x_{\rm AI}<0$.

**Sign criterion**: dividing the identity by $M_1$ gives the exact dimensionless form
$dS_{\rm pot}/M_1=\rho(\kappa-1)-q$ with $\rho=x_{\rm AI}/M_1$, $\kappa=\text{displacement}/x_{\rm AI}$,
$q=(M_0-M_1)/M_1$; residual **1.3 × 10⁻¹⁵**. This is an **algebraic rearrangement, not a
discovery**, and is reported as an accounting convention.

The substantive content is the sign structure of $q$:

| $q$ group | n | withdrawal falls | withdrawal rises | median $dS_{\rm pot}$ |
|---|---:|---:|---:|---:|
| $q>0$ | 349 | **349** | **0** | −14,325 |
| $q\approx0$ | 326 | 208 | 38 | −5,590 |
| $q<0$ | 477 | 192 | 285 | +1,907 |

**$q>0$ is sufficient for a city-level benefit (349/349, no exception).**

### S2b. Parameter-naming hazard and the nominal-vs-actual constraint tier

Two *different* quantities have been called `chi` in this project, with **overlapping numeric
ranges**:

| definition | formula | range | used by |
|---|---|---|---|
| **strictness** | `CoC_realized / CoC_design` | ~0.08–1.0 (continuous) | `T12` surface |
| **limit scale** | engine limit-scaling factor | 0.25 / 0.5 / 1.0 / 1e6 | A13c, A15, A17, A22, Fig. 1 |

The value `1.0` means "exactly at the design ceiling" in the first convention but "still
binding" in the second, while the second convention uses `1e6` for the non-binding limit.
We therefore publish an authoritative semantics table (`A26_语义统一/CHI_SEMANTICS.md`) and add
three explicit columns to every affected product — `limit_scale`, `chi_strictness`,
`quality_binding` — without renumbering anything.

**This exposed a disclosure we had been missing: the nominal tier does not determine whether
the constraint actually binds.**

| nominal `limit_scale` | share of scenarios where the constraint actually binds |
|---:|---:|
| 0.25 | 100% |
| 0.50 | 92% |
| 0.98 | **58%** |
| 1.0 | **48%** |
| 1e6 | **0%** |

So almost half of the scenarios labelled "quality-limited" at 0.98 in fact reach the design
ceiling and are *not* quality-constrained. Analysing by nominal tier alone therefore mixes two
different physical regimes. The `quality_binding` column separates them, and we report it
alongside every tier-based statistic.

---

### S3.0 Solver-reliability gate (added after the A25 audit)

A full audit found that **58 of 1,152 scenarios (5.03%)** in the main grid did not return
`converged_unique`: `no_convergence` (38) and `non_unique` (20). In these scenarios the joint
quality/allocation solver returns **zero allocations**, yet `displaced` and `dS_pot` are still
computed — so they silently contaminate any summary.

| product | all | unreliable | share |
|---|---:|---:|---:|
| `supply_state_regimes.csv` (main grid) | 1,152 | **58** | **5.03%** |
| `potable_flows.csv` (A13c) | 408 | **35** | **8.58%** |
| `ablation_matrix.csv` | 64 | 2 | 3.13% |
| `holdout_fit_ha.csv` | 204 | 16 | 7.84% |
| `holdout_holdout_co.csv` | 204 | 19 | 9.31% |
| `holdout_predictions.csv` | 816 | 48 | 5.88% |
| `grid_resolution_points.csv` | 14,196 | 541 | 3.81% |

**Effect on headline numbers (main grid)**

| quantity | all | reliable only |
|---|---:|---:|
| scenarios | 1,152 | **1,094** |
| $dS_{
m pot}<0$ | 749 | **729** |
| $dS_{
m pot}>0$ | 323 | **285** |
| zero-displacement | 446 | **441** |
| $q>0$ | 349 | **329** |
| $q>0$ but harmful | **0** | **0** |
| criterion agreement | 1.0000 | **1.0000** |
| identity residual (ML) | 1.16e−10 | **1.16e−10** |

> **An algebraic relation cannot certify its own inputs.** The residual and the criterion
> agreement are *identical* on both sets, because they are rearrangements that hold for any
> input — including zero allocations. A 100% criterion agreement is therefore **not** evidence
> that the scenarios are trustworthy; only the solver status is.

**Artefacts this gate removed.** In A13c, 11 `no_convergence` rows (all with `x_ai = 0`) had
been counted as "withdrawal rises". On the main grid, all 38 `x_ai = 0` rows were failures, and
the apparent 31/7 harmful cases for LADWP / the placeholder composition were likewise failures;
the reliable counts are **237/0** and **241/0**.

### S3.1 Closed form for the sign of $q$

Since $M(\mathrm{CoC})=E\,\mathrm{CoC}/(\mathrm{CoC}-1)$:

$$q=\frac{M_0-M_1}{M_1}=\frac{\mathrm{CoC}_1-\mathrm{CoC}_0}
{\mathrm{CoC}_1(\mathrm{CoC}_0-1)},\qquad
q>0\iff\mathrm{CoC}_1>\mathrm{CoC}_0$$

Residual **5.6 × 10⁻¹⁷** (numeric vs analytic). "Does reclaimed cooling reduce facility
makeup?" is therefore **exactly equivalent** to "does blending reclaimed water raise the
admissible CoC?"

**Sufficient external condition.** If *every* constrained species satisfies
$c^{\rm rec}_i<c^{\rm pot}_i$, then the blend concentration falls with $\varphi$, CoC rises, and
$q>0$. **Zero violations** across the compositions tested (`q_theory_samples.csv`).

**Why no single indicator suffices** (best of seven predictors: 0.768):

| mechanism | demonstration |
|---|---|
| one dirty species can take over the minimum | Figshare RW: 3 species present, 2 exceed potable → $\mathrm{CoC}_1/\mathrm{CoC}_0=0.40$ |
| the design ceiling truncates the benefit | LADWP: `limit_scale`=5.0 → $\mathrm{CoC}_0=\mathrm{CoC}_1=5.000$ ($q=0$); `limit_scale`=0.5 → $2.500\to5.000$ ($q>0$) |

### S3.2 Empirical classifier comparison (why the downgrade is warranted)

Seven candidates, full sample, no filtering:

| predictor | accuracy | TP | FP | TN | FN |
|---|---:|---:|---:|---:|---:|
| reclaimed TDS < potable TDS | **0.803** | — | — | — | — |
| reclaimed Cl < potable Cl | 0.768 | 185 | 103 | 700 | 164 |
| either indicator cleaner | 0.768 | 185 | 103 | 700 | 164 |
| both indicators cleaner | 0.768 | 185 | 103 | 700 | 164 |
| CoC constrained below design | 0.428 | 205 | 515 | 288 | 144 |
| $\kappa=0$ (no displacement) | 0.576 | 153 | 293 | 510 | 196 |
| chemistry ∧ constraint | 0.748 | 90 | 31 | 772 | 259 |

Per composition (reliable subset): IEUA **1.000**, Figshare 0.993, LADWP 0.720, AI-UWM assumption **0.456**.

### S3.3 Data-integrity gap

The quality dictionary supplies only species present in a sample, so a missing species enters
as **zero** and its limit never binds. IEUA and LADWP are complete (5/5); Figshare RW lacks
alkalinity and silica; the `AI-UWM model assumption` entry carries **only TDS and chloride**.

Imputing missing species from observed-source medians over 192 scenarios: makeup changes by up
to **2,869 ML** for the incomplete entry, but **zero sign flips in $q$ (0/192)**.

> The gap is real but does not alter qualitative conclusions. The placeholder composition
> should not be presented alongside published observations as a "water composition"; we flag
> it and recommend exclusion or explicit labelling. (`A22_判据分解/A22_判据分解报告.md`)

### S3.2 The 17 exceptions at zero displacement (physical, not noise)

When $C=0$ the identity reduces to $dS=-(M_0-M_1)-x_{\rm AI}$, so $dS>0$ **iff**

$$M_1-M_0 > x_{\rm AI}$$

i.e. the facility's *quality penalty alone* exceeds the volume it draws from the reclaimed
pool, making its discharge $F$ **negative**. The facility then withdraws *more* potable water
than without reuse while displacing nobody. Measured: 17/446 cases, criterion agreement
**100%**, median penalty/draw ratio 1.44 in the positive group vs 0.00 in the negative group,
occurring only for the high-salinity composition under severe quality tiers.

> **Reclaimed cooling can raise urban potable withdrawal with zero competition**, purely
> through its own water-chemistry penalty. Quality is therefore an independent, reversible
> force — not a correction term on displacement.

---

## S4. Water quality, composition, and **solver path**

### S4.0 The primary convention and its alternative (read first)

Two quality solvers exist in the engine and they disagree qualitatively. This is the single
most important caveat on the "quality penalty" mechanism.

| | **volume-only** (primary) | **R10a dynamic solute state** (opt-in) |
|---|---|---|
| loop concentration | instantaneous blend of makeup sources | maintained loop solute stock |
| CoC at $\varphi=0$ | 5.500 | 5.500 |
| CoC at $\varphi=0.4$ | 2.292 | **7.801** |
| CoC at $\varphi=0.6$ | **1.824** | **7.986** |
| makeup at $\varphi=0.6$ | 47 735 ML | **25 804 ML** (−46%) |
| behaviour as blending rises | CoC **collapses** | CoC **holds** near design |

Water closure on both paths: **9.77 × 10⁻¹⁵ ML**. Both satisfy mass balance
($M/B=\mathrm{CoC}$, 16/16).

**Consequence.** The quality penalty $(M_0-M_1)$ that drives our mechanism is large on the
volume-only path and ≈0 on the dynamic path. Our **central direction** ("reclaimed cooling
does not automatically save city water") holds on both, but the **mechanism attribution**
holds only for volume-only. We adopt volume-only as the primary convention because it is the
conservative bound **and** because the engine's own R10 gate marks the dynamic path
`NOT_READY_FOR_E3`. The dynamic path is reported as a structural sensitivity.
(`A21_动态状态/A21_动态状态报告.md`)

**Storage.** Introducing cooling storage raises makeup by **+3.45%** (D-HA) and **+7.02%**
(D-CO), identically for 50, 200 and 800 ML capacity — a discrete "storage present" effect,
not a capacity gradient.

### S4.1 Solute-state sensitivity

**Switch.** With `limit_scale` = 10⁶ (realised CoC = design 5.000):
$dS_{\rm pot}=$ **0.000000 ML exactly** in the committed branch (80/80); ≤ 0 in the surplus
branch. Non-binding quality ⇒ pure reallocation.

**Units correction.** `limit_scale` is a limit-scaling factor, **not**
$\chi=\mathrm{CoC}_{\lim}/\mathrm{CoC}_{\rm design}$. At `limit_scale` = 1.0 the constraint
still binds (realised CoC 4.60), so the earlier "non-binding" check was invalid.

**Composition.** With the constraint active, composition changes the outcome:

| composition | realised CoC | mean $dS_{\rm pot}$ (surplus / committed) |
|---|---|---:|
| LADWP AWPF (RO, TDS 22) | 2.50–5.00 | −19,726 / −8,510 |
| IEUA RP-1 (tertiary, TDS 443) | 1.90–2.45 | −12,257 / −4,690 |
| AI-UWM assumption (TDS 650) | 1.98–3.49 | −16,359 / −7,504 |
| **Figshare RW (TDS 1,378)** | 1.14–2.46 | **+8,895 / +28,437** |

**A high-salinity source reverses the sign.** Tiers: 0.98 = GSA/NREL 2023 metered upper bound
(CoC 4.34–4.91); 0.50 = PHREEQC calcite-limited IEUA (2.52/5.0 = 0.504); 0.25 = GB/T
19923-2024 make-up-water tier, retained **only** as a labelled extrapolation (response there
reaches 5.99 × 10⁵ ML, outside observed operation).

---

## S5. Finite supply transforms the outcome

Nested thresholds (D-HA; natural cap 380 ML/day):

| threshold | ML/day | share |
|---|---:|---:|
| $W_{\rm nat}$ | 380 | 100% |
| $W_{\rm engage}$ | 342 | 90% |
| $W_{\rm gap}$ | 323 | 85% |
| $W^{*}_{\rm break}$ | 304 | 80% |

Four outcomes, all measured: (1) old conclusion holds when supply is adequate;
(2) **converts to a necessary-service gap** when scarce (up to 62,080 ML);
(3) sign reverses in the surplus branch; (4) **the data centre is itself curtailed**
(up to 8,519 ML). Propositions H1–H4 hold in both domains with **zero falsifiers**.

---

## S6. Robustness (all re-run after the cache fix)

| experiment | gates | key result |
|---|---|---|
| Ablation 2³ (64 cells) | **5/5 pass** | identity residual 3.6e−12; capacity-regime main effect +9,620 ML |
| Holdout + boundary | **5/5 pass** | true holdout **R² = 0.558** (baseline −0.044); no-quality case exactly 0; penalty monotone in quality (6,478 → 21,674 → 116,581) |
| Grid resolution | boundary-position criterion: **100% within one grid step** (max shift 0.015625) | **11 of 39 (28%) curves are now non-monotone** |
| Prior sensitivity | re-run in progress | — |

> **A correction and a new finding.** An earlier assessment reported "only 15.4% of feasible
> sets agree" and inferred resolution sensitivity; that criterion compared *counts of feasible
> grid points*, which must grow with refinement, so it was invalid. On the correct
> boundary-position criterion the boundary moves at most one step in **100%** of cases.
> However, after the cache fix the composition dimension is live and **non-monotone feasible
> regions appear in 11/39 curves (28%)** — i.e. there exist parameter intervals where the
> city-level outcome fails, recovers, and fails again. Before the cache fix these were
> invisible (0/39) because composition carried no variation; they are therefore a
> **genuine structural feature**, and coarse-grid scans can miss them; we report them rather
> than rely on first-failure identification.

> The holdout R² of 1.000 is an **algebraic re-derivation** (it reuses the holdout domain's
> $M_0,M_1$) and is **not** validation. The genuine out-of-sample number is **0.558**.

---

## S6b. External anchoring (observed infrastructure)

**The project's largest weakness was external validity.** We located, downloaded and
integrity-checked a public, reproducible dataset accompanying Shen et al. (2026,
*Nature Water*): 10,826 Chinese wastewater treatment plants with design capacity, load rate
and location, released CC-BY-4.0 on Zenodo (`10.5281/zenodo.22138940`).

**Verification performed**

| check | result |
|---|---|
| archive retrieved | 2,683,047 bytes (record lists 2.7 MB) |
| plant count | **10,826 rows** — matches the count in the paper's own title |
| internal consistency | reported load rate reproduces annual volume / 365 / design capacity, **r = 1.0000** |

**Observed distributions**

| quantity | value |
|---|---:|
| design capacity, P25 / **P50** / P75 / P90 | 1.4 / **8.0** / 25 / 60 ML/d |
| aggregate design capacity | 268,599 ML/d |
| load rate, P10 / P25 / **P50** / P75 / P90 | 0.09 / 0.31 / **0.594** / 0.83 / 0.97 |
| load rate > 1 | 6.2% |
| industrial cooling-water share (39 sectors) | median of sector means **0.184** |
| urban water price (n = 39,083) | median **1.45** CNY/m³ |

**Consequences**

1. **Parameter placement.** Our nominal deliverable reclaimed supply is 33.4 ML/d (D-HA) and
   30.7 ML/d (D-CO) — the **81st percentile** of observed plants. The work therefore describes
   cities with **above-median reclaimed-water provision**, and is labelled so.
2. **Supply-expansion headroom.** Median utilisation is 0.594 of design capacity and only
   6.2% of plants exceed capacity, so most plants retain **spare treatment capacity**: there
   is physical scope to produce additional reclaimed water.

> **A correction we record here.** An earlier draft of this section used load rate as a direct
> proxy for the committed-share and reported the prevalence of the two regimes as
> 41.6% / 29.8% / 28.6%. That mapping is **wrong in direction**: the regime is set by the
> demand-side ratio $\text{elig}/P_0$, and since $P_0 \approx \text{load rate} \times$
> $\text{design capacity}$, a *low* load rate implies *less* reclaimed water produced and hence
> a *higher* demand-to-supply ratio, pushing the system **toward** the committed branch — the
> opposite of what was claimed. Load rate is a production-side quantity; regime membership is
> demand-side. We therefore do **not** report regime prevalence from these data.

### S6c. Which regime do real systems occupy? (external validity test)

We place the regimes on the observed **scale** distribution — the legitimate independent
variable. The required deliverable reclaimed volume to enter the zero-displacement (surplus) branch
is the threshold `pool_scale` times the model's per-day base supply. Measured empirically, surplus
**first appears** at `pool_scale` = 2.0 and reaches 50% prevalence at 2.2 (D-HA) / 2.4 (D-CO),
i.e. **≈ 66.9 / 61.4 ML/d** (first appearance) and **≈ 73.5 / 73.7 ML/d** (50% level).

| $r$ | D-HA surplus % (first) | D-HA surplus % (50% level) | D-CO surplus % (first) | D-CO surplus % (50% level) |
|---:|---:|---:|---:|---:|
| 1.00 | 5.99 | 5.37 | 6.55 | 5.34 |
| 0.80 | 4.50 | 4.05 | 5.07 | 4.01 |
| 0.50 | 2.14 | 1.88 | 2.48 | 1.88 |
| 0.30 | 0.88 | 0.79 | 1.04 | 0.79 |
| 0.20 | 0.47 | 0.39 | 0.54 | 0.39 |

Observed treated volume (n = 10,826): median 3.0, P75 16.8, P90 44.4, P95 77.8 ML/d.

> **The committed branch dominates: above 93% for all $r$ and above 99% for $r \le 0.3$; surplus
> covers only 0.4–6.6%.** The regime in which our central result bites hardest is the empirically
> dominant one, so the result is not an artefact of a parameter corner; the supply-expansion route
> is realistic only for the largest systems and should not be a universal prescription.

> **Methodological note.** We use **empirically measured** thresholds, not the closed-form
> `elig/P0` (2.384 / 2.567), because surplus already appears at `pool_scale` = 2.0. The transition is
> smooth rather than a step: at `pool_scale` = 1.5 unused reclaimed water is present (2,828 ML) while
> displacement still occurs (11,896 ML), so "unused water present" ≠ "no displacement". The empirical
> thresholds are therefore the conservative choice. (`A24_外部锚定/external_validity.py`,
> `fix_threshold.py`, `explain_transition.py`)

> **We do not claim external validation.** The data constrain parameter ranges and bound the
> scope for expanding supply; they do not validate city-level predictions, and no
> facility-level cooling-operations data were obtainable (engine gate G3 remains `NOT_READY`).
> (`A24_外部锚定/A24_外部锚定报告.md`)

---

## S7. Model bridging

Periodic representative-day model vs full daily engine, identical inputs, **24 pairs**
(2 domains × 2 compositions × 3 pool levels × 2 mixing ratios, 730 days each):

| quantity | median relative difference | max |
|---|---:|---:|
| $M_0$ | **0.000000** | **0.000000** (identical in 24/24) |
| $M_1$ | 7.7% | 63.7% |
| $\varphi_{\rm eff}$ | 0.7% | 17.3% |
| CoC | 11.2% | 62.1% |
| **$dS_{\rm pot}$ sign agreement** | **20/24 (83%)** | — |

By composition: **IEUA 12/12** sign agreement; **LADWP 8/12**. The disagreements concentrate
in the RO-product composition — precisely the one whose chemistry changes the limiting phase.

**Conclusion.** The cooling-physics and water-volume *conventions* are **proven equivalent**
($M_0$ identical to the last digit in every pair). The residual differences are
**composition resolution**: the daily engine resolves per-day chemistry and reaches higher
CoC for pure sources, which the periodic representative-day model averages out. This is a
quantified, attributed difference — not an unexplained discrepancy.

**Harness defect found and fixed**: the daily arm initially passed facility *makeup* where
*evaporation* was required, inflating $M_0$ by 1.60×; corrected, the two agree exactly.

Remaining caveat: storage, solute accumulation and treatment delay were **zero in both
models**, so dynamic-state effects remain untested.

---

## S8. Evidence-status disclosure (required)

Engine-side register applies a stricter bar than the paper side. Disclosed:

| engine claim | status |
|---|---|
| C3 "reclaimed use always reduces city withdrawal" | REFUTED_IN_BOUNDED_RUN |
| C4 quality feedback vs independent chemistry | NOT_READY |
| C5 facility makeup/blowdown out-of-sample | NOT_READY |
| C7 A0–A3 adaptation restores net savings | NOT_READY |
| C8 synthetic hydrology represents observed reliability | NOT_READY |
| G2 chemistry gate / G3 facility holdout | NOT_READY |

---

## S9. Defects, findings and corrections in this round

All are documented in `19_缺陷报告_缓存与桥接_2026-10-15.md` and
`A21_动态状态/A21_动态状态报告.md`.

1. **Evaluator cache key omitted water composition** → with a shared cache, the first
   composition's results were reused for all others, and the composition axis carried no
   variation. After the fix, composition spans both signs of the outcome.
   *Gate added*: any factor claimed to be swept must be demonstrated to produce variation.
2. **Bridging harness used makeup where evaporation was required** → 1.60× inflation;
   corrected, $M_0$ agrees exactly in 24/24 pairs.
   *Gate added*: cross-model comparisons must assert equality of shared quantities.
3. **A displacement-ratio heuristic was over-claimed in an intermediate draft.** We had
   claimed the ratio's extremes were "pure". With composition live, **114 purely-displaced
   cases are negative**; the three-term criterion, not the ratio, is correct.
4. **The quality penalty is solver-path dependent** (§S4.0). Both paths satisfy closure, but
   they diverge qualitatively; both directions support our central claim, while the
   *mechanism attribution* holds only for the volume-only path.
5. **No new mechanism beyond conservation was found** in the dynamic-state experiment. We
   report this rather than constructing a narrative.

---

## S10. Retracted and negative results (retained)

**Retracted earlier:** "two opposing channels"; supply-stress $\psi$; critical ratio
$\varphi^*$; supply floor — all traced to treating the engine's `gap` (unmet *reclaimed*
demand) as potable demand and subtracting an unmet-demand gap from a withdrawal change.

**Retained negatives:**
1. In the committed branch with non-binding quality, $dS_{\rm pot}=0$ **exactly** — no saving.
2. Grid-resolution "15.4% agreement" was a **wrong criterion** (feasible-point counts);
   the corrected boundary-displacement criterion gives 1-step convergence.
3. Earlier retractions unchanged: A3 "+13,974 ML/yr" was a degenerate-day artefact; τ axis
   retired; index B `NOT_IDENTIFIABLE_FROM_AVAILABLE_DATA`; dimensionless "collapse law" is an
   algebraic identity.
