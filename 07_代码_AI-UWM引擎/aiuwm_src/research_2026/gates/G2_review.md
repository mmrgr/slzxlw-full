# G2 Chemistry Review

Updated: 2026-10-13

## Evidence currently available

The existing PHREEQC cross-check contains 129 observed Water Quality Portal /
USGS activity records. It is an ambient-water screening exercise, not a
reclaimed-water cooling-water validation set. The pilot reports a reduced-order
engineering-limit rule and a PHREEQC mineral-saturation rule, with 125/129
reduced-order false-safe classifications and rank Spearman correlation about
0.25.

## Interpretation

The two rules are not yet demonstrated to be equivalent estimands. The
reduced-order rule is based on registered TDS/chloride limits and linear
concentration accumulation. The independent calculation tests saturation of
selected mineral phases. Their disagreement is therefore evidence of a
criterion mismatch risk, not an observed facility failure probability.

The pilot also reports incomplete ion coverage and a maximum major-ion charge
balance error of about 14.81%. PHREEQC results cannot by themselves establish
microbial control, corrosion kinetics, or field-scale scaling safety.

## Newly identified candidate source

The Zenodo record `10.5281/zenodo.19096845` describes wastewater-treatment
plant process samples and lists temperature, pH, chloride, sulfate, calcium,
magnesium, sodium and bicarbonate fields. Its files are embargoed until
2026-12-31, so no rows were downloaded or promoted into the gate inventory.
The metadata is a lead for future acquisition, not evidence that the current
G2 input is complete or reclaimed-water compatible.

The public Figshare/PLOS table `10.1371/journal.pone.0322846.t002` was
downloaded and normalized as `FIGSHARE-28948753`. It contains one reclaimed-
water row from an irrigation study and one brackish-water comparison row. The
reclaimed row has major cations/anions, EC and pH and passes a simple charge-
balance screen (2.68%); the brackish comparison row requires review (-5.39%).
Because the table has no sampling date, treatment-stage metadata, temperature,
TDS, analytical uncertainty, cooling-tower context or independent PHREEQC
output, it is recorded as an E2 candidate for plausibility bounds only. It does
not change the G2 decision.
The API metadata and raw-file checksum are preserved under
`research_2026/external_evidence/figshare_reclaimed_water_2025/`.

## Required before G2 can be READY

1. Obtain reclaimed-water samples with provenance, treatment stage, sampling
   date, temperature, pH, TDS, chloride, calcium, magnesium, sodium, sulfate,
   alkalinity and silica, with measurement uncertainty where available.
2. Freeze a common safety estimand and document whether the reduced-order and
   independent criteria answer the same engineering question. If not, report
   `INVALID_COMPARISON` rather than a precision statistic.
3. Re-run sample-level chemistry with verified input/output hashes and an
   independent review record satisfying `audit_g2_g3_evidence.py`.

Current status: **NOT_READY**. No formal G2 claim is made.

The accessible SIPIBEL Zenodo archive (record `5176161`) is a useful wastewater
observatory inventory, but its 961-sample treated matrix does not provide the
required cooling-relevant ion panel: only pH was observed for the required
indicators, while temperature, TDS, chloride, calcium, magnesium, sodium,
sulfate, alkalinity and silica were not observed. 461 samples are marked
`UNCERTAIN`. The inventory is therefore E2 provenance and acquisition-planning
evidence only, not a G2 chemistry comparison.

A snapshot of the California SDWIS portal for Inland Empire Utilities Agency's
`001B EFFLUENT - RP1 RECYCLED WATER` provides direct utility recycled-water
provenance. The snapshot contains 149 lab sample IDs and 1,177 analyte rows
from 2023-08-09 through 2026-07-28; chloride, calcium, magnesium, sodium,
sulfate and total alkalinity recur, but pH, temperature, TDS and silica are not
present. It is therefore a useful major-ion plausibility bound, not a complete
G2 sample panel or cooling-tower validation package.

The IEUA 2025 RP-1 official report is the strongest accessible chemistry
candidate. It reports pH, TDS, bicarbonate alkalinity, calcium, chloride,
magnesium, sodium, sulfate and silica with average/minimum/maximum values based
on monthly averages. Temperature, sample-level records, measurement
uncertainty and independent solver outputs are absent, so the normalized
candidate is suitable for prior bounds only and cannot open G2.

The official LADWP AWPF pilot report adds a temperature-bearing RO-product
candidate. Table 4-3 reports TDS, chloride, sulfate, calcium, magnesium (ND),
sodium, silica, temperature, pH and alkalinity with detection limits. It is a
single pilot analytical result rather than a replicated reclaimed-water time
series; the normalized record therefore retains the magnesium non-detect and
does not impute it. The candidate is useful for bounded temperature-dependent
criterion testing, but missing replicated uncertainty, charge-balance inputs and
independent solver review keep G2 **NOT_READY**.
