# -*- coding: utf-8 -*-
"""登记扩展扫描与 CO 三网格的新数字到两个数字门禁。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent

EN_ADD = ('    # ---- 非 informative 范围依赖（_verify_noninformative_range 25/25）----\n'
          '    "4000": ["扫描上限 4000 MW"],\n'
          '    "3000": ["CO unmet_cooling 首失效"],\n'
          '    "0.8992": ["HA wwtw 最大利用率"],\n'
          '    "0.8755": ["CO wwtw 最大利用率"],\n'
          '    "3.45": ["50/1450 百分比"],\n')

SI_ADD = ('    # ---- 扩展扫描 ----\n'
          '    "4000": ["扫描上限"],\n'
          '    "3000": ["CO unmet_cooling 首失效"],\n'
          '    "2050": ["HA reliability 首失效"],\n'
          '    "2550": ["CO reliability 首失效"],\n'
          '    "2300": ["HA unmet_cooling / CO peak 首失效"],\n'
          '    "2350": ["CO domestic_unmet 首失效"],\n'
          '    "0.8992": ["HA wwtw 最大"],\n'
          '    "0.8755": ["CO wwtw 最大"],\n'
          '    "3.45": ["百分比"],\n'
          '    # ---- CO 三网格 ----\n'
          '    "1125": ["HA cawcc_25mw r=0.8"],\n'
          '    "1130": ["HA cawcc_10mw r=0.8"],\n'
          '    "1140": ["HA cawcc_10mw r=0.7"],\n'
          '    "1425": ["CO cawcc_25mw r=0.9"],\n'
          '    "1440": ["CO cawcc_10mw r=0.9"],\n'
          '    "1460": ["CO cawcc_10mw 基线"],\n'
          '    # ---- CO 联合 vs 纯物理差距 ----\n'
          '    "700": ["CO r=0.9 联合"],\n'
          '    "750": ["CO 联合 r=0→0.9 降幅"],\n'
          '    "850": ["HA r=0.9 政策失效点"],\n'
          '    "-300": ["HA r=0.9 差距"],\n'
          '    "-450": ["CO r=0.7 差距"],\n'
          '    "-600": ["CO r=0.8 差距"],\n'
          '    "-700": ["CO r=0.9 差距"],\n')

for name, add in (("_wr_num_gate.py", EN_ADD), ("_si_num_gate.py", SI_ADD)):
    p = HERE / name
    t = p.read_text(encoding="utf-8")
    # 在 dict 结尾 "}" 前插入（找最后一个 "\n}" ）
    idx = t.rfind("\n}")
    if idx < 0:
        print(f"{name}: 找不到 dict 结尾")
        continue
    t = t[:idx + 1] + add + t[idx + 1:]
    p.write_text(t, encoding="utf-8")
    print(f"OK {name}")
