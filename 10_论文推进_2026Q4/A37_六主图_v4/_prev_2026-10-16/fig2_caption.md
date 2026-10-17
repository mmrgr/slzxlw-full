# Fig. 2 | Water chemistry and cooling: opposite-signed CoC responses and the binding species

**Water quality controls the direction of the cooling-water response.** Blending reclaimed water
with potable make-up changes the achievable cycles of concentration (CoC). Panel **a** shows that the
two complete-species samples drive CoC in **opposite directions** as the blending ratio φ rises:
IEUA tertiary reclaimed water is alkalinity-limited and its CoC **falls** (3.5 → 2.65), whereas LADWP
RO product rises until it is truncated at the design cap of **5.000**. Panel **b** identifies why
alkalinity is the binding constraint for IEUA: its limit-to-concentration ratio is **2.500**, the
smallest of the five species, while TDS is 4.966, hardness 5.019, chloride 7.000 and silica 7.292.
Because only alkalinity is close to its limit, the other four species have headroom and cannot bind.
Panel **c** shows that which species binds CoC depends on the criterion used: the engine's
single-species TDS judgement gives 4.97 for IEUA, an all-species ratio judgement gives 3.57
(alkalinity), and a PHREEQC calcite-saturation judgement gives 2.52.

**Data and methods.** Panels **a** uses `A33_WP4_组成重构/wp4_results.csv` at the `pool_scale = 1`
slice; panel **b** uses `A4_水化学参数域/T6_water_chemistry_samples.csv` together with the cited
baseline limit tier (GB/T 50050-2017, total hardness + alkalinity = 1 100 mg/L) recorded in
`A27_引用限值/A27_引用限值报告.md`; panel **c** uses `A4_水化学参数域/T6_coc_limits.csv`.

**n.** n_eff = 47 city-level scenarios after the dual gate (`status == converged_unique` AND
NOT `coc_floor_degenerate`), split IEUA n = 24 and LADWP n = 23. φ = 0 rows are removed by the
gate because the CoC floor becomes degenerate there.

**Limitations.** Panel **b** is a **static headroom ratio** at the baseline limit tier, not a dynamic
threshold; the corresponding dynamic sign-flip point for alkalinity is ≈ 2.615× (see Fig. 5). Only
**two** complete-species samples exist, so the opposite-signed curves in panel **a** are a
two-sample contrast and must not be read as a population-level result. The engine exposes limits
per species, whereas GB/T 50050-2017 states a combined hardness + alkalinity criterion, so no single
bar in panel **b** reproduces the standard verbatim.
