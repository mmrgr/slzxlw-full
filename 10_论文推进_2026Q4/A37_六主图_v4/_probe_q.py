# -*- coding: utf-8 -*-
"""核验 q = (M0-M1)/M1 的分组（当前为 q>0 263 / q≈0 288 / q<0 288）。

注意：数字由脚本实时计算，docstring 中的写法仅为历史说明。
"""
import numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
d = pd.read_csv(ROOT/"A13_可靠性机制"/"supply_state_regimes.csv")
rel = d[(d.status=='converged_unique') & (~d.coc_floor_degenerate.astype(bool))].copy()
rel["q"] = (rel.M0_ml - rel.M1_ml) / rel.M1_ml
q = rel["q"]
print("n_rel", len(rel))
for tol in [0.0, 1e-9, 1e-6, 1e-3]:
    print(f"tol={tol:g}: q>0 {(q>tol).sum()}  q<-tol {(q<-tol).sum()}  |q|<=tol {(q.abs()<=tol).sum()}")
print("exact: >0", (q>0).sum(), " <0", (q<0).sum(), " ==0", (q==0).sum())
print("len M1==0:", (rel.M1_ml==0).sum())

qpos = rel[q>0]
print("q>0 harmful (ds>0):", (qpos.dS_pot_ml>0).sum(), "/", len(qpos))
print("q>0 dS describe:", qpos.dS_pot_ml.describe()[["min","50%","max"]].to_dict())
