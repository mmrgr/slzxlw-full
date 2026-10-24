# Decision Log

## 2026-10-13

1. Located the active project at `Desktop\论文\算力中心\07_代码_AI-UWM引擎\aiuwm_src`; the surrounding `Documents\sjz` directory is not the AI-UWM Git checkout.
2. Preserved the dirty worktree. No reset, checkout, clean, commit, push, or history rewrite was performed.
3. Kept all formal R10 scenarios `not_ready` and G2/G3 closed. Pilot artefacts are not promoted to external evidence.
4. Added `.` to pytest's configured `pythonpath` so the documented suite can import root-level `scripts.*` modules.
5. Recorded the missing `phreeqpython` package as an environment blocker rather than weakening the chemistry test or replacing PHREEQC with a mock.
6. Recorded R9 and reservoir results as scoped model diagnostics only; synthetic hydrology is not described as observed evidence.
7. Identified literature novelty as a conditional framework claim. No “first” or universal reclaimed-water failure claim is made.
8. Installed the declared chemistry and API test dependencies into a temporary target directory, ran the complete suite, and observed 138 passed after adding the closure CLI regression test. This resolves the local missing-dependency failure without changing the repository environment.
9. Replaced Unicode checkmark/cross output in `scripts/audit_water_balance_closure.py` with ASCII-safe status labels. The 90-row closure audit now exits 0 after writing its result.
10. Added versioned G1 component/closure summaries plus explicit G2 sample, chemistry-comparison, review, and G3 evidence-gap/manifest artifacts. These inventories preserve `NOT_READY` where independent evidence is absent.
11. Added an R10a production-engine diagnostic for two declared treated-output TDS scenarios. It passed internal closure, solver, provenance and monotonicity checks, but is explicitly `diagnostic_only` and cannot serve as G2/G3 evidence.
12. Hardened the G2 manifest auditor to reject duplicate `sample_id` rows in both hashed input and per-sample output; added a regression test while preserving the live G2/G3 `NOT_READY` result.
13. Recomputed and checked all 34 versioned artifact entries; no path or SHA-256 mismatch remains except the intentional `.git/HEAD` symbolic-ref record.
14. Ran the read-only E4 adapter on the 730-day `co/cap_1000` ledger. Because no caller-supplied adaptation parameters were declared, A0-A3 were neutral and identical; this is retained as an input-boundary diagnostic rather than interpreted as evidence that adaptations have no cost.
15. Summarized the public AquaSPICE pilot as an E2 parameter screen. Median flow recovery was 0.8183 for RO_CTMU and 0.7495 for RO_CTBD; median TDS rejection was 0.9925 and 0.9875, respectively. These values are not promoted to G2/G3 or to data-centre energy/cost calibration.
16. Re-ran the full recorded test environment after the E2 screen addition: 141 tests passed.
17. Registered the embargoed Zenodo wastewater hydrochemistry record (`10.5281/zenodo.19096845`) as a future G2 acquisition lead only; no inaccessible data were treated as observations.
18. Added an explicit E4 parameterization guard: read-only runs without caller-supplied adaptation parameters are labeled `NEUTRAL_POLICY_ONLY_DEFAULTS`, expose `formal_parameterization_ready=false`, and cannot be interpreted as adaptation benefit or cost evidence.
19. Added and clean-installed the exact package lock `research_2026/environment_lock_2026-10-13.txt`; the clean target reproduced all 141 tests, so the remaining G0 gap is durable cross-host/CI verification rather than an unrecorded local dependency set.
20. Re-ran the live R10 dry-run for `R10_Q0_Ls_A0`; it remains correctly rejected because the scenario is `not_ready`, G2/G3 are `NOT_READY`, and no formal mode was authorized.
21. Acquired the public Figshare/PLOS table `10.1371/journal.pone.0322846.t002` as `FIGSHARE-28948753`, normalized its two rows with a charge-balance diagnostic, and classified it as `CANDIDATE_REVIEW_REQUIRED`; it is not cooling-tower or facility evidence and leaves G2/G3 closed.
22. Added `xlrd==2.0.2` to the versioned lock for binary-XLS ingestion and reran the clean locked suite: 144 tests passed; the live G2/G3 inventory remains `NOT_READY`.
23. Added an external-registry contract test for `E2-FIGSHARE-28948753`; the locked target now passes 145 tests while preserving `G2_NOT_READY|G3_NOT_READY`.
24. Preserved the Figshare API metadata, DOI, license, file MD5 and raw SHA-256 under the external-evidence directory; the candidate remains audit-traceable without being promoted to formal G2 evidence.
25. Acquired the public SIPIBEL Zenodo archive (`10.5281/zenodo.5176161`), recorded its source metadata and generated an inventory without imputation. The archive contains 961 wastewater samples, but the treated matrix lacks the required cooling-relevant ion panel; it is classified as E2 inventory/acquisition-planning evidence and leaves G2/G3 closed.
26. Snapshotted the public California SDWIS recycled-water portal for Inland Empire Utilities Agency's `001B EFFLUENT - RP1 RECYCLED WATER`. The 149-lab-sample inventory provides direct major-ion provenance but lacks pH, temperature, TDS and silica; it is retained as incomplete E2 evidence and leaves G2/G3 closed.
27. Added `lxml==6.1.1` to the exact environment lock for deterministic HTML-table ingestion and clean-installed the new target; the full suite passed 149 tests in 12.19 seconds.
28. Acquired the official IEUA 2025 RP-1 recycled-water report and normalized its complete reported ion panel. The report remains an aggregate prior because temperature, row-level samples, uncertainty and independent chemistry outputs are absent; G2/G3 remain closed.
29. Clean-installed the locked environment after the IEUA candidate addition; the full suite passed 151 tests in 11.28 seconds. The new candidate remains gate-safe and does not authorize formal E3/E4.
30. Acquired and normalized the official LADWP AWPF pilot RO-product chemistry table. The panel includes temperature and detection limits, but magnesium is non-detect and the source is a single pilot analytical result without replicated uncertainty or independent solver review; G2/G3 remain closed.
31. Ran the locked-target regression suite after adding the LADWP candidate and tests: 153 passed in 12.13 seconds. The result is a software reproducibility update only; formal E3/E4 remain unauthorized because G1 production integration, G2 and G3 are still not ready.
32. Reinstalled the exact dependency lock into a fresh temporary target and reran the full suite: 153 passed in 16.07 seconds. This confirms local clean-install reproducibility; it is not cross-host validation and does not alter G2/G3.
33. Acquired and normalized the official GSA/NREL Lloyd D. George Courthouse cooling-tower evaluation. It supplies metered makeup/blowdown and CoC over three aggregate periods (102 days), but one non-data-center facility lacks the registered 3-unit/12-month IT-energy/PUE/WUE holdout fields; G3 remains closed.
34. Ran the full test suite after adding the GSA candidate and tests: 155 passed in 15.85 seconds in the fresh lock target. This is a local reproducibility result only; G2/G3 and formal E3/E4 remain closed.
35. Ran the frozen G3 runner against the GSA aggregate candidate as a preflight; it conservatively returned `NOT_READY` because the table lacks daily timestamps, energy/PUE/WUE, weather, provenance and prediction fields. No formal holdout result was generated.

