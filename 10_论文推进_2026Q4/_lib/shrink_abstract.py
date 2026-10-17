"""压缩 Abstract 至 <=300 词 (2026-10-17)."""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

P = Path(__file__).resolve().parent.parent / "A16_英文稿/manuscript_en_v3.md"
t = P.read_text(encoding="utf-8")

PAIRS = [
    # 精简措辞, 不删任何定量声明
    ("Cooling AI data centres with reclaimed water is usually assessed by facility-level accounting,\n"
     "which assumes displaced users can always find replacement potable water and that delivered\n"
     "water equals abstracted water. Testing both on a daily urban water engine, we replace them with\n"
     "a three-account ledger",
     "Cooling AI data centres with reclaimed water is usually assessed by facility-level accounting,\n"
     "which assumes displaced users can always find replacement potable water and that delivered\n"
     "water equals abstracted water. Testing both on a daily engine, we replace them with a\n"
     "three-account ledger"),
    ("The sign follows from competition between a quality term, predictable from pre-intervention\n"
     "chemistry, and a displacement term needing demand-side information.",
     "The sign follows from competition between a quality term, predictable from\n"
     "pre-intervention chemistry, and a displacement term needing demand-side data."),
    ("Sensitivity analysis finds one sign\nlever within the cited limits — reclaimed-water alkalinity — but it is **not panel-invariant**:\n"
     "under a stricter make-up-water tier the binding species shifts and no single-species\nperturbation flips the sign.",
     "Sensitivity analysis finds one sign lever within the cited limits — reclaimed-water\n"
     "alkalinity — but it is **not panel-invariant**: under a stricter make-up-water tier the\n"
     "binding species shifts and no single-species perturbation flips the sign."),
    ("Observed heatwaves and droughts change magnitude by at most\n1.14× without reversing the outcome, whereas a binding supply cap converts the effect into a\nservice gap and curtails the data centre.",
     "Observed heatwaves and droughts change magnitude by at most 1.14× without reversing the\n"
     "outcome, whereas a binding supply cap converts the effect into a service gap and curtails\n"
     "the data centre."),
]

n = 0
for a, b in PAIRS:
    if a in t:
        t = t.replace(a, b, 1)
        n += 1
    else:
        print(f"  MISS: {a[:60]}")

P.write_text(t, encoding="utf-8")
i = t.index("## Abstract")
j = t.index("\n---", i)
print(f"替换 {n}/{len(PAIRS)}; Abstract 词数 = {len(t[i:j].split())}")
