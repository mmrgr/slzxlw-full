# -*- coding: utf-8 -*-
"""登记 C_p 精度反解的 5 个新数字。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent

p = HERE / "_wr_num_gate.py"
t = p.read_text(encoding="utf-8")
OLD = '    "-1.0096": ["cp_impact: C_p=545.5 时 r*"],\n}'
NEW = ('    "-1.0096": ["cp_impact: C_p=545.5 时 r*"],\n'
       '    # ---- C_p 精度反解（_cp_precision.py，r=0.499 临界）----\n'
       '    "230.8": ["cp_precision: r=0.499 的临界 C_p"],\n'
       '}')
if OLD in t:
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK 英文 +1")
else:
    print("英文未匹配")

p = HERE / "_si_num_gate.py"
t = p.read_text(encoding="utf-8")
OLD = '    "-1.1000": ["cp_impact: C_p=550 时 r*"],\n}'
NEW = ('    "-1.1000": ["cp_impact: C_p=550 时 r*"],\n'
       '    # ---- C_p 精度反解（_cp_precision.py）----\n'
       '    "230.8": ["cp_precision: r=0.499 临界"],\n'
       '    "272.3": ["cp_precision: r=0.444 临界"],\n'
       '    "50.8": ["cp_precision: 180 距 230.8 的余量"],\n'
       '    "380.2": ["cp_precision: C_r=500 时临界"],\n'
       '    "81.4": ["cp_precision: C_r=800 时临界"],\n'
       '}')
if OLD in t:
    p.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK SI +5")
else:
    print("SI 未匹配")
