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

**Sign criterion** (100% agreement, 1,152/1,152): $dS_{\rm pot}<0 \iff x_{\rm AI}+(M_0-M_1) > C_{\rm disp}$.

### S3.1 No single ratio predicts the sign

| $C/x_{\rm AI}$ | n | $dS<0$ | range (ML) |
|---|---:|---:|---|
| 0.00 | 447 | 430 (96%) | −98,158 … +33,217 |
| 0.01–0.25 | 122 | 97 (80%) | −95,375 … +485,436 |
| 0.25–0.50 | 128 | 66 (52%) | −87,758 … +598,752 |
| 0.50–0.75 | 66 | 20 (30%) | −78,507 … +343,916 |
| 0.75–1.00 | 351 | 136 (39%) | −66,322 … +255,180 |

An intermediate draft claimed the extremes were "pure" (ratio 0 ⇒ no positive; ratio 1 ⇒ no
negative). That was a **pre-fix artefact** of frozen composition; with composition live
**114 purely-displaced cases are negative**, because a severe quality penalty can outweigh a
complete displacement. The three-term criterion above supersedes the ratio heuristic.

**Composition modulation**: LADWP 237 negative / 31 positive; AI-UWM 261/7; IEUA 153/115;
Figshare RW 98/170. With quality fully relaxed (`limit_scale` = 10⁶): **208 negative, 0
positive**.

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
