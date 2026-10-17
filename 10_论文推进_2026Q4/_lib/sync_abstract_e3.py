"""同步 Abstract 中的 E3 表述 (2026-10-17)."""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MS = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"
t = MS.read_text(encoding="utf-8")

OLD = """chemistry, and a displacement term needing demand-side information. A chemistry-only criterion predicts that sign no better than chance (0.67 versus a
0.86 baseline), the widely quoted "sign-criterion agreement" is an accounting check rather
than a prediction; adding one pre-intervention demand-side quantity raises in-sample accuracy to
0.91 but **not robustly out of sample** (median fold gain 0.000). Sensitivity analysis finds one sign"""

NEW = """chemistry, and a displacement term needing demand-side information. A chemistry-only criterion
predicts that sign no better than chance (0.67 versus a 0.81 baseline), so the widely quoted
"sign-criterion agreement" is an accounting check rather than a prediction; adding one
pre-intervention demand-side quantity raises in-sample accuracy to 0.91 and, under
fold-wise validation, gives a **median gain of +0.09** — with only two of four folds
informative, we report it as a candidate. Sensitivity analysis finds one sign"""

if OLD in t:
    MS.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("Abstract E3 段已更新")
else:
    print("MISS: 未找到锚点")
    i = t.find("chemistry-only criterion predicts")
    print(repr(t[i - 100:i + 500]) if i > 0 else "N/A")
