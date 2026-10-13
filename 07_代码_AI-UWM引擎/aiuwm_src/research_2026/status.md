# AI-UWM Research Status

Updated: 2026-10-13

## Gates

| Gate | Status | Basis |
|---|---|---|
| G0 reproducibility | IN_PROGRESS | Dirty worktree; baseline, hashes, and an exact temporary-target lock are recorded. |
| G1 isolated quality/allocation | PASS | Dedicated tests and closure checks pass. |
| G1 main production integration | NOT_READY_FOR_E3 | Daily-slice/diagnostic paths exist; full production time series is not cleared. |
| G2 chemistry | NOT_READY | Ambient WQP/PHREEQC pilot, bounded Figshare/SIPIBEL/SDWIS/IEUA/LADWP candidates, and no complete reclaimed-water PASS manifest. |
| G3 facility holdout | NOT_READY | GSA/NREL courthouse cooling-tower aggregate is a bounded operational lead; no three-unit, 12-month non-synthetic leave-one-out dataset exists. |
| G4 mechanism | BLOCKED_BY_PREVIOUS_GATES | Formal E3 is gated. |
| G5 adaptation | READ_ONLY_PILOT / MAIN_MODEL_NOT_READY | Standalone A0-A3 ledger exists, but no coupled formal E4. |
| G6-G8 | BLOCKED_BY_PREVIOUS_GATES | No transport, archetype, or global expansion. |

## Current test state

- `python -m compileall -q src scripts`: PASS.
- `python -m pytest -q` from a fresh install of the versioned lock: 155 passed in 15.85 s; the prior clean reinstall baseline was 153 passed in 16.07 s before the GSA candidate tests.
- Focused quality/allocation/closure/R10 tests: 49 passed.
- G2/G3 inventory and R10 diagnostic preflight: PASS as gate controls, with gates remaining closed.
- Water closure artefact: 90/90 rows PASS; the audit CLI now exits 0 on the Windows console.
- Documentation consistency: 12 historical mismatches are classified in `gates/doc_consistency_resolution_2026-10-13.md`; current machine artifacts are designated as the source for new work, while the historical plan remains unchanged.
- Versioned gate deliverables now include the G1 component audit/closure summary, G2 source-batch and criterion review, and G3 facility-evidence gap/validation manifest; these artifacts do not change the closed G2/G3 decisions.
- The R10a single-DC quality invariant diagnostic returned `PASS_INTERNAL_DIAGNOSTIC`: treated-output TDS 100 versus 900 mg/L converged, all listed water/solute/storage/partition closures passed, and quality-limited CoC decreased from 8.0 to 1.5942. This is an internal diagnostic only and does not upgrade G2/G3.
- The 80-row artifact manifest has no missing paths or hash mismatches (excluding the intentional `.git/HEAD` ref entry), including the LADWP chemistry and GSA operational candidates.
- A read-only E4 diagnostic over the 730-day 1000 MW synthetic ledger evaluated A0-A3, but the policy-only defaults are neutral: all four returned identical zero adaptation energy/cost. This is recorded as a boundary diagnostic, not an adaptation finding.
- The E4 runner now records `NEUTRAL_POLICY_ONLY_DEFAULTS` and `formal_parameterization_ready=false` when no caller-supplied adaptation configuration is provided; identical outputs are explicitly non-evidence.
- AquaSPICE E2 screening extracted measured RO flow-recovery and TDS-rejection ranges; missing energy, cost and complete ion-panel evidence remain explicit.
- A public Figshare/PLOS table was downloaded and normalized as `FIGSHARE-28948753`: one reclaimed-water row with major ions, EC and pH passes a 2.68% charge-balance screen; the brackish comparison row is flagged for review. This is an irrigation-context E2 candidate only and does not upgrade G2.
- A Zenodo wastewater-treatment hydrochemistry dataset was identified as a future G2 candidate, but its files are embargoed until 2026-12-31 and therefore remain unavailable evidence.
- The public SIPIBEL Zenodo archive (`SIPIBEL-5176161`) was acquired and inventoried locally: 961 samples across 45 sampling points, with 500 `CORRECT` and 461 `UNCERTAIN` quality labels. The treated matrix has observed pH but not the required temperature/TDS/major-ion/alkalinity/silica panel, so it remains E2 inventory evidence and does not upgrade G2 or G3.
- A snapshot of the California SDWIS recycled-water portal for Inland Empire Utilities Agency (`SDWIS-IEU-RP1`) was added as direct utility evidence: 149 lab sample IDs and 1,177 analyte rows across 2023-2026. Major ions and alkalinity recur, but pH, temperature, TDS and silica are absent; it remains an incomplete E2 candidate and does not upgrade G2 or G3.
- The IEUA 2025 RP-1 official report was normalized as `IEUA-RP1-2025`: pH, TDS, alkalinity, calcium, chloride, magnesium, sodium, sulfate and silica are all reported with average/minimum/maximum monthly-average bounds. Temperature and row-level uncertainty are absent, so it is the strongest current chemistry prior but still not formal G2 evidence.
- The official LADWP AWPF pilot report was normalized as `LADWP-GWR-AWPF-2012`: its RO-product result includes temperature, pH, TDS, major ions, silica and alkalinity with detection limits; magnesium is non-detect. It is a single pilot result without replicated uncertainty or independent solver review and therefore does not upgrade G2.
- The official GSA/NREL Lloyd D. George Courthouse evaluation was normalized as `GSA-GPG-BDR-LLOYD-2023`: metered makeup/blowdown, drift, evaporation, heat rejected, water-per-heat and water-balance CoC are available for three aggregate periods totaling 102 days. It is one non-data-center facility without IT energy/PUE/WUE, 12-month daily coverage or holdout predictions, so G3 remains NOT_READY.

## Scientific claim state

- R9 numerical convergence: verified within its declared synthetic/fixed-point scope.
- City-wide net saving under reclaimed water: unresolved; R9 has bounded counterexamples under fixed inputs, but no general claim is allowed.
- Chemistry feedback as an external phenomenon: unverified.
- Facility prediction: unverified.
- Engineering adaptation restoring city savings: untested as a coupled estimand.

