# -*- coding: utf-8 -*-
"""同步复算脚本与两个数字门禁中的 Alameda 数值（545.5 / −1.0096）。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent

# ---- 1) 复算脚本：C_p=546 -> 545.5 ----
p = HERE / "_verify_gama_anchor.py"
t = p.read_text(encoding="utf-8")
t = t.replace("546: (546.0, -1.0096)", "545.5: (545.5, -1.0096)")
t = t.replace('ck("C_p=546 时 r* < 0（进入情形 I）", rstar(546.0) < 0, f"{rstar(546.0):.4f}")',
              'ck("C_p=545.5 时 r* < 0（进入情形 I）", rstar(545.5) < 0, f"{rstar(545.5):.4f}")')
t = t.replace('"−1.01", "Regime I"', '"−1.0096", "Regime I"')
p.write_text(t, encoding="utf-8")
print("OK 复算脚本已同步")

# ---- 2) 英文数字门禁：-1.01 -> -1.0096 ----
p = HERE / "_wr_num_gate.py"
t = p.read_text(encoding="utf-8")
t = t.replace('"-1.01": ["cp_impact: C_p=546 时 r*=-1.0096"],',
              '"-1.0096": ["cp_impact: C_p=545.5 时 r*"],')
p.write_text(t, encoding="utf-8")
print("OK 英文门禁已同步")

# ---- 3) SI 数字门禁：546 -> 545.5 ----
p = HERE / "_si_num_gate.py"
t = p.read_text(encoding="utf-8")
t = t.replace('"546": ["gama: Alameda 县中位"],', '"545.5": ["gama: Alameda 县中位"],')
p.write_text(t, encoding="utf-8")
print("OK SI 门禁已同步")
