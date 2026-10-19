# -*- coding: utf-8 -*-
"""登记 Bowers 一致性检验的新数字，并把核验加入总门禁。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent

# ---- 英文门禁 ----
p = HERE / "_wr_num_gate.py"
t = p.read_text(encoding="utf-8")
OLD = '    "230.8": ["cp_precision: r=0.499 的临界 C_p"],\n}'
NEW = ('    "230.8": ["cp_precision: r=0.499 的临界 C_p"],\n'
       '    # ---- 冷却技术档 × Bowers（_tech_wue_benchmark.json，_verify_bowers_benchmark 9/9）----\n'
       '    "616.7": ["bowers: 0.5 AF = 616.7 m3/yr"],\n'
       '    "0.001": ["bowers: WUE 下界（IT=72MW）"],\n'
       '    "0.07": ["bowers: WUE 上界（IT=1MW）"],\n'
       '    "0.398": ["模型 dry_first 档 WUE"],\n'
       '    "2.205": ["模型 evaporative 档 WUE"],\n'
       '}')
if OLD in t:
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK 英文 +5")
else:
    print("英文未匹配")

# ---- SI 门禁 ----
p = HERE / "_si_num_gate.py"
t = p.read_text(encoding="utf-8")
OLD = '    "150": ["HA 降漏损 +150"],\n}'
NEW = ('    "150": ["HA 降漏损 +150"],\n'
       '    # ---- 冷却技术档 × Bowers ----\n'
       '    "616.7": ["bowers: 0.5 AF 换算"],\n'
       '    "0.398": ["dry_first WUE"],\n'
       '    "0.606": ["hybrid WUE"],\n'
       '    "0.000": ["dry WUE"],\n'
       '    "1.912": ["liquid_to_water WUE"],\n'
       '    "2.117": ["efficient_evaporative WUE"],\n'
       '    "2.205": ["evaporative WUE"],\n'
       '    "56.9": ["dry_first 年补水 m3"],\n'
       '    "86.1": ["hybrid 年补水 m3"],\n'
       '    "251.7": ["liquid_to_water 年补水 m3"],\n'
       '    "278.7": ["efficient_evaporative 年补水 m3"],\n'
       '    "290.2": ["evaporative 年补水 m3"],\n'
       '    "0.0070": ["bowers WUE @10MW"],\n'
       '    "0.0704": ["bowers WUE @1MW"],\n'
       '    "0.0010": ["bowers WUE @72MW"],\n'
       '    "315": ["湿冷/Bowers 倍数"],\n'
       '    "61": ["PDF p.61 页码"],\n'
       '    "60": ["PDF p.60 页码"],\n'
       '    "4.18": ["EIR printed p.4.18-2 页码"],\n'
       '    "-2": ["EIR 页码 4.18-2 的尾号"],\n'
       '}')
if OLD in t:
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK SI +20")
else:
    print("SI 未匹配")

# ---- 总门禁 ----
p = HERE / "_wr_final_gate.py"
t = p.read_text(encoding="utf-8")
OLD = '    ("UWMP 水质证据核验（11 项）", "_verify_uwmp_quality.py"),\n'
NEW = OLD + '    ("冷却技术档×Bowers 核验（9 项）", "_verify_bowers_benchmark.py"),\n'
if OLD in t and "_verify_bowers" not in t:
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK 总门禁已加入")
else:
    print("总门禁未匹配")
