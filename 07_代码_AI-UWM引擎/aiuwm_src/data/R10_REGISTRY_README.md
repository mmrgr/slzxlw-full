# R10 registry fixtures

`parameter_registry.csv` and `scenario_registry.csv` are the first executable R10 registry fixtures. They are intentionally conservative: chemistry point values are marked `E0_assumption` and `scenario_prior`, and every Q/L/A combination is `not_ready` until the main-model quality/allocation coupling and G2/G3 gates pass.

The files are not a claim that these inputs are observed distributions. Before formal E3/E4, replace or extend them with source-linked parameter ranges, observation populations, correlation groups, paired seeds, and the actual run commit.

The external evidence registry also records a 129-sample Water Quality Portal
ambient-water pilot from USGS site `USGS-07241550`. It is retained as
`E2_observed_ambient`: the normalized chemistry and PHREEQC output are useful
for screening and provenance checks, but ambient river samples are not reclaimed
water and do not satisfy the reduced-model comparison or false-safe review
required for G2.
