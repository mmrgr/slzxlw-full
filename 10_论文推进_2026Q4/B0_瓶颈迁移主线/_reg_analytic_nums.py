# -*- coding: utf-8 -*-
"""登记解析边界的新数字。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent

EN_ADD = ('    # ---- 解析边界（_verify_analytic_boundary 17/17）----\n'
          '    "2.11": ["10MW 网格 r=0.9 相对误差"],\n'
          '    "22.9": ["解析残差 22.86 MW"],\n'
          '    "1088.9": ["解析预测 CAWCC"],\n'
          '    "1111.76": ["1MW 精扫真值"],\n')

SI_ADD = ('    # ---- 解析边界 ----\n'
          '    "1111": ["1MW 最后合规容量"],\n'
          '    "1112": ["1MW 首次越界容量"],\n'
          '    "2.11": ["10MW 相对误差"],\n'
          '    "22.86": ["解析残差"],\n'
          '    "1088.9": ["解析预测"],\n'
          '    "1111.76": ["精扫真值"],\n'
          '    "0.949889": ["最后合规取水比"],\n'
          '    "0.950034": ["首次越界取水比"],\n')

for name, add in (("_wr_num_gate.py", EN_ADD), ("_si_num_gate.py", SI_ADD)):
    p = HERE / name
    t = p.read_text(encoding="utf-8")
    idx = t.rfind("\n}")
    t = t[:idx + 1] + add + t[idx + 1:]
    p.write_text(t, encoding="utf-8")
    print(f"OK {name}")
