> # ⛔ OBSOLETE / 已作废 (2026-10-14)
> **请勿引用本文件。** 其"两条符号相反的通道""供水紧张度 ψ""临界混合比 φ*"
> **全部撤回** —— 源于两处实质错误：(i) 把既有用户的**再生水缺口**（引擎 gap）
> 当作**自来水需求**；(ii) 把【取水量变化】与【未满足需求缺口】相减（量纲错误）。
> 完整审计见 `../A13_可靠性机制/AUDIT_2026-10-14_撤回声明.md`。
> **替代文件**：`manuscript_en_v2.md`（排放—索取平衡口径）。

---

# Two opposing channels govern the urban water outcome of reclaimed-water cooling in AI data centres

**Working draft — Results (core).** All numbers traceable to frozen artefacts under
`10_论文推进_2026Q4/`. See `reproduction_manifest.md` for the script→artefact→figure map.

---

## Abstract (draft)

Data centres are increasingly proposed to cool with municipal reclaimed water, on the
assumption that doing so relieves pressure on potable supplies. Whether that assumption
holds depends not on how much water a facility withdraws, but on two urban-scale effects
that have been assessed only in isolation. Using a paired, mass-conserving urban water
model driven by a real engine, we show that reclaimed-water cooling acts on the city
through **two channels of opposite sign**. A *water-quality channel* worsens the urban
water balance, because blending reclaimed water lowers the admissible cycles of
concentration and therefore raises total makeup demand. A *supply-reliability channel*
improves it, because the same substitution withdraws the data centre from the potable
system and lowers municipal supply stress. Across 3,840 grid scenarios the two channels
oppose each other in 75% of cases, and the net sign depends on which is accounted for.
We further show that the widely used "facility saving equals city saving" identity is an
algebraic consequence of assuming displaced users can always obtain replacement water —
an assumption that, when relaxed, understates urban losses by up to 39,641 ML per period.
The outcome is therefore not zero-sum but **sign-variable**, and we derive the closed-form
mixing ratio at which the city crosses its shortage threshold.

## Results

### 1. The facility-to-city identity is an accounting artefact, not a finding
We first establish what can and cannot be concluded from the existing framework. Define
the city-level net withdrawal change as the difference between a matched
all-reclaimed and all-potable counterfactual:

$$S_{\rm city} = S_{\rm AI} + r_{\rm inc} - P,\qquad
S_{\rm AI} = (M_0 - M) + x_{\rm AI}$$

where $M$ is facility makeup, $M_0$ its value with no reuse, $x_{\rm AI}$ and $r_{\rm inc}$
are reclaimed volumes allocated to the data centre and to incumbent users, and $P$ is the
available reclaimed pool.

Evaluating the engine across both domains and four mixing ratios
(`conservation_check.csv`) gives

| quantity | measured |
|---|---:|
| $\lvert x_{\rm AI}+r_{\rm inc}-(P+\Delta P)\rvert$ (max) | **3.638 × 10⁻¹² ML** (pool 24,404 ML) |
| $\lvert S_{\rm city}-(M_0-M)\rvert$ at $\Delta P=0$ (max) | **3.638 × 10⁻¹² ML** |

The allocator is exactly conservative against the **total budget** $P+\Delta P$:

$$x_{\rm AI}+r_{\rm inc}\equiv P+\Delta P
\quad\Longrightarrow\quad
S_{\rm city}=(M_0-M)+(r_{\rm inc}-P)
$$

This exposes the structure of the claim, and it requires us to separate two regimes that
are routinely conflated:

- **Share-only regime** ($\Delta P=0$ — no new capacity). Then $r_{\rm inc}\le P$, so
  $r_{\rm inc}-P\le0$ and $S_{\rm city}\equiv M_0-M\le0$ **to machine precision**.
- **Capacity-inclusive regime** ($\Delta P>0$). Once added capacity exceeds the incumbent
  shortfall (here $\text{gap}/P=1.38$, so $\Delta P\ge P$ suffices), incumbents draw
  *more* than the original pool and $r_{\rm inc}-P$ turns positive.

> **A caution that changes how the headline number must be read.** In the
> capacity-inclusive regime the probability that $S_{\rm city}>0$ is 0.62, but that
> positivity arises because **incumbent users receive more water than the original pool
> contained** — it is capacity expansion and its attribution, *not* the relief of
> reclaimed-water competition. In the share-only regime the same probability is
> **zero (numerically zero)**.
>
> This 0.62 is also **prior-dependent**: across 11 prior combinations it spans **0.45–0.71**
> (median 0.64; SI §S6). Only the *trend* — ≈0 at $\Delta P=0$, then a plateau — is
> transferable; the absolute level is not a real-world probability. By contrast, the
> share-only probability stays at 0–0.003 under **every** prior tested, so the mechanism
> result below is prior-insensitive.
>
> **All probabilities in this paper are model probabilities under the stated priors and
> scenario set, not observed event frequencies.**

The two are not contradictory, and neither may be reported alone. All mechanism results
below are obtained in the **share-only** regime, which is what makes them orthogonal to
capacity expansion.

The identity is therefore a conservation statement, not a physical law. It holds if and
only if (i) the reclaimed pool is exogenous and (ii) displaced incumbent demand is
backfilled from an effectively unbounded potable source. Condition (ii) is the
load-bearing one and has never been tested: it is precisely the assumption that "urban
water security" is supposed to interrogate. Reported as a discovery, $S_{\rm city}\le0$
would be a restatement of its own premises — a criticism the project's own evidence
register already carries (`C3 = REFUTED_IN_BOUNDED_RUN`, `C8 = NOT_READY`).

### 2. Relaxing infinite backfill yields a falsifiable shortage criterion

We replace unbounded potable backfill with a finite, reliability-constrained municipal
source. Define the dimensionless **supply stress**

$$\psi = \frac{D_{\rm inc} + W_{\rm AI,pot}}{W}$$

with $W$ the available municipal supply, $D_{\rm inc}$ incumbent potable demand, and
$W_{\rm AI,pot}$ the data centre's actual potable draw. Unmet incumbent demand is

$$\Delta = W\cdot\max(0,\ \psi-1),$$

and the city balance becomes

$$S_{\rm city} = \underbrace{(M_0-M)}_{\text{quality channel } \le 0}
\;-\;\lambda\,\Delta.$$

The criterion is falsifiable in a single line: $\Delta>0 \iff \psi>1$.

**Test.** A four-dimensional grid over supply availability, incumbent demand, reclaimed
fraction and water-quality severity, spanning two domains and four published
water-chemistry sources (**3,840 scenarios, zero failures**):

| group | n | prediction | result |
|---|---:|---|---|
| $\psi>1$ (supply tight) | 1,308 | $\Delta>0$ | ✅ **holds for all** |
| $\psi\le1$ (supply ample) | 2,532 | $\Delta=0$ | ✅ **holds for all** |

**Zero exceptions in 3,840 cases.** The criterion is exact, not fitted.

Because the identity *omits* $\Delta$, it **systematically understates urban loss**:
extra loss peaks at **39,641 ML per period** (median 8,335 ML among the 1,308 affected
cases). The magnitude is domain-consistent (ha 39,641; co 38,662 ML; 2.5% apart).

### 3. Two channels of opposite sign

Writing the two terms separately exposes the central result. Over $\varphi:0\to0.8$ at
zero added capacity (`channel_decomposition.csv`):

| channel | mechanism | mean change | direction |
|---|---|---:|---|
| **Q** — water quality | $\varphi\uparrow\Rightarrow$ CoC$\downarrow\Rightarrow M\uparrow$ | **−13,937 ML** | worsens |
| **R** — supply reliability | $\varphi\uparrow\Rightarrow W_{\rm AI,pot}\downarrow\Rightarrow\psi\downarrow\Rightarrow\Delta\downarrow$ | **+4,742 ML** | improves |
| net | $S_{\rm city}$ | −9,195 ML | worsens |

The channels carry **opposite signs in 75% of scenarios**, and the decomposition is exact
(residual 0.0 ML). The two mechanisms have never been jointly accounted for: assessing
only Q yields "reclaimed cooling harms the city"; assessing only R yields "it helps".
**The sign of the conclusion depends on which channel is counted** — which is why
published assessments, each capturing one side, reach opposite verdicts.

The analytic form of the stress channel is exact to machine precision
($\max$ error **0.0** over 612 scenarios):

$$\psi(\varphi) = \frac{D_{\rm inc} + (1-\varphi_{\rm eff})\,M(\varphi)}{W}$$

### 4. A critical mixing ratio the city must exceed

Setting $\psi(\varphi^*)=1$ defines the reclaimed fraction needed for the city to escape
its shortage threshold. The value is set by the supply margin and is **predictable**,
not fitted:

| supply availability $W_{\rm scale}$ | $\psi(\varphi{=}0)$ | $\psi(\varphi{=}0.8)$ | $\varphi^*$ |
|---:|---:|---:|---:|
| 0.80 | 1.250 | 1.093 | **not reachable** |
| 0.85 | 1.176 | 1.029 | **not reachable** |
| 0.90 | 1.111 | 0.971 | **0.55** (co: 0.70) |
| 0.95 | 1.053 | 0.920 | **0.25** (co: 0.30) |
| 1.00 | 1.000 | 0.874 | **0.00** |

Two robust features:

1. **Looser supply lowers the required mixing ratio.** The worse the municipal supply
   margin, the *more* reclaimed water the city needs to clear the threshold.
2. **There is a supply floor.** At $W_{\rm scale}\le0.85$, raising $\varphi$ to 0.8 still
   leaves $\psi>1$: reclaimed cooling **cannot** close the shortfall on its own.

The domain split has a physical explanation. The ratio $D_{\rm inc}/M_0$ is 0.925 (ha)
and 0.973 (co); the city with the larger incumbent share needs a higher $\varphi^*$
(0.671 vs 0.542, interpolated). This is a testable prediction, not a fitted one.

### 5. The mechanism is orthogonal to capacity expansion (falsification control)

A natural objection is that these effects merely restate the known result that adding
reuse capacity can turn $S_{\rm city}>0$ — with added capacity the existing model already
yields positive values in ~62% of samples. We therefore ran every test in §3–4 at
**zero added capacity** (`dp_all_zero = True`, dp ≡ 0). The reliability channel remains
fully active: $\Delta$ falls from 7,028 ML to 0 ML across $\varphi:0\to0.8$.

**The two effects are independent axes.** Capacity expansion buys volume; supply
reliability changes *who actually receives water*. Neither subsumes the other.

### 6. Honest negative result: the water-volume account never turns positive

We report a result that constrains our own claim. Across all six audit groups, $S_{\rm city}$
is **monotone with maximum at $\varphi=0$** (`argmax_phi = 0.0`, `n_nonmonotone = 0`):
reclaimed cooling **always worsens** the urban water-volume account, even though it
**improves** reliability. Channel R's gain (+4,742 ML) does not offset channel Q's loss
(−13,937 ML). No $\varphi$ makes the volume account positive.

The two accounts must therefore be reported **separately** and never merged into a single
"sustainability score". Merging them would erase the mechanism entirely — which is the
methodological error this work identifies.

---

## Draft take-home

The urban outcome of reclaimed-water cooling is **not zero-sum; it is sign-variable**, and
its sign is determined by which of two opposing channels a study accounts for. Facility-level
water savings are conserved away in the volume account, yet the same substitution genuinely
reduces municipal supply stress. Framing the question as "does reclaimed cooling save water?"
therefore has no single answer; the answerable question is *which* urban account, under
*what* supply margin and *what* water-quality constraint.
