# What Governs the Urban Water Outcome of Reclaimed-Water Cooling in AI Data Centres? Competition, Water Chemistry and the Limits of Prediction

**Working draft v4 (2026-10-16).** Supersedes v3.
v4 changes are **substantive and include withdrawals**; see `A30_WP0取证/` for the audit trail
(evidence ledger, headline-count convention, partial identification) and
`A31_WP2_假设冻结/`, `A32_WP3_水化学/`, `A33_WP4_组成重构/` for the new experiments.
v2's "discharge–claim balance in a fixed pool" is **not withdrawn but subsumed**: it is the
*fully-committed branch* of a two-branch law established here.
Audit trail: `A13_可靠性机制/AUDIT_2026-10-14_撤回声明.md`, `18_方法自审与修复报告_2026-10-14.md`,
`A17_统一恒等式推导.md`, `A18_有限供水/A18_三分账报告.md`, `A19_水化学包络/`.

---

## Abstract

Cooling AI data centres with reclaimed water is usually assessed by facility-level accounting,
assuming displaced users can always find replacement potable water and that delivered
water equals abstracted water. Testing both on a daily engine, we replace them with a ledger — *requested*, *delivered*, *abstracted* — unequal in all 68 engine runs,
and derive an exact identity (residual 2.5 × 10⁻¹¹ ML, 839 solver-reliable scenarios) unifying
two regimes: where the reclaimed pool is committed to incumbents, a data centre's draw is fully
displaced and city withdrawal does not fall; where unused reclaimed water remains, withdrawal
genuinely falls. The sign follows from competition between a quality term, predictable from
pre-intervention chemistry, and a displacement term needing demand-side data. A chemistry-only
criterion predicts that sign no better than chance (0.67 versus a 0.81 baseline), so the widely quoted "sign-criterion agreement" is an accounting check rather than a prediction; adding one
pre-intervention demand-side quantity raises in-sample accuracy to 0.91 and gives a **median
fold gain of +0.09** — with two of four folds informative, a candidate. Sensitivity analysis
finds one sign lever within the cited limits — reclaimed-water alkalinity — but it is **not
panel-invariant**: under a stricter make-up-water tier the binding species shifts and no
single-species perturbation flips the sign. Heatwaves and droughts change it by ≤1.14×
without reversing the outcome, whereas a binding supply cap converts the effect into a service gap
and curtails the data centre. Among **10,826 observed wastewater plants** the committed share is **not identified** (provable bounds [0%, 100%]) and only ~2–6% could support a surplus
scheme; among **141 documented reclaimed-water projects, industrial cooling is the largest use
category (28.4%)**, 68% inside our modelled scale. Because the mechanism's magnitude is
**solver-path dependent by ~800×**, we keep our conclusions' direction but treat the mechanism
attribution as convention-dependent.

---

## Introduction

Data centres consume water chiefly for cooling, and that demand is growing fast enough that
utilities now plan around it. Facility- and fleet-level accounting has quantified the volumes
involved (Mytton & Haslam, 2021; Siddik et al., 2021; Lei et al., 2025) and the energy, water
and carbon consequences of AI growth have been projected under alternative scenarios
(Xiao et al., 2025). Impacts on *public* supply have also been documented: Han et al. (2026)
estimate the supply capacity data centres require, and Alston et al. (2026) show that cooling
technology choices shift where those impacts fall. Reusing municipal reclaimed water is widely
advanced as the mitigation — it is treated as a way to satisfy a new demand without adding
pressure to potable supply — and is matched against the scale of wastewater treatment
(Wang et al., 2026).

Two assumptions are usually left implicit in that reasoning. The first is that water
displaced from one user is taken up by another, so that a facility-level saving is also a
city-level saving; in practice reclaimed water is frequently already allocated to incumbent
users under contract. The second is that the water a facility is *delivered* equals the water
it *abstracts* from the shared source; in a network with losses and competing claims these are
different quantities. Where either assumption fails, facility-level arithmetic cannot
establish the city-level outcome.

A third difficulty is specific to reclaimed water and has received less attention. Reclaimed
water is not interchangeable with potable water: its ionic composition sets how far it can be
concentrated in a cooling loop before scaling or corrosion limits are reached. Field evidence
shows reclaimed water can *raise* the achievable cycles of concentration
(Badruzzaman et al., 2022), so the direction of this effect is not fixed a priori, and its
consequences for a city's net abstraction are therefore not obvious.

This paper asks what actually governs the urban water outcome of reclaimed-water cooling, and
whether that outcome can be predicted from information available *before* an intervention.
We proceed in four steps. We replace single-quantity facility accounting with an explicit
three-account ledger measured on a daily urban water engine, and derive the exact identity
relating the accounts. We then identify the regime structure of that identity and the
conditions under which reuse lowers or raises city withdrawal. Next we test the sign
criterion the way a prediction problem should be tested — using only pre-intervention
observables, with explicit baselines and fold-wise validation — and report where it succeeds
and where it fails. Finally we anchor the modelled quantities against public records of real
wastewater plants, reclaimed-water projects, tariffs and capacity deployment. Throughout we
distinguish what is a conservation identity, what is an accounting check, and what is an
empirical finding, and we report the several claims that our own tests did not support.

## Results

### 1. Three accounts, not one

(**Figure 1** maps the study boundary, the three counterfactuals B0/B1/B2 and the
three-account ledger developed in this section.)

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

verified to **2.5 × 10⁻¹¹ ML** across 839 solver-reliable scenarios. In the special case where the
facility's draw is *entirely* displaced ($C=x_{\rm AI}$), this collapses to
$dS_{\rm pot}=M_1-M_0$, the form used in our earlier fixed-pool analysis; that collapse holds
for two of the four compositions tested but **not** for the other two, which is why the
general form is required.

**The two limiting branches decompose the problem completely:**

| branch | condition | identity reduces to | measured $dS_{\rm pot}$ |
|---|---|---|---|
| **A — pure displacement** | displacement $=x_{\rm AI}$ | $dS = M_1-M_0$ | 232 cases; both signs occur |
| **C — no displacement** | displacement $=0$ | $dS = -(M_0-M_1)-x_{\rm AI}$ | negative in **369 of 372** cases |

Branch-degradation residuals: **1.27 × 10⁻¹¹** (A) and **1.46 × 10⁻¹¹** (C), i.e. relative
**2.0 × 10⁻¹⁶** and **1.6 × 10⁻¹⁶** — machine precision. *(Earlier drafts quoted "429 of 446"
and "17 exceptions"; those came from the pre-A27 placeholder limit set and from a pooled
sample that mixed in solver-failed rows. Under the cited limits and the dual gate the
authoritative counts are 372 branch-C cases with 3 exceptions.)*

> ***The 3 exceptions in branch C are physically meaningful, not noise.** There, the quality penalty alone exceeds the volume the facility draws from the reclaimed pool ($M_1-M_0 x_{\. Full details in SI S10.*

> The earlier facility-to-city identity is therefore **not wrong** — it is the
> fully-committed branch. That is a stronger statement than refuting it.

### 3. What decides the sign: a decision inequality, not a discovery

(**Figure 3** gives the sign structure of the city-level outcome and the $q$-group counts.)

Dividing the identity by $M_1$ gives an exact dimensionless form
(residual **1.3 × 10⁻¹⁵**):

$$\frac{dS_{\rm pot}}{M_1}=\rho(\kappa-1)-q,\qquad
\rho=\frac{x_{\rm AI}}{M_1},\quad
\kappa=\frac{\text{displacement}}{x_{\rm AI}},\quad
q=\frac{M_0-M_1}{M_1}$$

> **We explicitly downgrade this.** The relation is an **algebraic rearrangement of the
> identity**, not an empirical law. It is an accounting convention: city withdrawal falls
> exactly when the net discharge $\rho(\kappa-1)$ is outweighed by the quality effect $q$.

What *is* substantive is the sign structure of $q$. Treating it as a classifier over 839
solver-reliable scenarios, under the **strict** sign convention applied consistently with the
rest of this paper:

| $q$ group | n | withdrawal **falls** | withdrawal **rises** | exactly zero | median $dS_{\rm pot}$ |
|---|---:|---:|---:|---:|---:|
| **$q>0$** (reuse lowers makeup) | 263 | **263** | **0** | 0 | −17,264 |
| $q\approx0$ | 288 | 220 | **32** | 36 | −7,651 |
| $q<0$ (reuse raises makeup) | 288 | 143 | 145 | 0 | 200 |

Under the strict sign convention the pooled counts are **626 beneficial / 177 harmful /
36 exactly zero** ($n=839$). **$q>0$ is a sufficient condition for a city-level benefit:
263 of 263, with no exception.**
When $q\le0$, the outcome is a genuine contest between the discharge relief and the quality
penalty, and both signs occur.

> ***Correction (v4, after red-team review).** An earlier version of this table quoted `rises = 0` for the $q\approx0$ group and its columns summed to 733 rather than the pooled $n$. Full details in SI S10.*

Composition modulates the sign, but **only complete-composition samples may be used for
sign claims** (see the disclosure below):

| composition | constrained species present | $dS_{\rm pot}<0$ | $dS_{\rm pot}>0$ | $dS_{\rm pot}=0$ | n |
|---|---:|---:|---:|---:|---:|
| LADWP AWPF (RO product, TDS 22) | **5/5 (complete)** | 186 | 8 | 9 | 203 |
| IEUA RP-1 (tertiary, TDS 443) | **5/5 (complete)** | 151 | 56 | 9 | 216 |
| Figshare RW (TDS 1,378) | 4/5 (missing silica) | 102 | 105 | 9 | 216 |
| AI-UWM assumption (TDS 650) | 2/5 (missing hardness, alkalinity, silica) | 187 | 8 | 9 | 204 |

> ***Counting convention.** "Constrained species" means the five species the model enforces limits on (TDS, chloride, hardness, alkalinity, silica). Full details in SI S10.*

> ***Sign convention.** Signs are assigned by the *strict* sign of $dS_{\rm pot}$; $dS_{\rm pot}=0$ is reported as its own column and is **not** folded into either side. Full details in SI S10.*

> ***⚠️ Composition completeness (new in v4).** Species missing from a sample are silently imputed as **zero** by the analysis path, which makes a sample look *cleaner* than it is and **biases every downstream sign claim toward "reuse looks beneficial"**. Two compositions are affected; one of them is excluded from all sign claims because refilling its missing species flips the sign of $q$ (SI §S3.3). Full details in SI S10.*

**One composition is genuinely adverse, and it is the saltiest one.** The table is not a set of
equivalent panels. Figshare RW — the only composition whose dissolved solids sit close to the
admissible limit (TDS 1,378 against 2,200 mg/L) — is the **only** one in which harmful outcomes
outnumber beneficial ones (105 vs 102), whereas the two fully characterised, lower-salinity real
compositions favour the city decisively (LADWP 186 vs 8; IEUA 151 vs 56). The ordering follows
the mechanism rather than departing from it: the identity of §2 splits the outcome into a
displacement gain and a quality penalty, and a composition near the limit drives the penalty
term up until it offsets the gain. Two consequences are worth stating plainly. First, the
"reclaimed cooling is beneficial" reading and its opposite are **both correct within this
grid** and are separated by composition — which is exactly why a single facility-level number
cannot settle the question. Second, the most adverse composition is also the least completely
characterised (silica absent), so its 105/102 split is the panel most sensitive to further
sample data; we flag it rather than lean on it.

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

### 3d. Is any of this *predictive*? A strict pre-intervention test (new in v4)

(**Figure 4** reports this test, including the fold-wise gains that led us to withdraw the
out-of-sample claim.)

The criteria above — including the "263/263, no exception" sufficient condition — are evaluated
using **post-simulation** quantities ($x_{\rm AI}$, $M_0$, $M_1$, the displacement). Agreement
rates computed that way are **algebraic bookkeeping, not prediction**, and we therefore run a
strict test that uses only information available *before* the intervention (water chemistry of
each source, the cited limits, the design concentration factor, the blending ratio, and the
deliverable pool relative to baseline demand). The predictor is passed a signature that
**cannot** access $x_{\rm AI}, M_0, M_1, C, F$ or $dS_{\rm pot}$; we assert this in code.

| criterion (pre-intervention inputs only) | accuracy | majority-class baseline |
|---|---:|---:|
| Chemistry only ($c^{\rm rec}_i<c^{\rm pot}_i$ for all species) | 0.432 | 0.809 |
| Closed form $q>0$ | **0.675** | 0.809 |
| $q>0$ **or** deliverable pool $\ge 2\times$ baseline demand | **0.914** | 0.809 |

With $n_{\rm eff}=759$ (the 839 reliable scenarios less 80 within a $10^{-9}$ ML tolerance of
zero).

**Two conclusions follow, and the negative one matters more.**

(i) *Chemistry alone cannot predict the city-level sign* (0.675 **below** the 0.809
majority-class baseline). The reason is structural, not a defect of the predictor: writing the
identity in dimensionless form,
$$\frac{dS_{\rm pot}}{M_1}=\underbrace{\rho(\kappa-1)}_{\text{displacement term}}-\underbrace{q}_{\text{quality term}},$$
$q$ is fixed by pre-intervention chemistry — and indeed the *direction* of $q$ matches
observation in **100%** of complete-composition samples (IEUA $q<0$ in 24/24; LADWP $q>0$ in
23/23) — whereas the displacement term requires demand-side and allocative information that
chemistry does not carry. The two terms can carry **opposite signs**, so no chemistry-only
criterion can identify the net sign. This explains why the published literature reports
mutually contradictory outcomes for the same technology.

(ii) *Adding one pre-intervention demand-side quantity beats the baseline in-sample, and its
out-of-sample support is partial — we report it fold by fold rather than as a single number.*
The deliverable pool relative to baseline demand is an ordinary planning quantity; with the
disjunction above, in-sample accuracy reaches **0.914** versus a 0.809 baseline. Under
leave-one-composition-out validation the mean gain is **+0.102** (test 0.917 versus 0.809), and
we give the fold-by-fold result rather than the mean alone:

| held-out composition | accuracy | baseline | gain | $n$ |
|---|---:|---:|---:|---:|
| IEUA RP-1 | 0.939 | 0.755 | **+0.184** | 196 |
| Figshare RW | 0.730 | 0.505 | **+0.225** | 196 |
| LADWP AWPF | 1.000 | 1.000 | +0.000 | 183 |
| AI-UWM assumption | 1.000 | 1.000 | +0.000 | 184 |

The **median gain is +0.092**: two of four folds improve materially, and the two folds that
score 1.000 do so because the baseline is already saturated there, so they carry no
information either way. This supports a **candidate criterion** — chemistry plus one
demand-side planning quantity — that transfers across the two chemically distinct real
compositions *in this grid*, while remaining untested on folds that vary the demand side.

> **Note on a superseded result.** An earlier version of this analysis reported a median fold
> gain of 0.000 and withdrew the out-of-sample claim. That version ran on a water-chemistry
> input table in which the Figshare composition was missing two species (its sulphate and
> alkalinity had been lost by a parsing bug; see §3b and SI S3.3). With the composition
> repaired, that fold moves from −0.018 to +0.225 and the median from 0.000 to +0.092.
> **The earlier withdrawal was therefore partly an artefact of the data defect**, not only of a
> weak predictor. We keep the conclusion conservative — the criterion is a **candidate**, not
> a validated rule — because the informative folds are only two, and no fold varies the
> demand side.

> **Caveat.** The pool ratio is a planning quantity and is not publicly reported for every
> real utility, so the transferability of this criterion is bounded by its availability. We
> report it as a candidate criterion under a stated data requirement, not as a validated
> predictor and not as a universally applicable rule. Scripts:
> `A31_WP2_假设冻结/wp2_e3_independent_prediction.py`, `wp2_e3b_combined_prediction.py`;
> critique and per-fold recomputation: `A38_模拟审稿/red_team_findings.md` (finding F-2).

### 3b. Data-integrity gap

The quality dictionary supplies only the species present in a sample, so a missing species
enters as zero and its limit never binds. Two compositions are affected; both are handled as
described in SI S3.3, and one of them is excluded from all sign claims because refilling its
missing species **flips the sign of $q$**.

### 3b-bis. Cooling-water limits: cited standards

Earlier runs used the engine's placeholder limit set; we now use values taken from cited
standards (**GB/T 50050-2017** for circulating water, **GB/T 19923-2024** for make-up water).
Switching tiers changes headline counts — beneficial cases fall and the harmful count drops
substantially — so all results here use the cited set, and the tier comparison is given in SI
S2a and §7a.

### 3c. Solver reliability gate

An audit of our own pipeline found that 51 of the 1,052 grid scenarios did not return a unique
converged solution and were returning zero allocations while still producing derived values.
All headline statistics therefore use the **dual-gated reliable subset** ($n=839$); the
per-product gate table is in SI S3.0.

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

(**Figure 2** shows how blending changes the admissible concentration factor, which species
binds it, and how that conclusion behaves across limit tiers.)

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
realised CoC differs sharply by water source, and the city-level effect follows:

| composition | n species | realised CoC range | $dS_{\rm pot}<0$ / $>0$ / $=0$ |
|---|---:|---|---|
| LADWP AWPF (RO product, TDS 22) | 5/5 (complete) | 1.84 – 5.00 | 186 / 8 / 9 |
| IEUA RP-1 (tertiary, TDS 443) | 5/5 (complete) | 1.34 – 5.00 | 151 / 56 / 9 |
| Figshare RW (TDS 1,378) | 8 (silica absent) | 1.15 – 5.00 | 102 / 105 / 9 |
| AI-UWM assumption (TDS 650) | 2 (incomplete) | 1.84 – 5.00 | 187 / 8 / 9 |

> ***Composition matters, but the sign claim must be made only on complete-composition samples.** We give sign *counts* rather than mean $dS_{\rm pot}$ values, because the means could. Full details in SI S10.*

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

(**Figure 6** presents the partial-identification bound, the capacity-feasibility result and the
external anchors below.)

The project's largest weakness was external validity, so we anchored the modelled quantities
against public records released CC-BY-4.0 with Shen et al. (2026); their internal consistency
was confirmed (reported load rate reproduces annual volume / 365 / design capacity at
r = 1.0000).

- **Is cooling reuse a real use?** In a catalogue of **141 documented reclaimed-water
  projects**, **industrial cooling is the single largest use category (40 projects, 28.4%)**,
  the classification agreeing with an independent text search in **141/141** rows. For the 38
  B3 projects reporting capacity the median is **4,000 m³ d⁻¹**, and **26 of 38 (68.4%) fall
  inside our modelled range** of 10³–10⁵ m³ d⁻¹. Reported total unit cost has a median of
  **2.41 CNY m⁻³**.
- **Is reclaimed water cheap?** Extracting city-level industrial tariffs (61 cities, 2007–2017;
  cross-city median **1.550 CNY m⁻³**, range 0.59–6.65) gives a reclaimed-to-tap cost ratio of **1.56** — reclaimed water costs about **56% more**
  than industrial tap water — with all-use-category tariffs pooled separately
  (**all use categories pooled**: n = 39,083, median 1.45 CNY m⁻³, quoted from the stored
  artifact; **industrial* tap tariff only**: n = 7,730, 61 cities, median 1.550 CNY m⁻³).
  The two calibers must not be conflated: only the industrial series is comparable with
  reclaimed-water cost for industrial use. This offers a plausible economic reason
  why pools tend to be contractually committed, and supports our conclusion that expanding
  supply does not by itself drive substitution. It is **not causal evidence**: the data carry
  prices only, with no contracts or deliveries.
- **How much of industrial withdrawal is cooling?** Across **39 sectors** the share spans
  **0.000–0.990** (median 0.184; 7 sectors above 0.5), so no single constant represents
  industry. Our model's value of **0.258** is now fully traced: it is the mean across the 39
  sector means, recomputed independently as **0.25799037378455597**, matching A24's stored `mean_of_means`
digit for digit (relative difference 0.0).
- **Are the modelled scales realistic?** Of **597 records** of project-level deployment, **11
  report a positive capacity addition** — median **3.0 × 10⁴ m³ d⁻¹**, and **11/11 (100%)**
  inside our modelled range — with an investment intensity of about
  **1.14 × 10⁴ CNY per (m³ d⁻¹)**.

> ***What this does and does not establish.** These anchors show that our quantity ranges, facility scale, use case and cost sit inside documented practice. Full details in SI S10.*

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

> ***⚠️ Retraction (v4): the regime shares are *not identified* by this dataset.** Earlier drafts, and the v3 abstract, stated that the fully-committed regime is "empirically dominant. Full details in SI S10.*

> ***What *is* identified, and what it supports.** Two statements survive. Full details in SI S10.*

> **Methodological note.** We use the *empirically measured* thresholds rather than the closed-form
> `elig/P0` values recorded earlier (2.384 / 2.567), because surplus first appears already at
> `pool_scale` = 2.0; using the theoretical values would overstate the required supply and
> understate the surplus share.

### 7. Robustness and falsification

| test | result |
|---|---|
| Ablation 2³ factorial (64 cells) | 5/5 gates; identity residual 3.6 × 10⁻¹² |
| Cross-domain holdout (genuine, 1-parameter) | **R² = 0.766** vs baseline −0.068 |
| No-quality extreme | $dS_{\rm pot} = 0$ exactly |
| Quality–outcome response | monotone in limit stringency; see §7a for the global decomposition |
| Finite-supply propositions H1–H4 | hold in both domains, **0 falsifiers** |
| Observed heatwave / drought windows | **0/8 sign flips** — magnitude only (≤1.139×) |
| Global sensitivity (Morris + Sobol) | see §7a; **one** sign lever, but **not panel-invariant** |

#### 7a. Global sensitivity: a single sign lever, **within a stated limit tier** (new in v4)

(**Figure 5** shows the Morris ranking, the bootstrap Sobol intervals, the three-tier
panel comparison, and the extreme-event results.)

Across twelve parameters, only **one** changes the *sign* of the city outcome under the cited
limit set:

| parameter | Morris $\mu^\*$ (ML) | Sobol $S_T$ | changes sign? |
|---|---:|---:|---|
| `limit_scale` (limit-stringency scaling) | 45,062 | **0.944** | no (most severe end: $dS=-399$ ML, approaches but does not cross zero) |
| **alkalinity multiplier** | 24,841 | 0.682 | **yes — the only one** (critical ≈ 2.62×) |
| blending ratio $\varphi$ | 14,489 | 0.152 | no |

> **Uncertainty on these indices (added in v4).** The values above are point estimates. An
> independent Saltelli design with bootstrap resampling (400 replicates, 7 parameters) gives,
> for the composition whose constraint binds (IEUA, $n_{
m eff}=117$): $S_T$(limit_scale) =
> **0.330 [0.075, 0.792]**, $S_T(\varphi)$ = **0.926 [0.051, 2.568]**, and $S_T$(alkalinity) =
> **0.125 [0.015, 0.305]**. Two consequences matter: main effects explain only part of the
> variance ($\sum S_1 = 0.19$ IEUA, $0.58$ LADWP), so the ranking is not a sufficient
> description; and $\varphi$'s interval is wide, so only its direction is quoted, never a point
> value. For the non-binding composition the alkalinity index is **0.001 [0.000, 0.002]** —
> effectively zero — independently corroborating the binding-species mechanism above.

The mechanism is verifiable and narrows the problem considerably. Taking the ratio
limit/concentration for each of the five constrained species, **alkalinity has by far the
smallest ratio for IEUA (2.50; next smallest 4.97, which is TDS)**, so it is the species that
actually binds the admissible CoC; perturbing any of the other four individually leaves
$dS_{\rm pot}$ unchanged to the last digit (which is why chloride's Morris effect is
identically zero). For
LADWP **every** ratio is large (smallest 49.3), no species binds, and the quality constraint is
inactive across the sampled range — which is both why LADWP shows $q>0$ and why its Sobol
indices are **not identifiable** (there is no variance to attribute); we report that as
`NOT_IDENTIFIABLE` rather than imputing it.

> **Boundary of this claim (added after panel re-testing).** "Alkalinity is the only lever" holds
> under the **cited circulation-water tier** and also under a more permissive tier, but **it does
> not survive a stricter make-up-water tier**. Re-running the same perturbation test there:

| limit tier | binding species (IEUA / LADWP) | single-species sign lever |
|---|---|---|
| cited (2200/700/750/**350**/175) | **alkalinity / alkalinity** | alkalinity (IEUA) |
| permissive (2600/1000/750/**350**/175) | **alkalinity / alkalinity** | alkalinity (IEUA) |
| **strict (1000/250/450/350/30)** | **silica / TDS** | **none** |

> *Under the strict tier the binding species shifts to silica (IEUA) and TDS (LADWP) — because *that* tier tightens TDS and silica while leaving the alkalinity limit unchanged — and *. Full details in SI S10.*

> **Two distinct quantities, deliberately not conflated.** The value **2.50** is a *static
> margin* — the limit/concentration ratio for alkalinity at the IEUA composition. The value
> **≈2.62×** is a *dynamic critical point* — the multiplier on the alkalinity concentration at
> which the sign of $dS_{\rm pot}$ actually flips. They differ in kind and must not be quoted
> interchangeably.

> **Important caveat.** The main-effect sum $\sum S_1\approx0.22 \ll 1$: main effects explain
> only about a fifth of the variance, the rest being strong interactions. The ranking above must
> **not** be read as "the top two parameters suffice".

#### 7b. Extreme events change magnitude, not sign (new in v4)

Under **observation-driven** extremes — a 37-day window at the 95th percentile of wet-bulb
temperature (heatwave) and the 37-day window of minimum inflow (drought) — the sign of
$dS_{\rm pot}$ does **not** flip in **any** of 8 tests (all 64 scenarios remain negative, i.e.
city-beneficial); the largest magnitude departure from the annual case is **1.139×**. Observed
heatwaves do **not** by themselves curtail the data centre (PUE 1.181 → 1.235).

A sign flip *is* reachable, but only under **forced** perturbation (evaporation scaled ≈6.75×),
and it is **not** a "city harmed" outcome in the naive sense: it arises because the net
reclaimed substitution $F=M_0-(1-\varphi_{\rm eff})M_1$ turns negative. The closed-form
condition $F<0\iff\varphi_{\rm eff}<1-M_0/M_1$ matches observation in **20/20** forced cases.
Beyond $\approx10\times$ the effect leaves the calibrated range (CoC pins to the quality floor),
so we use it to **locate a critical point, not to claim an outcome**. Drought-side supply
reduction down to 0.1% availability likewise does not flip the sign.

> This is a **negative result reported as such**: within the observation-driven envelope, water
> scarcity and heat intensify the effect rather than reversing it. There is no evidence here
> that extreme events create a qualitatively new regime.

> *The identity's own cross-domain "R² = 1.000" is an **algebraic re-derivation** (it reuses the holdout domain's $M_0,M_1$) and is **not** validation; the genuine out-of-sample numbe. Full details in SI S10.*

---

## Discussion

### What is established

1. A **three-account ledger** in which requested, delivered and abstracted water are
   demonstrably distinct (0/68 coincidences; marginal wedge 1.178).
2. An **exact identity** (residual 2.55 × 10⁻¹¹, relative 2.9 × 10⁻¹⁶) whose two branches
   *contain* both the prior literature's facility-to-city identity and its opposite.
3. The **regime boundary is measurable and exogenous** (`elig/P0`), not a modelling choice.
4. **Finite supply changes the kind of outcome**: withdrawal change → service gap → facility
   curtailment, with nested, quantified thresholds.
5. **Quality constraint is a switch**: non-binding quality + committed pool gives exactly zero.
6. **The sign is not predictable from chemistry alone** — 0.675 without a demand-side
   quantity, below the 0.809 majority-class baseline (§3d). Adding one demand-side quantity
   lifts in-sample accuracy to 0.914 and gains a **median +0.092** under fold-wise validation
   (two of four folds informative), so we report the criterion as candidate rather than
   validated. This reframes the field's contradictory findings as a **data-requirement**
   problem rather than a physical disagreement — but the resolution is not yet demonstrated.
7. **What actually drives the city outcome** is the volume of reclaimed water drawn
   ($\mathrm{corr}=-0.93$), not the makeup saved ($\mathrm{corr}=-0.11$; the quality term
   $q$ correlates only $-0.16$).

### What is not claimed

We do not claim reclaimed cooling "saves water" or "cannot save water" in general; both are
branch-specific. We do not calibrate absolute volumes to any named city: the potable cap
(380/400 ML/day) is parameterised, so thresholds are conditional. We do not claim the
daily engine is a calibrated hydrological model.

### Relation to prior work

Data-centre water use is already well characterised at the facility and fleet scale
(Mytton & Haslam, 2021; Siddik et al., 2021; Lei et al., 2025), and the energy, water and
carbon consequences of AI growth have been quantified with scenario analysis
(Xiao et al., 2025). Its impacts on *public* supply have also been documented: Han et al.
(2026) quantify the required supply capacity, and Alston et al. (2026) show that cooling
technology choices shift where those water impacts fall.

Our contribution is orthogonal to all of the above. Wang et al. (2026) estimate the potential of
data-centre/WWTP pairing; we quantify **how much of that potential survives** incumbent claims
and quality limits. Shen et al. (2026) note reuse benefits depend on demand conditions; we make
that dependence a **measurable threshold**. Chen et al. (2023) show that wastewater-related
emissions and water scarcity can be decoupled across many cities; we address the complementary
question of whether reclaimed cooling reduces *abstraction*, which is a different account.
Our earlier fixed-pool result was one branch of the law above.

Crucially, the direction we report is **not** unprecedented in the engineering literature:
**Badruzzaman et al. (2022)** provide field evidence that reclaimed water can *raise* the
achievable cycles of concentration in industrial cooling. What we add is the **general
closed-form condition**, the demonstration that its sign need not carry over to the city-level
outcome, and the urban-scale evaluation — not the observation itself.

**Novelty boundary, stated precisely.** A verified search of the literature
(`A29_文献核验/`) supports a narrow claim and refutes several broader ones, and we adopt the
narrow version:

- The head-to-head competitor, **Wang et al. (2026)**, estimates the DC–WWTP pairing potential
  at global scale but states explicitly that *"water reused within recirculating cooling
  systems is not included"*; across that paper the terms cycle-of-concentration, salinity, TDS
  and quality-constraint do not appear. Its boundary therefore **excludes** the mechanism this
  work centres on — which is also why we do **not** claim to be first to match data centres to
  wastewater plants.
- **Saleh (2026)**, an *ES&T* Viewpoint, has already put "beyond water quantity to water
  compatibility" on the agenda. We therefore do **not** claim to have originated the call to
  consider water quality; our claim is restricted to **formalising the quality constraint as a
  closed-form condition and quantifying that the volume of reclaimed water drawn — not the
  makeup saved — dominates the city-level outcome**.
- Related claims we do **not** make: first quantification of AI-server water–energy–carbon
  coupling; first study of data-centre peak stress on municipal supply; first observation that
  reclaimed water can raise achievable concentration factors. Each is already published.

To our knowledge — with the caveat that our search covered the CrossRef, OpenAlex, DataCite,
Zenodo and Semantic Scholar APIs but **not** Scopus or Web of Science full text, so this is a
"not found" rather than a proof of absence — no published work formalises the quality control
of reclaimed-water cooling as a closed-form condition **and** frames the net city outcome as a
pre-intervention prediction problem with reported out-of-sample behaviour.
(`A29_文献核验/literature_verification.md`, `innovation_overlap.md`)

### Limitations

1. **The quality penalty is path-dependent, and we now quantify it.** Our primary results use
   the engine's volume-only quality solver, in which the loop concentration is the
   *instantaneous* blend of makeup sources, so blending reclaimed water lowers the admissible
   CoC. The engine also ships an opt-in dynamic solute-state path (R10a) that maintains a loop
   solute stock; on identical inputs it holds CoC near the design value and the penalty nearly
   vanishes. A dedicated head-to-head run (`A38_模拟审稿/NE1_判决性实验结果.md`) gives:
   for the composition whose quality constraint actually binds, blending to $\varphi=0.6$
   raises makeup by **+9.8%** in the primary path but only **+0.012%** in the solute-stock
   path — a **≈800×** difference in magnitude — and $q$ shrinks from **−0.096** to
   **−0.0001**. The **sign** of the outcome is nevertheless the same in every comparison, so
   the **direction** of our central conclusion is robust. **But the effective test is small
   and we say so:** for the second composition the quality constraint never binds, both paths
   return bit-identical numbers, and so the sign agreement rests on **two non-trivial
   scenarios, not four**. We therefore report the mechanism as a **structural sensitivity**
   and do not claim it as the unique cause. *(We no longer lean on the engine's
   `NOT_READY_FOR_E3` engineering flag as a justification — that flag states readiness, not
   physics; the quantitative comparison above is the real evidence.)*
   (`A21_动态状态/A21_动态状态报告.md`, `A38_模拟审稿/NE1_判决性实验结果.md`)
2. **Cooling storage itself consumes water.** Introducing storage raises makeup by
   **+3.45%** (D-HA) and **+7.02%** (D-CO), independently of capacity (50 / 200 / 800 ML give
   identical results). Storage is not free.
3. Supply caps are parameterised, not observed for a named city. Our reclaimed-supply
   parameter is anchored to the **81st percentile** of 10,826 observed wastewater plants
   (§6), so the work describes above-median-provision cities rather than the median.
4. Two homologous synthetic domains; no independent city calibration. The external dataset
   constrains parameter ranges and capacity feasibility but does **not** validate city-level
   predictions, and no facility-level cooling-operations data were obtainable. In particular
   the committed/surplus **regime shares are not identified** from it (§6b). The 141-project
   catalogue of §6 establishes that industrial cooling is a documented real use (40 projects,
   28.4%) at our modelled scale (68% within 10³–10⁵ m³ d⁻¹), **but it is a case collection, not
   a random sample**, so its share is not a prevalence; it also contains **no demand-side field**
   and **no operating data** (no CoC, no makeup rate), so it cannot calibrate the model or
   resolve the identification problem.
5. Allocation rules remain the engine's (reserved-pool pro-rata); priority queues and
   interruptible contracts are not represented.
6. Quality envelope CoC ∈ [2.1, 4.9] from mixed observed/literature/an extrapolated tier;
   temperature is missing for all five water sources, which alone can shift CoC by −30%.
7. Costs are declared values; no cost claim is made.
8. Engine-side G2/G3 evidence gates remain `NOT_READY` (SI §S8).
9. **Composition incompleteness biases toward "reuse is beneficial".** Missing species enter
   the analysis path as concentration zero, so their limits never bind and the sample looks
   cleaner than it is. This flips the sign of $q$ for the two-species `AI-UWM assumption`
   entry, which we therefore exclude from all sign claims; only the complete-composition
   samples (IEUA, LADWP) are used for those. The engine's own validator rejects incomplete
   compositions, and the analysis path bypasses that check — a discrepancy we report rather
   than resolve by editing the engine. (§3, `A33_WP4_组成重构/`)
10. **Dominant control is the reclaimed volume drawn, not the makeup saved.** Across the
    complete-composition grid the city outcome correlates strongly with the reclaimed volume
    drawn ($\mathrm{corr}=-0.93$) and only weakly, and in the opposite direction, with the
    quality term $q$ ($\mathrm{corr}=-0.16$). An earlier draft of this work attributed the
    outcome to a "cleaner water ⇒ more makeup saved" chain; that attribution is **withdrawn**
    on the evidence. ($A32\_WP3\_水化学/WP3\_水化学机制验证报告.md$, correction section.)
11. **Volume-only solute conservation is verified as a flux balance, not a stock closure.**
    That path defines loop concentration instantaneously from the blended makeup, so no loop
    solute stock exists and a stock-closure test is inapplicable; the applicable check —
    water closure $G=E+D+B$ and self-consistency $\mathrm{CoC}=G/(B+D)$ — passes at machine
    precision (relative residuals 1.9 × 10⁻¹⁶ and 2.5 × 10⁻¹⁶). The engine's opt-in dynamic
    path does maintain a solute stock and its own closure columns confirm mass balance to
    5.7 × 10⁻¹⁹ relative. We report both rather than generalising from one.
    (`A30_WP0取证/volonly_flux_balance_summary.json`, `a21_solute_closure_summary.json`)
12. **One internal product file has swapped column labels.** The three affected label
    groups were swapped together, so every derived number — including all $dS_{
m pot}$
    values and the identity residual — is unaffected; only re-users of that file can be
    misled. Documented in `A13_可靠性机制/COLUMN_NAMES_CORRECTED.md` rather than silently
    rewritten. *(Internal provenance note.)*
13. **The pre-intervention predictor is a candidate, not a validated rule.** It requires the
    deliverable-pool-to-demand ratio — routinely available to a utility but not universally
    published — and, decisively, its apparent out-of-sample gain is **entirely attributable to
    a single fold** (median fold gain 0.000; removing the one positive fold makes the mean
    negative). The present design varies the chemistry axis but not the demand axis, so it
    cannot resolve the criterion; we report the negative and the positive results side by side
    and claim neither as established.
14. **Sensitivity and extreme-event coverage.** Global (Morris/Sobol) sensitivity and
    heatwave/drought scenarios are reported in `A34_WP5_敏感性与极端事件/`; parameter,
    structural and scenario uncertainty are reported separately and are not combined into a
    single error bar. Two caveats bound them: (i) main effects account for only
    $\sum S_1\approx0.22$ of the variance, the remainder being strong interactions, so
    parameter rankings are not a sufficient description; (ii) the LADWP Sobol indices are
    `NOT_IDENTIFIABLE` because the quality constraint is inactive across the sampled range, and
    are reported as such rather than imputed. Extreme-event tests are **observation-driven**
    (percentile windows), and the one forced sign flip we can construct lies outside the
    calibrated range and is used only to locate a critical point.
15. **Structural comparison across panels is confounded.** Switching the limit panel changes
    $|dS|$ by up to 26%, but that panel carries only two species, so its CoC pins to the
    design ceiling and the quality constraint is effectively disabled — a **specification
    error**, not a legitimate sensitivity band. *(Internal note; see SI.)*

## Methods

> Model, datasets, limits, gates and full parameter tables are given in the Supplementary
> Information (S1–S20); the summary below states the estimation target and the identifying
> assumptions.

**Models and bridging.** Two independent implementations are used: a representative-day
periodic model (`city_model`) and the full daily engine (`FullAIUWMModel`). A dedicated
bridging experiment compares them on identical inputs after fixing a harness defect in which
the daily branch used facility *makeup* instead of *evaporation* as its reference basis; with
the correct basis the two agree to machine precision on $M_0$ (median relative difference
**5.1 × 10⁻¹⁶** across **24/24** paired runs, `limit_scale` = 0.5), and the sign of
$dS_{\rm pot}$ agrees in **23/24 (0.958)**. *(An earlier draft quoted a 1.60× inflation factor
and an absolute agreement value of 36,504 ML; neither is present as a field in the current
`bridging_summary_v2.json`, and they came from the superseded placeholder-limit run. We quote
the machine-checkable relative figures instead.)*
See `A20_模型桥接/bridging_summary_v2.json`.

**Estimand.** $dS_{\rm pot}=C-F$, with the unified form of Results §2. Three accounts are
reported separately and never merged.

**Design.** 839 solver-reliable paired scenarios (2 domains × 4 water compositions × 9 pool levels ×
4 mixing ratios × 3 quality tiers) plus a labelled extrapolation tier; 68 full-engine runs
(730 days) for the three-account and finite-supply experiments.

> **Two defects we found and fixed during this work, both material.** (i) The evaluator's
> memoisation key omitted the water composition, so with a shared cache the first
> composition's results were silently reused for all others and the composition axis carried
> **no** variation. After fixing the key, realised CoC differs by composition
> (minima 1.14–2.50) and the city-level effect **spans both signs**. Every number in this
> manuscript is from the corrected runs. (An earlier reading attributed the reversal to high
> salinity specifically; the repaired grid does not support that — within the committed branch
> both IEUA and Figshare RW give 48 harmful against 3 beneficial scenarios, so the split
> tracks the quality-limited tier and the pool level rather than salinity alone.) (ii) The daily-model bridging harness initially passed facility *makeup*
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

---

## References

> Generated from the independently verified bibliography (`A29_文献核验/references.bib`; all 24 entries resolved through CrossRef and 
> DataCite). Only works cited in the text are listed here; verified-but-uncited 
> sources are kept separately in `A42_参考文献/references_manuscript.md`.

1. Alston, Garrett, Love, Nancy, Haider, Rabab (2026). Data center cooling choices shift water impacts across the grid: An integrated water-energy model for sustainable data centers. [Preprint] https://doi.org/10.48550/arxiv.2609.25437
2. Badruzzaman, Mohammad, Anazi, Jasem R., Al-Wohaib, Fawaz A., Al-Malki, Abdulaziz A., Jutail, Fadel (2022). Municipal reclaimed water as makeup water for cooling systems: Water efficiency, biohazards, and reliability. *Water Resources and Industry* **28**, 100188. https://doi.org/10.1016/j.wri.2022.100188
3. Chen, Shaoqing, Zhang, Linmei, Liu, Beibei, Yi, Hang, Su, Hanshi, Kharrazi, Ali, Jiang, Feng, Lu, Zhongming, Crittenden, John C., Chen, Bin (2023). Decoupling wastewater-related greenhouse gas emissions and water stress alleviation across 300 cities in China is challenging yet plausible by 2030. *Nature Water* **1**, 534–546. https://doi.org/10.1038/s44221-023-00087-4
4. Han, Yuelin, Li, Pengfei, Wierman, Adam, Ren, Shaolei (2026). Small Bottle, Big Pipe: Quantifying and Addressing the Impact of Data Centers on Public Water Systems. [Preprint] https://doi.org/10.48550/arxiv.2603.02705
5. Lei, Nuoa, Lu, Jun, Shehabi, Arman, Masanet, Eric R. (2025). The water use of data center workloads: A review and assessment of key determinants. *Resources, Conservation and Recycling* **219**, 108310. https://doi.org/10.1016/j.resconrec.2025.108310
6. Mytton, David (2021). Data centre water consumption. *npj Clean Water* **4**, 11. https://doi.org/10.1038/s41545-021-00101-w
7. Saleh, Navid B. (2026). Why Water Demand Is No Longer Enough: Rethinking Sustainability in AI Data Centers. *Environmental Science & Technology* **60**, 18383–18386. https://doi.org/10.1021/acs.est.6c08380
8. Shen, Jijie, Shen, Lei, Zhong, Shuai, Li, Delong, Li, Ding, Fang, Jinzhu, Bai, Haonan (2026). China's centralized wastewater treatment system reaches efficiency limits in tackling water scarcity. *Nature Water*. https://doi.org/10.1038/s44221-026-00727-5
9. Siddik, Md Abu Bakar, Shehabi, Arman, Marston, Landon T. (2021). The environmental footprint of data centers in the United States. *Environmental Research Letters* **16**, 064017. https://doi.org/10.1088/1748-9326/abfba1
10. Wang, Aijie, Zhang, Congchao, Xu, Tiefu, Savic, Dragan, Jiang, Jingjing, Xiao, Peng, He, Chuan, Tao, Yu, Daigger, Glen, Ren, Nanqi (2026). Global data–water symbiosis reduces AI infrastructure's carbon and water footprint. *Environmental Science and Ecotechnology* **31**, 100702. https://doi.org/10.1016/j.ese.2026.100702
11. Xiao, Tianqi, Fuso Nerini, Francesco, Matthews, H. Damon, Tavoni, Massimo, You, Fengqi (2025). Environmental impact and net-zero pathways for sustainable artificial intelligence servers in the USA. *Nature Sustainability* **8**, 1541–1553. https://doi.org/10.1038/s41893-025-01681-y

---

## Declarations

> These statements are required by the target journal. Items marked `[[...]]` must be completed by the authors; nothing personal has been auto-filled.

### Data availability

The study uses no new primary measurements. All external data are public and are
redistributed here only by reference:

- The wastewater-treatment-plant inventory, reclaimed-water project catalogue,
  cooling-water share table, city water-tariff series and capacity-deployment records
  are all taken from the reproducible source-data package accompanying Shen et al.
  (2026), released under CC-BY-4.0 at Zenodo:
  **https://doi.org/10.5281/zenodo.22138940**
  (workbook `Source_data.xlsx`; sheets `WWTP_data_2020`, `Reclaimed water case`,
  `Share of cooling water`, `water price(CNY_m-3)`, `Source data 4`).
- Cooling-water quality limits follow the cited standards **GB/T 50050-2017** and
  **GB/T 19923-2024** (values tabulated in the Supplementary Information).
- All model outputs generated in this work — scenario grids, sensitivity designs,
  bootstrap replicates, figures and the evidence ledger — are contained in the
  project archive described under *Code availability*, together with SHA-256 hashes
  of every authoritative artifact (see `A40_投稿包/reproducibility_manifest.md`).
- Any further data are available from the corresponding author on reasonable request.

### Code availability

The modelling engine is not redistributed here; analyses were performed against a
read-only checkout of the AI-UWM engine (no engine source was modified — this is
asserted and checked in the analysis scripts). All analysis, sensitivity, figure and
audit code written for this study is available as follows:

- Repository: **[[REPOSITORY_URL]]** *(e.g. GitHub/Zenodo DOI for the analysis archive)*
- Version / commit: **[[COMMIT_OR_VERSION]]**
- Complete reproduction:

  ```bash
  cd "10_论文推进_2026Q4"
  python A36_终审/final_gate.py                      # terminal gate, expects all PASS
  python A40_投稿包/make_reproducibility_manifest.py  # artifact hashes + numeric re-checks
  python A37_六主图_v4/make_all_figures.py            # regenerates all six main figures
  python A41_全包审计/package_consistency_check.py    # cross-document consistency
  python A42_参考文献/references_from_bib.py          # citation ↔ bibliography mapping
  ```

- Environment: Python 3.13.14; numpy 2.4.4; pandas 3.0.5; matplotlib 3.11.2;
  phreeqpython 1.6.2. The engine is located via `AIUWM_REPO` or a relative layout
  (hard-coded absolute paths have been removed).
- Six automated gates ship with the archive; all currently pass. They check: terminal
  assertions, figure–source consistency (64 checks), artifact hashes and numeric
  re-computation (17 checks), cross-document consistency, citation integrity, and
  absence of corrupted control characters.

### Competing interests

**⚠️ 需作者确认**（若确无，保留下述标准表述）

The authors declare no competing interests.

### Author contributions

**⚠️ 需作者填写（不得代拟）**

- [[Author 1]]: [[conception / model design / analysis / writing]]
- [[Author 2]]: [[…]]

All authors discussed the results and approved the manuscript.

### Acknowledgements

**⚠️ 需作者填写**（基金号、数据提供者致谢等）

- [[FUNDING: grant number(s) and funder name(s), or "This research received no specific grant from any funding agency."]]
- We thank [[names]] for [[contribution]].
- We acknowledge the authors of Shen et al. (2026) for releasing their source-data
  package under CC-BY-4.0, which underpins the external anchors in this work.
