# -*- coding: utf-8 -*-
"""把 r* 参数锚定/敏感性的新数字登记进两个数字门禁。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent

EN_OLD = '    "57": ["kstar: rho=0.10 的系统数"],\n}'
EN_NEW = ('    "57": ["kstar: rho=0.10 的系统数"],\n'
          '    # ---- r* 四参数 ±10% 敏感性（_rstar_sens_exact.py 精确复算）----\n'
          '    "0.018": ["rstar_sens: C_p 最大偏移"],\n'
          '    "0.089": ["rstar_sens: C_r 最大偏移"],\n'
          '    "0.094": ["rstar_sens: L 最大偏移"],\n'
          '    "0.104": ["rstar_sens: CoC_d 最大偏移"],\n'
          '    "0.19": ["rstar_sens: 两端跨度上限 0.1872/0.1891"],\n'
          '}')

SI_OLD = '    "8.0787": ["_diag: 夹在精确值与取整值之间的那个系统的 k"],\n}'
SI_NEW = ('    "8.0787": ["_diag: 夹在精确值与取整值之间的那个系统的 k"],\n'
          '    # ---- r* 四参数锚定与敏感性（_rstar_param_anchoring.py / _rstar_sens_exact.py）----\n'
          '    "0.0936": ["rstar_sens: L 最大偏移"],\n'
          '    "0.1040": ["rstar_sens: CoC_d 最大偏移"],\n'
          '    "0.0888": ["rstar_sens: C_r 最大偏移"],\n'
          '    "0.0178": ["rstar_sens: C_p 最大偏移"],\n'
          '    "0.1872": ["rstar_sens: L 两端跨度"],\n'
          '    "0.1891": ["rstar_sens: CoC_d 两端跨度"],\n'
          '    "0.1560": ["rstar_sens: C_r 两端跨度"],\n'
          '    "0.0343": ["rstar_sens: C_p 两端跨度"],\n'
          '    "0.46": ["rstar_sens: 下界（L -10%）"],\n'
          '    "0.66": ["rstar_sens: 上界（L +10%）"],\n'
          '}')

ok = 0
p = HERE / "_wr_num_gate.py"
t = p.read_text(encoding="utf-8")
if EN_OLD in t:
    p.write_text(t.replace(EN_OLD, EN_NEW, 1), encoding="utf-8")
    print("OK 英文稿门禁 +5")
    ok += 1
else:
    print("英文稿门禁未匹配")

p = HERE / "_si_num_gate.py"
t = p.read_text(encoding="utf-8")
if SI_OLD in t:
    p.write_text(t.replace(SI_OLD, SI_NEW, 1), encoding="utf-8")
    print("OK SI 门禁 +10")
    ok += 1
else:
    print("SI 门禁未匹配")
