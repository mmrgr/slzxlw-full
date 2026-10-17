"""Abstract 精简 v2: 真正删减词语至 <=300 (2026-10-17)."""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"
t = P.read_text(encoding="utf-8")

# 用单行(已展开)形式精确替换; 先取当前 abstract 文本
i = t.index("## Abstract")
j = t.index("\n---", i)
old_ab = t[i:j]

NEW = """## Abstract

Cooling AI data centres with reclaimed water is usually assessed by facility-level accounting,
which assumes displaced users can always find replacement potable water and that delivered
water equals abstracted water. Testing both on a daily engine, we replace them with a
three-account ledger — *requested*, *delivered*, *abstracted* — unequal in all 68 engine runs,
and derive an exact identity (residual 2.5 × 10⁻¹¹ ML, 839 solver-reliable scenarios) unifying
two regimes: where the reclaimed pool is committed to incumbents, a data centre's draw is fully
displaced and city withdrawal does not fall; where unused reclaimed water remains, withdrawal
genuinely falls. The sign follows from competition between a quality term, predictable from
pre-intervention chemistry, and a displacement term needing demand-side data. A chemistry-only
criterion predicts that sign no better than chance (0.67 versus a 0.81 baseline), so the widely
quoted "sign-criterion agreement" is an accounting check rather than a prediction; adding one
pre-intervention demand-side quantity raises in-sample accuracy to 0.91 and gives a **median
fold gain of +0.09** — with two of four folds informative, a candidate. Sensitivity analysis
finds one sign lever within the cited limits — reclaimed-water alkalinity — but it is **not
panel-invariant**: under a stricter make-up-water tier the binding species shifts and no
single-species perturbation flips the sign. Heatwaves and droughts change magnitude by ≤1.14×
without reversing the outcome, whereas a binding supply cap converts the effect into a service
gap and curtails the data centre. Among **10,826 observed wastewater plants** the committed
share is **not identified** (provable bounds [0%, 100%]) and only ~2–6% could support a surplus
scheme; among **141 documented reclaimed-water projects, industrial cooling is the largest use
category (28.4%)**, 68% inside our modelled scale. Because the mechanism's magnitude is
**solver-path dependent by ~800×**, we keep our conclusions' direction but treat the mechanism
attribution as convention-dependent.
"""

t = t[:i] + NEW + t[j:]
P.write_text(t, encoding="utf-8")

i2 = t.index("## Abstract")
j2 = t.index("\n---", i2)
print(f"Abstract 词数 = {len(t[i2:j2].split())}")
