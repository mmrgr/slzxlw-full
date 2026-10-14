# Supplementary Information (A16, v2)

Companion to `manuscript_en_v2.md` — *Facility-versus-city accounting of reclaimed-water
cooling in AI data centres: a discharge–claim balance*.

> **Version note.** This SI replaces the v1 SI, which accompanied a manuscript whose
> "two opposing channels" mechanism has been **withdrawn** following a method audit
> (`../A13_可靠性机制/AUDIT_2026-10-14_撤回声明.md`).

---

## S1. Symbol table

| Symbol | Meaning | Unit | Source |
|---|---|---|---|
| $M$ | Facility cooling makeup (total) | ML/period | engine |
| $M_0$ | $M$ in the all-potable counterfactual ($\varphi=0$), same scenario | ML/period | engine |
| $M_1$ | $M$ in the reclaimed-substitution scenario | ML/period | engine |
| $E$ | Cooling-tower evaporation | ML/period | engine |
| $\mathrm{CoC}$ | Cycles of concentration | – | engine |
| $\varphi$ | Requested reclaimed volume fraction of makeup | – | control |
| $\varphi_{\rm eff}$ | Realised reclaimed fraction | – | engine |
| $x_{\rm AI}$ | Reclaimed volume allocated to the data centre | ML/period | allocator |
| $r_{\rm inc}$ | Reclaimed volume allocated to incumbent users | ML/period | allocator |
| $P$ | Nominal reclaimed pool (excludes added capacity) | ML/period | engine |
| $\Delta P$ | **Added** reclaimed capacity | ML/period | control |
| $F$ | **Discharge**: potable water the data centre stops withdrawing | ML/period | §S2 |
| $C$ | **Claim**: potable water displaced incumbents must now withdraw | ML/period | §S2 |
| $dS_{\rm pot}$ | City potable-withdrawal change $=C-F$ | ML/period | §S2 |
| $\chi$ | Quality severity, $\mathrm{CoC}_{\lim}/\mathrm{CoC}_{\rm design}$ | – | §S4 |
| $S_{\rm city}$ | Legacy estimand $=S_{\rm AI}+r_{\rm inc}-P$ | ML/period | §S2.3 |

Units: ML = 10³ m³; "period" = the 730-day frozen base unless stated.

**Withdrawn symbols (do not use):** $\psi$ (supply stress), $\Delta$ (unmet demand),
$\varphi^*$ (critical mixing ratio). See §S9.

---

## S2. Estimand

### S2.1 The discharge–claim balance

$$dS_{\rm pot} \;=\; C - F$$

$$F = M_0 - (1-\varphi_{\rm eff})\,M_1
\qquad
C = r_{\rm inc}(B_2) - r_{\rm inc}(B_1)$$

> **Critical definitional point.** $C$ must be evaluated **within the same scenario** as the
> counterfactual — i.e. $r_{\rm inc}$ at $\varphi=0$ under the *same* capacity regime.
> Using a fixed nominal pool $P$ instead happens to be equivalent when $\Delta P=0$ but is
> **wrong** when $\Delta P>0$, because the total budget is then $P+\Delta P$. (This defect
> was found and corrected in the audit.)

### S2.2 Why not the previous formulation

The superseded draft computed $S_{\rm city}=S_{\rm algebra}-\lambda\Delta$ with
$\Delta=W\max(0,\psi-1)$. That is invalid on two counts:

1. **Category error.** $D_{\rm inc}$ was read from the engine's `gap`, which is
   `reuse_elig − P0` — the incumbents' unmet **reclaimed-water** demand
   (`A7_质量分配联合/T2_joint_quality_allocation.py:97-102`), not their **potable** demand.
2. **Dimensional error.** $S_{\rm city}$ is a *withdrawal change*; $\Delta$ is an
   *unmet-demand gap*. Subtracting them conflates two different physical quantities,
   violating the project's own rule that indices A/B/C must never be merged.

### S2.3 Relation to the legacy estimand

$$dS_{\rm pot} = M_1 - M_0 = -(M_0 - M_1)$$

In the fixed-pool regime this equals $-S_{\rm city}$ (up to the quality-penalty term), so
**$dS_{\rm pot}\ge0 \iff S_{\rm city}\le0$**: the original conclusion is confirmed, now via
an explicit two-flow balance.

---

## S3. Main results and their exactness

| Quantity | Value | Residual |
|---|---|---|
| Pure displacement: $x_{\rm AI}=r_{\rm inc}(B_2)-r_{\rm inc}(B_1)$ | — | **5.5 × 10⁻¹² ML** |
| Identity $C-F=M_1-M_0$ | — | **3.3 × 10⁻¹¹ ML** (sign agreement 1.000) |
| $dS_{\rm pot}\ge0$, all 408 scenarios | 0 negative / 384 positive / 24 zero | — |
| No-quality-constraint case ($\chi\to\infty$) | $dS_{\rm pot}=0.0000$ ML | 8/8 configurations |
| $\varphi\to0$ | $dS_{\rm pot}=0$ | 12/12 scenarios |

### S3.1 Quality dependence

| $\chi$ | max $dS_{\rm pot}$ (ML) | mean (ML) | realised CoC |
|---|---:|---:|---|
| 1.00 | 910 | 494 | 4.40–5.00 |
| 0.50 | 2 953 | 1 649 | 2.23–2.50 |
| 0.25 | **29 103** | 19 086 | 1.18–1.25 |

Monotone in quality severity — verified as gate H4.

### S3.2 Regime boundary

| Regime | $F$ vs $C$ | $dS_{\rm pot}$ (ML) |
|---|---|---|
| Fixed pool ($\Delta P=0$) | $F\le C$ | ≥ 0 |
| Added capacity ($\Delta P>0$) | $F$ may exceed $C$ | **−15 030 to −4 639** |

---

## S3.3 Allocation-rule sensitivity

The displacement premise ($x_{\rm AI}\equiv$ incumbent loss) is a property of the model's
allocator. It is tested against the engine's **native incumbent-protection** parameter
(`JointQualityRequest.incumbent_reclaimed_ml`, "protected before incremental demand",
`reclaimed_allocation.py:60`). Coverage: 2 domains × 2 compositions × 5 protection levels ×
4 mixing ratios = 80 scenarios.

| protection level | $dS_{\rm pot}$ range (ML) | substantive n | trivial n |
|---|---:|---:|---:|
| 0.00 (AI priority = A13c) | 974 – 2 953 | 16 | 0 |
| 0.25 | 743 – 2 196 | 16 | 0 |
| 0.50 | 355 – 1 203 | 16 | 0 |
| 0.75 | — | 0 | 16 |
| 1.00 | — | 0 | 16 |

- **Pure displacement holds exactly at every level**: $\max|x_{\rm AI}-C| = 0.0$ ML.
- **$dS_{\rm pot}>0$ in all 48 substantive scenarios** (0 negative).
- Protection **monotonically reduces** the effect (2 953 → 2 196 → 1 203 ML).
- **Trivial cases excluded**: at protection $\ge0.75$ the protected claim
  (0.75 × 33 779 = 25 334 ML) exceeds the pool (24 404 ML), so the pool is fully reserved,
  the data centre receives **zero** reclaimed water ($x_{\rm AI}=0$, $\varphi_{\rm eff}=0$),
  and $dS_{\rm pot}=0$ is vacuous. **These 32 cases are reported as non-evidence.**

> **Interpretation.** Protecting incumbent users mitigates the city-level cost but cannot
> turn it into a net benefit. The **sign** of the effect is not an artefact of the
> allocation rule within the range where reuse actually occurs.

---

## S4. Water chemistry

- Constraint: `coc_mode='quality_limited'`; fixed point solved so blended makeup stays
  within limits.
- Independent implementation: PHREEQC via `phreeqpython==1.6.2` with `vitens.dat`;
  phases Calcite / Dolomite / Gypsum / Anhydrite / SiO₂(a).
- IEUA tertiary reclaimed water: ratio criterion gives CoC = 3.57; PHREEQC gives **2.52**
  (calcite-controlled) → the ratio method **overestimates** admissible CoC by ~40%.
- **Quality tiers used here are anchored to verified values**:
  $\chi=0.50$ corresponds to the PHREEQC-derived 2.52/5.0 = **0.504** (IEUA).
  $\chi=1.00$ means the limit does not bind. **$\chi=0.25$ is an extrapolated stress tier**
  (severer than any observed sample) and is labelled as such.
- Limits: strict = **GB/T 19923-2024**, baseline/permissive = **GB/T 50050-2017**.
  The engine placeholder tier (hardness + alkalinity 1,200 > 1,100 mg/L) violates
  GB/T 50050-2017 and is **retracted**.

**Limitations**
1. **No antiscalant.** Real towers use scale inhibitors to hold LSI well above calcite
   saturation. Our constraint is a **no-dosing thermodynamic upper bound**, so the quality
   cost is a **conservative (high)** estimate.
2. **Database mismatch.** `vitens.dat` is a **drinking-water** thermodynamic database;
   reclaimed water contains organics, phosphate and trace metals. "Calcite-dominated" holds
   **within this database**.
3. Engine placeholder parameters remain (see §S7).

---

## S5. Counterfactual design

| Scenario | Meaning |
|---|---|
| **B0** | No data centre |
| **B2** | Data centre, all potable ($\varphi=0$) — the reference for $C$ |
| **B1** | Data centre, reclaimed at target $\varphi$ |

Matched drivers (same meteorology, load factor, representative day) across B1/B2; the
primary contrast is B2→B1. Allocation is called from the reviewed repository functions
(`allocate_shared_surplus`, `allocate_dedicated_incremental`,
`solve_joint_quality_allocation`); **no rule logic is re-implemented**.

**Regimes.** *Fixed pool* ($\Delta P=0$) is the primary regime. *Added capacity*
($\Delta P>0$) is reported separately because the identity does not hold there.

---

## S6. Priors, uncertainty and their limits

- Morris screening + Sobol variance decomposition on the legacy estimand
  $y=S_{\rm city}/M_0$: `gap_scale` $S_1=0.417/S_T=0.762$; `pool_scale` 0.265/0.334;
  `dp_scale` 0.141/0.228; `ai_target` 0.021/0.028.
- 700-sample LHS under **uniform** priors.
- **Prior sensitivity** (`prior_bounds.json`, **27 prior combinations** = 3×3×3 over
  pool/gap/dp priors × 600 LHS samples = 16 200 engine solves, 3 099 s):

| quantity | min | median | max | **span** |
|---|---:|---:|---:|---:|
| $P(S_{\rm city}>0\mid\Delta P{=}0)$ | 0.0000 | 0.0000 | 0.0050 | **0.0050** |
| $P(S_{\rm city}>0\mid\Delta P{=}1)$ | **0.4283** | 0.6383 | **0.7850** | **0.3567** |
| $P(\Delta P^*\le1)$ | 0.2650 | 0.6017 | 0.7750 | 0.5100 |

> **Two findings.**
> (i) The **share-only probability is robustly zero**: across all 27 prior combinations it
> never exceeds 0.0050, and those values are floating-point residuals (§S2.2). The
> mechanism conclusion is therefore **prior-insensitive**.
> (ii) The **capacity-inclusive 0.62 is not robust at all**: it spans **0.428–0.785**
> (range 0.357). The frozen value 0.62 is the *uniform-prior* value and lies inside the
> range, but the manuscript reports it **only as "under uniform priors"** and never as a
> real-world probability of benefit. **Red-team item M5/P2 is closed as a concession, not
> a fix.**

> **Discipline**: all probability statements are **model probabilities under the stated
> priors**, not observed event frequencies. Note also that the water-sample dimension is
> drawn uniformly over 5 laboratory samples, one of which is non-reclaimed (brackish) and
> two of which have estimated TDS, so it carries no global-frequency meaning.

---

## S7. Placeholder and declared-value inventory

| Item | Status | Action |
|---|---|---|
| Engine hardness / alkalinity / SiO₂ placeholders | remain in engine | replace before submission |
| PUE = 1.3 | placeholder | cite source |
| Design CoC = 5.0 | arbitrary (red-team C6) | report with effective CoC 5.444 |
| Assumed TDS = 650 mg/L | placeholder (2 ions only) | cite or bound |
| Membrane / chemical energy and reagent use | **declared values** | cite (Stillwell 2014 candidate) |
| Carbon intensity 0.35 kgCO₂e/kWh | engine ratio | replace with grid factor |
| Cost figures (CNY) | declared values | **relative ordering only** |
| GSA facility anchor | 102 days, one non-DC facility | magnitude only; **no point prediction** |
| Antiscalant | **not modelled** | quality cost is conservative |

---

## S8. Evidence-status disclosure (required)

The engine-side evidence register applies a stricter bar (external observation) than the
paper side (within-model numerical closure). The difference must be disclosed:

| Engine claim | Status |
|---|---|
| C3 "reclaimed use always reduces city withdrawal" | **REFUTED_IN_BOUNDED_RUN** |
| C4 quality feedback vs independent chemistry | NOT_READY |
| C5 facility makeup/blowdown out-of-sample | NOT_READY |
| C7 A0–A3 adaptation restores net savings | NOT_READY |
| C8 synthetic hydrology represents observed reliability | NOT_READY |
| G2 chemistry gate / G3 facility holdout | NOT_READY |

---

## S9. Retracted results (audit trail)

Following the 2026-10-14 method audit, the following are **withdrawn** and must not be
cited from any document:

| Retracted claim | Reason |
|---|---|
| "Two opposing channels (quality vs reliability)" | Quality channel used mis-specified $D$; "reliability channel" was an artefact of subtracting an unmet-demand gap from a withdrawal change |
| Supply stress $\psi=(D_{\rm inc}+W_{\rm AI,pot})/W$ | $D_{\rm inc}$ read from `gap` = unmet **reclaimed** demand, not potable demand |
| $\Delta=W\max(0,\psi-1)$; "3,840 grid points, zero exceptions" | Formula has no physical basis |
| "Old identity understates urban loss by up to 39,641 ML" | That figure was the maximum of the invalid $\Delta$ |
| Critical mixing ratio $\varphi^*$; "supply floor" at $W_{\rm scale}\le0.85$ | Dependent on the invalid $\psi$ |
| "Mechanism is orthogonal to capacity expansion" | Premise was the invalid formula |

**Retained and now independently derived:** $S_{\rm city}\le0$ in the fixed-pool regime.

---

## S10. Negative and failed results (retained)

1. **$dS_{\rm pot}$ never becomes negative in the fixed-pool regime** — reclaimed
   substitution never reduces urban potable withdrawal when supply is fixed.
2. **The identity is exact only in the fixed-pool regime.** In the added-capacity regime it
   fails (deviation up to 1.5 × 10⁴ ML) and the sign reverses; this is reported as a
   regime boundary, not hidden.
3. **Cross-domain transfer is weak.** The only genuine holdout — a one-parameter transfer of
   $\varphi_{\rm eff}$ with the parameter fitted on D-HA and frozen — gives
   **R² = 0.599** (median absolute error 0.028) against a trivial baseline of −0.034.
   The identity's own "R² = 1.000" in the holdout domain is an **algebraic re-derivation**
   (it reuses the holdout domain's $M_0,M_1$) and is **not** validation.
4. **Ablation gate G5 records a deliberate non-failure**: the identity is *expected* not to
   hold in the added-capacity regime.
5. **Grid resolution — corrected assessment.** An earlier version of this analysis reported
   that only **15.4%** of feasible sets agreed between coarse and fine grids, and inferred
   that bottleneck identification is resolution-sensitive. **That inference was wrong**: the
   criterion compared *counts of feasible grid points*, but when the quality limit is loose
   almost the whole grid is feasible, so a finer grid necessarily contains more feasible
   points (24 → 48 → 96 → 192) and the counts can never be equal. With the correct criterion
   — the **displacement of the feasible boundary** $\rho_{\min}$ — the boundary moves by
   **at most one grid step (0.015625)**, and **100%** of $({\rm sample},\chi)$ curves
   converge at every refinement level (11/11 × 3 samples). No non-monotone feasible regions
   were found (**0/39** curves).
   **Residual limitation**: the published rule "the constraint with the largest exceedance at
   the first failing grid point" is **not reproducible** from current outputs, because
   `city_outcome` does not expose per-species concentrations and limits. The manuscript
   therefore does **not** rest any claim on that rule.
6. **Earlier retractions (unchanged)**: A3 "+13,974 ML/yr" was a degenerate-day artefact;
   the τ stress axis is retired; index B (basin net consumption) is
   `NOT_IDENTIFIABLE_FROM_AVAILABLE_DATA`; the dimensionless "collapse law" is an algebraic
   identity, not a migratable law.
