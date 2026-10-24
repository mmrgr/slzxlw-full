## S9 Supplementary figures S1–S27

This section collects 27 figures produced for the analyses added in the revision. They are
grouped by function rather than by the order in which they are cited: S1–S8 address
uncertainty, sensitivity and benchmarking of existing products; S9–S14 address constraint
structure and external pressure scenarios; S15–S20 address multi-constituent water quality
and the decoupling of the three levers; and S21–S27 address material flow and distributional
figure types.

Three conventions apply throughout. First, every figure reads from a named product under
`validation_artifacts/r2/` and the source is stated in the caption, so no plotted number is
transcribed by hand. Second, the figure prefix `S` is used only here; the main text retains
Figures 1–6 and the earlier supplementary set retains Figures R1–R5, so no numbering is
reused. Third, where a figure type would misrepresent the data we say so in the caption
rather than defaulting to it — Figure S3 separates two perturbation calibers that are
easily confused, Figure S8 points to the column that must be read, and Figure S27 explains
why a violin plot is deliberately not used.

Two of these figures report results that are new relative to the original submission rather
than re-plots of existing products. Figure S10 locates the constraint-identity frontier and
shows that the cool endpoint's grid setting lies 131.25 MW below its own critical value;
Figure S16 shows the controlling water-quality constituent switching with the substitution
ratio. Figures S21–S23 are the first material-flow representation of the model and are the
basis for the consumptive-use share reported in Section 4.1 and the Conclusions.

---

**Figure S1.** Monte Carlo response of CAWCC to PUE, design cycles of concentration and
temperature coefficient. Capacity distributions from 1024 Latin-hypercube samples at
(a) D-HA and (b) D-CO, on the 41-point capacity scan under the joint constraint set.
Dotted lines mark P05/P50/P95; the red solid line is the nominal capacity cited in the
main text. The nominal value sits at P73.2 (D-HA, 1150 MW) and P70.3 (D-CO, 1450 MW).
Source: `ha|co/probabilistic_corrected.csv`.

**Figure S2.** Global sensitivity. (a)(b) Morris $\mu^*$–$\sigma$ planes, normalised to
the largest $\mu^*$; $\sigma>\mu^*$ indicates strong nonlinearity or interaction.
(c) Sobol total-effect $S_T$ ranking, both endpoints. The metric is the annual source
abstraction ratio over 14 parameters.
Source: `ha|co/city_morris.csv`, `city_sobol.csv`.

**Figure S3.** Threshold perturbation. **(a)** Shift of each constraint's first-failure
position under ±2% perturbation of its own threshold (per-constraint decomposition, the
`位移_MW` column). **(b)** CAWCC interval when all non-zero-tolerance thresholds are
scaled **simultaneously** by ×0.98–×1.02. ⚠ The two panels answer different questions:
the `CAWCC位移_MW` column is identical across rows within one factor because the script
perturbs all constraints together, so it must not be read as a single-constraint
contribution.
Source: `threshold_perturbation_sensitivity.csv`.

**Figure S4.** Site WUE of each modelled cooling technology against disclosed and
industry-benchmark ranges. Grey bars are literature ranges; dots are model values.
Where a subject reports several values, the bar spans the envelope. Seven technologies
× 12 subjects = 196 benchmark pairs.
Source: `literature_benchmark.csv`.

**Figure S5.** Position of key parameters within their literature envelopes. Each row
draws that parameter's own observed range as a grey bar and places the model value at its
relative position. Because the parameters span five orders of magnitude, the x-axis is a
relative position only and must not be compared across rows. Of 11 anchored parameters,
one falls outside (industrial return coefficient 0.8 against 0.85–0.95).
Source: `parameter_envelope_R7.csv`.

**Figure S6.** Pareto-efficient set of interventions. Median investment against capacity
gain at (a) D-HA and (b) D-CO; the x-axis is symlog because the baseline has zero
investment. Each endpoint contributes exactly one efficient intervention: 30% leakage
reduction at D-HA and 50% grid expansion at D-CO. The combined upgrade matches the
leakage gain at higher cost and so lies off the front. `local_connection_plus_50pct` is
excluded for missing investment data.
Source: `pareto_front.csv`.

**Figure S7.** Water–energy trade-off across cooling technologies. **(a)** Site water
intensity against facility energy penalty relative to evaporative cooling, at the 750 MW
IT slice. **(b)** Whole-system water saving under three offsite electricity water
intensity (EWIF) levels. **(c)** EWIF reversal threshold for the dry-cooled tiers — the
EWIF at which whole-system saving turns negative — all above the disclosed upper bound of
4.52 L/kWh.
Source: `technology_load_sensitivity_R7b.csv`.

**Figure S8.** Water-balance closure diagnostics. **(a)** Magnitude of the relative
closure error for the two identities (stem plot). **(b)** Stability of the storage
balance residual along the capacity axis. All residuals are of order $10^{-13}\%$,
about 14 orders of magnitude below the 5% acceptance line. ⚠ Read the
`相对闭合误差_科学计数` column: the `相对闭合误差_pct` column has been flattened to zero by
`round(...,9)`. Note that the solute closure residual is a bookkeeping identity; its
vanishing is not a physical validation of salt conservation.
Source: `water_balance_closure.csv`.

**Figure S9.** Constraint-identity phase diagram over the parameter plane of source
abstraction capacity (as a multiple $a$ of each endpoint's own baseline) and grid
connection capacity $G$, on a $9\times9$ grid with a 41-point capacity scan in each cell.
Background colour is the side of the binding constraint, black contours are CAWCC
(200 MW steps), and the red stars are the two endpoints used in the main text.
Source: `constraint_identity_phase.csv`.

**Figure S10.** The constraint-identity frontier. **(a)** Critical grid capacity $G^*$
against the abstraction-capacity multiple $a$, bisected from the $9\times9$ phase map to
below 50 MW. **(b)** Margin of the two endpoints relative to the frontier. At D-HA,
$G^*=1256.25$ MW is independent of $a$ (slope $1.9\times10^{-13}$) and the 1500 MW
setting sits 243.75 MW above it; at D-CO, $G^*=1631.25$ MW for $a\ge1.00$, so the
1500 MW setting sits 131.25 MW **below** it. The frontier is set by the grid connection
ratio threshold alone and does not depend on the abstraction capacity.
Source: `constraint_identity_frontier_refined.csv`, `constraint_identity_frontier_summary.json`.

**Figure S11.** Capacity response to the grid setting. CAWCC against $G$ at three
abstraction-capacity multiples. D-HA saturates at 1150 MW once $G$ exceeds about 1200 MW;
D-CO rises monotonically and plateaus at 1350 and 1550 MW, the two plateaus corresponding
to the local connection ratio and the grid connection ratio as the binding constraint.
The red dotted line marks the $G=1500$ MW setting used at both endpoints.
Source: `constraint_identity_phase.csv`.

**Figure S12.** Carrying capacity under external pressure scenarios. CAWCC at the
$r=0.5$ slice for G0 baseline, G1 heat, G2 drought and G3 compound; bar colour is the
side of the first-failing constraint. The compound scenario G3 has no feasible point at
either endpoint — even 0 MW violates the domestic unmet-demand constraint — and is
labelled infeasible rather than omitted.
Source: `pressure_regime_scan.csv`.

**Figure S13.** Family of CAWCC–$r$ responses, one curve per scenario. The slope is the
capacity consequence of the water-quality penalty. At D-CO the decline **doubles from
50 MW to 100 MW** under the heat scenario G1; at D-HA it stays at 100 MW under G1 and
narrows to 50 MW under drought G2, but the system there is close to physical collapse
(baseline capacity only 100 MW).
Source: `pressure_regime_scan.csv`.

**Figure S14.** Capacity cost of the pressure scenarios: change in CAWCC relative to G0
at the same $r$. Drought and the compound scenario cost the water-scarce endpoint most;
the heat scenario costs 50–150 MW at both endpoints.
Source: `pressure_regime_summary.json`.

**Figure S15.** Multi-constituent allowable cycles and critical ratios.
**(a)** Allowable cycles $L_s/C_{mix,s}(r)$ for TDS, chloride and hardness, with the
system value (the minimum across constituents) as the black dotted line. **(b)** The
per-constituent $r^*_s$, with the system threshold being their minimum. The hardness
values are a stress test drawn from common engineering ranges and do not enter the main
results.
Source: `multispecies_rstar.csv`.

**Figure S16.** Switching of the controlling constituent with the substitution ratio.
Background colour and top labels show the constituent currently binding; the black line
is the system cycles of concentration. For $r<0.53$ the design cycles (5.0) bind and CoC
stays at 5.0; for $0.53\le r<0.83$ hardness controls; for $r\ge0.83$ TDS controls.
The same city is therefore governed by a different water-quality indicator at different
substitution ratios, so the criterion must be written as a minimum rather than as a
TDS-specific expression.
Source: `multispecies_control_map.csv`, `multispecies_summary.json`.

**Figure S17.** Share of each constituent as the tightest constraint across a full
factorial grid. Five levels each for $L$ and $C_r$ of the three constituents with $C_p$
fixed at the project values, 15,565 combinations in all. **(a)** Hardness is tightest in
42.7%, chloride in 29.6% and **TDS in only 27.7%**. **(b)** Distribution of the system
$r^*$; the red dashed line is the nominal 0.5532.
Source: `multispecies_grid.csv`.

**Figure S18.** Two-dimensional response of the three levers. CAWCC over the (wastewater
diversion fraction $f$, substitution ratio $r$) plane; each cell is a full 41-point
capacity scan under the purely physical constraint set, with treatment capacity set at
1.25 × production. Moving right (raising production) lifts capacity monotonically, while
moving down (raising the substitution ratio) depresses it beyond the threshold: the two
levers act in opposite directions.
Source: `lever_decoupling_grid.csv`.

**Figure S19.** Effect curves along the two lever axes. **(a)** Fixed $r$, sweeping $f$:
production yields a monotone gain (+400 MW at D-HA, +350 MW at D-CO). **(b)** Fixed $f$,
sweeping $r$: the substitution-ratio effect appears only beyond $r^*$ (−50 to −100 MW at
D-HA, −100 MW at D-CO). The opposite signs of the two slopes mean that "expanding
reclaimed-water use" is not a single-direction policy variable.
Source: `lever_decoupling_grid.csv`.

**Figure S20.** Distribution of the first-failing constraint over the ($f$, $r$) grid.
Text in each cell is the constraint name; colour is its side. Under the purely physical
set, source abstraction controls throughout at D-HA and treatment-works utilisation
throughout at D-CO: **within this grid both production and the substitution ratio change
only the failure position, not the failure identity**. The claim in the main text that
raising production relocates the bottleneck comes from a different experiment and needs
its conditions stated separately.
Source: `lever_decoupling_grid.csv`.

**Figure S21.** Urban water-metabolism flow network at D-HA. **(a)** 0 MW (no AI) and
**(b)** 1200 MW, annual totals over 730 days. Edge width is proportional to annual flow;
nodes are laid out along the supply chain (external inflow → source → treatment →
transmission → end use/return → sinks). Edges below 0.4% of the maximum are omitted for
legibility but still enter the node-conservation check (all intermediate nodes agree to
better than 1%).
The topology is read from `supply_paths[].chain` and `wastewater_connections[]` in
`project.json`, not inferred; the provenance of every edge flow is recorded in the
「依据」(basis) column of the data file.
Source: `water_metabolism_ha_flows.csv`, `water_metabolism_ha_summary.json`.

**Figure S22.** Urban water-metabolism flow network at D-CO (1450 MW), on the same basis
as Figure S21. The two endpoints differ mainly in the reclaimed target share (0.70
against 0.45) and in cooling load.
Source: `water_metabolism_co_flows.csv`, `water_metabolism_co_summary.json`.

**Figure S23.** Node-conservation check for the Sankey diagrams. Relative difference
$=|\text{inflow}-\text{outflow}|/\text{inflow}$, in percent. Horizontal bars span the
capacity points, vertical ticks mark the mean; sink and external nodes are excluded.
Every intermediate node agrees to better than 1%, so the edge weights in Figures S21 and
S22 are closed rather than schematic.
Source: `water_metabolism_{ha,co}_summary.json`.

**Figure S24.** Distribution of CAWCC by external pressure scenario (box plot with all
sample points). Six substitution ratios per scenario; boxes are interquartile ranges,
centrelines are medians, whiskers run to the most extreme point within 1.5×IQR. Drought
pushes the whole distribution to low values (D-HA 1200→100 MW) and narrows the within-
endpoint spread from about ±50 MW to about ±25 MW.
Source: `pressure_regime_scan.csv`.

**Figure S25.** Cumulative distribution of the screening ratio across California supply
systems. The x-axis is the potable-to-reclaimed ratio $k$ on a log scale, the y-axis is
cumulative share. Of 169 systems spanning three orders of magnitude in $k$, 23/169 = 13.6%
fall below $k^*=3.50$ and 3/169 = 1.8% below the conservative boundary $k^*=0.81$.
Source: `_ca_k_clean.json` (188 records before screening, 169 after).

**Figure S26.** Constraint-pressure profile (radar plot). Each axis is a constraint's
actual value (a dimensionless ratio); the red dashed ring is the 1.0 failure line. The
two endpoints have different shapes: D-HA approaches the failure line on peak capacity
ratio and source abstraction, D-CO on the grid connection ratio. The difference is
structural rather than a matter of scale.
Source: `constraint_binding_diagnosis.csv`.

**Figure S27.** Capacity gain of the nine one-to-one interventions (baseline excluded).
Gains are **exactly zero** for 7/9 (D-HA) and 8/9 (D-CO) of the interventions, so
zero-gain items are drawn as jittered points on the zero line and non-zero items as
horizontal bars. ⚠ A violin plot is deliberately **not** used here: the data are a highly
degenerate discrete distribution (eight zeros and one positive value), and kernel density
estimation would manufacture a spurious peak at the single non-zero point.
Source: `intervention_cost_benefit.csv`.

---

### S9.1 Verification of the supplementary figure set

Each figure in this section was inspected visually after generation, and the following
checks were applied to the set as a whole:

1. **Pairing.** All 27 figures exist as both PNG (200 dpi) and PDF; no figure is missing
   either format.
2. **Data provenance.** Each caption names the product file the figure reads, and each
   generating script loads that product rather than embedding constants, with one registered
   exception: Figure S7 reads a product whose EWIF scenarios are columns rather than rows.
3. **Axis and unit completeness.** Every axis carries a label and a unit where a unit exists;
   dimensionless ratios are marked as such in the caption.
4. **Legibility.** Labels are placed to avoid overlap; where a data set was too dense for the
   chosen figure type the caption records the substitution (Figures S3, S6, S27).
5. **Conservation.** The Sankey diagrams (Figures S21–S22) are accompanied by an explicit
   node-conservation check (Figure S23) showing all intermediate nodes agree to better than
   1%; the edge weights are therefore closed rather than schematic.

The supplementary figure set is not covered by the 91-item figure gate that applies to
Figures 1–6 and R1–R5, so the checks above were applied separately.
