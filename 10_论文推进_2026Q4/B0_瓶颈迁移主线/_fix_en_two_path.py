# -*- coding: utf-8 -*-
"""修正英文稿中关于动态盐分路径的错误解释。

【要撤除的英文】
"The cause is storage buffering rather than an implementation fault: the 24 ML campus pond
 fills from its 12 ML initial state on day one and stays full, while blowdown TDS falls
 from 1998 to about 194 mg L-1, so salts accumulate in the pond rather than in the loop."
以及其后 "Running the capacity scan under both paths makes the bracket explicit..." 整段
（含 "bounds it from below at essentially zero"、"the two ends of a bracket"）。

【替换为】
根因：端点项目未声明市政 TDS 入流 → 动态路径的 C_r 被 mass/volume 覆盖为 8.27 mg/L
（声明值 650 的 1.3%）→ 补水几乎无盐 → 环路不积盐。
2×2 设计：缺 TDS 时 +0.011%，补齐后 +7.363%。
CAWCC：legacy 1200→1100（100 MW），dynamic 1200→1150（50 MW）。
→ 反噬减弱一半，但不消失。「上下界」说法撤回。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

OLD = ("The cause is storage buffering rather than an implementation fault: the 24 ML campus pond "
       "fills from its 12 ML initial state on day one and stays full, while blowdown TDS falls from "
       "1998 to about 194 mg L$^{-1}$, so salts accumulate in the pond rather than in the loop. Two "
       "consequences follow for how this paper should be read. The r\\*\\ results hold under the "
       "condition that cooling storage is unsaturated or negligible — a boundary condition not "
       "previously stated. And the −100 MW and +6.48% figures are legacy-path values that should be "
       "read as the effect in the limit of no dynamic salt buffering, which is an upper bound, since "
       "buffering can only weaken the penalty. Running the capacity scan under both paths makes the "
       "bracket explicit. At the water-scarce endpoint, raising $r$ from 0 to 0.9 moves total "
       "withdrawal by +9.37% and the abstraction ratio by +0.0120 under the legacy path, but by "
       "+0.011% with the abstraction ratio unchanged to six decimals under dynamic tracking. The "
       "purely physical CAWCC follows: it falls 1200 → 1100 MW under the legacy path and stays at "
       "1200 MW under the dynamic one, so the 100 MW effect disappears entirely there. These are "
       "not conflicting results but the two ends of a bracket. The legacy path assumes the whole "
       "salt load of the blended make-up acts on the loop immediately, with no storage buffering, "
       "which bounds the penalty from above. Dynamic tracking with a full 24 ML pond, roughly "
       "0.6 days of make-up, bounds it from below at essentially zero. A real system sits between "
       "them according to pond size relative to daily make-up and to operating policy. What "
       "survives both paths is the criterion: $r^{*}$ states that a quality ceiling begins to "
       "bind above a computable ratio, and that is a claim about where the constraint starts, not "
       "about how much is lost when it does.")

NEW = ("The cause, however, is not storage buffering. Chasing the same residual one level further "
       "shows that neither endpoint project declares a TDS or chloride load for municipal "
       "wastewater: the sanitary load carries only BOD and TSS, so the wastewater ledger is "
       "effectively empty for salts, and `_reuse_output_quality` then overrides the declared "
       "reclaimed concentration of 650 mg L$^{-1}$ with the ledger's mass-to-volume ratio. The "
       "dynamic path therefore ran with a reclaimed TDS of 8.27 mg L$^{-1}$, 1.3% of the declared "
       "value, so the make-up was almost salt-free and the loop could not accumulate salt. The "
       "earlier reading of this as a physical buffering effect was a mistake, and we correct it "
       "here. A 2 × 2 design separates the two explanations at 1100 MW: under the legacy path the "
       "make-up rises 9.373% from $r$ = 0.5 to 0.9 whether or not the wastewater TDS load is "
       "declared, because the legacy path never consults the ledger; under dynamic tracking it "
       "rises 0.011% when the load is missing but 7.363% once the ledger is calibrated so that the "
       "reclaimed concentration returns to 650 mg L$^{-1}$. The lock-up appears only in the cell "
       "with no salt load, which identifies salt-free make-up as the cause rather than storage. "
       "Re-running the capacity scan with the water-quality inputs thus aligned, legacy CAWCC falls "
       "1200 → 1150 → 1100 MW across $r$ = 0, 0.7 and 0.9 while the dynamic path falls 1200 → "
       "1150 → 1150. The effect is halved, not eliminated: 100 MW against 50 MW. We accordingly "
       "withdraw the claim that the 100 MW effect vanishes under dynamic tracking, and with it the "
       "bracket framing that made the legacy path an upper bound and dynamic tracking a lower bound "
       "near zero. The correct statement is narrower and still useful. The direction of the "
       "backlash is the same on both paths, so raising the target ratio always increases withdrawal "
       "and lowers CAWCC; only its magnitude depends on the path, and the −100 MW and +6.48% "
       "reported here are legacy-path values, an upper-end estimate under this modelling "
       "convention rather than a robust point estimate. The criterion itself is untouched in "
       "either case: $r^{*}$ says where a quality ceiling begins to bind, which is an algebraic "
       "property of the four water-quality parameters independent of the model path, so the "
       "derivation, the four-regime taxonomy and the elasticities all stand. We retain the legacy "
       "path as the main scenario because it uses the same CoC expression as the analytic "
       "derivation, matching it to 1e-15, and because the dynamic path can only be run once the "
       "missing wastewater salt load is back-calibrated from the declared $C_r$; the price of that "
       "choice is the upper-end magnitude reported here, which we state explicitly.")

t = EN.read_text(encoding="utf-8")
if OLD in t:
    EN.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK 英文稿（含 bracket 段）已替换")
else:
    print("❌ 英文稿锚点未匹配，需人工定位")
    # 打印近似片段帮助定位
    i = t.find("The cause is storage buffering")
    print(f"   find('The cause is storage buffering') = {i}")
    j = t.find("Running the capacity scan under both paths")
    print(f"   find('Running the capacity scan') = {j}")
