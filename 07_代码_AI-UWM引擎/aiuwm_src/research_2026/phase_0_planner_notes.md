# AI-UWM Phase 0 Planner Notes

Audit date: 2026-10-13  (workspace: `aiuwm_src`)

## Baseline

- Git branch: `main`; `HEAD=8ff14f5` (`T0.3` convergence diagnostics), ahead of `origin/main` by 11 commits.
- The worktree is intentionally treated as dirty and must not be reset. Tracked edits span the model, validation, scripts, examples, and documentation; untracked files include the R10 registries, pilot runners, quality/allocation modules, and their tests.
- Source layout: `src/aiuwm/full_engine.py` is the daily orchestration layer; `data_center.py` computes IT load, PUE, cooling, CoC, and the water ledger; `quality_state.py` and `reclaimed_allocation.py` are opt-in R10a quality/allocation primitives; `ai_capacity.py` computes capacity scans and constraint boundaries; `adaptation.py` is a standalone E4 A0-A3 ledger and is explicitly decoupled from the main engine.

## Dependency and verification state

- `pyproject.toml` requires Python >=3.10, NumPy >=2.0, pandas >=2.2, and matplotlib >=3.9. Test, chemistry, and Studio dependencies are optional extras. `requirements.txt` does not include the optional extras, and there is no environment lock file.
- `python -m compileall -q src scripts` passes.
- The active runtime has NumPy 2.3.5 and pandas 3.0.1, but no pytest, SciPy, FastAPI, httpx, or matplotlib. Therefore `python -m pytest -q` cannot run (`No module named pytest`). Do not claim the README's historical `58 passed` result as a current verification; install the appropriate extras in a pinned environment first.

## Gate state

`python scripts/audit_g2_g3_evidence.py --repo-root . --json` reports:

- G2: `NOT_READY`; only the WQP/PHREEQC pilot artifact is present, without a complete PASS manifest, verified input/output hashes, chemistry provenance, independent review, and false-safe statistic.
- G3: `NOT_READY`; `examples/demo_full/observed.csv` is classified as synthetic/scenario data and no non-synthetic facility holdout manifest exists.
- Registry inventory: 10 parameter rows, 16 scenarios, all 16 scenario rows `not_ready`.

`python scripts/run_r10_pilot.py --scenario-id R10_Q0_Ls_A0 --mode diagnostic --dry-run --json` returns `DIAGNOSTIC_PREFLIGHT_ONLY`, `formal_e3_e4_eligible=false`, and keeps both G2/G3 gates closed. This runner is preflight only and must not be changed into a formal executor as part of Phase 0.

The frozen R10-R12 plan and gate status documents agree with this runtime audit: G0 is `IN_PROGRESS`; isolated G1c quality primitives pass, while main-model integration is only daily-slice/diagnostic; G2 and G3 are `NOT_READY`; G4-G8 are blocked by previous gates. The explicit stop condition is to avoid formal E3/E4, city expansion, CAWCC refinement, and global mapping until G2/G3, full production time-series coupling, and end-to-end closure are complete.

## Minimum safe Phase 0 plan

1. Preserve the current dirty worktree and record `HEAD`, `git status`, registry SHA-256 values, Python/package versions, and gate audit output as the reproducibility baseline.
2. Provide or activate a pinned test environment (`.[test]` at minimum; add `.[chemistry]`/`.[studio]` only for the corresponding workflows), then run the full Python test suite and the narrow R10 registry/preflight tests.
3. Run syntax/import checks and the read-only G2/G3 evidence inventory. Keep every formal status `NOT_READY` until independent evidence, provenance, hashes, review, and frozen pass criteria exist.
4. Treat R10 quality/allocation and E4 adaptation code as pilot or opt-in paths. Do not change default model semantics, synthetic-data labels, registry statuses, or formal gate decisions in Phase 0.
5. After the baseline is reproducible, implement one narrowly scoped contract/test improvement at a time, with model output diffs and gate-state checks before any documentation claims are updated.

## Current risks to carry forward

- A dirty tree mixes committed T0.3 convergence work with uncommitted R8/R10 work, so broad refactors can accidentally combine incompatible experimental states.
- Missing dependency locks and the unavailable pytest runtime prevent an independently reproducible test claim today.
- Pilot artifacts and synthetic examples are not admissible evidence for G2/G3; no code path should promote them by filename or by passing synthetic metrics.
- The main model's quality-state integration is opt-in; adaptation accounting is standalone. Claims that E3/E4 are already coupled to the production engine would exceed the current implementation boundary.
