# Fig. 6 | External anchoring and partial identification: the committed share is not identified

**The share of real facilities in the committed branch is bounded, not estimated — and none of the
new external evidence changes that.** Panel **a** states the central point: because the demand side
is unobserved, the physical constraint 0 ≤ E_i ≤ D_i admits both branch states for any plant, so the
prevalence of the fully-committed regime is a **partial-identification** problem whose only provable
bound is **[0 %, 100 %]**. No point estimate and no confidence interval are reported, and the
superseded claim that "above 95 % of real facilities are fully committed" is **withdrawn**
(`status_of_original_claim = WITHDRAWN_AS_UNIDENTIFIED`). Panel **b** shows the one distributional
fact that *is* observable: real plant throughput is **strongly right-skewed** (median 3.0, p90 44.4,
p99 210.4), so a few very large plants carry the tail, while panel **c** reports the one quantity that
*is* identifiable — **capacity feasibility**, i.e. the fraction of plants whose production capacity
(throughput × r) could support a scheme exceeding the modelled threshold. That fraction spans
**0.39 % to 6.55 %**, rising with the recovery fraction r and slightly higher under the coastal domain.

Panels **d–g** add the external-validity evidence obtained after this figure was first built. Panel
**d** classifies **141 documented real reclaimed-water projects** by the source table's own category
codes: **industrial cooling / general industrial reuse (B3) is the single largest category, 40
projects (28.4 %)**, and **68.4 % (26 of 38)** of the B3 projects reporting capacity fall inside the
scale range modelled here (10³–10⁵ m³ d⁻¹; B3 capacity median 4,000 m³ d⁻¹, p25 1,050, p75 17,500).
Panel **e** shows the cooling-water share of industrial withdrawal across **39 sectors**: it spans the
entire range, **0.000 to 0.990**, with median **0.184** and 7 sectors above 0.5. The model's **0.258**
is the **mean of the 39 sector means**, independently recomputed as **0.25799037378455597** and
identical digit-for-digit to the stored anchor, placing it near the **62nd percentile** — a mid-to-upper
representative value, not a universal constant. Panel **f** compares **city-level industrial tap-water
tariffs** (62 city series, 7,730 monthly observations, 2007–2017; **61 summarisable cities**) with the
documented cost of B3 projects: the cross-city median tariff is **1.550 CNY m⁻³** (city range
**0.590–6.650**), against a B3 reclaimed-water total unit cost median of **2.413 CNY m⁻³** — a ratio of
**1.56**, i.e. **reclaimed water costs about 56 % more than industrial tap water** — and only **17 of
61 cities (27.9 %)** have a tariff above the reclaimed-water cost. Panel **g** summarises what this
buys and what it does not: the use case, its scale, the traceability of 0.258 and the order-of-magnitude
cost comparison are **gained**; the identification problem is **not changed**.

**Data and methods.** `A30_WP0取证/a24b_partial_id_summary.json` (panels **a**, **b**) and
`A30_WP0取证/a24b_capacity_table.csv` (panel **c**). Panels **d–f** use
`A39_WP8_外部效度/wp8_real_reuse_cases_summary.json`,
`A39_WP8_外部效度/wp9_cooling_share_summary.json` and
`A39_WP8_外部效度/wp10_water_price_summary.json`, all derived from the CC-BY source-data package of
Shen et al. (2026, *Nature Water*). Category codes in panel **d** are extracted mechanically from the
text prefix and cross-checked against a plain-text search for "Industrial cooling" (agreement on
141 of 141 rows). Threshold anchors in panel **c** are 61.4–66.9 ML d⁻¹ (first-year) and
73.5–73.7 ML d⁻¹ (half-threshold).

**n.** Panel **b**: n = **10 826** real treatment plants. Panel **d**: n = **141** documented projects
(38 with capacity, 40 with cost). Panel **e**: n = **39** of 41 sectors carrying a mean; the 2 missing
sectors are counted explicitly and **not** zero-filled. Panel **f**: 62 city tariff series, 7,730
monthly observations, 61 summarisable cities. **No sample size is attached to the committed share**,
because the quantity is not identified and therefore has no estimator.

**Limitations.** Panel **c** states **capacity feasibility only** — that a plant *could* produce enough
reclaimed water to exceed the modelled threshold. It says nothing about existing demand, and it must
not be converted into a statement about how many plants actually sit in the committed branch. The
WP8 catalogue is a **case collection, not a random sample**, so **28.4 % characterises those documented
projects and is not a national prevalence**; it contains **no demand-side field** and therefore does
**not** shrink, weaken or narrow the [0 %, 100 %] bound of panel **a**, which remains the only statement
about committed prevalence. Panel **e** measures "cooling withdrawal / industrial withdrawal", which is
a different quantity from "reclaimed water used for cooling" and must not be substituted for it; the
sector codes carry no name mapping in the source table and none is guessed. Panel **f** is an
**order-of-magnitude comparison only**: it contains prices with no contracts, allocations or deliveries,
so no causal claim (cost → pool occupancy) can be built from it and no investment or net-present-value
statement is made; the tariffs are also not those of the (synthetic) model domain. Taken together the
external data constrain parameter ranges and bound the physical scope for expanding reclaimed supply;
they do **not** validate city-level predictions and do **not** determine regime prevalence.

**Not shown in this figure (text-only anchor).** A further external source — the same
package's project-level deployment records (597 records) — is reported in the main text §6
but deliberately **not** drawn here: of the 597 records only **11 report a positive
reclaimed-water capacity addition** (median **3.0 × 10⁴ m³ d⁻¹**; **11/11 = 100%** inside the
modelled 10³–10⁵ m³ d⁻¹ range), and the sheet is stored as **two blocks that disagree for six
provinces**, so it must not be summed. It is therefore kept to a single sentence in the text
with its limits stated, rather than given a panel that could invite a quantity reading.
