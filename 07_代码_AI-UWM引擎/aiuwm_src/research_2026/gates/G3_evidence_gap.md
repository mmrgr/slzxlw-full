# G3 Facility Evidence Gap

Updated: 2026-10-13

The only local candidate discovered by the gate audit is
`examples/demo_full/observed.csv`. It is a scenario/example file and is not an
independent facility observation. Public annual operator disclosures are
useful for order-of-magnitude checks but do not provide the daily or traceable
makeup, blowdown and CoC observations required by the registered holdout
protocol.

The public GSA/NREL Lloyd D. George U.S. Courthouse evaluation is a stronger
operational lead than an annual disclosure: it reports metered makeup and
blowdown, drift/evaporation, heat rejected, water per heat rejected and
water-balance CoC for baseline and 2021/2022 evaluation periods. The normalized
candidate covers one facility and three aggregate periods totaling 102 days.
It has no IT/facility energy, PUE/WUE, daily timestamps or model predictions,
so it remains bounded E2 evidence and cannot satisfy the G3 holdout minimum.

## Required validation package

- At least three distinguishable facility or study units.
- At least 12 months per unit, with timestamps and timezone.
- IT and facility energy, PUE/WUE, makeup, blowdown, CoC and relevant weather
  or cooling technology fields.
- Source URI, meter identifier, observed/synthetic marker, quality flags and
  explicit training-facility identifiers for leave-one-unit-out predictions.
- Hashed input/output files and an independent review record.

Until this package exists, G3 remains **NOT_READY**. Synthetic rows, annual
disclosures transformed into daily observations, or model-generated data must
not be promoted to a facility holdout.
