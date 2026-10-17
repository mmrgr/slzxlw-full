# Fig. 1 | Study boundary, counterfactuals and the three-way water account

**System boundary and the estimator.** The study accounts for municipal water abstraction over a
city-scale boundary containing a reclaimed-water source (the "pool"), an AI data-centre cooling
system, incumbent users, and an external make-up supply (panel **a**). The primary estimand is

```text
dS_pot = C - F = max(0, inc_B2 - inc_B1) - [ (M0 - M1) + x_AI ]
```

where dS_pot > 0 means the city's net abstraction rises (harmful) and dS_pot < 0 means it falls
(beneficial). Panel **b** defines the three counterfactuals: **B0** (no data centre, baseline
account), **B1** (data centre present but not using reclaimed water, so x_AI ≡ 0 by definition) and
**B2** (data centre using reclaimed water, x_AI > 0, drawing on the pool). Panel **c** illustrates the
three-way account — requested, delivered and abstracted volumes — for one grid scenario.

**Data and methods.** Panel **c** uses one row of `A13_可靠性机制/supply_state_regimes.csv` (the
authoritative main-grid file, 1 052 rows before gating). Symbols and definitions follow
`A26_语义统一/CHI_SEMANTICS.md`. Note that `x_ai_B1_ml` and `x_ai_B2_ml` in that file have
**swapped names** relative to their meaning; values are unaffected because all labels were exchanged
consistently (see `A13_可靠性机制/COLUMN_NAMES_CORRECTED.md`).

**n.** Panel **c** shows n = 1 illustrative scenario; panels **a** and **b** are schematic
definitions and carry no statistical sample size.

**Limitations.** Panels **a** and **b** are conceptual schematics, not evidence. The estimator is an
accounting identity; its residual (2.55 × 10⁻¹¹ ML) is a numerical consistency check and does not by
itself constitute a scientific finding. The `max(0, ·)` clamp is physically required to avoid
double-counting x_AI when the pool is exhausted in B1.
