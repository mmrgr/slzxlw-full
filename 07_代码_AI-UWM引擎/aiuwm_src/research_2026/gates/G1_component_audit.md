# G1 Component Audit

Updated: 2026-10-13

This is an implementation audit, not an external validation claim. `PASS`
means that the declared internal invariant is exercised by an automated test or
the dated closure run. `NOT_READY_FOR_FORMAL_EXPERIMENT` means that the code
exists but the production coupling or independent evidence is not sufficient
for an E3/E4 claim.

| Boundary or mechanism | Current implementation | Evidence | Status | Formal limitation |
|---|---|---|---|---|
| Volume accounting | `FullAIUWMModel` carries component storage, inflow, outflow and loss; data-centre finalization records source-specific withdrawal and return flow | `scripts/audit_water_balance_closure.py`; `gates/water_balance_closure_2026-10-13.csv`; `tests/test_ai_water_balance.py` | PASS (internal) | The check is an identity test, not agreement with observations |
| Solute storage and partition | `quality_state.py` tracks volume and mass; `partition_blowdown_solutes` separates recovered return, sewer return and removal | `tests/test_quality_state.py`; `tests/test_data_center.py` | PASS (unit scope) | Scenario-prior water quality is not reclaimed-water evidence |
| Dynamic Q1 cooling | `data_center.py` solves quality-limited CoC and `full_engine.py` carries storage/recovered-return state | `tests/test_quality_state.py`; `tests/test_same_day_wwtw_phase.py` | PASS (opt-in slice) | Shared-pool production runs remain diagnostic until G2/G3 |
| Same-day WWTW feedback | Explicit co-current diagnostic fixed point with volume and mass residuals | `tests/test_same_day_wwtw_phase.py` | DIAGNOSTIC_ONLY | Not promoted to formal E3; ordinary mode remains end-of-day carryover |
| Shared incumbent allocation | `reclaimed_allocation.py` and joint evaluator preserve incumbent requests and report closure residuals | `tests/test_reclaimed_allocation.py`; `tests/test_r10_pilot_runner.py` | PASS (unit/opt-in) | No formal scenario is gate-ready |
| Multi-data-centre order invariance | Joint allocation path is explicitly tested for deterministic allocation behavior | `tests/test_reclaimed_allocation.py`; `tests/test_quality_state.py` | PASS (tested path) | External quality and facility evidence are absent |
| Dedicated incremental source | Dedicated allocator primitive exists and requires its own source/capacity fields | `src/aiuwm/reclaimed_allocation.py` | NOT_READY_FOR_FORMAL_EXPERIMENT | Full main-model source integration and measured incremental supply are not present |
| Cooling technology/adaptation | Cooling plans change makeup, CoC, blowdown and energy within the data-centre plan; A0-A3 ledger is standalone | `tests/test_data_center.py`; `tests/test_adaptation.py` | PASS (isolated); NOT_READY (coupled) | No paired B2/E4 feedback run is approved |

## Frozen numerical checks

- The closure audit uses a declared relative-error acceptance threshold of 5%
  for the existing R2 output family. All 90 rows passed; the companion
  summary retains the unrounded maximum residuals calculated from the source
  daily files.
- R10 fixed-point and mass residual targets remain `1e-10` and `1e-8` in the
  diagnostic configuration. They are not relaxed based on observed results.
- The full test environment recorded in `research_2026/environment_2026-10-13.txt`
  ran 138 tests successfully, including the chemistry-dependent tests.

## Gate interpretation

G1 is a partial internal pass: the tested primitives and accounting identities
are operational, but the main production time series is not cleared for formal
E3/E4. G2 and G3 remain independent prerequisites and are still `NOT_READY`.
