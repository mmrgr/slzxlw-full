# Fig. 6 | External anchoring and partial identification: the committed share is not identified

**The share of real facilities in the committed branch is bounded, not estimated.** Panel **a**
states the central point: because the demand side is unobserved, the physical constraint
0 ≤ E_i ≤ D_i admits both branch states for any plant, so the prevalence of the fully-committed
regime is a **partial-identification** problem whose only provable bound is **[0 %, 100 %]**. No
point estimate and no confidence interval are reported, and the superseded claim that "above 95 %
of real facilities are fully committed" is **withdrawn** (`status_of_original_claim =
WITHDRAWN_AS_UNIDENTIFIED`). Panel **b** shows the one distributional fact that *is* observable:
real plant throughput is **strongly right-skewed** (median 3.0, p90 44.4, p99 210.4), so a few very
large plants carry the tail, while panel **c** reports the one quantity that *is* identifiable —
**capacity feasibility**, i.e. the fraction of plants whose production capacity (throughput × r)
could support a scheme exceeding the modelled threshold. That fraction spans **0.39 % to 6.55 %**,
rising with the recovery fraction r and slightly higher under the coastal domain.

**Data and methods.** `A30_WP0取证/a24b_partial_id_summary.json` (panels **a** and **b**) and
`A30_WP0取证/a24b_capacity_table.csv` (panel **c**). The threshold anchors are 61.4–66.9 ML d⁻¹
(first-year) and 73.5–73.7 ML d⁻¹ (half-threshold).

**n.** n = **10 826** real treatment plants for the throughput distribution in panel **b**. No sample
size is attached to the committed share, because the quantity is not identified and therefore has
no estimator.

**Limitations.** Panel **c** states **capacity feasibility only** — that a plant *could* produce
enough reclaimed water to exceed the modelled threshold. It says nothing about existing demand, and
it must not be converted into a statement about how many plants actually sit in the committed
branch. Exactly two claims are permitted: (a) real plant throughput is strongly right-skewed; and
(b) only about 0.4–7 % of plants have the capacity for a surplus-type scheme at the modelled
threshold. External data serve only as a capacity-distribution comparison; with no demand-side
observation, the branch share remains unidentifiable and is reported as a provable bound.
