# Fig. 3 | City-level outcomes and the sign structure of dS_pot

**Most scenarios are beneficial, and q > 0 never fails.** Across the 813 solver-reliable grid
scenarios, the strict-sign partition of the primary estimand is **643 negative (beneficial) /
134 positive (harmful) / 36 exactly zero** (panel **b**). The 36 zeros are not numerical noise: they
are the exact analytic roots of the identity on the q = 0 branch, all 36 satisfying q = 0 with an
exactly zero identity residual, and they are kept as a separate class rather than being discarded
into a tolerance band. Panel **a** shows the full distribution on a symmetric-log axis, which is
strongly asymmetric: beneficial cases extend to about −64 000 ML while harmful cases reach about
+42 000 ML. Panel **c** partitions the same scenarios by q = (M₀ − M₁)/M₁ into **290 (q > 0) /
288 (q = 0) / 235 (q < 0)**, and within the q > 0 group the number of harmful outcomes is **0 of
290** — that is, q > 0 is a sufficient condition for the city to benefit.

**Data and methods.** All three panels use `A13_可靠性机制/supply_state_regimes.csv`, the
authoritative main grid. q is computed as (M0_ml − M1_ml) / M1_ml; the file does not carry a q
column. Column names `x_ai_B1_ml` / `x_ai_B2_ml` are swapped relative to their meaning and must be
read per `A13_可靠性机制/COLUMN_NAMES_CORRECTED.md`. City-level complete-species results are in
`A33_WP4_组成重构/wp4_results.csv` (n_eff = 47, all 47 beneficial, q split 23 / 24, 0 harmful).

**n.** n_eff = **813** of 1 052 grid rows after the dual gate (`status == converged_unique` AND
NOT `coc_floor_degenerate`); 239 rows are excluded. **Zero convention:** strict sign, dS_pot == 0.0
counted separately with no tolerance band. Applying a tolerance band of |dS_pot| < 10⁻⁹ instead
yields the older 631 / 102 split on only 733 judged rows and must not be used.

**Limitations.** The q > 0 sufficiency check has no positive counterexample (0 / 290 harmful) partly
because q > 0 is algebraically tied to the same accounting identity — it is an accounting
consistency check, not an independent predictive test, and the word "confirmed" must not be applied
to it. The city-level complete-species subset is only n_eff = 47.
