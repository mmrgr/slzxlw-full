# Reproduction manifest (A16, v2 — after method audit)

Maps every reported number to the script that produces it and the artefact that stores it.

## 0. Environment lock

```
Python       3.13.14 (MSC v.1944 64-bit, Windows)
numpy        2.4.4
pandas       3.0.5
matplotlib   3.11.2
phreeqpython 1.6.2
```

Interpreter: `C:/Users/mmrgr/.workbuddy/binaries/python/envs/default/Scripts/python.exe`
Engine (read-only, never modified): `07_代码_AI-UWM引擎/aiuwm_src/`

---

## 1. ⚠ Script status (post-audit)

Following the 2026-10-14 method audit (`A13_可靠性机制/AUDIT_2026-10-14_撤回声明.md`),
the following are **marked obsolete in place** and must not be run or cited:

| Obsolete (do not use) | Superseded by |
|---|---|
| `A13_可靠性机制/reliability_model.py` | `potable_flow_corrected.py` |
| `A13_可靠性机制/two_channel_analysis.py` | `potable_flow_corrected.py` |
| `A13_可靠性机制/make_figA13.py` | `A16_英文稿/make_fig1_v2.py` |
| `A15_稳健性/ablation_matrix.py` | `ablation_matrix_corrected.py` |
| `A15_稳健性/holdout_validation.py` | `holdout_validation_corrected.py` |
| `A15_稳健性/boundary_stress.py` | `holdout_validation_corrected.py` (H1–H5) |
| `A16_英文稿/manuscript_en_core.md` | `manuscript_en_v2.md` |
| `A16_英文稿/manuscript_en_intro_discussion.md` | `manuscript_en_v2.md` |
| `A16_英文稿/make_fig1.py` | `make_fig1_v2.py` |

**Unaffected and still valid:** `A15_稳健性/prior_sensitivity.py` (+ recovered results),
`A15_稳健性/grid_resolution_check.py`, and all pre-existing `A9`–`A12` artefacts.

Retracted data artefacts are prefixed `OBSOLETE_` inside `A13_可靠性机制/`.

---

## 2. Live artefacts

### 2.1 Core result — `A13_可靠性机制/`

| Script | Artefacts | Reported in |
|---|---|---|
| `potable_flow_corrected.py` | `potable_flows.csv`, `potable_flows_summary.json`, `a13c_repro_log.txt` | Results §1–§3 |
| `allocation_rule_sensitivity.py` | `allocation_rule_sensitivity.csv`, `allocation_rule_summary.json`, `a13d_repro_log.txt` | Results §6 |
| `make_fig1_v2.py` (in `A16_英文稿/`) | `Fig1_discharge_claim.png` | Fig. 1 |

| Number in text | Value | Source | Key |
|---|---:|---|---|
| scenarios | 408 | `potable_flows.csv` | n rows |
| pure-displacement residual | 5.5e−12 ML | `potable_flows.csv` | `x_ai − (pool − inc_recl)` |
| identity residual $C-F-(M_1-M_0)$ | **3.3e−11 ML** | `potable_flows.csv` | computed |
| negative $dS_{\rm pot}$ count | **0** | `potable_flows.csv` | `dS_pot_ml` |
| positive / zero counts | 384 / 24 | `potable_flows.csv` | `dS_pot_ml` |
| max $dS_{\rm pot}$ | 29 103 ML | `potable_flows.csv` | `dS_pot_ml` max |
| $\chi$=1.00 max / mean | 910 / 494 ML | `potable_flows.csv` | groupby `chi` |
| $\chi$=0.50 max / mean | 2 953 / 1 649 ML | `potable_flows.csv` | groupby `chi` |
| $\chi$=0.25 max / mean | 29 103 / 19 086 ML | `potable_flows.csv` | groupby `chi` |

### 2.2 Robustness — `A15_稳健性/`

| Script | Artefacts | Outcome |
|---|---|---|
| `ablation_matrix_corrected.py` | `ablation_matrix.csv`, `ablation_summary.json`, `ablation.log` | **5/5 gates pass** |
| `holdout_validation_corrected.py` | `holdout_fit_ha.csv`, `holdout_holdout_co.csv`, `holdout_summary.json`, `holdout.log` | **5/5 gates pass** |
| `prior_sensitivity.py` → `prior_sensitivity.csv`, `prior_bounds.json` | **27 combinations** (16 200 solves) | **current** |
| `grid_resolution_check.py` → `grid_resolution_summary.json` | boundary-position criterion: 100% converged | **current** |

> ⚠ **Superseded partial results.** `OBSOLETE_prior_sensitivity_recovered_11of27.csv` and
> `OBSOLETE_prior_bounds_recovered_11of27.json` are an interrupted 11-combination recovery.
> Their range (0.452–0.713) is **narrower than the true 27-combination range
> (0.428–0.785)** and would **understate** prior sensitivity. Use `prior_bounds.json`.

> ⚠ **Corrected metric.** An earlier grid-resolution assessment used *feasible-point counts*
> and reported 15.4% agreement, implying resolution sensitivity. That criterion is invalid —
> a finer grid necessarily has more feasible points when the quality limit is loose. The
> corrected criterion (boundary displacement) gives **100% convergence** with a maximum shift
> of one grid step (0.015625).

| Number in text | Value | Source | Key |
|---|---:|---|---|
| ablation n | 64 cells | `ablation_summary.json` | `n_rows` |
| G1 no-quality $dS_{\rm pot}$ | 0.000 ML | `ablation_summary.json` | `gates[0]` |
| G4 identity residual | 3.638e−12 ML | `ablation_summary.json` | `gates[3]` |
| added-capacity range | −15 030 … −4 639 ML | `ablation_summary.json` | `dS_pot_range_flow_ml` |
| quality main effect | +3 994 ML | `ablation_summary.json` | `main_effects` |
| capacity-regime main effect | +10 964 ML | `ablation_summary.json` | `main_effects` |
| H2 true holdout R² | **0.599** | `holdout_summary.json` | `H2_true_holdout.co_R2_phi_eff` |
| H2 baseline R² | −0.034 | `holdout_summary.json` | `trivial_baseline_R2` |
| H2 median abs error | 0.028 | `holdout_summary.json` | `co_median_abs_err` |
| H3 no-quality max \|dS\| | 0.0000 ML | `holdout_summary.json` | `H3_...` |
| H5 φ=0 max \|dS\| | 0.0 | `holdout_summary.json` | `H5_...` |
| P(dp=1) prior span | **0.4283–0.7850** | `prior_bounds.json` | `drift_dp1` |
| P(dp=0) prior span | 0 → 0.0050 | `prior_bounds.json` | `drift_dp0` |
| rule sensitivity, substantive n | 48 (of 80) | `allocation_rule_sensitivity.csv` | `x_ai > 0` |
| rule sensitivity, $dS_{\rm pot}$ range | 355 – 2 953 ML | `allocation_rule_summary.json` | `effective_regime_dS_range_ml` |
| pure displacement across rules | 0.0 ML | `allocation_rule_summary.json` | `pure_displacement_max_abs_ml` |

### 2.3 External anchoring — `A14_外部锚定/`

| File | Content |
|---|---|
| `A14_literature_verification.md` | 17 references verified (CrossRef / Semantic Scholar / OSTI / arXiv) |
| `A14_increment_table.md` | Increment boundary vs 9 competitors |
| `A14_parameter_anchors.csv` | 52 anchors (45 VERIFIED / 7 UNVERIFIED) |
| `A14_refs.bib` | 27 BibTeX entries |

Anchors used in this round: `COC_PHREEQC_IEUA` = 2.52 (⇒ χ = 0.504),
`COC_DESIGN_AIUWM` = 5.0, `COC_GSA_RANGE` = 2.8–4.91.

---

## 3. Rerun order

```bash
PY="C:/Users/mmrgr/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
cd "C:/Users/mmrgr/Desktop/论文/算力中心/10_论文推进_2026Q4"

# 1. core corrected mechanism
cd A13_可靠性机制 && "$PY" potable_flow_corrected.py
# 2. figure
cd ../A16_英文稿 && "$PY" make_fig1_v2.py
# 3. robustness (corrected)
cd ../A15_稳健性 && "$PY" ablation_matrix_corrected.py \
   && "$PY" holdout_validation_corrected.py \
   && "$PY" recover_prior_sensitivity.py
```

Total runtime: under 1 minute for the corrected scripts (the obsolete
`prior_sensitivity.py` full sweep takes ~30 min and its results are already recovered).

---

## 4. Integrity statement

- The engine under `07_代码_AI-UWM引擎/aiuwm_src/` was **read-only**; no source or frozen
  artefact was modified.
- **No historical value was altered.** The audit found errors in *this round's* new
  mechanism; the project's original conclusion was independently re-derived and confirmed.
- Every number in `manuscript_en_v2.md` is traceable to a row above.
- Retractions are preserved in place and cross-referenced rather than deleted.
- Negative results are retained: the identity fails in the added-capacity regime (expected,
  reported); the genuine holdout is only R² = 0.56; grid resolution affects bottleneck
  identification.
- **RETRACTED (A25 audit, 2026-10-16)**: the earlier statement "`dS_pot` never negative in
  the fixed-pool regime" no longer holds. After the composition cache-key fix, the reliable
  subset of A13c (n = 373, `pool = P0`) contains **121 negative values** (LADWP 59/91 and the
  AI-UWM placeholder 58/90 negative; Figshare RW 90/96 and IEUA 96/96 positive). The earlier
  "zero negatives" was an artefact of the composition dimension being inactive. See
  `A25_终审/A25_全面终审报告.md` §3.
- **Solver-status gate (new)**: every product must report `n_all / n_reliable / n_excluded`;
  scenarios with `status != converged_unique` are excluded from headline statistics
  (A17: 58/1152; A13c: 35/408). See `A25_终审/A25_全面终审报告.md` §1.
