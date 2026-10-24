# AquaSPICE Adaptation Parameter Screen

This artifact uses the public AquaSPICE cooling-treatment pilot registered as
E2 evidence. It is a parameter screen for treatment-flow behavior, not a
data-centre validation set and not a formal chemistry gate.

## Measured screening ranges

| Stream | Rows | Flow recovery median (5th–95th percentile) | TDS rejection median (5th–95th percentile) |
|---|---:|---:|---:|
| RO_CTMU_Enhanced | 17,984 | 0.8183 (0.7764–0.9179) | 0.9925 (0.9866–0.9949) |
| RO_CTBD | 20,984 | 0.7495 (0.7101–0.7659) | 0.9875 (0.9788–0.9915) |

Flow recovery is calculated as `RO_Perm_Flow / (RO_Perm_Flow +
RO_Conc_Flow)`. TDS rejection is calculated as `1 - RO_C_Perm /
RO_C_Feed_TDS` for rows with positive finite values. Quantiles are descriptive
statistics over the pilot rows, not independent facility replicates.

## Scope and limitations

These measurements can inform A2 membrane recovery/rejection ranges and A1/A2
water-partition accounting. The files do not supply a complete ion panel,
data-centre heat load, treatment energy, carbon intensity, chemical cost,
capital cost or field-scale reliability. No E4 cost or energy result should be
calibrated from zeros or from these flow ratios alone.

The machine-readable output is
`research_2026/experiments/aquaspice_adaptation_screen_2026-10-13.json`.
G2 and G3 remain `NOT_READY`; the screen is `PASS_E2_SCREEN` only.
