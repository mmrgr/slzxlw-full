# -*- coding: utf-8 -*-
"""把英文稿中 k* 敏感性的数字登记进跨语言数字门禁。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
GATE = HERE / "_wr_num_gate.py"

OLD = '    "1450": ["1450"],\n}'
NEW = ('    "1450": ["1450"],\n'
       '    # ---- k* 敏感性（_verify_kstar_table.py 29/29 从原始数据复算）----\n'
       '    "0.10": ["kstar: rho 行"],\n'
       '    "0.2308": ["kstar: rho=6/26"],\n'
       '    "0.61": ["kstar: r* 行"],\n'
       '    "8.08": ["kstar: rho=0.10 的 k*"],\n'
       '    "0.81": ["kstar: rho=1.0 的 k*（保守边界）"],\n'
       '    "4.33": ["kstar: r*=0.50 的 k*"],\n'
       '    "2.77": ["kstar: r*=0.61 的 k*"],\n'
       '    "57": ["kstar: rho=0.10 的系统数"],\n'
       '}')

t = GATE.read_text(encoding="utf-8")
if OLD not in t:
    print("未匹配")
else:
    GATE.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK 已登记 8 个 k* 数字")
