"""修正 SI 折外验证段落 (2026-10-17).

旧文:
  "mean out-of-sample accuracy 0.917 vs mean out-of-sample baseline 0.859, a gain of +0.042.
   The in-sample best criterion is therefore *not* post-hoc selection, since the same
   criterion is chosen out-of-fold."
问题: 基线 0.859 与实际 0.815 不符; 增益 +0.042 与实际 +0.102 不符;
      且"not post-hoc selection"的强断言与主稿"candidate"口径不一致。
"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
SI = ROOT / "A16_英文稿/supplementary_information.md"
e3b = json.loads((ROOT / "A31_WP2_假设冻结/wp2_e3b_combined_prediction_summary.json")
                 .read_text(encoding="utf-8"))
oos, bl, gain = e3b["oos_mean_test_acc"], e3b["oos_mean_baseline"], e3b["oos_gain"]

OLD = """   evaluate on the held-out one): mean out-of-sample accuracy **0.917** vs mean out-of-sample
   baseline **0.859**, a gain of **+0.042**. The in-sample best criterion is therefore *not*
   post-hoc selection, since the same criterion is chosen out-of-fold."""

NEW = (
    f"   evaluate on the held-out one): mean out-of-sample accuracy **{oos:.3f}** vs mean "
    f"out-of-sample\n   baseline **{bl:.3f}**, a gain of **{gain:+.3f}**. The criterion is "
    "re-selected inside each\n"
    "   fold, so the in-sample winner is not purely a post-hoc artefact; but only two of the four\n"
    "   folds are informative (the other two have a saturated baseline), so we report the criterion\n"
    "   as a **candidate** rather than a validated predictor (main text §7)."
)

t = SI.read_text(encoding="utf-8")
if OLD in t:
    SI.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("折外段落已重写:")
    for line in NEW.split("\n"):
        print("  ", line)
else:
    print("MISS: 未命中整块")
    i = t.find("mean out-of-sample accuracy")
    print(repr(t[max(0, i - 120):i + 320]))
