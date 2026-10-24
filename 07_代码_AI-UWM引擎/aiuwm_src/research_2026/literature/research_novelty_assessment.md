# Research Novelty Assessment

## Provisional assessment

AI-UWM is not yet entitled to claim a new empirical finding. Water chemistry as a sustainability concern is already explicit in Saleh's 2026 ES&T Viewpoint, and data-water symbiosis is already quantitatively modelled by Wang et al. The strongest current novelty statement is narrower, methodological, and conditional:

> AI-UWM specifies an auditable paired estimand for translating data-centre potable-water savings into city source-water savings while jointly exposing reclaimed-water quality, shared-pool allocation, incumbent displacement, and adaptation feedback.

This statement is supported by the R10 specifications and code structure, not by a completed formal experiment.

## Why the mechanism is not redundant

Facility LCA and WUE work answer how much water a configuration uses. Grid-coupled work answers where indirect water moves when electricity demand changes. Global symbiosis work answers where data centres and WWTPs could be paired. Saleh identifies chemistry and constituent enrichment as overlooked compatibility issues but does not quantify an urban allocation response. WaterMet2 answers how to represent urban flows. AI-UWM could add a matched counterfactual that asks whether the facility saving survives both city allocation and quality constraints, including the incumbent-user response.

## What would falsify the novelty

The contribution should be downgraded if any of the following occurs:

- `S_city` tracks `S_AI` across all reasonable allocation rules and quality states.
- Q1 changes outputs only because of a non-equivalent or invalid safety criterion.
- The incumbent displacement is an artefact of traversal order or an arbitrary priority rule.
- A low-cost adaptation universally removes the difference with no material energy, carbon, cost, or reliability trade-off.
- Independent facility or chemistry evidence contradicts the model within its declared scope.

If those tests fail, retain the auditable framework as a reproducibility contribution and center the paper on conditions and limits rather than a “reuse failure” narrative.

## Required evidence before a high-impact claim

1. Reproducible pinned environment and green test suite including the chemistry runner.
2. G2 PASS or an explicit, defensible `INVALID_COMPARISON` outcome.
3. G3 facility/study leave-one-out validation with non-synthetic observations.
4. Formal paired Q0/Q1 × Ls/Ld experiments with B0/B1/B2 separation.
5. Grouped uncertainty over hydrology, parameters, structure, and numerical resolution.
6. Coupled A0-A3 adaptation results with infeasible/NA handling and full source terms.

