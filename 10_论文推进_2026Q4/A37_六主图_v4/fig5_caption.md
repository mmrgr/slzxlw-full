# Fig. 5 | Sensitivity and extreme events: a sign lever within a bounded limit domain

**Which parameter moves the outcome, how much of the variance do the main effects explain, does
the sign lever survive a change of limit tier, and do observed extremes flip the sign?** Panel **a**
ranks parameters by Morris μ\*: `limit_scale` (≈ 4.5 × 10⁴ ML) and `x_alkalinity` (≈ 2.5 × 10⁴ ML)
lead by a wide margin, with all remaining parameters an order of magnitude smaller; the very large σ
values indicate strong interaction. Panel **b** gives the Sobol decomposition for the same
configuration — `limit_scale` S_T = **0.944** and `x_alkalinity` S_T = **0.682** — now overlaid with
**95 % bootstrap confidence intervals** from an independent Saltelli design (400 replicates, 7
parameters, 128 base samples per configuration): S_T(`limit_scale`) = **0.330 [0.075, 0.792]**,
S_T(φ) = **0.926 [0.051, 2.568]** and S_T(alkalinity) = **0.125 [0.015, 0.305]**. The sum of
first-order indices is **ΣS₁ = 0.19 for IEUA (n_eff = 117) and 0.58 for LADWP (n_eff = 128)** — far
below 1 — so main effects explain only part of the variance and the ranking must not be read as "the
top two parameters suffice". Because φ's interval is so wide, **only its direction is quoted; no
single value is reported for it**. Panel **c** carries the panel-robustness result: the claim that
alkalinity is the only single-species sign lever holds under the **cited** (2200/700/750/**350**/175)
and **permissive** (2600/1000/750/**350**/175) tiers — both of which leave the alkalinity limit at
350 — but **not** under the **strict** make-up tier (1000/250/450/350/30), where the binding species
become **silica** (IEUA) and **TDS** (LADWP) and **no single-species perturbation flips the sign at
all**. Panel **d** shows that observed-driver extremes produce **no sign flip**: 4 comparable heatwave
and 4 comparable drought windows yield **0 / 8** flips, the largest magnitude shift being only 1.139×
the full-year value.

**Data and methods.** `A34_WP5_敏感性与极端事件/wp5_morris.csv`, `wp5_sobol.csv`,
`wp5_extreme_cases.csv` and `wp5_extreme_summary.json` (panels **a**, **b** point estimates, **d**);
`A38_模拟审稿/ne4_sobol_bootstrap_summary.json` (panel **b** intervals; Saltelli + Sobol estimator
with 400 bootstrap replicates, seed 20261016) and `A38_模拟审稿/ne2_panel_robustness_summary.json`
(panel **c**; 3 limit tiers × 2 complete-species samples × 2 domains at φ = 0.6, single-species
concentration perturbed ×0.5 / ×2.0). Extreme windows reuse the frozen module and replace only the
window totals (energy, representative day, pool, gap), consistent with the established
time-resolution methodology.

**n.** Morris/Sobol point estimates: Saltelli design on `ha | IEUA`, 2048 points. NE-4 confidence
intervals: n_eff = **117** (IEUA, 11 of 128 points degenerate and dropped) and **128** (LADWP).
NE-2: 2 complete-species samples × 3 tiers × 2 domains. Extreme-event analysis: n_eff = **64** of 64
windowed scenarios after the dual gate. Both Morris/Sobol configurations are identified: the LADWP configuration retains all 128 base
points, while the IEUA configuration loses 11 of 128 to degenerate evaluations, which are
dropped rather than imputed. **Zero convention:**
|dS_pot| < 10⁻⁶ ML counted as 0.

**Limitations.** (i) ΣS₁ = 0.19 (IEUA) / 0.58 (LADWP) is far below 1, so the parameter ranking
describes only part of the variance, the remainder being interactions; (ii) φ's total-effect interval
[0.051, 2.568] is so wide that no point value for it may be quoted; (iii) the alkalinity critical
value ≈ 2.615× has **no observational support** (authoritative samples: IEUA 140 mg/L, LADWP
7.1 mg/L), so it is a sensitivity boundary rather than a predicted operating regime, and the "only
sign lever" statement is a lever **identified within an explicitly bounded limit domain** — it does
not survive the strict tier, where the tier change alone also flips the sign for LADWP (0 → +2.821 ML);
(iv) sign flips do occur under forced perturbation (`e_scale` ≈ 6.75×, 20 / 20 matching the
closed-form condition), but that direction is an accounting artefact of F turning negative, not a
city becoming harmed, and beyond `e_scale` ≈ 10 the engine is in linear extrapolation; (v) the
observed-extreme result rests on a single city domain.
