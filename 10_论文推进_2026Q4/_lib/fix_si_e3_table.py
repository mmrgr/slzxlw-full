"""修正 SI E3 表 + 分支计数 (2026-10-17).

用实测值(从 summary.json 读取)对齐:
  E3 P1 化学: acc 0.432, tp 183, fp 0, tn 145
  E3 P2 q>0 : acc 0.675, tp 367, fp 0, tn 145
  E3b C4    : acc 0.914, tp 602, fp 53, tn 92, fn 12
  基线       : 0.809
  分支 C 计数: 3 of 391 (原 3 of 372)
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
WP2 = ROOT / "A31_WP2_假设冻结"

e3 = json.loads((WP2 / "wp2_e3_independent_prediction_summary.json").read_text(encoding="utf-8"))
e3b = json.loads((WP2 / "wp2_e3b_combined_prediction_summary.json").read_text(encoding="utf-8"))

p1 = e3["predictors"]["P1 化学(全部物种更干净)"]
p2 = e3["predictors"]["P2 q>0 (CoC判据)"]
c4 = e3b["candidate_criteria"]["C4  q>0 或 pool_scale>=2"]
base = e3b["majority_baseline"]

OLD_E3 = (
    "| Chemistry only ($c^{\\rm rec}_i<c^{\\rm pot}_i$, all species) | 0.389 | 183 | 0 | 102 | 448 |\n"
    "| Closed form $q>0$ | 0.675 | 367 | 0 | 145 | 247 |\n"
    "| $q>0$ or pool ratio $\\ge 2$ | 0.906 | 602 | 40 | 62 | 29 |\n"
    "| *majority-class baseline* | *0.861* | — | — | — | — |"
)
NEW_E3 = (
    f"| Chemistry only ($c^{{\\rm rec}}_i<c^{{\\rm pot}}_i$, all species) "
    f"| {p1['acc']:.3f} | {p1['tp']} | {p1['fp']} | {p1['tn']} | {p1['tn'] and ''}"
    f"{(448 if False else 391 - p1['tp'] - p1['tn'])} |\n"
    f"| Closed form $q>0$ | {p2['acc']:.3f} | {p2['tp']} | {p2['fp']} | {p2['tn']} "
    f"| {391 - p2['tp'] - p2['tn']} |\n"
    f"| $q>0$ or pool ratio $\\ge 2$ | {c4['acc']:.3f} | {c4['tp']} | {c4['fp']} "
    f"| {c4['tn']} | {c4.get('fn', 391 - c4['tp'] - c4['tn'])} |\n"
    f"| *majority-class baseline* | *{base:.3f}* | — | — | — | — |"
)

t = SI.read_text(encoding="utf-8")
n = 0
if OLD_E3 in t:
    t = t.replace(OLD_E3, NEW_E3, 1)
    n += 1
    print("E3 表已替换")
else:
    print("MISS: E3 表整块未命中, 逐行处理")
    pairs = [
        ("| Chemistry only ($c^{\\rm rec}_i<c^{\\rm pot}_i$, all species) | 0.389 | 183 | 0 | 102 | 448 |",
         f"| Chemistry only ($c^{{\\rm rec}}_i<c^{{\\rm pot}}_i$, all species) | {p1['acc']:.3f} "
         f"| {p1['tp']} | {p1['fp']} | {p1['tn']} | {391 - p1['tp'] - p1['tn']} |"),
        ("| $q>0$ or pool ratio $\\ge 2$ | 0.906 | 602 | 40 | 62 | 29 |",
         f"| $q>0$ or pool ratio $\\ge 2$ | {c4['acc']:.3f} | {c4['tp']} | {c4['fp']} "
         f"| {c4['tn']} | {c4.get('fn', 391 - c4['tp'] - c4['tn'])} |"),
        ("| *majority-class baseline* | *0.861* | — | — | — | — |",
         f"| *majority-class baseline* | *{base:.3f}* | — | — | — | — |"),
    ]
    for a, b in pairs:
        if a in t:
            t = t.replace(a, b, 1)
            n += 1
        else:
            print("  MISS:", a[:60])

if "**3 of 372**" in t:
    t = t.replace("**3 of 372**", "**3 of 391**", 1)
    n += 1
    print("分支计数 372 -> 391")

SI.write_text(t, encoding="utf-8")
print(f"\n合计 {n} 处")
