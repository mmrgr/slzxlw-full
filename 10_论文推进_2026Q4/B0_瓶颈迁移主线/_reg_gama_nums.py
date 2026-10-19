# -*- coding: utf-8 -*-
"""登记 GAMA / C_p 锚定的新数字进两个数字门禁。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent

EN_OLD = '    "0.19": ["rstar_sens: 两端跨度上限 0.1872/0.1891"],\n}'
EN_NEW = ('    "0.19": ["rstar_sens: 两端跨度上限 0.1872/0.1891"],\n'
          '    # ---- C_p 外部锚定尝试（GAMA 实测，_gama_statewide.py）----\n'
          '    "420": ["gama: 全州 TDS 中位"],\n'
          '    "10090": ["gama: TDS 记录数"],\n'
          '    "0.0870": ["cp_impact: C_p=420 时 r*"],\n'
          '}')

SI_OLD = '    "0.104": ["rstar_sens: CoC_d 最大偏移"],\n}'
SI_NEW = ('    "0.104": ["rstar_sens: CoC_d 最大偏移"],\n'
          '    # ---- GAMA TDS 分布与 C_p 影响（_gama_statewide.py / _cp_anchor_impact.py）----\n'
          '    "120": ["gama: p5"],\n'
          '    "239": ["gama: p25"],\n'
          '    "420": ["gama: p50"],\n'
          '    "2100": ["gama: p95"],\n'
          '    "10090": ["gama: TDS 记录数"],\n'
          '    "546": ["gama: Alameda 县中位"],\n'
          '    "550": ["gama: LA 县中位"],\n'
          '    "0.0870": ["cp_impact: C_p=420"],\n'
          '    "0.5227": ["cp_impact: C_p=210"],\n'
          '    "0.8125": ["cp_impact: C_r=500"],\n'
          '    "0.4194": ["cp_impact: C_r=800"],\n'
          '    "0.3171": ["cp_impact: C_r=1000"],\n'
          '}')

for name, old, new in (("_wr_num_gate.py", EN_OLD, EN_NEW),
                       ("_si_num_gate.py", SI_OLD, SI_NEW)):
    p = HERE / name
    t = p.read_text(encoding="utf-8")
    if old in t:
        p.write_text(t.replace(old, new, 1), encoding="utf-8")
        print(f"OK {name}")
    else:
        print(f"未匹配 {name}")
