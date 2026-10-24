# Reviewer 2 Attack List

## 1. Is the “local saving versus city saving” result a bookkeeping artefact?

- Current evidence: R9 reports B0 and B1/B2 quantities separately and exposes incumbent potable changes.
- Missing evidence: independent review of allocation rules, multi-DC production time series, and alternative priority policies.
- Required experiment: permutation and policy sensitivity under shared and dedicated supply with fixed paired drivers.
- Safe wording until resolved: “The model identifies conditions under which the estimands diverge”; do not state a universal failure.

## 2. Does Q1 use a valid water-quality criterion?

- Current evidence: reduced-order TDS/chloride and an IPhreeqc ambient pilot.
- Missing evidence: reclaimed-water provenance, complete ion balance, criterion equivalence, and manual chemistry review.
- Required experiment: frozen sample-level PHREEQC/reduced-order comparison with a complete PASS manifest.
- Safe wording: “scenario-prior quality feedback” until G2 passes.

## 3. Are synthetic sequences being treated as independent cities or observed hydrology?

- Current evidence: 20-sequence ensemble records `hydrology_validation=NONE`.
- Missing evidence: observation-constrained hydrology or independent city archetype data.
- Required experiment: grouped uncertainty analysis and external driver validation.
- Safe wording: “synthetic mechanism ensemble,” never “20 observed cities.”

## 4. Does adaptation feed back into the main model?

- Current evidence: A0-A3 ledger and read-only adapter tests.
- Missing evidence: coupled same-day production, water-quality, energy, and city-source feedback.
- Required experiment: formal E4 only after G2/G3 and paired B2 baseline are ready.
- Safe wording: “standalone adaptation accounting.”

## 5. Are direct and indirect water metrics mixed?

- Current evidence: registries and R9 outputs distinguish source abstraction, potable delivery, reclaimed delivery, and WWTW flows.
- Missing evidence: an end-to-end audit of every figure and manuscript table.
- Required experiment: claim-to-column and withdrawal/consumption/return-flow audit before manuscript freeze.

## 6. Can the result generalize beyond D-HA and D-CO?

- Current evidence: endpoint parameter domains and historical gradients.
- Missing evidence: independent archetype validation and a stable low-dimensional boundary.
- Required experiment: G6-G8 after the earlier gates; report continuous response surfaces if no stable threshold exists.

