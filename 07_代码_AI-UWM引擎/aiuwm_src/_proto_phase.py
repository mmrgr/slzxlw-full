# -*- coding: utf-8 -*-
"""原型：验证 (取水能力 x 电网容量) 二维相图扫描可行，测量单点耗时。"""
import sys, json, time, copy
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
ROOT = Path(__file__).resolve().parent
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import pandas as pd
from run_r2 import load_domain, scan_with_mean, daily_constraints, CAPACITIES_SCAN
from aiuwm.ai_capacity import find_ai_carrying_capacity


def cawcc(scan, cons):
    return find_ai_carrying_capacity(scan, cons)


proj, ts, cons = load_domain("ha")
day_cons = daily_constraints(cons)
print("约束数（日尺度）:", len(day_cons), list(day_cons))

t0 = time.time()
scan = scan_with_mean(proj, ts, CAPACITIES_SCAN)
t1 = time.time()
r = cawcc(scan, day_cons)
t2 = time.time()
print(f"41 点扫描 {t1-t0:.1f}s, 求阈值 {t2-t1:.2f}s")
print("CAWCC:", r["maximum_safe_ai_capacity_mw"], "首失效:", r["limiting_constraint"],
      "首失效容量:", r["first_failed_capacity_mw"])

# 试旋钮：取水能力 x 电网容量
for abst, grid in [(380, 1500), (340, 1500), (380, 1200), (380, 1800)]:
    trial = copy.deepcopy(proj)
    trial["components"]["RES1"]["abstraction_capacity_ml_day"] = float(abst)
    trial["components"]["AI_DC1"]["grid_connection_capacity_mw"] = float(grid)
    s = scan_with_mean(trial, ts, CAPACITIES_SCAN)
    rr = cawcc(s, day_cons)
    print(f"  abst={abst:>4} grid={grid:>5} -> CAWCC {rr['maximum_safe_ai_capacity_mw']:>6} MW, "
          f"{rr['limiting_constraint']}")
