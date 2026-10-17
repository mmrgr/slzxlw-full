# Fig. 4 | Independent pre-intervention prediction of the sign of dS_pot

**Chemistry alone fails; chemistry combined with allocation succeeds out of sample.** Using only
quantities observable *before* the intervention, panel **a** compares three predictors against the
majority baseline of **0.861**. A chemistry-only rule (q > 0) reaches only **0.671** — worse than
predicting the majority class — while an allocation-only rule reaches 0.760 and the combined
disjunction C4 (q > 0 **OR** pool_scale ≥ 2) reaches **0.906**. Panel **b** shows the leave-one-sample-out
test, in which the rule is re-selected on three samples and evaluated on the held-out fourth: the
mean held-out accuracy is **0.901** against a mean baseline of **0.859**, the gain surviving on the
real (non-model) samples IEUA (0.94 vs 0.76) and LADWP (1.00 vs 1.00). Panel **c** breaks the
chemistry-only failure down by sample, showing it collapses on real samples — IEUA 0.24 and
Figshare RW 0.45 — while appearing perfect on the AI-UWM model assumption (1.00) and LADWP (1.00).
Panel **d** shows the C4 decision space with its confusion counts (TP = 602, FN = 29, TN = 62,
FP = 40).

**Data and methods.** `A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json`,
`wp2_e3b_combined_prediction_summary.json`, `wp2_e3_predictions.csv` and `wp2_e3b_features.csv`.
The predictor signature uses only pre-intervention quantities (`rec_chem`, φ, pool_scale); all
post-simulation quantities (x_AI, M0, M1, C, F, dS_pot, φ_eff, CoC_AI) are on the forbidden-input
list, and leakage is prevented by group-wise (leave-one-sample-out) splitting.

**n.** n = 813 reliable scenarios; n_eff = **733** after excluding 80 near-zero rows
(|dS_pot| < 10⁻⁹). Held-out group sizes are 184 / 170 / 196 / 183.

**Limitations.** The predictor is causal only for the mechanism it encodes and still requires
allocation-side (pool) data, so it is not a purely chemical early-warning rule; it provides no
city-level calibration and has not been validated on operational utility data. AI-UWM and
Figshare RW are incomplete-species samples (2–3 of 5 species), so their per-sample accuracies in
panels **b** and **c** are supplementary-only. The earlier claim that the 1.0000 criterion agreement
constituted a prediction or discovery is downgraded to an accounting consistency check.
