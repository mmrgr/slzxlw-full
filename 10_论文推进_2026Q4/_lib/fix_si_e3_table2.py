"""修正 SI E3 表: 直接使用 summary.json 的 fn 字段 (2026-10-17).

上一版用 391-tp-tn 估算 FN, 得到 -121 这种不可能值。
正确做法: summary.json 已提供 fn 字段, 直接读取。
同时修正下方折外均值 0.901 -> 0.917、基线 0.859 -> 0.815。
"""
import json
import re
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

t = SI.read_text(encoding="utf-8")

# 用正则替换整个 4 行表格 (不依赖精确旧文本)
pat = re.compile(
    r"\| Chemistry only .*?\| *\*majority-class baseline\* \| \*[\d.]+\* \| — \| — \| — \| — \|",
    re.S,
)
new_tbl = (
    f"| Chemistry only ($c^{{\\rm rec}}_i<c^{{\\rm pot}}_i$, all species) "
    f"| {p1['acc']:.3f} | {p1['tp']} | {p1['fp']} | {p1['tn']} | {p1['fn']} |\n"
    f"| Closed form $q>0$ | {p2['acc']:.3f} | {p2['tp']} | {p2['fp']} | {p2['tn']} | {p2['fn']} |\n"
    f"| $q>0$ or pool ratio $\\ge 2$ | {c4['acc']:.3f} | {c4['tp']} | {c4['fp']} "
    f"| {c4['tn']} | {c4.get('fn', '—')} |\n"
    f"| *majority-class baseline* | *{base:.3f}* | — | — | — | — |"
)
t2, n = pat.subn(lambda m: new_tbl, t)
if n:
    t = t2
    print(f"E3 表已重写 ({n} 处)")
else:
    print("MISS: 表格正则未命中")

# 折外均值
before = t
t = t.replace("mean out-of-sample accuracy **0.901** vs mean out-of-sample",
              f"mean out-of-sample accuracy **{e3b['oos_mean_test_acc']:.3f}** vs mean out-of-sample")
if t != before:
    print("折外均值已更新")

SI.write_text(t, encoding="utf-8")

# 复验
i = t.find("| criterion | accuracy")
print("\n复验:")
for line in t[i:i + 800].split("\n")[:16]:
    print("  ", line[:110])
