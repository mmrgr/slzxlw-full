# 存档：v4 超长版 Abstract（954 词）

> 保留原因：该版本含全部撤回与限制的完整披露，信息量完整；
> 但它远超期刊摘要长度（Nature 系列约 150–200 词），已替换为规范摘要。
> 若审稿人要求补充说明，可由此回取。

---

Whether cooling AI data centres with municipal reclaimed water relieves or aggravates urban
water stress has been assessed mostly with facility-level accounting, implicitly assuming
that displaced users can always draw replacement potable water and that delivered water
equals abstracted water. We test both assumptions on a full daily urban water-engine and
replace them with an explicit three-account ledger — *requested*, *delivered* and
*abstracted* — whose quantities are shown to be mutually unequal across 68 engine runs
(0/68 rows agree; path efficiency 0.849, so abstraction exceeds delivery by a factor
1.17–1.18 at the margin). We then derive an exact accounting identity
(residual 2.5 × 10⁻¹¹ ML, 813 solver-reliable scenarios under cited limits) that **unifies two opposite regimes**. When the
reclaimed pool is already committed to incumbent users, a data centre's reclaimed draw is
fully displaced: the city's potable withdrawal does not fall, and the old facility-to-city
identity is recovered exactly. When unused reclaimed water remains, the draw is *not*
displaced and urban potable withdrawal genuinely falls — by up to 27,354 ML per period in
our tests. We show that the sign of the outcome is decided by a **decision inequality** —
the net discharge must outweigh the water-quality effect — and we **explicitly downgrade this
to an accounting convention rather than a discovery**, since it is an algebraic rearrangement
of the underlying identity. What is substantive is the sign structure beneath it: reuse lowers
facility makeup in 290 of 813 scenarios, and in **all 290** the city benefits, with no
exception; when reuse instead raises makeup, the outcome is a genuine contest that goes both
ways. We do **not** claim a single external predictor for that sign: a strict pre-intervention
prediction test (using only information available before the intervention) gives 0.67 accuracy
for the best chemistry-only criterion against a 0.86 majority-class baseline, so the widely
quoted "sign-criterion agreement" is an **accounting consistency check, not a prediction**
(we report this negative result explicitly). The reason is structural: the city outcome is set
by the *competition* between a quality term $q$ — which pre-intervention water chemistry **does**
predict, with the direction of $q$ matching observation in 100% of complete-composition samples —
and a displacement term that requires demand-side information. Adding one such pre-intervention
quantity (the deliverable pool relative to baseline demand) raises in-sample accuracy to 0.906,
but under leave-one-composition-out validation the gain is **not robust** — the median fold
gain is 0.000 and only one of four folds improves — so we report the criterion as **candidate,
not validated**. Global sensitivity over
twelve parameters shows that, **within the cited limit set used here**, only **one** quantity
changes the sign of the outcome — the alkalinity of the reclaimed water, the species that
actually binds the admissible concentration factor. **This lever is not panel-invariant, and we
say so:** re-running under a stricter make-up-water limit tier moves the binding species to
silica and TDS, and no single-species perturbation then flips the sign. What *is* transferable
is the rule that identifies which species binds, namely the smallest limit-to-concentration
ratio. Exposing
the effect to observed heatwaves and droughts changes its magnitude by
at most 1.139× **without ever reversing it**. Imposing a finite
potable-supply cap shows the effect
is not merely redistributed but transformed: as the cap binds, the apparent "extra
abstraction" becomes a **necessary-service gap** (up to 62,080 ML) and the data centre is
itself curtailed. Finally,
setting the water-quality constraint to non-binding makes the outcome exactly zero in the
committed regime — establishing that "reclaimed cooling does not save water" is a property
of *quality-limited, fully-committed* systems rather than of reuse in general. **One
structural caveat bounds the mechanism, and we state it here rather than only in the
Limitations:** the engine supports a second, opt-in quality solver that tracks a loop solute
stock. We ran both paths on identical inputs. They agree on the **sign** of the outcome in all
comparisons, but the quality penalty itself is **path-dependent in magnitude by roughly 800×**
(for the binding composition, blending to $\varphi=0.6$ raises makeup by **+9.8%** in the
primary path versus **+0.012%** in the solute-stock path), and the quality term $q$ shrinks
from −0.096 to −0.0001. Only one of the two compositions actually tests this — for the other,
the quality constraint never binds and both paths return identical numbers — so the effective
evidence is **two scenarios, not four**. We therefore retain the direction of the conclusion
but treat the **mechanism attribution as convention-dependent**, reporting it as a structural
sensitivity rather than resolving it.
Anchoring
against a public dataset of **10,826 observed wastewater treatment plants** shows our supply
parameter sits at the **81st percentile** of that distribution, and that most plants retain spare
treatment capacity (median utilisation 0.594). **We do *not* report the prevalence of the
fully-committed regime in that dataset**: the treated-volume distribution constrains deliverable
*supply* only, whereas the regime is set by committed *demand*, which is unobserved here. We
therefore report a partial-identification result — the share is **not identified** and its
provable bounds are the full [0%, 100%] interval — together with the quantity that *is*
identified: only ~2–6% of plants (depending on the reuse fraction) have the treatment capacity
to support a surplus-type scheme at all. A separate catalogue of **141 documented real
reclaimed-water projects** shows that **industrial cooling is the single largest use category
there (40 projects, 28.4%)** and that **68% of those projects fall within the scale range
modelled here** — so the application studied is not an edge case, though the catalogue is a
case collection rather than a random sample and carries no demand-side field. The result is
thus relevant to most real
systems, while the supply-expansion route that does reduce withdrawal is realistic only for
the largest ones.
