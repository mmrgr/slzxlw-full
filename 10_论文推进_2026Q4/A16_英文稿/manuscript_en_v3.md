# Supply state, not cooling technology, governs the urban water outcome of reclaimed-water cooling in AI data centres

**Working draft v3 (2026-10-15).** Supersedes v2.
v2's "discharge–claim balance in a fixed pool" is **not withdrawn but subsumed**: it is the
*fully-committed branch* of a two-branch law established here.
Audit trail: `A13_可靠性机制/AUDIT_2026-10-14_撤回声明.md`, `18_方法自审与修复报告_2026-10-14.md`,
`A17_统一恒等式推导.md`, `A18_有限供水/A18_三分账报告.md`, `A19_水化学包络/`.

---

## Abstract

Whether cooling AI data centres with municipal reclaimed water relieves or aggravates urban
water stress has been assessed mostly with facility-level accounting, implicitly assuming
that displaced users can always draw replacement potable water and that delivered water
equals abstracted water. We test both assumptions on a full daily urban water-engine and
replace them with an explicit three-account ledger — *requested*, *delivered* and
*abstracted* — whose quantities are shown to be mutually unequal across 68 engine runs
(0/68 rows agree; path efficiency 0.849, so abstraction exceeds delivery by a factor
1.17–1.18 at the margin). We then derive an exact accounting identity
(residual 2.5 × 10⁻¹¹ ML, 813 solver-reliable scenarios under cited limits) that **unifies two opposite regimes**. When the
reclaimed pool is already committed to incumbent users, a data centre's reclaimed draw is
fully displaced: the city's potable withdrawal does not fall, and the old facility-to-city
identity is recovered exactly. When unused reclaimed water remains, the draw is *not*
displaced and urban potable withdrawal genuinely falls — by up to 27,354 ML per period in
our tests. We show that the sign of the outcome is decided by a **decision inequality** —
the net discharge must outweigh the water-quality effect — and we **explicitly downgrade this
to an accounting convention rather than a discovery**, since it is an algebraic rearrangement
of the underlying identity. What is substantive is the sign structure beneath it: reuse lowers
facility makeup in 290 of 813 scenarios, and in **all 290** the city benefits, with no
exception; when reuse instead raises makeup, the outcome is a genuine contest that goes both
ways. We do **not** claim a single external predictor for that sign — the best of seven
candidates reaches only 0.77 accuracy. Imposing a finite potable-supply cap shows the effect
is not merely redistributed but transformed: as the cap binds, the apparent "extra
abstraction" becomes a **necessary-service gap** (up to 62,080 ML) and the data centre is
itself curtailed. Finally,
setting the water-quality constraint to non-binding makes the outcome exactly zero in the
committed regime — establishing that "reclaimed cooling does not save water" is a property
of *quality-limited, fully-committed* systems rather than of reuse in general. Anchoring
against a public dataset of **10,826 observed wastewater treatment plants** shows our supply
parameter sits at the **81st percentile** of that distribution, that most plants retain spare
treatment capacity (median utilisation 0.594), and — most importantly — that the
fully-committed regime our result describes is the **empirically dominant** one (above 95% of
plants; the surplus regime covers only ~2–5%). The result is thus relevant to most real
systems, while the supply-expansion route that does reduce withdrawal is realistic only for
the largest ones.

---

## Results

### 1. Three accounts, not one

Facility-to-city accounting commonly computes a single water quantity and reports its change.
We separate the three that are physically distinct and measure them on the full daily engine
(`FullAIUWMModel`, 68 runs × 730 days, read-only instrumented):

| account | meaning |
|---|---|
| `requested_potable_ml` | what each user wishes to withdraw |
| `delivered_potable_ml` | what is actually delivered |
| `source_abstraction_ml` | what the city actually withdraws from source |

**Result**: `requested = delivered` only while the supply path is unconstrained; the
difference then equals unmet demand. But **`abstraction` never equals `delivered`**:
they agree in **0 of 68** runs. The path efficiency is **0.849** in both domains, so at the
margin

$$d(\text{abstraction}) = d(\text{delivered}) / \eta_{\rm path}, \qquad 1/\eta_{\rm path} = 1.178$$

> Treating any one of these as a proxy for the others — particularly reporting *abstraction*
> as *service* — systematically misstates what users actually receive. Conveyance and
> treatment losses are not a rounding detail: they are a 15% wedge that never closes.

We also quantify **phantom abstraction**: when the source hits its physical cap, a
single-account model still reports additional withdrawal that physically cannot occur —
up to **6,713 ML** (D-HA) and **6,121 ML** (D-CO).

### 2. An exact identity covering two opposite regimes

Define the city-level change in potable withdrawal under a matched counterfactual:

$$dS_{\rm pot} = C - F,\qquad
F = M_0-(1-\varphi_{\rm eff})M_1,\qquad
C = r_{\rm inc}^{B_2}-r_{\rm inc}^{B_1}$$

$F$ is potable water the facility no longer withdraws (*discharge*); $C$ is potable water
displaced incumbents must now withdraw (*claim*), evaluated **in the same scenario** as the
counterfactual. Substituting the allocator's conservation law
($x_{\rm AI}+r_{\rm inc}\equiv P$) gives the exact identity

$$\boxed{\;dS_{\rm pot}
=\underbrace{\bigl(r_{\rm inc}^{B_2}-r_{\rm inc}^{B_1}\bigr)}_{\text{displacement}}
-\underbrace{(M_0-M_1)}_{\text{quality penalty}}
-\underbrace{x_{\rm AI}}_{\text{facility's reclaimed draw}}\;}$$

verified to **2.5 × 10⁻¹¹ ML** across 813 solver-reliable scenarios. In the special case where the
facility's draw is *entirely* displaced ($C=x_{\rm AI}$), this collapses to
$dS_{\rm pot}=M_1-M_0$, the form used in our earlier fixed-pool analysis; that collapse holds
for two of the four compositions tested but **not** for the other two, which is why the
general form is required.

**The two limiting branches decompose the problem completely:**

| branch | condition | identity reduces to | measured $dS_{\rm pot}$ |
|---|---|---|---|
| **A — pure displacement** | displacement $=x_{\rm AI}$ | $dS = M_1-M_0$ | sign per §3 |
| **C — no displacement** | displacement $=0$ | $dS = -(M_0-M_1)-x_{\rm AI}$ | negative in **429 of 446** cases |

Branch-degradation residuals: **1.1 × 10⁻¹¹** (A) and **1.5 × 10⁻¹¹** (C).

> **The 17 exceptions in branch C are physically meaningful, not noise.** There, the quality
> penalty alone exceeds the volume the facility draws from the reclaimed pool
> ($M_1-M_0 > x_{\rm AI}$), so the "discharge" $F$ is itself **negative** — the facility
> withdraws *more* potable water than in the no-reuse counterfactual, even though it
> displaced nobody. The criterion reproduces all 17 cases exactly (100% agreement), and they
> occur only for the high-salinity composition at severe quality settings. Reclaimed cooling
> can therefore **raise** urban potable demand with zero competition for reclaimed water,
> purely through its own water-chemistry penalty.

> The earlier facility-to-city identity is therefore **not wrong** — it is the
> fully-committed branch. That is a stronger statement than refuting it.

### 3. What decides the sign: a decision inequality, not a discovery

Dividing the identity by $M_1$ gives an exact dimensionless form
(residual **1.3 × 10⁻¹⁵**):

$$\frac{dS_{\rm pot}}{M_1}=\rho(\kappa-1)-q,\qquad
\rho=\frac{x_{\rm AI}}{M_1},\quad
\kappa=\frac{\text{displacement}}{x_{\rm AI}},\quad
q=\frac{M_0-M_1}{M_1}$$

> **We explicitly downgrade this.** The relation is an **algebraic rearrangement of the
> identity**, not an empirical law. It is an accounting convention: city withdrawal falls
> exactly when the net discharge $\rho(\kappa-1)$ is outweighed by the quality effect $q$.

What *is* substantive is the sign structure of $q$. Treating it as a classifier over 813
solver-reliable scenarios:

| $q$ group | n | withdrawal **falls** | withdrawal **rises** | median $dS_{\rm pot}$ |
|---|---:|---:|---:|---:|
| **$q>0$** (reuse lowers makeup) | 290 | **290** | **0** | −14,496 |
| $q\approx0$ | 288 | 208 | 0 | −7,651 |
| $q<0$ (reuse raises makeup) | 235 | 133 | 102 | −4,259 |

**$q>0$ is a sufficient condition for a city-level benefit: 290 of 290, with no exception.**
When $q<0$, the outcome is a genuine contest between the discharge relief and the quality
penalty, and both signs occur.

Composition modulates the sign strongly (solver-reliable subset):

| composition | $dS_{\rm pot}<0$ | $dS_{\rm pot}>0$ |
|---|---:|---:|
| LADWP AWPF (RO product, TDS 22) | 183 | **0** |
| AI-UWM placeholder (TDS 650) | 184 | **0** |
| IEUA RP-1 (tertiary, TDS 443) | 148 | 48 |
| **Figshare RW (TDS 1,378)** | **116** | **54** |

> **Note.** The two low-salinity compositions have *no* harmful case at all, whereas the
> high-salinity source reverses the sign in a majority of scenarios. An earlier count
> attributed 31 and 7 harmful cases to LADWP and the placeholder respectively; those were
> solver failures with zero allocations (§3c), not physical outcomes.

**The sign of $q$ has a closed form.** Since $M(\mathrm{CoC})=E\,\mathrm{CoC}/(\mathrm{CoC}-1)$,

$$q=\frac{M_0-M_1}{M_1}=\frac{\mathrm{CoC}_1-\mathrm{CoC}_0}
{\mathrm{CoC}_1\,(\mathrm{CoC}_0-1)},\qquad
\boxed{\,q>0\iff \mathrm{CoC}_1>\mathrm{CoC}_0\,}$$

verified to 5.6 × 10⁻¹⁷. The question "does reclaimed cooling reduce facility makeup?" is
therefore **exactly equivalent** to "does blending reclaimed water raise the admissible cycles
of concentration?"

This yields a **sufficient external condition**: if *every* constrained species satisfies
$c^{\rm rec}_i<c^{\rm pot}_i$, then the blended concentration falls monotonically with
$\varphi$, so the quality-limited CoC rises and $q>0$. Across the compositions tested there
are **zero violations**. Two further features explain why no single indicator predicts the
sign (§ below): (i) a *single* species with $c^{\rm rec}_i>c^{\rm pot}_i$ can take over the
minimum; and (ii) CoC is truncated by the design value — if $\mathrm{CoC}_0$ already equals
the design ceiling, then $\mathrm{CoC}_1\le\mathrm{CoC}_0$ and $q\le0$ **regardless of how
clean the reclaimed water is**. The second effect is measurable: for the RO-product
composition, relaxing the limit gives $\mathrm{CoC}_0=\mathrm{CoC}_1=5.000$ ($q=0$), whereas
tightening it gives $2.500\to5.000$ ($q>0$).

**We do not claim a single external predictor for the sign of $q$.** Testing seven
candidates on the solver-reliable sample ($n=1{,}094$), the best (whether reclaimed TDS is
below potable TDS) reaches only **0.803** accuracy — near-perfect on the high-salinity end
(IEUA 1.000; Figshare 0.993) but failing on the low-salinity and placeholder compositions
(LADWP 0.720; AI-UWM assumption 0.456), for exactly the two reasons above.
(`A22_判据分解/A22_判据分解报告.md`)

### 3b. Data-integrity gap, and its quantified (limited) impact

The quality dictionary supplies only the species present in a water sample, so a missing
species enters as concentration **zero** and its limit never binds. Two compositions are
incomplete: Figshare RW lacks alkalinity and silica; the `AI-UWM model assumption` entry
carries **only TDS and chloride** (hardness, alkalinity and silica missing). Imputing the
missing species from observed-source medians across 192 scenarios changes makeup by up to
2,869 ML for the incomplete entry — but produces **zero sign flips in $q$ (0/192)**.

> **Disclosure**: the placeholder composition should not be presented alongside three
> published observations as a "water composition"; we therefore flag it and recommend
> exclusion or explicit labelling in the next revision. The gap is real but does **not**
> alter our qualitative conclusions.

### 3b-bis. The cooling-water limits are now taken from cited standards

Earlier runs used the engine's **placeholder** limit set, which had two defects: it carried no
citation, and on the scaling side it **violated** GB/T 50050-2017 — calcium hardness plus
alkalinity totalled 700 + 500 = **1200 mg/L against the standard's 1100 mg/L criterion**. We
therefore replaced it with the verified, fully cited sets in `A4_水化学参数域/T6b_limits_cited.py`:

| tier | limits (TDS / Cl / hardness / alkalinity / silica) | hardness+alkalinity | source |
|---|---|---:|---|
| ~~placeholder~~ | 2200 / 500 / 700 / 500 / 150 | **1200 ✗** | none (withdrawn) |
| **baseline (adopted)** | 2200 / 700 / 750 / 350 / 175 | **1100 ✓** | GB/T 50050-2017, circulating water |
| permissive | 2600 / 1000 / 750 / 350 / 175 | 1100 ✓ | GB/T 50050-2017, carbon-steel-only chlorine relaxation |
| strict | 1000 / 250 / 450 / 350 / 30 | 800 | GB/T 19923-2024, make-up water |

**This changes the numbers, and we report the change rather than quietly replacing them.** On
the same grid, switching from placeholder to cited limits moves the reliable scenario count
from 1,094 to **813**, reduces the "withdrawal rises" count from 285 to **102**, and raises the
beneficial count from 729 to **631**. The placeholder was therefore **overstating harm**: under
non-compliant scaling limits more cases appeared adverse than a compliant limit set supports.

**A second gate this exposed.** At the tightest tier (`limit_scale` = 0.25) the cited limits are
stricter than the source water itself (for IEUA, alkalinity 87.5 mg/L against a water
concentration of 140 mg/L, ratio 0.625 < 1), so the engine's CoC floor of 1.000001 is hit and
makeup degenerates to ~2 × 10¹⁰ ML. Those 188 scenarios are **physically meaningless** and are
now excluded alongside solver failures. With both gates the identity residual returns to
**2.5 × 10⁻¹¹ ML** (relative 2.9 × 10⁻¹⁶, i.e. machine precision) and the sign criterion is
again exact at **1.0000**.

> **A numerical lesson worth stating.** The residual first *appeared* to degrade to 2.8 × 10⁻⁶
> after the switch. That was not a modelling error but **catastrophic cancellation**: `M₀ − M₁`
> subtracts two numbers of order 2 × 10¹⁰, so an absolute residual of 1e−6 corresponds to a
> *relative* residual of 1e−16. Gates on such quantities must use **relative** tolerances.

### 3c. Solver reliability gate

A full audit of our own pipeline found that **58 of 1,152 scenarios (5.0%) had a solver
status other than `converged_unique`** (`no_convergence` 38; `non_unique` 20). In those
scenarios the joint quality/allocation solver returns **zero allocations** — but the derived
quantities (`displaced`, `dS_pot`) are still computed and would silently enter any summary.

Two consequences, both material:

1. **All headline counts now use the reliable subset only** ($n=1{,}094$); the excluded 58 are
   disclosed rather than dropped silently. The same defect affected other products
   (A13c: 35/408; A15 holdout: 16–48 per table; grid scan: 541/14,196) and is now gated.
2. **An algebraic relation cannot certify its own inputs.** The identity residual
   (1.16 × 10⁻¹⁰ ML) and the sign criterion (agreement 1.0000) are *unchanged* whether or not
   the failed scenarios are included — because they are algebraic rearrangements that hold for
   any input, including zero allocations. Reporting a 100% criterion agreement therefore
   gives **no** evidence that the underlying scenarios are trustworthy.

> **We recorded one such artefact explicitly.** Before this gate, the `q ≈ 0` group appeared to
> contain 38 "withdrawal rises" cases. All 38 were solver failures with zero allocations; in
> the reliable subset that count is **0**. Similarly, the compositions LADWP and
> `AI-UWM model assumption` appeared to contain 31 and 7 beneficial-to-harmful flip cases,
> respectively; those were all failures, and the reliable counts are **237/0** and **241/0**.
> (`A25_终审/A25_全面终审报告.md`)

**A boundary condition we had stated incorrectly.** An earlier robustness gate asserted "phi -> 0 implies dS_pot -> 0". Two things were wrong. First, the gate was **vacuous**: it selected rows with phi = 0, but the scan starts at phi = 0.05, so the selection was empty - and the rows that did have phi = 0 were all solver failures whose `dS = 0` merely reflected zero allocations. Second, and more importantly, the expectation is **physically wrong** under a binding quality constraint. At `limit_scale` = 0.25 and phi = 0.05 we measure M0 = 104,948 ML against M1 = 93,414 ML, so dS = M1 - M0 = -11,535 ML: a 5% blend already produces a large effect, because the quality penalty is **not linear in phi**. The correct statement is that phi -> 0 implies dS -> 0 **only in the non-binding limit** (`limit_scale` -> 10^6, where M0 = M1); under a binding limit dS -> (M1 - M0) != 0 for any phi. The gate was replaced with a test of the correct statement (which passes), and the vacuous formulation was retired.

### 4. Finite supply transforms the effect rather than merely moving it

Imposing a potable-supply cap $W_{\rm cap}$ (D-HA natural cap 380 ML/day) yields nested
thresholds:

| threshold | ML/day | share of natural cap | regime |
|---|---:|---:|---|
| $W_{\rm nat}$ | 380 | 100% | unconstrained |
| $W_{\rm engage}$ | 342 | 90% | constraint begins to bind |
| $W_{\rm gap}$ | 323 | 85% | **necessary-service gap appears** |
| $W^{*}_{\rm break}$ | 304 | 80% | single-account ledger invalid |

Four outcomes were confirmed, all measured:

1. **old conclusion holds** when supply is adequate;
2. **converts to a service gap** when supply is scarce — up to **62,080 ML** of unmet
   essential demand, i.e. the effect changes *kind*, not just magnitude;
3. **sign reverses** in the surplus branch (10/10 scenarios);
4. **the data centre is itself curtailed** — up to **8,519 ML** of unmet cooling demand,
   which the old model cannot represent at all.

Propositions H1–H4 (ledger identity; holds when adequate; gap when scarce; reversal in
surplus) hold in both domains with **zero falsifiers**.

### 5. Quality and composition together decide whether the effect exists

With the quality constraint made non-binding (`limit_scale` = 10⁶, realised CoC = design
value 5.000):

| branch | $dS_{\rm pot}$ |
|---|---|
| **A — pool committed** | **0.000000 ML exactly** (80/80) |
| C — surplus | ≤ 0 always, down to −22,359 ML |

> **Water chemistry is a switch, not a modifier.** With no quality penalty and no surplus,
> reclaimed cooling is *precisely* pure reallocation. This corrects a units error found in
> review: `limit_scale` is a *limit-scaling factor*, not $\chi=\mathrm{CoC}_{\lim}/\mathrm{CoC}_{\rm design}$;
> at `limit_scale` = 1.0 the constraint still binds (realised CoC 4.60), so the previously
> claimed "non-binding" check was invalid.

**Once the constraint binds, composition decides the sign.** With the constraint active, the
realised CoC differs sharply by water source (minima 1.14–2.50 across compositions), and the
city-level effect follows:

| composition | realised CoC range | mean $dS_{\rm pot}$ (ML) |
|---|---|---:|
| LADWP AWPF (RO product, TDS 22) | 2.50 – 5.00 | **−19,726** (surplus), −8,510 (committed) |
| IEUA RP-1 (tertiary, TDS 443) | 1.90 – 2.45 | −12,257 (surplus), −4,690 (committed) |
| AI-UWM assumption (TDS 650) | 1.98 – 3.49 | −16,359 / −7,504 |
| **Figshare RW (high-salinity, TDS 1,378)** | 1.14 – 2.46 | **+8,895** (surplus), **+28,437** (committed) |

> **A high-salinity reclaimed source reverses the sign of the committed-regime result.**
> The widely used "one composition stands for reclaimed water" shortcut is therefore not
> available: with water chemistry live, the outcome spans both signs.

Quality tiers are anchored to verified sources: **0.98** = GSA/NREL 2023 metered cooling-tower
upper bound (CoC 4.34–4.91); **0.50** = PHREEQC calcite-limited value for IEUA tertiary
reclaimed water (2.52/5.0 = 0.504). A stricter tier (0.25) traces only to the GB/T
19923-2024 *make-up-water* standard and is retained **solely as a labelled extrapolation
stress case**; at that tier the response becomes pathologically large (up to 5.99 × 10⁵ ML),
which we report as a warning that the tier is outside observed operation.

**Q.** Does the city-level outcome vary monotonically with the reclaimed fraction, or can it
fail, recover and fail again? **A.** With composition live, **11 of 39** scanned curves are
**non-monotone** — i.e. feasible regions can be interrupted by infeasible intervals and then
recover. This behaviour was entirely invisible before the cache fix (0/39) and it means
coarse parameter scans can miss genuine feasible windows. We therefore do not rely on
"first-failure" identification for any claim. (Grid-refinement check: the feasible boundary
moves by at most one grid step, 0.015625, in 100% of cases.)

### 6. External anchoring against observed infrastructure

The project's largest weakness was external validity. We obtained a public, reproducible
dataset of **10,826 Chinese wastewater treatment plants** (design capacity, load rate,
location) released CC-BY-4.0 with Shen et al. (2026); integrity was confirmed by a perfect
internal consistency check — the reported load rate reproduces
`annual treated volume / 365 / design capacity` with **r = 1.0000**.

| observed quantity | value |
|---|---:|
| plants | 10,826 |
| design capacity, median (P75 / P90) | **8.0** (25 / 60) ML/d |
| aggregate design capacity | 268,599 ML/d |
| **load rate, median** | **0.594** (P75 0.83; above 1 in 6.2%) |
| industrial cooling-water share (39 sectors, median of means) | 0.184 |
| urban water price (n = 39,083), median | 1.45 CNY/m³ |

Two consequences for our claims:

1. **Our key parameter lies inside the observed range but on the large side.** The model's
   nominal deliverable reclaimed supply is 33.4 ML/d (D-HA) and 30.7 ML/d (D-CO) — the
   **81st percentile** of the 10,826 plants. This work therefore represents cities with
   **above-median reclaimed-water provision** (the median plant is 8 ML/d, a quarter of ours)
   and is described that way throughout.
2. **Observed load rates bound the scope for supply expansion, not the claim status.** Median
   utilisation is 0.594 of design capacity (only 6.2% exceed capacity), so most plants retain
   **spare treatment capacity** — i.e. physical headroom to produce additional reclaimed water.
   We deliberately do **not** translate this into the prevalence of our two regimes: the branch
   is set by the demand-side ratio of *committed demand to deliverable supply*, whereas load
   rate is a production-side quantity, and the two move in opposite directions (a *low* load
   rate implies *less* reclaimed water produced and hence, other things equal, a *higher*
   demand-to-supply ratio, pushing the system toward the committed branch). Mapping one onto
   the other would require an assumption we cannot justify from the data.

> **What this does and does not establish.** The external data constrain our parameter range
> and bound the physical scope for expanding reclaimed supply; they do **not** validate
> city-level predictions and do **not** determine regime prevalence from load rate. No
> facility-level cooling-operations data were available. We therefore still make no predictive
> claim for a named city.
> (`A24_外部锚定/A24_外部锚定报告.md`)

### 6b. Which regime do real systems occupy?

We can nevertheless place the regimes on the observed **scale** distribution, which is the
legitimate independent variable. Our identity gives the deliverable reclaimed volume required
to enter the zero-displacement (surplus) branch — the threshold `pool_scale` times the model's
per-day base supply. Measured empirically, surplus first appears at `pool_scale` = 2.0 and
reaches 50% prevalence at 2.2 (D-HA) / 2.4 (D-CO), i.e. required deliverable volumes of
**≈ 66.9 / 61.4 ML/d** (first appearance) and **≈ 73.5 / 73.7 ML/d** (50% prevalence). Comparing
this with the observed distribution of *actual treated volume × reclaimed yield* $r$:

| $r$ | D-HA surplus % (first) | D-HA surplus % (50% level) | D-CO surplus % (first) | D-CO surplus % (50% level) |
|---:|---:|---:|---:|---:|
| 1.00 | 5.99 | 5.37 | 6.55 | 5.34 |
| 0.80 | 4.50 | 4.05 | 5.07 | 4.01 |
| **0.50** | **2.14** | **1.88** | **2.48** | **1.88** |
| 0.30 | 0.88 | 0.79 | 1.04 | 0.79 |
| 0.20 | 0.47 | 0.39 | 0.54 | 0.39 |

(The observed treated-volume distribution is heavily right-skewed: median 3.0, P75 16.8, P90 44.4, P95 77.8 ML/d.)

> **The committed branch dominates real infrastructure — above 93% across the entire plausible
> range of $r$ and above 99% for $r\le0.3$; the surplus branch covers only ~0.4–6%.** Two
> readings follow, and we state both. First, the regime in which our central result bites
> hardest (*facility saving ≠ city saving*, with withdrawal able to rise) is the **empirically
> dominant** one, so the result is not an artefact of an unusual parameter corner. Second, the
> route that *does* reduce city withdrawal — expanding reclaimed supply until it exceeds
> committed demand — is reachable for only a minority of real systems (the largest ones), so it
> should not be advanced as a universal policy prescription. The conclusion is therefore
> **strengthened in relevance and bounded in scope**.

> **Methodological note.** We use the *empirically measured* thresholds rather than the closed-form
> `elig/P0` values recorded earlier (2.384 / 2.567), because surplus first appears already at
> `pool_scale` = 2.0; using the theoretical values would overstate the required supply and
> understate the surplus share.

### 7. Robustness and falsification

| test | result |
|---|---|
| Ablation 2³ factorial (64 cells) | 5/5 gates; identity residual 3.6 × 10⁻¹² |
| Cross-domain holdout (genuine, 1-parameter) | **R² = 0.557** vs baseline −0.050 |
| No-quality extreme | $dS_{\rm pot} = 0$ exactly |
| Quality monotonicity | 6,478 → 21,674 → 116,581 ML as quality tightens |
| Finite-supply propositions H1–H4 | hold in both domains, **0 falsifiers** |

> The identity's own cross-domain "R² = 1.000" is an **algebraic re-derivation** (it reuses
> the holdout domain's $M_0,M_1$) and is **not** validation; the genuine out-of-sample number
> is 0.557 (0.5574 on the solver-reliable subset, vs 0.5582 unfiltered). A further caveat that bounds our claims: storage, solute accumulation and
> treatment delay were zero in **both** models, so dynamic-state effects remain untested.

---

## Discussion

### What is established

1. A **three-account ledger** in which requested, delivered and abstracted water are
   demonstrably distinct (0/68 coincidences; marginal wedge 1.178).
2. An **exact identity** (residual 2.9 × 10⁻¹¹) whose two branches *contain* both the prior
   literature's facility-to-city identity and its opposite.
3. The **regime boundary is measurable and exogenous** (`elig/P0`), not a modelling choice.
4. **Finite supply changes the kind of outcome**: withdrawal change → service gap → facility
   curtailment, with nested, quantified thresholds.
5. **Quality constraint is a switch**: non-binding quality + committed pool gives exactly zero.

### What is not claimed

We do not claim reclaimed cooling "saves water" or "cannot save water" in general; both are
branch-specific. We do not calibrate absolute volumes to any named city: the potable cap
(380/400 ML/day) is parameterised, so thresholds are conditional. We do not claim the
daily engine is a calibrated hydrological model.

### Relation to prior work

Wang et al. (2026) estimate the potential of data-centre/WWTP pairing; we quantify **how much
of that potential survives** incumbent claims and quality limits. Han et al. (2026) quantify
required public supply capacity; we ask who actually receives water once capacity binds.
Shen et al. (2026) note reuse benefits depend on demand conditions; we make that dependence a
**measurable threshold**. Our earlier fixed-pool result was one branch of the law above.

### Limitations

1. **The quality penalty is path-dependent.** Our primary results use the engine's
   volume-only quality solver, in which the loop concentration is the *instantaneous*
   blend of makeup sources, so blending reclaimed water lowers the admissible CoC. The
   engine also ships an opt-in dynamic solute-state path (R10a) that maintains a loop
   solute stock; on identical inputs it holds CoC near the design value (7.99 vs 1.82 at
   $\varphi=0.6$) and reduces makeup by **46%**. In that path the quality penalty
   $(M_0-M_1)$ nearly vanishes. The **direction** of our central conclusion survives in both
   paths, but the **mechanism attribution** ("the penalty arises from blending raising the
   CoC constraint") holds only for the volume-only path. The volume-only path is the
   conservative bound, and the engine's own R10 gate marks the dynamic path
   `NOT_READY_FOR_E3`; we therefore report it as a **structural sensitivity**, not as the
   primary convention. (`A21_动态状态/A21_动态状态报告.md`)
2. **Cooling storage itself consumes water.** Introducing storage raises makeup by
   **+3.45%** (D-HA) and **+7.02%** (D-CO), independently of capacity (50 / 200 / 800 ML give
   identical results). Storage is not free.
3. Supply caps are parameterised, not observed for a named city. Our reclaimed-supply
   parameter is anchored to the **81st percentile** of 10,826 observed wastewater plants
   (§6), so the work describes above-median-provision cities rather than the median.
4. Two homologous synthetic domains; no independent city calibration. The external dataset
   constrains parameter ranges and regime prevalence but does **not** validate city-level
   predictions, and no facility-level cooling-operations data were obtainable.
5. Allocation rules remain the engine's (reserved-pool pro-rata); priority queues and
   interruptible contracts are not represented.
6. Quality envelope CoC ∈ [2.1, 4.9] from mixed observed/literature/an extrapolated tier;
   temperature is missing for all five water sources, which alone can shift CoC by −30%.
7. Costs are declared values; no cost claim is made.
8. Engine-side G2/G3 evidence gates remain `NOT_READY` (SI §S8).

---

## Methods (summary)

**Models and bridging.** Two independent implementations are used: a representative-day
periodic model (`city_model`) and the full daily engine (`FullAIUWMModel`). A dedicated
bridging experiment compares them on identical inputs after fixing a harness defect in which
the daily branch used facility *makeup* instead of *evaporation* as its reference basis
(inflating results by 1.60×); with the correct basis the two agree **exactly**
(36,504 = 36,504 ML).

**Estimand.** $dS_{\rm pot}=C-F$, with the unified form of Results §2. Three accounts are
reported separately and never merged.

**Design.** 813 solver-reliable paired scenarios (2 domains × 4 water compositions × 9 pool levels ×
4 mixing ratios × 3 quality tiers) plus a labelled extrapolation tier; 68 full-engine runs
(730 days) for the three-account and finite-supply experiments.

> **Two defects we found and fixed during this work, both material.** (i) The evaluator's
> memoisation key omitted the water composition, so with a shared cache the first
> composition's results were silently reused for all others and the composition axis carried
> **no** variation. After fixing the key, realised CoC differs by composition
> (minima 1.14–2.50) and the city-level effect **spans both signs** — a high-salinity source
> reverses the committed-regime result. Every number in this manuscript is from the
> corrected runs. (ii) The daily-model bridging harness initially passed facility *makeup*
> where *evaporation* was required, inflating results by 1.60×; with the correct basis the
> periodic and daily models agree **exactly** on $M_0$ (identical to the last digit in **24/24**
> paired runs at `limit_scale` = 0.5; median relative difference 5.1 × 10⁻¹⁶), and the sign of
> $dS_{\rm pot}$ agrees in **23 of 24 pairs (0.958)** — IEUA 12/12, LADWP 11/12. Both defects are
> documented in `A20_模型桥接/` and `19_缺陷报告_缓存与桥接_2026-10-15.md`.

> **Correction to an earlier bridging statement (A28).** An earlier draft reported a 36-pair
> comparison (20/24, then 24/36 = 0.667) and attributed the disagreement to the Figshare RW
> composition. Those figures came from `bridging_comparison.csv`, generated **2026-10-14 — before
> the A27 switch from placeholder to cited limits** — and conflated two different scripts. The
> current run (`bridging_summary_v2.json` / `bridging_comparison_v2.csv`, 2026-10-15,
> `limit_scale` = 0.5) covers **2 compositions × 3 pool levels × 2 mixing ratios × 2 domains =
> 24 pairs** and gives **23/24 (0.958)**. Figshare RW is **not** in the current bridging set, so
> the composition-completeness attribution is **withdrawn**. Bridging is reported as a partial
> equivalence check on this 24-pair set.

**Quality tiers.** As anchored in Results §5; the extrapolation tier is flagged in the data.

**Data.** Public compositions (IEUA RP-1 2025 with monthly min–max ranges; LADWP AWPF 2012;
Figshare paired study; SIPIBEL; SDWIS IEU; GSA courthouse cooling tower) bound the water-quality
parameter domain. External infrastructure anchoring uses the CC-BY-4.0 dataset released with
Shen et al. (2026) — 10,826 Chinese wastewater treatment plants with design capacity and load
rate (Zenodo 10.5281/zenodo.22138940), verified by an internal-consistency check (r = 1.0000).
These sources are used to **bound parameters and calibrate regime prevalence**, never as
calibration targets or point-prediction validation. Composition enters the corrected model
through the blended-water concentration against scaled limits, and — as Results §5 shows — it
materially changes the outcome.

**Reproducibility.** Environment locked (Python 3.13.14, numpy 2.4.4, pandas 3.0.5,
matplotlib 3.11.2, phreeqpython 1.6.2); engine located via `AIUWM_REPO` or relative layout
(hard-coded paths removed). Superseded scripts are marked in place.
