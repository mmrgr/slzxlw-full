# -*- coding: utf-8 -*-
"""核对符号统计口径（严格 <0 / >0 / ==0，当前为 626/177/36）。

注意：数字由脚本实时计算，docstring 中的写法仅为历史说明。
"""
import numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
d = pd.read_csv(ROOT/"A13_可靠性机制"/"supply_state_regimes.csv")
rel = d[(d.status=='converged_unique') & (~d.coc_floor_degenerate.astype(bool))]
ds = rel.dS_pot_ml
print("n_rel", len(rel))
for lab, m in [("==0 exact", ds==0.0), ("abs<1e-12", ds.abs()<1e-12),
               ("abs<1e-9", ds.abs()<1e-9), ("abs<1e-6", ds.abs()<1e-6),
               ("abs<1", ds.abs()<1), ("abs<100", ds.abs()<100)]:
    print(f"{lab:14s} n={m.sum():4d}  <0:{(ds<-0).sum() if lab.startswith('==0') else ''}")
print("strict (<0,>0,==0):", (ds<0).sum(), (ds>0).sum(), (ds==0.0).sum())
print("tol1e-9:", (ds< -1e-9).sum(), (ds>1e-9).sum())
print("tol0 excl band:", (ds<0).sum(), (ds>0).sum(), (ds==0).sum())
# 按 WP0 文档 §6 原样
print("doc-repro strict:", (ds<0).sum(), (ds>0).sum(), (ds==0).sum())
print("doc-repro tol1e-9:", (ds<-1e-9).sum(), (ds>1e-9).sum())

# q 定义探明
for c in ["pool_ml","elig_ml","inc_demand_ml","unused_B2_ml","displaced_ml"]:
    v = rel[c]
    print(f"{c:16s} <0:{(v<0).sum():4d} ==0:{(v==0).sum():4d} >0:{(v>0).sum():4d}")
print("state_by_pool:", rel.state_by_pool.value_counts().to_dict())
