# -*- coding: utf-8 -*-
"""登记技术档敏感性的新数字，并把核验加入总门禁。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent

# ---- 英文门禁 ----
p = HERE / "_wr_num_gate.py"
t = p.read_text(encoding="utf-8")
OLD = '    "2.205": ["evaporative 档 WUE"],\n}'
NEW = ('    "2.205": ["evaporative 档 WUE"],\n'
       '    # ---- 技术档敏感性（_tech_sensitivity.json，_verify_tech_sensitivity 11/11）----\n'
       '    "2.125": ["ha evaporative WUE @1200MW"],\n'
       '    "0.558": ["hybrid WUE"],\n'
       '    "0.327": ["dry_first WUE"],\n'
       '    "6.478": ["evaporative 增幅%"],\n'
       '    "6.472": ["hybrid 增幅%"],\n'
       '    "7.851": ["dry_first 增幅%"],\n'
       '    "0.3972": ["r*(CoC=6)"],\n'
       '    "-1.69": ["CoC_d 弹性 -1.6921"],\n'
       '}')
if OLD in t:
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK 英文 +8")
else:
    print("英文未匹配")

# ---- SI 门禁 ----
p = HERE / "_si_num_gate.py"
t = p.read_text(encoding="utf-8")
OLD = '    "-2": ["EIR 页码 4.18-2 的尾号"],\n}'
NEW = ('    "-2": ["EIR 页码 4.18-2 的尾号"],\n'
       '    # ---- 技术档敏感性 ----\n'
       '    "2.125": ["evaporative WUE @1200MW"],\n'
       '    "0.558": ["hybrid WUE"],\n'
       '    "0.327": ["dry_first WUE"],\n'
       '    "6.478": ["evaporative 增幅"],\n'
       '    "6.472": ["hybrid 增幅"],\n'
       '    "7.851": ["dry_first 增幅"],\n'
       '    "0.3972": ["r*(CoC=6)"],\n'
       '    "-1.69": ["CoC_d 弹性"],\n'
       '}')
if OLD in t:
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK SI +8")
else:
    print("SI 未匹配")

# ---- 总门禁 ----
p = HERE / "_wr_final_gate.py"
t = p.read_text(encoding="utf-8")
OLD = '    ("冷却技术档×Bowers 核验（9 项）", "_verify_bowers_benchmark.py"),\n'
NEW = OLD + '    ("技术档敏感性核验（11 项）", "_verify_tech_sensitivity.py"),\n'
if OLD in t and "_verify_tech_sensitivity" not in t:
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK 总门禁已加入")
else:
    print("总门禁未匹配")
