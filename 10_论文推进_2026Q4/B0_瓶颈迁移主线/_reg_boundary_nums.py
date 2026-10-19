# -*- coding: utf-8 -*-
"""登记 SI S7.7 边界计数口径说明中的 3 个数字。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
GATE = HERE / "_si_num_gate.py"

OLD = '    "2.4": ["kstar_sensitivity: rho=0.50 占比"],\n}'
NEW = ('    "2.4": ["kstar_sensitivity: rho=0.50 占比"],\n'
       '    # 边界计数口径（_diag_kstar_boundary.py 复算；_verify_kstar_table.py 29/29）\n'
       '    "58": ["_diag: 用四舍五入边界会多算 1 个（57→58）"],\n'
       '    "8.0766": ["_diag: rho=0.10 的精确边界 k*"],\n'
       '    "8.0787": ["_diag: 夹在精确值与取整值之间的那个系统的 k"],\n'
       '}')

t = GATE.read_text(encoding="utf-8")
if OLD not in t:
    print("未匹配")
else:
    GATE.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK 已登记 3 个边界口径数字")
