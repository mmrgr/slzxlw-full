# Facility-versus-city accounting of reclaimed-water cooling in AI data centres: a discharge–claim balance

**Working draft v2 (2026-10-14, after method audit).** Supersedes `manuscript_en_core.md` v1,
whose "two opposing channels" mechanism was **withdrawn** (see
`A13_可靠性机制/AUDIT_2026-10-14_撤回声明.md`).
All numbers traceable via `reproduction_manifest.md` (to be regenerated).

---

## Abstract

Data centres are increasingly proposed to cool with municipal reclaimed water, on the
assumption that doing so relieves pressure on potable supplies. The relevant quantity is
not how much water a facility withdraws but how the urban potable balance changes. We
derive that balance explicitly, as a **discharge–claim** pair: reclaimed substitution
*discharges* potable water from the facility, while displaced incumbent users *claim*
potable water in its place. Across 288 paired scenarios spanning two urban domains and
three published reclaimed-water compositions, we obtain an exact accounting identity
(residual 1.1 × 10⁻¹¹ ML) that **unifies two opposite regimes**. When the reclaimed pool
is already fully committed, the local saving is entirely cancelled and the city's potable
withdrawal rises; when unused reclaimed water remains, the saving survives and urban
potable withdrawal genuinely falls, by up to 27,354 ML per period in our tests. Which
regime a city is in is decided by a single measurable ratio — the committed reclaimed
demand relative to deliverable supply — and not by the cooling technology. Three
consequences follow. First, "fixed supply implies no city-level benefit" is **not**
general: it holds only when the reclaimed pool is already fully used. Second, when water
quality imposes no constraint on cycles of concentration, the city-level effect is exactly
zero, so reclaimed cooling is then pure reallocation. Third, and conversely, the widely
used facility-to-city identity is recovered exactly in the fully-committed regime, so
prior work is not contradicted — it is located as one branch of a two-branch law.

---

## Results

### 1. The estimand: a discharge–claim balance

Define the city-level change in potable withdrawal under a matched counterfactual
(all-potable vs. reclaimed substitution):

$$dS_{\rm pot} = C - F$$

| term | meaning |
|---|---|
| $F$ | **discharge**: potable water the data centre no longer withdraws $= M_0-(1-\varphi_{\rm eff})M_1$ |
| $C$ | **claim**: potable water displaced incumbents must now withdraw $= r_{\rm inc}(B_2)-r_{\rm inc}(B_1)$ |

$M$ is facility makeup, $\varphi_{\rm eff}$ the realised reclaimed fraction, and
$r_{\rm inc}$ the reclaimed volume allocated to incumbent users. The incumbent reference
must be evaluated **in the same scenario** as the counterfactual (i.e. $r_{\rm inc}$ at
$\varphi=0$ under the same capacity), not against a fixed nominal pool.

This construction replaces the previous study's device of subtracting an unmet-demand gap
from a withdrawal change — a step that is dimensionally invalid, since *how much water the
city takes* and *how much demand goes unmet* are different physical quantities.

### 2. An exact identity in the fixed-pool regime

Over 408 scenarios (2 domains × 4 published reclaimed-water compositions × 3 quality
tiers × 17 mixing ratios), the allocator is **purely displacement-based**:

$$x_{\rm AI} \equiv r_{\rm inc}(B_2)-r_{\rm inc}(B_1)
\qquad(\text{residual } 5.5\times10^{-12}\ \text{ML})$$

Substituting into the balance gives

$$\boxed{\;C-F = M_1 - M_0\;}$$

verified to a **maximum residual of 3.3 × 10⁻¹¹ ML** with sign agreement of 1.000.

The consequence is unambiguous: **$dS_{\rm pot}\ge0$ in all 408 scenarios** (0 negative,
384 positive, 24 exactly zero), and no configuration makes the city's potable withdrawal
fall. The earlier facility-to-city identity is thus **confirmed**, but now as the
consequence of an explicit two-flow balance rather than as a bookkeeping tautology.

### 3. Quality is the sole driver — and its absence is exactly neutral

The identity makes the mechanism transparent: the city effect equals the **increase in
facility makeup caused by reduced cycles of concentration**.

| quality tier $\chi$ | max $dS_{\rm pot}$ (ML) | mean (ML) | realised CoC |
|---|---:|---:|---|
| 1.00 (no constraint) | 910 | 494 | 4.40–5.00 |
| 0.50 | 2 953 | 1 649 | 2.2–2.5 |
| 0.25 (severe) | **29 103** | 19 086 | 1.2 |

The limiting case is exact and decisive. With the quality limit set wide
($\chi\to\infty$), realised CoC stays at its design value of 5.0 and

$$dS_{\rm pot} = 0.0000\ \text{ML}\quad\text{(all 8 test configurations)}$$

> **Reclaimed-water cooling is *exactly* pure reallocation when water chemistry does not
> constrain the cooling system.** The "no net saving" claim is therefore not a general
> property of reuse; it is a property of quality-limited systems.

Boundary behaviour corroborates this: at $\varphi\to0$, $dS_{\rm pot}=0$ exactly
(12/12 scenarios), and the effect is monotone in quality severity
(910 → 2 953 → 29 103 ML as $\chi$ falls 1.0 → 0.5 → 0.25).

### 4. The identity has a regime boundary: added capacity reverses it

The identity is a property of the **fixed-pool regime**. When reclaimed water comes from
added capacity rather than incumbent allocation, the discharge is no longer bounded by the
incumbent claim, and the sign reverses:

| regime | $F$ vs $C$ | $dS_{\rm pot}$ (ML) | reading |
|---|---|---|---|
| **fixed pool** ($\Delta P=0$) | $F\le C$ | **≥ 0** | substitution costs the city potable water |
| **added capacity** ($\Delta P>0$) | $F$ may exceed $C$ | **−15 030 to −4 639** | substitution *reduces* urban potable withdrawal |

This is a substantive finding, not a technicality: it means the widely cited "reuse is a
wash" and "reuse saves water" positions are both correct **within their own regime**, and
the regime — whether reclaimed supply is fixed or expanded — is the decisive variable.

We also report the probabilistic version of this contrast, with an explicit caveat. Across
27 prior combinations (16 200 engine solves), the probability of a positive city-level
volume benefit is **≤ 0.005** in the fixed-pool regime under **every** prior, but spans
**0.428–0.785** in the added-capacity regime. The commonly quoted figure of 0.62 is the
*uniform-prior* value and lies inside that range; it is therefore reported **only as
"under uniform priors"** and never as a real-world probability of benefit. All
probabilities here are **model probabilities, not observed event frequencies**.

### 5. Ablation

A full 2³ factorial design (quality feedback × supply competition × fixed-vs-added
capacity) yields five gates, all satisfied:

| gate | rule | result |
|---|---|---|
| G1 | fixed pool, quality feedback off ⇒ $dS_{\rm pot}=0$ (pure reallocation) | ✅ max \|$dS_{\rm pot}$\| = **0.000 ML** |
| G2 | fixed pool, quality feedback on ⇒ $dS_{\rm pot}\ge0$ | ✅ min = 2 434.6 ML |
| G3 | fixed pool, all scenarios ⇒ $dS_{\rm pot}\ge0$ | ✅ min = −0.000 ML (n=32) |
| G4 | identity $dS_{\rm pot}=C-F=M_1-M_0$ in fixed pool | ✅ residual **3.638 × 10⁻¹²** ML |
| G5 | added-capacity regime: identity does **not** apply (expected) | ✅ separated and reported |

Main effects confirm quality and capacity regime dominate: quality feedback +3 994 ML,
fixed-vs-added capacity +10 964 ML.

### 6. The result is robust to the allocation rule

The identity's premise — that reclaimed allocation displaces incumbents one-for-one — is a
property of the model's allocator and could be an artefact of that choice. We test it
directly using the engine's **native incumbent-protection parameter**, scanning the
protected claim from 0% to 100% of the incumbent demand (80 scenarios, 2 domains × 2
compositions × 5 protection levels × 4 mixing ratios).

The displacement premise holds **exactly at every protection level**
($\max|x_{\rm AI}-C| = 0.0$ ML). Among the **48 substantive scenarios** — those in which the
data centre actually receives reclaimed water — $dS_{\rm pot}>0$ in **all** of them:

| protection | $dS_{\rm pot}$ range (ML) | substantive n |
|---|---:|---:|
| 0.00 (AI priority) | 974 – 2 953 | 16 |
| 0.25 | 743 – 2 196 | 16 |
| 0.50 | 355 – 1 203 | 16 |
| 0.75 – 1.00 | *AI receives no reclaimed water* | 0 |

Stronger incumbent protection **monotonically reduces** the city-level effect
(2 953 → 2 196 → 1 203 ML). At protection $\ge0.75$ the protected claim (0.75 × 33 779 =
25 334 ML) exceeds the pool (24 404 ML), so the pool is fully reserved, the data centre
receives nothing, and the effect is trivially zero — **we exclude these 32 cases as
non-evidence rather than presenting them as a benefit.**

> **Conclusion.** Protecting incumbent users **mitigates** the city-level cost but cannot
> convert it into a net gain. The sign of the effect is therefore **not an artefact of the
> allocation rule** within the range where reuse actually occurs.

### 7. Cross-domain transfer — a modest out-of-sample result

The identity itself cannot serve as validation, since it reuses the engine's $M_0,M_1$ in
the holdout domain. Reported as such, the only genuine holdout is a one-parameter transfer
of the realised mixing fraction ($\varphi_{\rm eff}\approx a\varphi$, $a$ fitted on D-HA
and frozen):

| test | result |
|---|---|
| frozen one-parameter law, D-CO holdout | **R² = 0.599**, median absolute error 0.028 |
| trivial constant baseline | R² = −0.034 |

**This is weak external evidence and is reported as such.** Two homologous synthetic
domains do not constitute city-level validation.

---

## Discussion

### What is established

1. An explicit **discharge–claim balance** for facility-to-city potable accounting,
   replacing a subtraction that mixed incompatible quantities.
2. An **exact identity** in the fixed-pool regime ($C-F=M_1-M_0$, residual 3.3 × 10⁻¹¹),
   which independently confirms the project's original conclusion $S_{\rm city}\le0$.
3. The **precise condition for neutrality**: zero city-level effect if and only if water
   chemistry does not constrain cycles of concentration (verified at 0.0000 ML).
4. A **regime boundary**: added reclaimed capacity reverses the sign, reducing urban
   potable withdrawal by 4 639–15 030 ML in our tests.
5. **Rule-robustness**: the displacement premise holds exactly under all tested incumbent
   protection levels, and $dS_{\rm pot}>0$ wherever reuse actually occurs, so the sign is not
   an artefact of the allocation rule.

### What is no longer claimed

The previously reported "two opposing channels", the supply-stress parameter $\psi$, the
critical mixing ratio $\varphi^*$, and the "supply floor" are **withdrawn**. They arose from
two defects: using the incumbent's unmet *reclaimed* demand as if it were *potable* demand,
and subtracting an unmet-demand gap from a withdrawal change. The audit trail is preserved
in `AUDIT_2026-10-14_撤回声明.md`.

### Relation to prior work

The result refines rather than contradicts Wang et al. (2026): where genuinely new
reclaimed capacity is built, we also find positive outcomes (§4). The addition is the
separation of *added supply* from *reallocation of existing supply*. In contrast to Han
et al. (2026), who quantify required public supply capacity, we ask what happens to the
potable balance for a given capacity.

### Limitations

1. **Two homologous synthetic domains**; the only genuine holdout is a one-parameter
   transfer (R² = 0.599).
2. **Water quality without antiscalant** — a no-dosing thermodynamic bound, so quality
   costs are conservative (high). The χ=0.50 tier matches the PHREEQC-derived value (0.504)
   for IEUA reclaimed water; the χ=0.25 tier is an extrapolated stress case.
3. **No city anchor** for absolute supply volumes; results are conditional on the frozen
   synthetic domains.
4. Engine placeholder parameters and declared cost values remain (SI §S7); G2/G3 evidence
   gates are `NOT_READY` on the engine side (SI §S8).
5. The identity is exact **within this model's allocator**; alternative allocation rules
   (e.g. protected incumbent rights) are not represented.

---

## Methods (summary)

**Model.** Urban water metabolism engine (`aiuwm_src`, called read-only): daily water
balance, cooling-tower mass balance, quality-limited cycles of concentration, and joint
reclaimed allocation. Allocation comes from the reviewed repository functions; no rule
logic is re-implemented.

**Estimand.** $dS_{\rm pot}=C-F=M_1-M_0$ in the fixed-pool regime, with $F$ and $C$ as
defined in Results §1. $M_1$ and $M_0$ are engine outputs at matched drivers.

**Design.** 408 paired scenarios: 2 domains × 4 published reclaimed-water compositions × 3
quality tiers ($\chi$ = 1.0, 0.5, 0.25) × 17 mixing ratios; plus a 2³ ablation (64 cells)
and boundary tests (quality-off, $\varphi\to0$).

**Quality tiers.** $\chi$ is the ratio of the quality-limited to design cycles of
concentration. $\chi=0.50$ corresponds to the PHREEQC calcite-derived value for IEUA
tertiary reclaimed water (2.52/5.0 = 0.504); $\chi=0.25$ is an extrapolated stress tier.

**Data.** Public water-chemistry sources (IEUA RP-1 2025; LADWP AWPF 2012; Figshare paired
study) are used as parameter-domain bounds, never as calibration targets or point-prediction
validation.

**Reproducibility.** Environment locked (Python 3.13.14, numpy 2.4.4, pandas 3.0.5,
matplotlib 3.11.2, phreeqpython 1.6.2). Obsolete scripts are marked in place and retained
for audit; superseding scripts are listed in `reproduction_manifest.md`.
