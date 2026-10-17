# Fig. 5 | Global sensitivity and extreme events: alkalinity is the only sign lever

**Two parameters dominate, interactions are strong, and observed extremes do not flip the sign.**
Panel **a** ranks parameters by Morris μ\*: `limit_scale` (≈ 4.5 × 10⁴ ML) and `x_alkalinity`
(≈ 2.5 × 10⁴ ML) lead by a wide margin, with all remaining parameters an order of magnitude
smaller; the very large σ values indicate strong interaction. Panel **b** gives the Sobol
decomposition for the same configuration: `limit_scale` has S_T = **0.944** and `x_alkalinity`
S_T = **0.682**, while the sum of all first-order indices is only **ΣS₁ ≈ 0.22** — that is, main
effects explain about one fifth of the variance and the rest is interaction plus unmodelled
dimensions. Panel **c** reports the boundary scan over 41 points × 2 domains × 2 samples with the
other parameters frozen: **`x_alkalinity` is the only single parameter that can change the sign**
of dS_pot, at a critical value of **≈ 2.615×**, whereas `limit_scale` — despite having the largest
μ\* and S_T — changes magnitude only and never crosses zero within the scanned range. Panel **d**
shows that observed-driver extremes produce **no sign flip**: 4 comparable heatwave windows and
4 comparable drought windows yield **0 / 8** flips, with the largest magnitude shift only 1.139× the
full-year value.

**Data and methods.** `A34_WP5_敏感性与极端事件/wp5_morris.csv`, `wp5_sobol.csv`,
`wp5_extreme_cases.csv` and `wp5_extreme_summary.json`. Morris/Sobol use a Saltelli design on the
`ha | IEUA` configuration. Extreme windows reuse the frozen module and replace only the window
totals (energy, representative day, pool, gap), consistent with the established time-resolution
methodology.

**n.** Extreme-event analysis: n_eff = **64** of 64 windowed scenarios after the dual gate.
Morris/Sobol: the LADWP configurations return **NOT_IDENTIFIABLE** (6–7 of 512 Saltelli points fail
the gate and the engine propagates NaN silently into the variance) and are therefore omitted, not
imputed. **Zero convention:** |dS_pot| < 10⁻⁶ ML counted as 0.

**Limitations.** The LADWP Sobol indices are genuinely not identifiable and are reported as such
rather than filled in. The alkalinity critical value of ≈ 2.615× has **no observational support** —
the authoritative samples are IEUA 140 mg/L and LADWP 7.1 mg/L — so it is a sensitivity boundary,
not a predicted operating regime; LADWP does not reach it (its limit/concentration ratio is 49.3).
Sign flips do occur under forced perturbation (e_scale ≈ 6.75×, 20 / 20 matching the closed-form
condition), but that direction is an accounting artefact of F turning negative, not a city becoming
harmed, and beyond e_scale ≈ 10 the engine is in linear extrapolation with no observational support.
The observed-extreme result rests on a single city domain.
