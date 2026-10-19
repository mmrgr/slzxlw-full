# -*- coding: utf-8 -*-
"""登记最后 3 个负值（Alameda / LA 县中位下的 r*）。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent

p = HERE / "_wr_num_gate.py"
t = p.read_text(encoding="utf-8")
OLD = '    "0.0870": ["cp_impact: C_p=420 时 r*"],\n}'
NEW = ('    "0.0870": ["cp_impact: C_p=420 时 r*"],\n'
       '    "-1.01": ["cp_impact: C_p=546 时 r*=-1.0096"],\n'
       '}')
if OLD in t:
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK 英文 +1")
else:
    print("英文未匹配")

p = HERE / "_si_num_gate.py"
t = p.read_text(encoding="utf-8")
OLD = '    "0.3171": ["cp_impact: C_r=1000"],\n}'
NEW = ('    "0.3171": ["cp_impact: C_r=1000"],\n'
       '    "-1.0096": ["cp_impact: C_p=546 时 r*"],\n'
       '    "-1.1000": ["cp_impact: C_p=550 时 r*"],\n'
       '}')
if OLD in t:
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK SI +2")
else:
    print("SI 未匹配")
