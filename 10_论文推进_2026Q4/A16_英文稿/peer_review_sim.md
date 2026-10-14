# Simulated peer review — manuscript v2 (post-audit)

**Purpose**: attack the *corrected* manuscript before a referee does.
**Discipline**: every attack answered with a traceable artefact or honestly conceded.

**Panel**: EIC (handling editor) · R1 (quantitative methods) · R2 (urban hydrology) ·
R3 (water chemistry / cooling) · R4 (policy / economics).

> **Context.** An earlier version of this work claimed a "two-channel" mechanism
> (water-quality vs supply-reliability). That claim was **withdrawn** after a method audit
> found a category error and a dimensional error. This review covers only the corrected
> manuscript. The retraction is itself relevant to how a referee should read the work:
> the authors found and disclosed the defect before submission.

---

## 0. Verdict

**One sentence**: the corrected manuscript states a **valid, exactly verifiable balance**,
identifies the precise condition under which reclaimed cooling is neutral, and reports a
genuine regime boundary — but its **external validity remains thin** (two homologous
synthetic domains; only genuine holdout R² = 0.599).

| Dimension | Rating | Note |
|---|:--:|---|
| Internal consistency / exactness | ★★★★★ | Identity to 3.3e−11; 21/21 audit checks pass |
| Claim discipline | ★★★★★ | Retraction disclosed; obsolete artefacts marked; negatives retained |
| **Mechanism** | ★★★☆☆ | The identity is algebraic; the *new* content is the no-quality neutral case and the regime boundary |
| External validity | ★★☆☆☆ | Synthetic domains; genuine holdout R² = 0.599 |
| Engineering / chemistry credibility | ★★★☆☆ | χ=0.50 anchored to PHREEQC 0.504; χ=0.25 extrapolated; no antiscalant |

**Recommendation**: submittable to **npj Clean Water / Water Research** as-is;
**Nature Communications** plausible with external anchoring; **Nature Water** needs a real
city anchor.

---

## 1. Attack list

| # | Attack | Referee | Severity | Blocking | Status |
|---|---|---|---|:--:|:--:|
| **E1** | The central identity is algebra, not a finding | EIC | **Critical** | **Yes** | ⚠ Partially closed (§2.1) |
| **E2** | Two homologous synthetic domains | EIC | Critical | Yes | ⚠ Conceded |
| **E3** | Is the "win–win" target real? | EIC | Major | No | ✅ Cited (Saleh 2026; Ajaz & Kunz 2026) |
| **M1** | The identity reuses the same expression it validates | R1 | **Critical** | **Yes** | ✅ Disclosed (§2.2) |
| **M2** | Cross-domain R²=1.0 is circular | R1 | Critical | Yes | ✅ Re-labelled as re-derivation; true holdout 0.599 |
| **M3** | Does the $C$ definition hold in both regimes? | R1 | **Critical** | **Yes** | ✅ Regime-conditioned (§2.3) |
| **M4** | A prior version contained a dimensional error — can this be trusted? | R1 | **Critical** | **Yes** | ✅ Audit trail published (§2.4) |
| **M5** | Prior sensitivity of the 0.62 probability | R1 | Major | No | ✅ 0.45–0.71; qualified |
| **M6** | Only one quality tier is anchored | R1 | Major | No | ⚠ Declared (§2.5) |
| **H1** | Rigid incumbent demand assumed | R2 | Major | No | ✅ Conservative upper bound |
| **H2** | Index B (basin) unidentifiable | R2 | Major | No | ✅ NOT_IDENTIFIABLE |
| **H3** | Allocation rule is the model's, not observed | R2 | **Critical** | **Yes** | ✅ **CLOSED by new experiment** (§2.6) |
| **H4** | Grid resolution | R2 | Minor | No | ✅ Disclosed (15.4%) |
| **C1** | Criterion (ratio vs saturation) | R3 | Critical | Yes | ✅ PHREEQC; χ anchored |
| **C2** | Antiscalant omitted | R3 | Major | No | ✅ Declared conservative |
| **C3** | `vitens.dat` is a drinking-water library | R3 | Major | No | ✅ Declared |
| **C4** | Engine placeholders remain | R3 | Major | No | ✅ SI §S7 list |
| **C5** | Cost parameters declared | R3 | Major | No | ✅ Ranges only |
| **P1** | Costs in CNY, not transferable | R4 | Major | No | ✅ Relative ordering only |
| **P2** | Policy reading of the regime boundary | R4 | Major | No | ⚠ Conditional statement only |

---

## 2. The blocking attacks in detail

### 2.1 E1 — "the identity is algebra, not a finding" ⚠ PARTIALLY CLOSED

**Attack**: $C-F=M_1-M_0$ follows from the allocator's no-overdraw property plus the
definition of $F$. A referee can derive it in three lines. Reporting it as a result is
dressing up conservation.

**Response**: the manuscript concedes this explicitly (§2 of Results describes it as an
exact identity, not a discovery) and locates the contribution elsewhere:

1. **The neutrality condition.** $dS_{\rm pot}=0$ **exactly** if and only if water chemistry
   does not bind (verified at 0.0000 ML, CoC = 5.0). This converts a vague "reuse is a wash"
   claim into a precise, testable condition.
2. **The regime boundary.** Added capacity reverses the sign (−15 030 to −4 639 ML). This is
   *not* derivable from the fixed-pool identity.
3. **The corrected accounting.** Replacing a dimensionally invalid subtraction with an
   explicit two-flow balance is a methodological contribution for this literature.

**Residual risk**: **medium**. A referee may still judge contributions 1–3 as incremental
relative to Wang et al. (2026).

### 2.2 M1 — "the identity reuses the expression it validates" ✅ DISCLOSED

**Attack**: the "holdout" R² = 1.000 in the co domain uses the co domain's own $M_0,M_1$;
that is circular.

**Response**: correct and now stated in the manuscript. The identity's cross-domain check is
labelled an **algebraic re-derivation**, and the only genuine holdout is a one-parameter
transfer of $\varphi_{\rm eff}$ (**R² = 0.599**, baseline −0.034), reported as weak.

**Residual risk**: low (disclosure is complete).

### 2.3 M3 — "does the $C$ definition hold in both regimes?" ✅ REGIME-CONDITIONED

**Attack**: $C$ was initially defined against a fixed nominal pool, which is only correct
when $\Delta P=0$.

**Response**: the definition now requires the incumbent reference to be evaluated **in the
same scenario** as the counterfactual. The manuscript states that the identity holds in the
fixed-pool regime and **does not** hold under added capacity, where it is reported separately
(ablation gate G5).

**Residual risk**: low.

### 2.4 M4 — "a prior version had a dimensional error" ✅ AUDIT TRAIL PUBLISHED

**Attack**: the authors previously reported a "two-channel" mechanism. Why should a reader
trust the corrected version?

**Response**: the defect, its cause, and every retracted claim are documented in
`AUDIT_2026-10-14_撤回声明.md`; obsolete scripts and artefacts are marked in place rather
than deleted; the retraction list includes the exact figures withdrawn. The corrected result
is independently re-derived and re-verified (21/21 checks).

**Residual risk**: low, provided the retraction is disclosed in the cover letter — a
referee who discovers it independently would otherwise suspect concealment.

### 2.6 H3 — "the allocation rule is the model's, not observed" ✅ CLOSED

**Attack**: pure displacement ($x_{\rm AI}\equiv$ incumbent loss) is a property of *this*
allocator. Real systems have contracts, priority rights, and protected users. The entire
result is conditional on a rule that was chosen, not observed.

**Response (new experiment, `allocation_rule_sensitivity.py`)**: the engine has a **native
incumbent-protection parameter** (`incumbent_reclaimed_ml`, "protected before incremental
demand"). Scanning it from 0% to 100% of incumbent demand (80 scenarios):

1. **The displacement premise holds exactly at every protection level** —
   $\max|x_{\rm AI}-C| = 0.0$ ML. So the premise is a structural property of the joint
   quality-allocation fixed point, not an artefact of one setting.
2. **$dS_{\rm pot}>0$ in all 48 substantive scenarios** — every case where the data centre
   actually receives reclaimed water.
3. **Protection monotonically reduces the cost** (2 953 → 2 196 → 1 203 ML).
4. **At protection ≥ 0.75 the protected claim exceeds the pool**, the data centre receives
   nothing, and $dS_{\rm pot}=0$ trivially. These 32 cases are **excluded as non-evidence**
   rather than presented as a benefit.

**Residual risk**: **medium-low**. The rule space is still the engine's (pro-rata of a
reserved pool); true priority queues, interruptible contracts, and cross-sector trading are
not represented. But the *sign* is now shown to be rule-robust over a meaningful range.

---

## 3. Conceded and not answered

| Attack | Why conceded |
|---|---|
| No city-calibrated volumes | No public anchor located |
| No facility-level holdout (G3 NOT_READY) | Needs ≥3 facilities × ≥12 months |
| No independent chemistry validation (G2) | Needs a complete cooling-relevant ion panel |
| Antiscalant omitted | Engineering reality; our bound is thermodynamic |
| Costs are declared values | No verified engineering cost source obtained |
| Only one quality tier anchored to observations | χ=0.25 is extrapolated |

---

## 4. Mandatory pre-submission actions

**P0 — claim integrity**
1. ✅ Identity disclosed as an identity.
2. ✅ Circular "holdout" re-labelled; true holdout reported at R² = 0.599.
3. ✅ Regime-conditioned $C$ definition.
4. ✅ Retraction documented and cross-referenced.
5. ⬜ **Disclose the retraction in the cover letter.**
6. ⬜ **State the allocation-rule dependence in Results**, not only Limitations.

**P1 — materially affects review**
7. ✅ **Allocation-rule sensitivity** (pro-rata, priority) — **completed**; sign is rule-robust.
8. ✅ Prior sensitivity (0.45–0.71) reported and qualified.
9. ✅ Policy target cited.
10. ✅ Engine-side NOT_READY items disclosed (SI §S8).

**P2 — minor**
11. ⬜ Symbol table (done, SI §S1); placeholder list (done, SI §S7);
    PHREEQC library limitation (done, SI §S4); grid resolution (done, SI §S10).

---

## 5. Bottom line

**Survives**: an exact, verifiable discharge–claim balance; the precise neutrality condition;
the regime boundary; a documented retraction with corrected, reproducible numbers.

**Does not survive**: any claim of a "supply-reliability channel"; any absolute statement
about a named city; any assertion of external validity beyond a modest one-parameter
transfer.

**Journal fit**: `npj Clean Water` / `Water Research` now; `Nature Communications` with
external anchoring; `Nature Water` only with a real city or an observed allocation rule.
