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
(residual 2.9 × 10⁻¹¹ ML, 1,152 scenarios) that **unifies two opposite regimes**. When the
reclaimed pool is already committed to incumbent users, a data centre's reclaimed draw is
fully displaced: the city's potable withdrawal does not fall, and the old facility-to-city
identity is recovered exactly. When unused reclaimed water remains, the draw is *not*
displaced and urban potable withdrawal genuinely falls — by up to 27,354 ML per period in
our tests. Which regime applies is governed by the **displacement ratio** (the share of the
facility's reclaimed draw taken out of incumbent supply), itself set by a measurable
quantity — committed reclaimed demand relative to deliverable supply (thresholds 2.384 for
D-HA and 2.567 for D-CO) — **not** by the cooling technology. Imposing a finite
potable-supply cap shows the effect is not merely redistributed but transformed: as the cap
binds, the apparent "extra abstraction" becomes a **necessary-service gap** (up to
62,080 ML) and the data centre is itself curtailed. Finally,
setting the water-quality constraint to non-binding makes the outcome exactly zero in the
committed regime — establishing that "reclaimed cooling does not save water" is a property
of *quality-limited, fully-committed* systems rather than of reuse in general.

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

verified to **5.8 × 10⁻¹¹ ML** across 1,152 scenarios. In the special case where the
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

### 3. The sign is set by the *degree* of displacement

Rather than a binary state label, the natural predictor is the **displacement ratio**
$C/x_{\rm AI}$ — the share of the facility's reclaimed draw that actually comes out of
incumbent supply (1 = pure displacement, 0 = drawn entirely from unused surplus). Over the
main scan (1,152 scenarios), $dS_{\rm pot}$'s sign tracks it monotonically:

| displacement ratio | n | $dS_{\rm pot}<0$ | range (ML) |
|---|---:|---:|---|
| **0.00** (pure surplus) | 424 | **424 (100%)** | −27,354 … −5,125 |
| 0.01 … 0.25 | 88 | 88 (100%) | −23,575 … −8,669 |
| 0.25 … 0.50 | 68 | 68 (100%) | −14,195 … −2,329 |
| 0.50 … 0.75 | 16 | 16 (100%) | −4,235 … −1,140 |
| 0.75 … 1.00 | 268 | 16 (6%) | −2,828 … +4,024 |

Both extremes are **pure**: at ratio 0 there is **not one** positive case, and at ratio 1
there is **not one** negative case. In between the sign is governed by
$x_{\rm AI}+(M_0-M_1) > C_{\rm disp}$, which reproduces the observed sign with **100%**
agreement.

The ratio itself is set by an external, measurable quantity — the ratio of committed
reclaimed demand to deliverable supply, `elig/P0` = **2.384** (D-HA) and **2.567** (D-CO).
In the surplus branch incumbents are satisfied in **100%** of cases, `C = 0.0` exactly, and a
mean **33,671 ML** of reclaimed water sits unused.

> **Consequence for practice.** A city cannot infer its outcome from the cooling technology
> or from the reuse fraction $\varphi$; it must first measure how much reclaimed water is
> already committed, and whether its usable surplus is genuinely unclaimed.

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

### 6. Robustness and falsification

| test | result |
|---|---|
| Ablation 2³ factorial (64 cells) | 5/5 gates; identity residual 3.6 × 10⁻¹² |
| Cross-domain holdout (genuine, 1-parameter) | **R² = 0.558** vs baseline −0.044 |
| No-quality extreme | $dS_{\rm pot} = 0$ exactly |
| Quality monotonicity | 6,478 → 21,674 → 116,581 ML as quality tightens |
| Finite-supply propositions H1–H4 | hold in both domains, **0 falsifiers** |

> The identity's own cross-domain "R² = 1.000" is an **algebraic re-derivation** (it reuses
> the holdout domain's $M_0,M_1$) and is **not** validation; the genuine out-of-sample number
> is 0.558. A further caveat that bounds our claims: storage, solute accumulation and
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

1. Supply caps are parameterised, not observed for a named city.
2. Two homologous synthetic domains; no independent city calibration.
3. Allocation rules remain the engine's (reserved-pool pro-rata); priority queues and
   interruptible contracts are not represented.
4. Quality envelope CoC ∈ [2.1, 4.9] from mixed observed/literature/an extrapolated tier;
   temperature is missing for all five water sources, which alone can shift CoC by −30%.
5. Costs are declared values; no cost claim is made.
6. Engine-side G2/G3 evidence gates remain `NOT_READY` (SI §S8).

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

**Design.** 1,152 paired scenarios (2 domains × 4 water compositions × 9 pool levels ×
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
> periodic and daily models agree **exactly** ($M_0$ identical to the last digit in **24/24**
> paired runs, median and maximum relative difference both 0.000000). Both defects are
> documented in `A20_模型桥接/` and `19_缺陷报告_缓存与桥接_2026-10-15.md`.

**Quality tiers.** As anchored in Results §5; the extrapolation tier is flagged in the data.

**Data.** Public compositions (IEUA RP-1 2025 with monthly min–max ranges; LADWP AWPF 2012;
Figshare paired study; SIPIBEL; SDWIS IEU; GSA courthouse cooling tower) bound the parameter
domain; they are never calibration targets or point-prediction validation. Composition enters
the corrected model through the blended-water concentration against scaled limits, and — as
Results §5 shows — it materially changes the outcome.

**Reproducibility.** Environment locked (Python 3.13.14, numpy 2.4.4, pandas 3.0.5,
matplotlib 3.11.2, phreeqpython 1.6.2); engine located via `AIUWM_REPO` or relative layout
(hard-coded paths removed). Superseded scripts are marked in place.
