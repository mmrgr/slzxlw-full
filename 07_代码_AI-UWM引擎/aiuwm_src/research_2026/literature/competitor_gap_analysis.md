# Competitor Gap Analysis

## What the closest papers already establish

The current literature already supports several points that AI-UWM must not present as new: cooling choices change water-energy-carbon trade-offs; AI deployment can create large direct and indirect water footprints; treated wastewater can be paired with data centres; reuse and recirculation raise chemistry and compatibility concerns; and urban water infrastructure can impose capacity and affordability constraints.

Alissa et al. provide a lifecycle comparison of advanced cooling technologies and quantify blue-water, energy, and GHG changes. Xiao et al. provide a national US AI-server footprint projection with uncertainty in siting, PUE, WUE, and grid pathways. Wang et al. provide the closest quantitative reuse competitor: a global data-centre/WWTP geodatabase, spatial optimization, engineering modelling, and LCA/LCC. Saleh's 2026 ES&T Viewpoint directly argues that reuse moves sustainability analysis beyond water demand toward chemistry, constituent enrichment, treatment demand, and blowdown. Han et al. focus on peak public-water capacity, while Alston et al. resolve hourly generator-side indirect water relocation. Masanet's 2026 review makes scope, representativeness, reproducibility, and terminology central quality criteria. WaterMet2 supplies the urban metabolism precedent.

## The narrow gap AI-UWM could fill

The unresolved question is an estimand problem rather than a generic footprint problem. Under matched AI workload and external drivers:

1. Does a lower data-centre potable withdrawal (`S_AI`) produce a lower city source withdrawal (`S_city`)?
2. When a reclaimed pool is shared, which incumbent user's potable demand changes?
3. Does reclaimed-water chemistry alter CoC, makeup, blowdown, and therefore the apparent city benefit?
4. Can an adaptation reduce the burden while accounting for its reject stream, energy, carbon, cost, and service reliability?

These questions require B0/B1/B2 pairing, explicit withdrawal/delivery/consumption/return-flow columns, an auditable shared-versus-dedicated allocation rule, a solute state, and independent G2/G3 evidence. The water-chemistry motivation itself is not novel: Saleh explicitly identifies compatibility and constituent enrichment as emerging concerns. The narrower gap is quantifying how those chemistry constraints interact with shared municipal allocation and incumbent-user response to change city-source withdrawal. None of the reviewed quantitative studies demonstrates all of these elements together.

## Strong competing explanations

- Wang et al. show that reuse and thermal symbiosis can produce large net benefits in a global pairing model. AI-UWM must therefore test positive as well as negative `S_city`; “reuse fails” cannot be the prior.
- Alston et al. show that water can move from a facility to generators when cooling changes. AI-UWM must keep off-site electricity water separate from municipal reclaimed-water flows to avoid double counting.
- Han et al. show that peak capacity, rather than annual volume, can bind. AI-UWM must report daily service constraints and not infer reliability from annual averages.
- Andrijevic et al. show that treatment can be maladaptive if its energy and emissions are omitted. A1/A2 cannot be treated as free chemistry fixes.

## Novelty decision

The project has a plausible conditional contribution: a city-scale, paired, quality-and-allocation estimand that links facility cooling to incumbent urban users. It is not yet a result. The contribution becomes publishable only if the independent chemistry and facility gates pass, the four Q×L cells are run under common drivers, and the effect survives alternative allocation policies and uncertainty decomposition.

## Access limitations

The Alissa, Xiao, Wang, Han, Alston, Behzadian, Andrijevic, and Skerker records were verified at abstract, landing-page, or open-PDF level as noted in `literature_evidence_matrix.csv`. Full supplementary-method extraction was not completed for every paper. No claim here relies on an inaccessible result beyond the cited abstract or open text.

