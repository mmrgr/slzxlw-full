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

**Residual 5.8 × 10⁻¹¹ ML** across the earlier placeholder-limit run (1,152 scenarios; the
current cited-limit run gives 4.37 × 10⁻¹¹ ML across 839 reliable scenarios).

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
| $q>0$ | 263 | **263** | **0** | −17,264 |
| $q\approx0$ | 288 | 208 | 0 | −7,651 |
| $q<0$ | 288 | 143 | 145 | 200 |

**$q>0$ is sufficient for a city-level benefit (263/263, no exception).**

> Figures are the **A27 cited-limit** run (reliable subset $n=839$). The superseded
> placeholder-limit figures were 349 / 326 / 477 with 285 harmful cases.

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

### S2a. Cooling-water limits: cited standards replace placeholders

All earlier runs used the engine's **placeholder** limit set, which (i) carried no citation and
(ii) **violated GB/T 50050-2017** on the scaling side: calcium hardness plus alkalinity gave
700 + 500 = **1200 mg/L against the standard's 1100 mg/L criterion**. We replaced it with the
verified cited sets (`A4_水化学参数域/T6b_limits_cited.py`):

| tier | TDS | Cl | hardness | alkalinity | silica | hard+alk | source |
|---|---:|---:|---:|---:|---:|---:|---|
| ~~placeholder~~ (withdrawn) | 2200 | 500 | 700 | 500 | 150 | **1200 ✗** | none |
| **baseline (adopted)** | 2200 | 700 | 750 | 350 | 175 | **1100 ✓** | GB/T 50050-2017 (circulating) |
| permissive | 2600 | 1000 | 750 | 350 | 175 | 1100 ✓ | GB/T 50050-2017 (C-steel Cl relaxation) |
| strict | 1000 | 250 | 450 | 350 | 30 | 800 | GB/T 19923-2024 (make-up water) |

**Effect (same grid):**

| quantity | placeholder | **cited** |
|---|---:|---:|
| reliable scenarios | 1,094 | **839** |
| withdrawal falls | 729 | **626** |
| **withdrawal rises** | **285** | **177** |
| zero-displacement | 441 | 391 |
| $q>0$ | 329 | 263 |
| $q>0$ but harmful | 0 | **0** |
| identity residual (ML) | 1.16e−10 | **4.37e−11** |
| criterion agreement | 1.0000 | **1.0000** |

> The placeholder was **overstating harm**: it set the scaling-side limits *looser* and the
> chloride limit *tighter* than the standard, and the net effect was to report 285 adverse cases
> where a compliant limit set supports 102.

### S2a-bis. Degenerate scenarios (a new gate)

At `limit_scale` = 0.25 the cited limits are stricter than the source water itself — for IEUA,
alkalinity 87.5 mg/L against a water concentration of 140 mg/L (ratio **0.625 < 1**) — so the
engine's CoC floor (1.000001) is reached and makeup degenerates to ≈ 2 × 10¹⁰ ML. These **188
scenarios are physically meaningless** and are now excluded alongside solver failures.

> **Numerical caution.** After the switch the identity residual *appeared* to worsen to
> 2.8 × 10⁻⁶. This is **catastrophic cancellation**, not modelling error: `M₀ − M₁` subtracts
> two numbers of order 2 × 10¹⁰, so an absolute residual of 1e−6 is a *relative* residual of
> 1.4 × 10⁻¹⁶ — machine precision. Gates on such quantities must use **relative** tolerances.
> With both gates the residual is 4.37 × 10⁻¹¹ and the criterion agreement is again exactly 1.0000.

---

### S3.0 Solver-reliability gate (added after the A25 audit)

A full audit found that **25 of the 1,052 scenarios (2.38%)** in the *current* main grid did not
return `converged_unique`: `no_convergence` (16) and `non_unique` (9), which exhaust the status
categories. In these scenarios the joint quality/allocation solver returns **zero
allocations**, yet `displaced` and `dS_pot` are still computed — so they silently contaminate
any summary.

| product | all | unreliable | share |
|---|---:|---:|---:|
| `supply_state_regimes.csv` (main grid, **current cited-limit run**) | **1,052** | **25** | **2.38%** |
| `potable_flows.csv` (A13c) | 408 | **35** | **8.58%** |
| `ablation_matrix.csv` | 64 | 2 | 3.13% |
| `holdout_fit_ha.csv` | 204 | 16 | 7.84% |
| `holdout_holdout_co.csv` | 204 | 19 | 9.31% |
| `holdout_predictions.csv` | 816 | 48 | 5.88% |
| `grid_resolution_points.csv` | 14,196 | 541 | 3.81% |

**Effect on headline numbers (main grid)**

| quantity | all | reliable only (dual gate) |
|---|---:|---:|
| scenarios | 1,052 | **839** |
| $dS_{\rm pot}<0$ | — | **626** |
| $dS_{\rm pot}>0$ | — | **177** |
| $dS_{\rm pot}=0$ (exact) | — | **36** |
| zero-displacement | — | 391 |
| $q>0$ | — | **263** |
| $q>0$ but harmful | **0** | **0** |
| identity residual (ML, relative) | — | **4.37e−11 (3.55e−16)** |

> **Sign convention: strict.** $dS_{\rm pot}=0$ is its own category and is never folded into
> either sign. *(Earlier versions of this table quoted 631 / 102 without a zero column; those
> values require an undisclosed tolerance band that removes 80 scenarios — only 36 of which are
> exact zeros, the other 32 being genuinely harmful. The corrected strict counts are 626 / 177 /
> 36 at $n=839$. Note that the earlier "1,152 scenarios / 58 unreliable" entry in this table
> described the **superseded placeholder-limit run**; the current grid has 1,052 rows.)*

> This table reflects the **A27 cited-limit** run. The earlier placeholder-limit run gave
> scenarios 1,152 / reliable 1,094, $dS<0$ 729, $dS>0$ 285, zero-displacement 441,
> $q>0$ 329, residual 1.16e−10. Both runs agree on the two qualitative facts that
> matter: there are **zero** $q>0$-but-harmful cases, and $q>0$ holds throughout.

> **An algebraic relation cannot certify its own inputs.** The residual and the criterion
> agreement are *identical* on both sets, because they are rearrangements that hold for any
> input — including zero allocations. A 100% criterion agreement is therefore **not** evidence
> that the scenarios are trustworthy; only the solver status is.

**Artefacts this gate removed.** In A13c, 11 `no_convergence` rows (all with `x_ai = 0`) had
been counted as "withdrawal rises". On the main grid, all 38 `x_ai = 0` rows were failures, and
the apparent 31/7 harmful cases for LADWP / the placeholder composition were likewise failures;
in the reliable subset their harmful counts are **8** and **8** (against 186 and 187
beneficial, with 9 exact zeros each). *(An earlier draft quoted "237/0" and "241/0";
neither could be traced to a machine artifact and both were replaced by the recomputed
values.)*

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

### S3.2 The exceptions at zero displacement (physical, not noise)

When $C=0$ the identity reduces to $dS=-(M_0-M_1)-x_{\rm AI}$, so $dS>0$ **iff**

$$M_1-M_0 > x_{\rm AI}$$

i.e. the facility's *quality penalty alone* exceeds the volume it draws from the reclaimed
pool, making its discharge $F$ **negative**. The facility then withdraws *more* potable water
than without reuse while displacing nobody. Under the **cited** limit set and the dual gate
(the authoritative convention) the figures are **11 of 391** branch-C cases; the earlier
"17 of 446" came from the withdrawn pre-A27 placeholder tier and from a pooled sample that
included solver-failed rows. The mechanism is unchanged and, in the repaired grid, occurs for
the compositions whose constraint binds under severe quality tiers — **not** for salinity as
such: within the committed branch IEUA and Figshare RW give the same 48 harmful / 3 beneficial
split, so an earlier draft's attribution to "high salinity" is not supported.

> **Reclaimed cooling can raise urban potable withdrawal with zero competition**, purely
> through its own water-chemistry penalty. Quality is an independent, reversible
> force — not a correction term on displacement.

> **Note (2026-10-16).** The magnitude of this effect is composition-sensitive and, with the
> two-species `AI-UWM assumption` entry excluded (§S14), rests on the high-salinity sample
> only, whose composition is itself incomplete (two species missing). The direction is robust
> to that imputation, but the count above should be read as conditional on the complete-data
> subset.

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
$dS_{\rm pot}=0$ **to machine precision** in the committed branch ($|dS_{\rm pot}|<10^{-11}$ ML in all 80/80 cases; 36 are exactly 0.0); ≤ 0 in the surplus
branch. Non-binding quality ⇒ pure reallocation.

**Units correction.** `limit_scale` is a limit-scaling factor, **not**
$\chi=\mathrm{CoC}_{\lim}/\mathrm{CoC}_{\rm design}$. At `limit_scale` = 1.0 the constraint
still binds (realised CoC 4.60), so the earlier "non-binding" check was invalid.

**Composition.** With the constraint active, composition changes the outcome:

| composition | realised CoC | mean $dS_{\rm pot}$ (surplus / committed) |
|---|---|---:|
| LADWP AWPF (RO, TDS 22) | 1.84–5.00 | 186 / 8 / 9 |
| IEUA RP-1 (tertiary, TDS 443) | 1.34–5.00 | 151 / 56 / 9 |
| Figshare RW (TDS 1,378) | 1.15–5.00 | 102 / 105 / 9 |
| AI-UWM assumption (TDS 650) | 1.84–5.00 | 187 / 8 / 9 |

*(Columns are $dS_{\rm pot}<0$ / $>0$ / $=0$ over the reliable subset. The mean-$dS$ values
quoted in earlier drafts could not be traced to a machine artifact and were removed; see
`A30_WP0取证/untraceable_traceability_summary.json`.)*

**The highest-salinity composition is the only net-adverse one.** Read the table as a
mechanism, not as four equivalent panels: the identity of §S2 splits the outcome into a
displacement gain and a quality penalty, and a composition whose dissolved solids sit close to
the admissible limit (TDS 1,378 vs 2,200 mg/L) drives the penalty up until it offsets the gain.
Figshare RW is therefore the only composition with harmful outcomes outnumbering beneficial
ones (105 vs 102), while the two fully characterised lower-salinity real compositions favour
the city decisively (LADWP 186 vs 8; IEUA 151 vs 56).

Two cautions attach to that statement. (i) The "reclaimed cooling is beneficial" reading and
its opposite are **both correct within this grid**, separated by composition — which is why no
single facility-level number settles the question. (ii) The adverse composition is also the
least completely characterised (silica absent), so its 105/102 split is the panel most
sensitive to further sample data; **we flag it rather than rely on it**, and no headline claim
rests on it. Do **not** read this as "high salinity generally reverses the sign" — the series
here is four compositions with confounded salinity and completeness, not a controlled salinity
scan.

Tiers: 0.98 = GSA/NREL 2023 metered upper bound
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
| Holdout + boundary | **5/5 pass** | true holdout **R² = 0.766** (baseline −0.068); no-quality case exactly 0; penalty monotone in limit stringency (global decomposition in §7a) |
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
| industrial cooling-water share (39 sectors) | mean of sector means **0.258** (the value 0.184 in an earlier draft could not be traced and was removed) |
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

### S6c. External validity: capacity adequacy, **not** regime prevalence

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

> **⚠️ Retraction (2026-10-16). An earlier version of this section read these percentages as
> the share of real plants *in the surplus regime*, concluding that "the committed branch
> dominates: above 93%". That reading is not identified by this dataset and is withdrawn.**
> The table above compares a plant's deliverable **supply** ceiling $D_i$ = treated volume
> $\times\,r$ against a threshold; whether a pool is *committed* is set by incumbent
> **demand** $E_i$, which is unobserved here. With only $0\le E_i\le D_i$ available, both
> branch states remain admissible for every plant, so the committed share's provable bounds
> are the uninformative interval **[0%, 100%]**.

> **Correct reading.** The percentages above quantify **treatment-capacity adequacy**, not
> regime prevalence: they state what fraction of plants *could* support a surplus-type scheme at
> all. Read that way they are informative and support exactly one conclusion — the
> supply-expansion route that reduces city withdrawal is **capacity-limited to a minority of
> systems** (2.1–6.6% depending on $r$), so it should not be advanced as a universal
> prescription. The stronger claim that most real systems are *already* fully committed is
> **not supported and is not made**. See main text §6b and
> `A30_WP0取证/a24b_partial_id_summary.json`.

> **Methodological note.** We use **empirically measured** thresholds, not the closed-form
> `elig/P0` (2.384 / 2.567), because surplus already appears at `pool_scale` = 2.0. The transition is
> smooth rather than a step: at intermediate `pool_scale` unused reclaimed water is present while
> displacement still occurs, so "unused water present" ≠ "no displacement". *(The absolute
> volumes 2,828 / 11,896 ML quoted in an earlier draft could not be traced to a machine
> artifact — `surplus_threshold_check.json` stores shares only — and have been removed.)* The empirical
> thresholds are therefore the conservative choice. (`A24_外部锚定/external_validity.py`,
> `fix_threshold.py`, `explain_transition.py`)

> **We do not claim external validation.** The data constrain parameter ranges and bound the
> scope for expanding supply; they do not validate city-level predictions, and no
> facility-level cooling-operations data were obtainable (engine gate G3 remains `NOT_READY`).
> (`A24_外部锚定/A24_外部锚定报告.md`)

---

## S7. Model bridging

Periodic representative-day model vs full daily engine, identical inputs, **24 pairs**
(2 domains × 2 compositions × 3 pool levels × 2 mixing ratios, `limit_scale` = 0.5,
aggregated over 730 days). Current run: `bridging_comparison_v2.csv` /
`bridging_summary_v2.json` (2026-10-15, after the A27 cited-limit switch of §S2a).

| quantity | value |
|---|---:|
| $M_0$ | identical to the last digit in **24/24** (median relative difference 5.1e−16) |
| $dS_{\rm pot}$ sign agreement | **23/24 (0.958)** |

By composition: **IEUA RP-1 12/12**; **LADWP AWPF 11/12**.

> **Correction (A28).** An earlier version reported 36 pairs with 20/24 (83%) and later 24/36
> (66.7%) agreement, and attributed the disagreement to Figshare RW's missing alkalinity and
> silica. Those figures came from `bridging_comparison.csv`, generated **2026-10-14 — before the
> A27 placeholder→cited-limit switch** — and conflated two scripts (`bridging_experiment.py`
> writes the 36-pair file; `bridging_v2.py` writes the 24-pair file). The current 24-pair run
> gives **23/24 (0.958)**, and **Figshare RW is not in it**, so the composition-completeness
> attribution is **withdrawn**. Bridging remains a **partial** equivalence check: exact on
> $M_0$, not a validated agreement on $dS$ sign.

> **Open item.** The older 36-pair run (which does include Figshare RW) has **not** been re-run
> after A27 and must not be cited. Re-running `bridging_experiment.py` to test whether the
> composition-completeness pattern survives under cited limits is a straightforward next step.

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

---

## S10. Retracted and negative results (retained)

**Retracted earlier:** "two opposing channels"; supply-stress $\psi$; critical ratio
$\varphi^*$; supply floor — all traced to treating the engine's `gap` (unmet *reclaimed*
demand) as potable demand and subtracting an unmet-demand gap from a withdrawal change.

**Retracted in v4 (2026-10-16):**

1. **"The fully-committed regime is empirically dominant (above 93–95% of real plants)."**
   Withdrawn as **not identified**: the supporting test observed deliverable supply only,
   never committed demand. Provable bounds are [0%, 100%]. See §S12.
2. **"Cleaner reclaimed water saves more water, hence reuse is more beneficial."** Withdrawn.
   Across the complete-composition grid the city outcome tracks the reclaimed volume drawn
   ($\mathrm{corr}=-0.93$), whereas the quality term $q$ correlates only $-0.16$ and with the
   *opposite* sign; higher admissible CoC also means less blowdown and therefore *less*
   reclaimed water needed. Only the intermediate statement survives — that water chemistry
   determines the sign of $q$ (100% of complete-composition samples). See main text §3 and
   `A32_WP3_水化学/` (correction section).
3. **"Sign-criterion agreement = 1.0000" as evidence of predictive content.** Downgraded to an
   accounting consistency check; the strict pre-intervention test gives 0.675 against a 0.809
   baseline. See §S11.
4. **"429 of 446 branch-C cases negative, with 17 physical exceptions."** Superseded: under the
   cited limits and the dual gate the authoritative figures are **380 of 391, with 11
   exceptions**.
5. **"R² = 0.557"** (holdout) and **"baseline −0.050"**. Superseded by **0.766** and
   **−0.0682** under the cited limit set; the old figures came from the pre-A27 placeholder
   tier. Multiple mutually inconsistent variants (0.557 / 0.5574 / 0.5582 / 0.558) appeared in
   the same draft and have been unified.
6. **"Figshare RW touches the CoC floor"** as the reason to exclude it. That value appears only
   at `limit_scale = 0.25` (an extrapolated, unsupported tier); at the default the sample gives
   CoC ≈ 2.02 and is not degenerate. The valid exclusion reason is **incomplete composition
   (two species missing) plus magnitude sensitivity**.
7. **"AI-UWM placeholder composition has no harmful case."** An artefact of missing species
   entering as zero; refilling from the observed range **flips the sign of $q$**. The entry is
   excluded from all sign claims.

**Retained negatives:**
1. In the committed branch with non-binding quality, $dS_{\rm pot}=0$ **exactly** — no saving.
2. Grid-resolution "15.4% agreement" was a **wrong criterion** (feasible-point counts);
   the corrected boundary-displacement criterion gives 1-step convergence.
3. Earlier retractions unchanged: A3 "+13,974 ML/yr" was a degenerate-day artefact; τ axis
   retired; index B `NOT_IDENTIFIABLE_FROM_AVAILABLE_DATA`; dimensionless "collapse law" is an
   algebraic identity.
4. **Chemistry-only prediction fails** (0.675 < 0.809 baseline) — reported, not hidden.
5. **The $q>0$ sufficient condition could not be meaningfully tested** in the complete-composition
   grid: all 47 reliable cases are beneficial, so "no exception" is a vacuous pass
   (gate 4). Stated as untested rather than confirmed.
6. **No new mechanism beyond conservation** was found in the dynamic-state experiment.

---

## S11. Pre-intervention prediction test (added 2026-10-16)

**Motivation.** Every agreement rate reported in the main text — including the headline
"263/263, no exception" sufficient condition — is computed with *post-simulation* quantities
($x_{\rm AI}$, $M_0$, $M_1$, displacement). Such a rate is an algebraic restatement of the
identity, so it cannot establish predictive content. We therefore ran a strict test using
only pre-intervention information.

**Information set.** Water chemistry of each source (`city_model.load_samples()` — the
authoritative table, never hand-entered); the cited limit set; design CoC; the blending ratio
$\varphi$; and the deliverable pool relative to baseline demand. The predictor function takes
only `(reclaimed_chemistry, φ)` plus the pool ratio, and the script asserts by signature
inspection that it cannot reach $x_{\rm AI}, M_0, M_1, C, F$ or $dS_{\rm pot}$.

**Results** ($n_{\rm eff}=759$; the 839 reliable scenarios less 80 within $10^{-9}$ ML of zero,
which are reported as a separate zero category, never folded into either sign):

| criterion | accuracy | TP | FP | TN | FN |
|---|---:|---:|---:|---:|---:|
| Chemistry only ($c^{\rm rec}_i<c^{\rm pot}_i$, all species) | 0.432 | 183 | 0 | 145 | 431 |
| Closed form $q>0$ | 0.675 | 367 | 0 | 145 | 247 |
| $q>0$ or pool ratio $\ge 2$ | 0.914 | 602 | 53 | 92 | 12 |
| *majority-class baseline* | *0.809* | — | — | — | — |

**Leave-one-composition-out validation** (select the criterion on the remaining compositions,
evaluate on the held-out one): mean out-of-sample accuracy **0.917** vs mean out-of-sample
baseline **0.815**, a gain of **+0.102**. The criterion is re-selected inside each
fold, so the in-sample winner is not purely a post-hoc artefact; but only two of the four
folds are informative (the other two have a saturated baseline), so we report the criterion
as a **candidate** rather than a validated predictor (main text section 7).

**Why chemistry alone fails (structural, not a tuning issue).** In dimensionless form
$dS_{\rm pot}/M_1=\rho(\kappa-1)-q$. The quality term $q$ is fixed by pre-intervention
chemistry, and its *direction* is predicted correctly in 100% of complete-composition samples
(IEUA $q<0$ in 24/24; LADWP $q>0$ in 23/23). The displacement term, however, requires
demand-side and allocative information. The two enter with opposite signs, so no
chemistry-only criterion can determine the net sign. Adding one demand-side planning
quantity resolves the ambiguity.

**Negative result retained.** We report the 0.671 figure explicitly. The "sign-criterion
agreement = 1.0000" quoted in earlier drafts is downgraded to an **accounting consistency
check** and is not presented as predictive skill.

---

## S12. Partial identification of regime shares (added 2026-10-16)

**Withdrawn claim.** Earlier drafts (and the v3 abstract) reported that the fully-committed
regime covers 93.5–97.9% of the 10,826 observed Chinese wastewater treatment plants, calling
it "empirically dominant". **We withdraw this.**

**Why it is not identified.** The test compared plant treated volume $\times$ reuse fraction
$r$ — call it $D_i$, the deliverable **supply** ceiling — against a threshold back-solved from
the synthetic grid, and labelled every plant below it "committed". Whether a pool is committed
is determined by incumbent **demand** $E_i$, which this dataset does not observe. The only
physical constraint is $0\le E_i\le D_i$; for every plant, values of $E_i$ realising *either*
branch are admissible. The provable bounds on the committed share are therefore the
uninformative interval **[0%, 100%]**, and any point estimate is a scenario proportion under
an unstated demand assumption.

**A concrete counterexample.** A small plant with $D_i=1$ ML/d whose incumbents claim only
0.1 ML/d has a largely idle pool (surplus), yet the withdrawn test labels it committed because
$1<33$. Supply and demand are logically independent here.

**What is identified.** Two statements survive, both about *supply*:

1. The treated-volume distribution is heavily right-skewed (median 3.0, P75 16.8, P90 44.4,
   P95 77.8, P99 210.4 ML/d), so large plants are a minority.
2. Consequently, only a minority of plants have the **treatment capacity** to support a
   surplus-type scheme: the share reaching the synthetic threshold of ~62–67 ML/d is

| $r$ | D-HA capacity-adequate | D-CO capacity-adequate |
|---|---:|---:|
| 1.0 | 5.99% | 6.55% |
| 0.8 | 4.50% | 5.07% |
| 0.5 | 2.14% | 2.48% |
| 0.3 | 0.88% | 1.04% |
| 0.2 | 0.47% | 0.54% |

This supports only a scoping conclusion (the supply-expansion route is capacity-limited), and
is deliberately silent about demand. Script:
`A30_WP0取证/a24b_partial_identification.py`.

---

## S12b. Prior sensitivity, and one caliber choice that must be stated

Because several inputs (pool scale, gap scale, incremental capacity) are set by assumption
rather than observation, we swept **27 prior configurations (3 × 3 × 3 over uniform,
log-uniform and triangular priors; 600 Latin-hypercube draws each, fixed seed)** through the
same evaluator (`A15_稳健性/prior_sensitivity.py`; `prior_sensitivity.csv`, `prior_bounds.json`).

The result is a **caliber-dependent sign**, and we state it rather than choose silently:

| caliber | what is held | median city outcome across the 27 priors |
|---|---|---|
| **A** (dp_scale = 0) | no incremental capacity; pure share question | **negative in 27/27** (range −10,409 to −0 ML) |
| **B** (dp_scale = 1.0) | pool budget inflated by `(1+dp_scale)` | **sign not stable** (range −9,125 to +22,414 ML) |

The mechanism is mechanical, not empirical: the engine implements incremental capacity as
`available = pool × (1 + dp_scale)`. At `dp_scale ≥ 1` the available pool is pushed past
existing-user demand, so a positive `S_city` is then produced by **displacement accounting** —
the same quantity counted on the other side of the ledger — rather than by a different physical
outcome.

**Consequence for this paper.** The main grid does not carry `dp_scale`; every headline number
in the main text is caliber A, where the sign of the city outcome is prior-invariant. Caliber B
is reported here because a reader who inflates the pool budget will land on the second row, and
should know that we know it. We do not claim the sign is prior-invariant under every
parameterisation — only under the one the paper uses, which is stated in the Methods.

## S13. Conservation checks on both quality solver paths (added 2026-10-16)

**Finding.** `A21_动态状态/dynamic_state.py` reported `solute_closure_max_abs_kg: NaN`. The
cause is a **wrong column name**: the script requested
`solute_balance_residual_kg_max_abs`, which the engine does not emit, and the
`pd.Series([np.nan])` fallback silently produced NaN with no error — a gate passing
vacuously. The engine's actual columns are `quality_solute_closure_residual_kg`,
`quality_process_solute_closure_residual_kg`, `quality_solute_closure_TDS_kg`, `_TSS_kg`,
`_BOD_kg`. The closure quantity was being computed all along and was never read.

**R10a dynamic path (maintains a solute stock).** Closure is satisfied to machine precision:
maximum relative residual **5.71 × 10⁻¹⁹** across 4 of 6 tested cases; the 200 ML storage case
gives 1.46 × 10⁻¹¹ kg. So the CoC ≈ 8 result of that path has conservation support and is not
a numerical artefact.

**Volume-only path (the primary convention).** This path defines loop concentration
instantaneously as blended makeup × CoC, so **no loop solute stock exists** and a stock-closure
test is not applicable — reporting it as PASS would be vacuous, reporting it as FAIL would be
a false accusation. The applicable checks are:

| check | identity | max relative residual |
|---|---|---:|
| Water closure | $G = E + D + B$ | **1.93 × 10⁻¹⁶** |
| CoC self-consistency | $\mathrm{CoC} = G/(B+D)$ | **2.50 × 10⁻¹⁶** |

**A caliber trap worth recording.** Our first version of this test used
`external_makeup_ml` and produced a spurious ~5.6% non-closure. That quantity is *gross* makeup
less internal recovery return; the correct inflow term is `gross_makeup_ml`, for which
$G-(E+D+B)=0$ exactly while $M-(E+D+B)=-2766.26$ ML — precisely the internal recovery volume.
A uniform ~5% "residual" across scenarios should first raise suspicion of a caliber error, not
an engine defect. The comparison is retained as a permanent assertion in
`A30_WP0取证/volonly_flux_balance.py`.

---

## S14. Product-integrity notes (added 2026-10-16)

1. **Swapped column labels.** In `A13_可靠性机制/supply_state_regimes.csv`, `x_ai_B1_ml` and
   `x_ai_B2_ml` are interchanged ($B_1$ is the no-reuse branch, where the reclaimed draw must
   be zero; the file has the opposite). Inspection shows the three affected label groups were
   swapped *together*, which is why the identity still closes to 4.37 × 10⁻¹¹ and every derived
   value remains correct. This is a labelling defect, not a numerical one: no result changes.
   Documented in `A13_可靠性机制/COLUMN_NAMES_CORRECTED.md`.
   *Gate added:* label correctness is independent of numerical correctness — products reused
   downstream need semantic assertions (e.g. "$B_1\Rightarrow x_{\rm AI}\equiv0$"), not only
   residual checks.
2. **Headline count convention.** Pooled sign counts depend on an undisclosed zero band. The
   strict convention gives 626 / 177 / 36 ($n=839$); an earlier convention applied
   $|dS|\le10^{-9}$ ML, dropping 80 near-zero scenarios and yielding 631 / 102 with an
   effective $n$ of 733 — while still labelling the sample as 813. We adopt the strict
   convention and report $n_{\rm eff}$ explicitly. The $q>0$ sufficient condition (263/263)
   is invariant to the choice.
3. **`Figshare BW` is brackish water, not reclaimed water**, and must not appear in reclaimed
   composition statistics; it is excluded.
4. **Solver-status vocabulary mismatch.** When a data centre uses no reclaimed water the
   engine returns `quality_solver_status='not_applicable'`, which the joint allocator's
   whitelist does not accept, so $B_1$ can be mislabelled `quality_not_converged`. Inspection
   confirms $B_1$ is a healthy solve (single root, zero closure residual); it does not affect
   $dS_{\rm pot}$ because both $C$ and $F$ are determined by the $B_2$ branch and $M$. We
   record the mismatch rather than editing the read-only engine.

---

## S15. Gates in force (cumulative)
1. Solver-status whitelist (never substring matching).
2. Semantic table — quantities with different definitions must not be merged across tables.
3. Algebraic relations are not evidence of correctness.
4. **No gate may pass vacuously** (empty sets, NaN, missing columns are never PASS).
5. **Relative tolerance for large-magnitude quantities** ($\ge10^{10}$).
6. Scanners must be precise — semantic allow-lists, not substring guessing.
7. **Observability must match identification**: supply-side observables may not be used to
   assert demand-side states; report provable bounds, not point estimates.
8. **Sign counts must declare the zero convention and the effective $n$.**
9. **Identities are not prediction** — any agreement rate must be recomputed with
   pre-intervention observables, or renamed "accounting consistency".
10. **Label correctness is independent of numerical correctness** (semantic assertions).
11. **Teammate conclusions require independent re-verification, and caliber must match** —
    subset-scope results may not be generalised to the full grid.
12. **`x or default` is unsafe when zero is a legitimate value.** In Python `0.0` is falsy, so
    the idiom silently converts valid zeros into "missing" — the mirror image of the rule that
    missing values must not be read as zero. One implementation in this work lost 54 of 128
    valid zero points this way and produced a mathematically impossible variance decomposition
    ($\sum S_1 = 1.30 > 1$); it is fixed, and the episode is recorded in §S16.3.
13. **Multiple calibers of one data source must be named at every citation.** When a single
    external table serves several uses (e.g. an all-category urban water price versus an
    industrial-only tariff), each citing location must state the **caliber and its $n$**;
    otherwise numbers in different sections read as mutually contradictory when they are not
    (§S19, and `A30_WP0取证/水价数字口径澄清.md`). Relatedly, when a stored statistic's
    filtering rule cannot be reconstructed from its own artifact, it may be quoted as
    *"as stored in that artifact"* but **must not** be described as independently reproduced.
14. **Figures and text must be regenerated together.** Figures built before a claim changes are
    stale even when their numbers were correct when drawn; this work re-ran four of six main
    figures after the post-review experiments, verifying 62 of 62 value and text checks.

---

---

## S16. Post-review verification experiments (added 2026-10-16)

These three experiments were run in response to adversarial review. Two of them **weakened our
own claims**, and we report them as such.

### S16.1 Solver-path head-to-head (NE-1)

The engine supports two quality solvers. On identical inputs and the complete-composition
samples:

| domain | composition | $dS$ volume-only | $dS$ solute-stock path | sign agrees | $q$ vol / stock |
|---|---|---:|---:|:---:|---|
| ha | IEUA RP-1 | **−3056** | **−3.72** | ✅ | −0.0960 / −0.0001 |
| ha | LADWP AWPF | 0 | 0 | ✅ (trivial) | 0.0000 / 0.0000 |
| co | IEUA RP-1 | −3019 | −3.71 | ✅ | −0.0960 / −0.0001 |
| co | LADWP AWPF | 0 | 0 | ✅ (trivial) | 0.0000 / 0.0000 |

For IEUA, blending to $\varphi=0.6$ raises makeup by **+9.8%** in the primary path but only
**+0.012%** in the solute-stock path — a **≈800×** difference in the penalty's magnitude — and
$q$ shrinks from −0.096 to −0.0001.

> **Reading.** The **sign** of the city outcome is robust across solver paths; the **magnitude
> and attribution of the mechanism are not**. Two of the four comparisons are *trivial* — for
> LADWP the quality constraint never binds and both paths return bit-identical values — so the
> effective evidence is **two scenarios, not four**. We no longer justify the primary convention
> by the engine's `NOT_READY_FOR_E3` flag, which states engineering readiness rather than
> physics. (`A38_模拟审稿/NE1_判决性实验结果.md`)

### S16.2 Is the "single sign lever" panel-invariant? (NE-2) — **no**

Repeating the single-species perturbation test under three limit tiers:

| limit tier | binding species (IEUA / LADWP) | any single-species sign lever? |
|---|---|---|
| cited (2200/700/750/**350**/175) | **alkalinity / alkalinity** | yes — alkalinity (IEUA) |
| permissive (2600/1000/750/**350**/175) | **alkalinity / alkalinity** | yes — alkalinity (IEUA) |
| **strict (1000/250/450/350/30)** | **silica / TDS** | **none** |

Under the strict tier the binding species shift to silica and TDS (that tier tightens TDS and
silica while leaving the alkalinity limit at 350), and no single-species perturbation flips the
sign. Changing the tier alone flips the sign for LADWP ($0 \to +2.821$ ML).

> **Reading.** "Alkalinity is the only sign lever" is a statement about a **bounded limit
> domain**, not a general property of reclaimed-water cooling. What transfers is the **rule**
> predicting which species binds — the smallest limit-to-concentration ratio. We downgrade the
> §7a claim accordingly. (`A38_模拟审稿/NE2_限值档稳健性结果.md`)

### S16.2b Morris screening: method, and why the engine's own routine was not used

The Morris $\mu^*$ column in the main text comes from a **trajectory-based elementary-effects
design of 32 trajectories over an 8-level grid** ($\Delta = 4/7$ of each parameter's range,
fixed seed), run through the same evaluator as the rest of this paper
(`A34_WP5_敏感性与极端事件/wp5_morris_sobol.py`;
`wp5_sensitivity_summary.json → morris`).

We did **not** use the engine's own `aiuwm.sensitivity.morris_sensitivity`. Its implementation
steps from the base point by clipping to `min(high, base+Δ)` or `max(low, base−Δ)`; when the
step lands on a range boundary the *realised* step can be far smaller than $\Delta$, yet the
effect is still divided by $\Delta/(high-low)$, which systematically **inflates** the reported
effect. It also does not detect `actual_delta == 0`. Our implementation uses a fixed grid step
and normalises by the realised step, and we record which of the two is used so the two are never
pooled. This is a **methodological substitution, not a defect in the results**: the ranking it
produces is what we report, and the substitution is stated here rather than left implicit.

### S16.3 Sobol indices with bootstrap intervals (NE-4)

Independent Saltelli design ($N_{\rm base}=128$, $d=7$, bootstrap 400 replicates, fixed seed):

| parameter | IEUA $S_T$ [95% CI] | LADWP $S_T$ [95% CI] |
|---|---|---|
| `limit_scale` | 0.330 [0.075, 0.792] | **0.891 [0.526, 1.333]** |
| blending ratio $\varphi$ | 0.926 [0.051, 2.568] | 0.243 [0.084, 0.488] |
| **alkalinity multiplier** | **0.125 [0.015, 0.305]** | **0.001 [0.000, 0.002]** |
| `pool_scale`, `gap_scale`, `e_scale` | 0.000 [0, 0] | 0.000 [0, 0] |
| $\sum S_1$ | **0.188** | **0.581** |

> **Reading.** Main effects explain only 19% (IEUA) and 58% (LADWP) of the variance, so the
> ranking is not a sufficient description. The $\varphi$ interval is very wide — direction
> certain, magnitude not — so we do not quote a single value for it. The alkalinity index is
> significant for the composition whose constraint binds and **effectively zero (0.001) for the
> one where it does not**, independently corroborating the binding-species mechanism of §7a.
> Note $\sum S_T > 1$ (1.381 / 1.172); this is estimator bias plus strong interactions under
> finite sampling and is expected for the Saltelli estimator.
> (`A38_模拟审稿/NE4_Sobol区间结果.md`)

> **Defect found and fixed during this experiment (recorded).** The first implementation wrote
> `evaluate(...) or np.nan`. Because a legitimate zero-displacement outcome is exactly `0.0`,
> and `0.0` is falsy in Python, **54 of 128 valid zero points were silently converted to NaN**,
> producing a mathematically impossible $\sum S_1 = 1.298 > 1$. This is the *mirror image* of
> the project's existing rule that missing values must not be silently read as zero — here a
> legitimate zero was silently read as missing. Corrected by distinguishing `None`
> (not identifiable) from `0.0` (valid). A degeneracy gate ($|dS|>10^6$ ML, three orders of
> magnitude above the physical scale) was added in the same pass and removed 11 points for IEUA.

### S16.4 Adversarial review outcome

Three simulated referee reports (water systems/policy, methodology/statistics, water-chemistry
engineering) each recommended **major revision**, with stated rejection conditions. Two
CRITICAL findings were confirmed by independent recomputation and are now corrected:

1. **Headline sign table was internally inconsistent** — its columns summed to 733 while the
   table was labelled $n=839$. The silently removed 80 scenarios were not all near-zero: **36
   were exact zeros but 32 were genuinely harmful ($dS_{\rm pot}>0$)**. Corrected to the strict
   convention.
2. **The apparent out-of-sample predictive skill was driven by a single fold** — per-fold gains
   were $+0.184 / 0.000 / 0.000 / -0.018$ (median **0.000**; only one of four positive), so the
   mean of $+0.0415$ is not a defensible summary. The claim is **withdrawn** and the criterion
   is reported as a candidate.

The reviewer also self-reported five hypotheses that its own evidence **disproved**, and marked
three further criticisms as not sustained — recorded for transparency in
`A38_模拟审稿/red_team_findings.md`.

---

---

## S17. Real reclaimed-water project catalogue (added 2026-10-16)

The public source package accompanying Shen et al. (2026) contains — besides the 10,826-plant
table — a catalogue of **141 real reclaimed-water projects** with documented entity, process
train, use classification, capacity and unit cost. We analyse it here for the first time in
this project.

**Use-category distribution** (codes extracted mechanically from the text prefix of the source
table's own category field; 141/141 rows classified):

| code | n | share | meaning |
|---|---:|---:|---|
| **B3** | **40** | **28.4%** | **industrial cooling / general industrial reuse** |
| A3 | 26 | 18.4% | agricultural / ecological reuse |
| B1 | 14 | 9.9% | urban non-potable reuse |
| B4 | 14 | 9.9% | low-cost landscaping / park irrigation |
| C1 | 11 | 7.8% | enhanced agricultural / rural-town reuse |
| A2 | 11 | 7.8% | agricultural reuse |
| B2 | 9 | 6.4% | landscape-water replenishment |
| C2 | 6 | 4.3% | other rural reuse |
| B5 | 5 | 3.5% | other urban reuse |
| A1 | 5 | 3.5% | agricultural reuse (primary) |

**Independent check.** A regex extraction of the `B3` prefix and a plain-text search for
"Industrial cooling" agree on **141 of 141 rows**, with zero disagreements — the classification
is not an artefact of the extraction rule.

**Scale and cost for B3 projects.**

| quantity | n | min | p25 | median | p75 | max |
|---|---:|---:|---:|---:|---:|---:|
| capacity (m³ d⁻¹) | 38 | 120 | 1,050 | **4,000** | 17,500 | 151,400 |
| operating cost (CNY m⁻³) | 40 | 0.047 | 0.600 | 1.950 | 3.655 | 16.15 |
| total unit cost (CNY m⁻³) | 40 | 0.052 | 0.856 | **2.413** | 4.500 | 19.33 |

**Comparison with the modelled domain.** Our model's facility scale is ~10³–10⁵ m³ d⁻¹;
**26 of 38 B3 projects (68.4%) fall inside that range**.

> **Claim limits.** This is a **case collection, not a random sample**: the 28.4% figure
> describes these documented projects and is **not** a national prevalence, and we do not use it
> as a share estimate. The table contains **no demand-side field**, so it cannot inform the
> committed-demand identification problem of §S12, and it carries no hydrological or
> supply–demand time series, so it is **not** calibration data. Its contribution is limited to
> establishing that the use case, its scale and its cost correspond to documented engineering
> practice. (`A39_WP8_外部效度/WP8_报告.md`)

---

## S18. Cooling-water share of industrial withdrawal (added 2026-10-16)

The same public source package provides the **cooling-water share of industrial withdrawal for
39 sectors**.

| statistic | value |
|---|---:|
| min | 0.0000 |
| p25 | 0.0955 |
| median | 0.1844 |
| p75 | 0.3464 |
| max | **0.9896** |
| mean | **0.2580** |
| sectors > 0.5 | 7 |
| sectors > 0.2 | 19 |

The spread is enormous (0.000–0.990), so **a single constant cannot represent all industry**.

> **Provenance of the 0.258 figure.** This work's analysis model had been using **0.258** for
> the cooling-water share without a traceable source. It is now fully traced: it is the **mean
> across the 39 sectors**, and recomputing it from the source column gives
> **0.25799037378455597** — identical to the stored value to the last digit (relative
> difference **0.0**). It sits at roughly the **62nd percentile** of the sector distribution,
> i.e. a mid-to-upper representative value rather than a universal constant, and it understates
> cooling demand in the water-intensive sectors above 0.6.
>
> **Parsing note (recorded).** In that sheet the first row holds the summary-statistic names
> `[NaN, 'Mean', 'Std', 'Min', 'Max']`, so `Mean` sits *under the share column* while
> `Std/Min/Max` occupy the three columns to its right. A naive "match column name to
> statistic" parse reads **all values as NaN**; our first implementation did exactly that and
> was corrected. (`A39_WP8_外部效度/WP9_报告.md`)
>
> **Claim limits.** The source table does not map sector codes to names, and gives no year or
> region scope, so we report codes only and make no industry attribution. Its definition is
> *cooling withdrawal / industrial withdrawal*, which is **not** the same quantity as
> "reclaimed water used for cooling", and the two must not be substituted for one another. It
> contains no demand-side information.

---

## S19. Industrial water tariffs versus reclaimed-water cost (added 2026-10-16)

The source package also contains **city-level tap-water tariffs** by use category
(130 × 342 table; a three-row header: city / fee type / **use category**).

| item | value |
|---|---|
| industrial-tariff series | **62** |
| monthly observations | **7,730** |
| period | 2007-01 – 2017-07 |
| cities aggregated | **61** |
| city median tariff (median across cities) | **1.550 CNY m⁻³** |
| city median tariff range | **0.590 – 6.650** |
| all-observation range | 0.180 – 8.150 |

**Comparison with reclaimed-water cost.**

| quantity | value | source |
|---|---:|---|
| B3 (industrial cooling) total unit cost, median | **2.413 CNY m⁻³** | §S17 |
| industrial tap tariff, cross-city median | **1.550 CNY m⁻³** | this table |
| **ratio (reclaimed / tap)** | **1.56** | — |

Only **17 of 61 city–source observations (27.9%; 31 distinct cities)** have an industrial tariff above the reclaimed-water cost, so
at this level **reclaimed water costs roughly 56% more than industrial tap water**.

> **Reading, and its limits.** This offers a plausible economic reason why reclaimed pools tend
> to be contractually committed rather than idle — when reclaimed water is not cheap, a utility
> has little incentive to reserve it for a new entrant — and it supports the policy conclusion
> that expanding supply does not by itself drive substitution. It is **not causal evidence**:
> the dataset has prices only, with no contracts, allocations or deliveries, so we do **not**
> claim that cost explains occupation. It cannot support any investment or net-present-value
> statement (no lifetimes, discount rates or scale economies), the tariffs are not those of our
> synthetic model domain, and prices are not demand.
>
> **Header-parsing note (recorded).** The use-category names sit in the **third** header row,
> not the second; our first implementation read row 2, found **zero** `Industrial` columns and
> correctly refused to proceed — i.e. it produced `NOT_IDENTIFIABLE` rather than a wrong number.
> The dataset is also far larger than this analysis needed (342 columns), so the aggregation
> step is where errors would hide; we therefore recomputed the headline statistics through an
> independent code path and obtained identical values (n_city = 61, median = 1.55, range
> 0.59–6.65). (`A39_WP8_外部效度/WP10_报告.md`)

---

## S20. Real reclaimed-water capacity deployment (added 2026-10-16)

The source package also contains project-level deployment records (*CWTS Deployment in Urban
Agglomerations*, 597 records) with investment, WWTP expansion, pipeline construction and
**reclaimed-water capacity**.

| quantity | n | zeros | positive | median | p75 | max | total |
|---|---:|---:|---:|---:|---:|---:|---:|
| total investment (10⁴ CNY) | 597 | 0 | **597** | 1.544e4 | 3.073e4 | 4.90e5 | **1.818e7** |
| WWTP scale expansion (m³/d) | 597 | 7 | 590 | 2.50e4 | 5.00e4 | 1.25e6 | 2.767e7 |
| pipeline (m) | 597 | 351 | 246 | 0 | 2.20e4 | 1.50e7 | 5.28e7 |
| **reclaimed-water capacity (m³/d)** | 597 | **586** | **11** | 0 | 0 | 8.00e4 | **3.654e5** |
| effluent-quality upgrade (m³/d) | 597 | 585 | 12 | 0 | 0 | 6.00e5 | 1.327e6 |

**Positive-capacity subset (the only informative reading).**

| quantity | value |
|---|---:|
| projects | **11** |
| **median capacity** | **3.0 × 10⁴ m³ d⁻¹** |
| p75 / max | 4.7 × 10⁴ / 8.0 × 10⁴ |
| total | 3.654 × 10⁵ m³ d⁻¹ |
| within modelled range 10³–10⁵ m³ d⁻¹ | **11/11 = 100%** |
| investment intensity (n = 11) | median **1.14 × 10⁴ CNY per (m³ d⁻¹)** |

> **Two parsing traps, both recorded.** (i) The sheet concatenates **two blocks horizontally
> with an *irregular* offset** — block 1 occupies columns 0–5, column 6 is empty, and block 2
> occupies columns 7–12. Our first implementation assumed a regular stride of 6 and therefore
> read block 2 with a one-column shift, reporting "block 2 has zero valid rows" and concluding
> there were no shared provinces; both statements were wrong. (ii) **586 of 597 rows leave the
> capacity column at zero**, because that column is populated *only when a project includes
> capacity construction*. Its overall median is therefore **0 and uninformative** — an earlier
> draft quoted that zero as a deployment anchor, which was corrected to the positive-only
> distribution above.
>
> **Claim limits.** The two blocks **disagree for six provinces** (e.g. Beijing 73,400 vs 0),
> so they are different project sets and **must not be summed**; we use block 1 only. The sheet
> carries **no year column**, so no deployment *rate* can be derived, and it is a project
> collection rather than a complete inventory, so no national total is claimed. There is **no
> demand-side field**. With no life-span, discount rate or operating cost, **no return or
> net-present-value statement** is made.

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
