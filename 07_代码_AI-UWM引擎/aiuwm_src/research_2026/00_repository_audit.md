# AI-UWM 2026 Repository Audit

Audit date: 2026-10-13 (Asia/Shanghai)

## Repository identity

- Actual project root: `C:\Users\mmrgr\Desktop\论文\算力中心\07_代码_AI-UWM引擎\aiuwm_src`
- Remote: `https://github.com/mmrgr/AI-UWM.git`
- Branch: `main`
- HEAD: `8ff14f52432a7a5ba2985dd2b215845a9a943360`
- HEAD summary: `T0.3 收敛诊断增强: 从部分批次 checkpoint 读样本 + 同尺寸优先完整批次`
- Relation to remote: local branch is ahead of `origin/main` by 11 commits.
- Worktree: intentionally dirty. Tracked edits affect the model, validation, scripts, examples, and documentation; untracked files include the R10 registries, pilot runners, quality/allocation modules, and tests. No reset, checkout, clean, commit, or push was performed.

## Runtime and dependency state

`pyproject.toml` declares Python >=3.10, NumPy >=2.0, pandas >=2.2, matplotlib >=3.9, with optional `test`, `chemistry`, and `studio` extras. An exact Windows/Python 3.12 verification lock is now recorded at `research_2026/environment_lock_2026-10-13.txt`; the locked temporary target reproduces the current 149-test run. Cross-host/CI verification remains a reproducibility limitation.

The pytest path contract was repaired in this round by changing `pythonpath = ["src"]` to `pythonpath = ["src", "."]`, because the tests import root-level `scripts.*` modules.

## Verification executed

| Command | Result | Interpretation |
|---|---|---|
| `python -m compileall -q src scripts` | PASS | Syntax compilation succeeds in the active runtime. |
| `python -m pytest -q` from the locked temporary target | 149 passed | Includes the SIPIBEL, SDWIS and external-registry regression tests; no formal gate is promoted. |
| Focused R10/closure tests (`quality_state`, `reclaimed_allocation`, `ai_water_balance`, `r10_pilot`, `e3`, `e4`) | 49 passed | Core diagnostic contracts pass without the optional PHREEQC dependency. |
| `python scripts/audit_g2_g3_evidence.py --repo-root . --json` | PASS as an audit command | Reports G2=`NOT_READY`, G3=`NOT_READY`; no gate is promoted. |
| `python scripts/run_r10_pilot.py --scenario-id R10_Q0_Ls_A0 --mode diagnostic --dry-run --json` | PASS as a preflight | Returns `DIAGNOSTIC_PREFLIGHT_ONLY`, `formal_e3_e4_eligible=false`, and both G2/G3=`NOT_READY`. |
| `python scripts/audit_water_balance_closure.py` | Scientific checks PASS; process exits 1 | 90 rows were written with PASS and zero failures. The final Unicode checkmark cannot be encoded by the Windows GBK console (`UnicodeEncodeError`). |
| `python scripts/audit_doc_consistency.py` | FAIL | 12 documentation/artefact mismatches remain. They are recorded as audit findings, not silently corrected. |
| `git diff --check` | PASS | No whitespace errors in the current diff. |

The full suite result is a current locked-target verification result, not the historical README claim. The presence of a passing PHREEQC pilot test is a software regression result only; no formal chemistry conclusion can be drawn from it while G2 remains closed.

## Core implementation map

- `src/aiuwm/full_engine.py`: daily orchestration, water-system components, opt-in R10 quality/allocation integration, provenance, and daily result export.
- `src/aiuwm/data_center.py`: IT load, PUE, cooling technology, CoC, quality-limited fixed point, and daily cooling ledger.
- `src/aiuwm/quality_state.py`: auditable water-quality state and solute mass primitives.
- `src/aiuwm/reclaimed_allocation.py`: shared incumbent-first and dedicated incremental allocation, joint quality/allocation fixed point, and closure diagnostics.
- `src/aiuwm/adaptation.py`: standalone A0-A3 E4 adaptation ledger. It is explicitly read-only with respect to the production engine.
- `src/aiuwm/ai_capacity.py`: capacity scans and constraint-boundary summaries.
- `scripts/run_e3_mechanism_pilot.py`, `scripts/run_e4_adaptation_pilot.py`, and `scripts/run_r10_pilot.py`: gate-safe diagnostics; they do not create formal estimands while gates are closed.

## Evidence artefacts checked

- `validation_artifacts/r2/reclaimed_compatibility_R9.csv`
- `validation_artifacts/r2/reclaimed_compatibility_verdict_R9.csv`
- `validation_artifacts/r2/reclaimed_compatibility_gate_R9.json`
- `validation_artifacts/r2/reservoir_multiyear_ensemble.json`
- `validation_artifacts/r2/water_balance_closure.csv`
- `data/parameter_registry.csv`, `data/scenario_registry.csv`, and `data/external_evidence_registry.csv`

R9's fixed-point gate reports 18 positive-target rows with unique converged roots and maximum absolute residual about `9.98e-11`, but its storage-quality and multi-DC joint gates remain `NOT_READY`. The R9 verdict reports increased city-source abstraction at a 0.9 reclaimed target in both D-HA and D-CO under its fixed 1000 MW, fixed-quality, zero-storage scope; this is a bounded model result, not a universal claim.

The 20-sequence reservoir ensemble reports synthetic hydrology only (`hydrology_validation=NONE`). Its median joint gate is 200 MW in D-HA (range 200-300 MW) and must not be presented as an observed reliability boundary.

## Current validity boundary

G1 isolated quality primitives, allocation invariants, daily-slice integration, and standalone adaptation accounting have executable tests. The full production time series is not cleared for formal E3/E4. G2 lacks a complete independent chemistry PASS manifest and real reclaimed-water provenance. G3 lacks at least three non-synthetic facility/study units with 12 months of held-out makeup, blowdown, CoC, and WUE data. Therefore G4-G8 remain blocked.

