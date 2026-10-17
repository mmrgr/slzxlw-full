"""重写 Discussion 的 "What is not claimed" (2026-10-17).

【问题】该节只有 3 条, 而 Limitations 有 15 条。
更严重的是: 本轮确立的**三条硬边界**都不在里面:
  · 需求侧不可识别 (committed 分支占比无解, 界 [0%,100%])
  · 机制路径依赖 (volume-only vs R10a 差 12/16 翻符号)
  · 预测器未验证 (中位增益 +0.092, 仅 2/4 折有信息)

"What is not claimed" 是审稿人最先看的部分, 必须把核心边界列全。
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MS = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"
t = MS.read_text(encoding="utf-8")

OLD = """### What is not claimed

We do not claim reclaimed cooling "saves water" or "cannot save water" in general; both are
branch-specific. We do not calibrate absolute volumes to any named city: the potable cap
(380/400 ML/day) is parameterised, so thresholds are conditional. We do not claim the
daily engine is a calibrated hydrological model."""

NEW = """### What is not claimed

We list these explicitly because several are the kind of claim this literature usually makes.

1. **That reclaimed cooling "saves water", or that it "cannot save water".** Both are
   branch-specific in our own grid: reuse lowers city withdrawal in some regimes and raises it in
   others, and the same composition can do both at different pool levels.
2. **That the prevalence of any regime is known.** The share of real plants in the
   fully-committed regime is **not identified** by the external data we have — treated volume
   constrains supply only, while the regime is set by committed demand, which is unobserved. The
   provable bounds are the uninformative full interval **[0%, 100%]** (§11, SI S12).
3. **That the composition effect is solver-independent.** The effect reported here is a property
   of the volume-only quality path. Under the opt-in dynamic path the two differ in sign in
   **12 of 16** matched scenarios and the compositions become nearly indistinguishable
   (§12, SI S21). We keep the volume-only path as the primary estimand and say so.
4. **That the sign criterion is a validated predictor.** A chemistry-only rule is no better than
   the majority class (0.675 vs 0.809); adding one demand-side planning quantity reaches 0.914
   in-sample and a **median fold gain of +0.092**, but only two of four folds are informative
   and no fold varies the demand side. We report it as a **candidate**, not a rule (§7).
5. **That absolute volumes are calibrated to a named city.** The potable supply cap
   (380/400 ML per day) is a parameter, so every threshold in this paper is conditional on it.
6. **That the daily engine is a calibrated hydrological model.** It is a mechanism-testing
   engine, anchored on observed water chemistry, supply scale and cost, not on a city's
   calibration record.
7. **That the mechanism is uniquely attributed.** Our own test of the quality path shows the
   magnitude of the penalty depends on which solver is used by roughly **800×**; we retain the
   direction of the conclusion but treat the mechanism attribution as convention-dependent.
8. **That the external anchors establish prevalence or totals.** The 141-project catalogue and
   the 597-record deployment table are collections, not random samples; one table is stored as
   two blocks that disagree for six provinces and must not be summed."""

if OLD in t:
    MS.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("已重写 What is not claimed (3 条 -> 8 条)")
else:
    print("MISS: 未找到原节")
