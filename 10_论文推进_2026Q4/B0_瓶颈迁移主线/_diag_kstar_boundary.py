# -*- coding: utf-8 -*-
"""诊断 ρ=0.1 的边界计数差异：用精确 k* 还是四舍五入后的 k*？

差异来源：k1 = (1/0.5532-1)/0.10 = 8.0774...，若用 round(...,2)=8.08 比较计数，
会把 k ∈ [8.0774, 8.08) 的系统也计入；用精确值则不计入。
这属于"边界并列"问题，必须在论文里说清用的是哪一个口径。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
recs = json.loads((HERE / "_ca_k_clean.json").read_text(encoding="utf-8"))["records"]
ks = sorted(float(r["k"]) for r in recs)
n = len(ks)

for rho in (0.10, 0.20, 0.50, 1.00):
    exact = (1.0 / 0.5532 - 1.0) / rho
    rounded = round(exact, 2)
    c_exact = sum(1 for x in ks if x < exact)
    c_round = sum(1 for x in ks if x < rounded)
    between = [x for x in ks if exact <= x < rounded]
    print(f"ρ={rho}: k*_exact={exact:.6f}  k*_round={rounded}  "
          f"n(exact)={c_exact}  n(round)={c_round}  差={c_round-c_exact}")
    if between:
        print(f"        落在 [exact, round) 区间内的 k: {between}")
