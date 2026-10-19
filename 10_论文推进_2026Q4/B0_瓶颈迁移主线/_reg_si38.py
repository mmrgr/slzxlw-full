# -*- coding: utf-8 -*-
"""登记 SI 第 38 条新增的 5 个数字。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
G = HERE / "_si_num_gate.py"

OLD = '    "0.66": ["rstar_sens: 上界（L +10%）"],\n}'
NEW = ('    "0.66": ["rstar_sens: 上界（L +10%）"],\n'
       '    # SI 第 38 条（与第 25/44 条同口径）\n'
       '    "0.19": ["rstar_sens: 两端跨度上限"],\n'
       '    "0.018": ["rstar_sens: C_p 最大偏移"],\n'
       '    "0.089": ["rstar_sens: C_r 最大偏移"],\n'
       '    "0.094": ["rstar_sens: L 最大偏移"],\n'
       '    "0.104": ["rstar_sens: CoC_d 最大偏移"],\n'
       '}')

t = G.read_text(encoding="utf-8")
if OLD in t:
    G.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK +5")
else:
    print("未匹配")
