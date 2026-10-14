# Manuscript (A16) — Introduction, Discussion, Methods

Companion to `manuscript_en_core.md` (Abstract + Results). Figures: `A13_可靠性机制/figA13_reversal.png`
plus the finalised set in `09_图定稿/`. All numbers traceable via `reproduction_manifest.md`.

---

## Introduction

The water demand of artificial-intelligence infrastructure has moved from a facility
question to a system question. National-scale assessments now quantify the energy, water
and carbon footprints of AI server fleets, including their spatial heterogeneity and
net-zero pathways (Xiao et al. 2025), and the direct plus indirect water footprints of
data centres have been mapped against water-stressed regions (Siddik et al. 2021).
Cooling architecture itself has been shown to shift life-cycle impacts substantially
(Alissa et al. 2025), and workload-level determinants of data-centre water use vary widely
across facilities (Lei et al. 2026). A parallel line of work has quantified the *public*
water capacity that data centres will require, estimating hundreds of millions of gallons
per day of new US supply capacity by 2030 (Han et al. 2026), and has shown that cooling
choices relocate water impacts across the grid and its sub-basins (Alston et al. 2026).

Because municipal reclaimed water is widely available and not potable, using it for
cooling is frequently proposed as a remedy. Global pairing analyses estimate very large
joint benefits from connecting data centres to wastewater treatment plants — on the order
of 1,300 million m³ of freshwater and 84 Mt CO₂-eq annually (Wang et al. 2026) — and
engineering practice has already demonstrated reclaimed water in direct evaporative
cooling systems (Cavanaugh et al. 2023). Conceptually, this literature treats pairing as
beneficial by construction.

Three features of real urban water systems complicate that assumption.

**First, reclaimed water is usually an existing, allocated resource, not spare capacity.**
Where a reclaimed pool already serves irrigation, industry or indirect potable reuse, a
new large consumer competes for a fixed volume rather than adding to supply. Evidence from
municipal systems shows that reuse strategies interact with the wider water–energy–pollution
nexus (Landa-Cansigno et al. 2020), and that the benefit of centralised reuse is
constrained by demand conditions and scale rather than a property of the technology alone
(Shen et al. 2026). The urban water metabolism literature provides the accounting
machinery to represent such systems (Behzadian & Kapelan 2015; Renouf et al. 2018), but not
the specific feedback a new large industrial user induces.

**Second, reuse can be self-limiting through water quality.** Concentration of dissolved
solids limits the cycles of concentration a cooling tower can sustain, which raises makeup
and blowdown for a given heat load. Saleh (2026) argues that evaluating AI cooling
sustainability requires moving beyond water demand to compatibility, constituent
enrichment and treatment demand — but as a Viewpoint, without a quantitative model or a
testable boundary. Analogous counter-intuitive feedbacks are documented elsewhere: water
conservation can raise wastewater salinity and thereby degrade reclaimed-water usability
(Schwabe et al. 2020).

**Third — and least examined — the urban outcome depends on whether displaced users can
actually obtain replacement water.** Standard facility-to-city accounting treats the
municipal supply as an unbounded backfill: if a data centre takes reclaimed water that an
incumbent was using, the incumbent is assumed to draw the same volume from the potable
system. Under that assumption, and with a fixed pool, the city-level change in source
withdrawal is *identically* equal to the change in the data centre's own potable use. The
"city benefit" then carries no information beyond facility-level water quality effects.

We show here that this identity — widely implicit in reuse assessments — is a conservation
artefact of two assumptions, and that relaxing the second turns the question into a
falsifiable mechanism. We introduce a finite, reliability-constrained municipal supply,
derive the resulting shortage criterion, and test it across a large controlled scenario
grid. The result is not that reclaimed cooling is good or bad, but that it acts on the city
through **two channels of opposite sign** whose balance determines the observed outcome —
and that prior assessments, each capturing one channel, therefore reach opposing verdicts.

To our knowledge, no published study has jointly addressed finite municipal supply
reliability, competition for an existing reclaimed pool, and cooling-water quality
constraints within a single city-scale framework. Each pairwise combination exists:
data centres and public water capacity (Han et al. 2026; Alston et al. 2026), reclaimed
water and data-centre cooling (Wang et al. 2026; Cavanaugh et al. 2023), reclaimed-water
competition and urban metabolism (Shen et al. 2026; Schwabe et al. 2020), and water-quality
limits on cycles of concentration (the cooling-water scaling literature). The three-way
intersection does not.

---

## Discussion

### What the two-channel result explains

Reports that reclaimed-water cooling "saves water" and reports that it "merely
reallocates" are both reproducible within our framework, because they account for
different channels. The water-quality channel is negative: blending reclaimed water lowers
the admissible cycles of concentration, raising total makeup, and this is what a
facility-comparison or attributional life-cycle study sees. The supply-reliability channel
is positive: the same substitution withdraws the data centre from the potable system,
lowering municipal supply stress and the unmet demand that stress implies — a quantity that
never appears in facility-level or national-footprint accounting.

Neither channel is exotic. What is new is that they operate simultaneously with **opposite
signs** in 75% of our scenarios, so the sign of the headline number is an artefact of
accounting scope rather than a property of the technology.

### The critical mixing ratio and its policy reading

The condition $\psi(\varphi^*)=1$ yields a mixing ratio above which the city clears its
shortage threshold. Two features are policy-relevant and robust:

1. **A tighter supply margin demands more reclaimed water.** $\varphi^*$ rises from 0.00 at
   $W_{\rm scale}=1.00$ to 0.55 at 0.90.
2. **There is a supply floor.** At $W_{\rm scale}\le0.85$ no achievable mixing ratio clears
   the threshold: reclaimed cooling cannot substitute for supply adequacy. Under such
   conditions the effective interventions are demand reduction, leakage control or
   additional supply — not cooling-water substitution.

The domain difference ($\varphi^*$ 0.542 ha vs 0.671 co) is explained by the incumbent
demand share ($D_{\rm inc}/M_0$ = 0.925 vs 0.973), giving a testable prediction: cities
with a larger competing reclaimed demand need proportionally more substitution before the
supply benefit appears.

### Why "does reclaimed cooling save water?" is the wrong question

The volume account is conserved: in the share-only regime $S_{\rm city}\equiv M_0-M\le0$
identically, and it is monotone with its maximum at $\varphi=0$. No reclaimed fraction
makes the city's water **volume** balance positive. Yet the same intervention
**improves** reliability. These are different physical quantities and must be reported
separately; merging them into a single sustainability score — as is common — destroys the
entire mechanism. A defensible planning statement is therefore conditional and two-part:
*substitution improves service reliability above a computable threshold, and it does not
create water.*

### Relation to existing work

Our results do not contradict Wang et al. (2026): where genuinely new reclaimed capacity is
built with no competing claim, benefits are real — our capacity-inclusive regime reproduces
positive outcomes. The difference is that we separate *new supply* from *reallocation of
existing supply*, and show that only the former creates volume benefit, while both affect
reliability. Similarly, we do not contest Han et al. (2026) on capacity: we agree public
supply is constrained, and we ask the complementary question of who receives water once it
is allocated.

### Limitations

1. **No city anchor for the supply margin.** $W$ is normalised, so $\psi(0)=1/W_{\rm scale}$
   by construction. We therefore claim the *structure* of the mechanism — slope,
   threshold location, quality coupling — and not the absolute level of $\psi$ for any
   real city. No public anchor for municipal supply-availability ratio was located.
2. **Two homologous synthetic domains.** ha and co come from one generator; cross-domain
   agreement is internal consistency, not external validity. The only genuine out-of-sample
   test is a one-parameter transfer of $\varphi^*$ (R² = 0.935), which is weak evidence.
3. **Water quality without antiscalant.** Our constraint is a no-dosing thermodynamic upper
   bound; real towers use scale inhibitors, so water-quality costs are conservative (high).
   Calcite dominance holds within the drinking-water database used.
4. **Declared cost and engineering parameters**; energy/carbon figures are magnitudes, and
   monetary values are internally consistent only.
5. **Indices A/B/C are never combined**; basin net consumption remains
   `NOT_IDENTIFIABLE_FROM_AVAILABLE_DATA`, and the peak-capacity index is load-side only.
6. **All probabilities are model probabilities under stated priors**, not event frequencies.
7. **Grid resolution affects bottleneck identification** (15.4% agreement between coarse and
   fine grids), so first-failure identification is not used as a primary claim.

### Conclusion

Reclaimed-water cooling of AI data centres is neither a demonstrated saving nor a pure
accounting transfer. It is a **sign-variable** intervention acting through two opposing
urban channels. Recognising them converts a bookkeeping identity into a falsifiable
mechanism with a computable threshold, and it changes the planning question from "how much
water does the facility save?" to "which urban account, under what supply margin and what
water-quality constraint?"

---

## Methods (summary)

**Model.** Urban water metabolism engine (`aiuwm_src`, called read-only): daily water
balance, cooling-tower mass balance, fixed-point solution for quality-limited cycles of
concentration, and joint reclaimed allocation.

**Cooling.** $M = E\cdot\mathrm{CoC}/(\mathrm{CoC}-1)$, with $E$ set by heat rejection and
wet-bulb temperature, independent of source composition. Design CoC = 5; the
water-balance-implied effective CoC is 5.444 (8.16% convention gap, reported). See SI §S4.

**Allocation.** Reviewed repository functions
(`allocate_shared_surplus`, `allocate_dedicated_incremental`,
`solve_joint_quality_allocation`) — no rule logic re-implemented. The pool is fixed, so
allocation is a pro-rata of a conserved budget.

**Supply closure (new).** $\psi=(D_{\rm inc}+W_{\rm AI,pot})/W$;
$\Delta=W\max(0,\psi-1)$; $S_{\rm city}=(M_0-M)-\lambda\Delta$, with $\lambda=1$.
Tested on a four-dimensional grid (supply availability × incumbent demand × reclaimed
fraction × quality severity) over two domains and four published water-chemistry sources:
3,840 scenarios, zero failures. Mechanism and two-channel analyses use $\Delta P=0$
(612 scenarios) to guarantee orthogonality to capacity expansion.

**Estimands.** $S_{\rm AI}=(M_0-M)+x_{\rm AI}$; $S_{\rm city}=S_{\rm AI}+r_{\rm inc}-P$;
$\eta_{\rm transfer}=S_{\rm city}/S_{\rm AI}$ (reported only when $S_{\rm AI}>0$).
Indices A/B/C are never merged (§S2).

**Statistics.** Morris screening plus Sobol variance decomposition on
$y=S_{\rm city}/M_0$; 700-sample Latin hypercube under uniform priors, with prior
sensitivity across uniform / log-uniform / triangular reported in SI §S6. All probability
statements are model probabilities.

**Data.** Public water-chemistry sources (IEUA RP-1 2025; LADWP AWPF 2012; Figshare paired
study; SIPIBEL; SDWIS IEU; GSA courthouse cooling tower) are used as parameter-domain
bounds and magnitude anchors, never as calibration targets or point-prediction validation.

**Reproducibility.** Environment locked (Python 3.13.14, numpy 2.4.4, pandas 3.0.5,
matplotlib 3.11.2, phreeqpython 1.6.2). Script→artefact→figure mapping in
`reproduction_manifest.md`; core CSVs verified byte-identical across reruns.

---

## Data and code availability

- Engine and frozen validation artefacts: repository `mmrgr/slzxlw-full` (public).
- This round's scripts and artefacts: `10_论文推进_2026Q4/A13_可靠性机制/`,
  `A14_外部锚定/`, `A15_稳健性/`.
- External anchors with DOI/URL: `A14_parameter_anchors.csv`.
- Reproduction order and environment lock: `A16_英文稿/reproduction_manifest.md`.
- Engine-side evidence register (including NOT_READY items) is disclosed in SI §S8.
