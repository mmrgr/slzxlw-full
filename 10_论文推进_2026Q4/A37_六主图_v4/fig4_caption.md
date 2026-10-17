# Fig. 4 | Independent pre-intervention prediction of the sign of dS_pot

**Chemistry alone fails; chemistry combined with one allocation quantity is a candidate.**
Using only quantities observable *before* the intervention, panel **a** compares three
predictors against the majority baseline of **0.809**. A chemistry-only rule (q > 0) reaches
only **0.675** — worse than predicting the majority class — while an allocation-only rule
reaches 0.760 and the combined disjunction C4 (q > 0 **OR** pool_scale ≥ 2) reaches **0.914**.
Panel **b** shows the leave-one-composition-out test, in which the rule is re-selected on three
samples and evaluated on the held-out fourth: the mean held-out accuracy is **0.917** against a
mean baseline of **0.815**, and the fold-by-fold gain printed under each pair of bars gives
IEUA **+0.184** (0.94 vs 0.76) and Figshare RW **+0.225** (0.73 vs 0.51), while the two folds
whose baseline is already saturated at 1.000 (AI-UWM and LADWP) give **+0.000** and carry no
information either way. The **median fold gain is +0.092**. Two informative folds out of four,
with no fold that varies the demand side, support the criterion as a **candidate** rather than
a validated rule, and we report it in those terms.

> **Superseded reading.** An earlier version of this figure reported a median fold gain of 0.000
> and withdrew the out-of-sample claim. That version used a water-chemistry table in which the
> Figshare composition was missing its sulphate and alkalinity (a parsing bug, since repaired —
> see SI S3.3). With the composition repaired the Figshare fold moves from −0.018 to +0.225 and
> the median from 0.000 to +0.092, so **that withdrawal was partly an artefact of the data
> defect**. The conclusion is kept conservative for the reason above, not because of the
> earlier fold pattern.

Panel **c** breaks the chemistry-only failure down by sample, showing it collapses on real
samples — IEUA 0.24 and Figshare RW 0.45 — while appearing perfect on the AI-UWM model
assumption (1.00) and LADWP (1.00). Panel **d** shows the C4 decision space with its confusion
counts.

**Data.** `A31_WP2_假设冻结/wp2_e3_independent_prediction_summary.json`,
`wp2_e3_predictions.csv`, `wp2_e3b_combined_prediction_summary.json`, `wp2_e3b_features.csv`.
Predictor construction uses chemistry and limits only; the solver is not called.
The equivalent computation on the two complete-composition samples only is reported in SI S16.
