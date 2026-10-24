# AI-UWM Phase 0 Report

Date: 2026-10-13

## 1. Project state

The real AI-UWM repository is the nested Git checkout under `Desktop\论文\算力中心\07_代码_AI-UWM引擎\aiuwm_src`, not the surrounding document workspace. The checkout is on `main` at `8ff14f5`, 11 commits ahead of `origin/main`, and contains substantial user/R10 worktree changes. The worktree was preserved exactly; no destructive Git operation was used.

The implementation has a clear separation between the legacy urban-water engine, opt-in R10 quality/allocation paths, and the standalone E4 adaptation ledger. This separation is scientifically useful because it prevents a diagnostic pilot from being mistaken for a production coupled model.

## 2. Existing results that are currently defensible

1. Internal water-balance closure is numerically strong for the available 90 scenario rows: all rows are marked PASS and the largest reported relative residual is below `4e-13%`. This is an internal identity check, not external validation.
2. R9 fixed-point iteration converges for its declared positive-target rows, with a unique root and residual near `1e-10`. The result is scoped to one active data centre, fixed TDS/chloride point values, zero cooling-storage volume, and the current model rules.
3. Shared allocation tests cover incumbent protection, order invariance, dedicated incremental supply, root diagnostics, cross-day returns, and water/solute closure.
4. The R10 preflight correctly refuses formal E3/E4 execution when the scenario is `not_ready` or G2/G3 are not ready.

## 3. Current blockers

- G0 is still `IN_PROGRESS` because the worktree is dirty and cross-host/CI verification of the new exact environment lock is outstanding.
- G1 isolated primitives pass, but full production time-series coupling remains `NOT_READY_FOR_E3`.
- G2 is `NOT_READY`: the available PHREEQC/WQP pilot is ambient-water screening, not a complete reclaimed-water validation package with independent review and frozen PASS criteria.
- G3 is `NOT_READY`: the only candidate named `observed.csv` is classified as synthetic; no non-synthetic facility/study holdout exists.
- G4-G8 are blocked by those gates. No formal Q×L estimand or adaptation ranking is admissible yet.
- The versioned temporary-target suite is green: a fresh lock install passes 155 tests after the pytest path fix, LADWP chemistry candidate tests and GSA operational candidate tests. Cross-host/CI reproduction remains outstanding.
- Public chemistry acquisition now includes an IEUA aggregate prior and a temperature-bearing LADWP AWPF RO-product pilot result; both remain E2 candidates without replicated uncertainty or independent solver review.
- Public operational acquisition now includes a GSA/NREL courthouse cooling-tower aggregate with metered makeup/blowdown and CoC; it remains a one-unit, short-period G3 lead without data-center energy/WUE or holdout predictions.
- `audit_doc_consistency.py` reports 12 mismatches. These must be resolved by tracing the affected claim to the intended artefact, not by editing numbers to make the audit green.

The 12 mismatches are concentrated in two groups: D-HA physical/integrated capacity and probability quantiles (for example 1100 vs 1150 MW and 1250 vs 1300 MW), and R8 reclaimed-fraction outputs (CoC, per-heat withdrawal, and sewer discharge). They appear in the frozen plan and project overview tables and are traceable to `capacity_threshold_corrected.json`, `probabilistic_corrected_summary.json`, and `reclaimed_fraction_sweep_R8.csv`. Resolve each against its exact registered scope before manuscript use.

## 4. Literature competition and gap

The literature search verified that the nearest published or public work covers different parts of the problem:

- Alissa et al. (Nature, 2025) uses lifecycle assessment to compare advanced cooling technologies and reports reductions in energy, greenhouse gases, and blue-water consumption. It does not model shared municipal reclaimed-water allocation or incumbent-user displacement.
- Xiao et al. (Nature Sustainability, 2025) estimates US AI-server water and carbon footprints under deployment and efficiency scenarios. It is a national footprint projection rather than a city water-balance counterfactual with water-quality state.
- Wang et al. (Environmental Science and Ecotechnology, 2026) couples data centres with WWTPs in a global geodatabase, engineering optimization, LCA, and LCC. Its headline symbiosis result supports potential freshwater and carbon benefits, but its global pairing model does not resolve the R10 question of how a shared reclaimed pool, water quality, and incumbent demand alter city-source withdrawal.
- Saleh (Environmental Science & Technology Viewpoint, 2026) explicitly argues that reuse and recirculation shift sustainability assessment beyond water quantity toward water compatibility, constituent enrichment, treatment demand, and blowdown management. This narrows the novelty claim: AI-UWM cannot claim to introduce chemistry as a concern; its possible addition is quantifying the interaction with municipal allocation and incumbent-user response.
- Han et al. (arXiv, 2026) focuses on peak withdrawal capacity and public-water-system infrastructure. It does not model reclaimed-water chemistry or a B0/B1/B2 estimand separation.
- Alston et al. (arXiv, 2026) links cooling choices to hourly dispatch, generator water use, and subbasin depletion. It addresses indirect water relocation across the grid, not municipal reclaimed-water competition.
- Masanet (arXiv review, 2026) synthesizes estimation best practices and evaluates 31 studies, underscoring scope, representativeness, reproducibility, uncertainty, and terminology as core review risks.
- WaterMet2 provides an integrated urban water mass-balance framework with supply, demand, wastewater, recovery, energy, and emissions. AI cooling chemistry and the paired data-centre counterfactual are outside its original scope.
- Andrijevic et al. (npj Clean Water, 2026) shows that wastewater treatment and desalination can be indispensable but maladaptive when energy and emissions are ignored. This supports treating A1/A2 adaptation costs as system outcomes rather than free fixes.

The defensible novelty candidate is therefore conditional: an auditable paired framework that separates local potable-water savings from city-source withdrawal while allowing reclaimed-water quality, shared allocation, incumbent displacement, and adaptation feedback to interact. This is a proposed scientific contribution, not a demonstrated “first” result. The present evidence cannot yet support a claim that reclaimed-water reuse fails in general.

## 5. Minimum safe change completed

`pyproject.toml` now includes the repository root in pytest's `pythonpath` (`["src", "."]`). This fixes test collection for root-level `scripts.*` modules and does not change model equations or default runtime semantics.

## 6. Reproduction commands

```powershell
Set-Location 'C:\Users\mmrgr\Desktop\论文\算力中心\07_代码_AI-UWM引擎\aiuwm_src'
python -m compileall -q src scripts
pytest.exe -q
python scripts\audit_g2_g3_evidence.py --repo-root . --json
python scripts\run_r10_pilot.py --scenario-id R10_Q0_Ls_A0 --mode diagnostic --dry-run --json
```

The chemistry test uses the pinned `phreeqpython==1.6.2` environment. The current locked target passes 155 tests; this software result does not promote G2 or G3 while independent evidence remains incomplete.

## 7. Evidence-gate decision

Keep G2 and G3 at `NOT_READY`; keep formal E3/E4 disabled; do not expand city archetypes, global maps, or strong adaptation claims. The next round should make the environment reproducible and resolve the 12 documentation mismatches before adding new model behavior.

