"""Probe 10: is the e_scale=6.75 'symbol flip' a real flip or a saturation artifact?"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wp5_common as W
import city_model as cm
import wp5_extreme_events as X

_, q_by, primary, _ = W.load_primary_samples()
dom = "ha"; nm = primary[0]
ed = X.daily_plan_e(dom)
sup = X.daily_reuse_supply(dom)
masks = X.make_windows(dom)
hb = X.window_basis(dom, masks["heatwave"], e_daily=ed, p0=None, sup=sup,
                    scale_pool_by_days=False)
print(f"heatwave window: n={hb['n_days']} E={hb['E_window_ml']:.2f} pool={hb['pool_window_ml']:.2f} "
      f"gap={hb['gap_window_ml']:.2f}")

print(f"\n{'e_scale':>9} {'dS':>14} {'C':>12} {'F':>12} {'x_ai':>10} {'M0':>11} {'M1':>11} "
      f"{'CoC0':>8} {'CoC1':>8} {'ok':>6}")
for es in (1, 2, 3, 4, 5, 6, 6.5, 6.75, 7, 8, 10, 20, 40):
    r = X.solve_window(dom, nm, q_by[nm], hb, phi=X.PHI, e_scale=float(es))
    print(f"{es:>9} {r['dS_pot_ml']:>14.4f} {r['C_ml']:>12.2f} {r['F_ml']:>12.2f} "
          f"{r['x_ai_ml']:>10.2f} {r['M0_ml']:>11.2f} {r['M1_ml']:>11.2f} "
          f"{r['CoC0']:>8.4f} {r['CoC1']:>8.4f} {str(r['reliable']):>6}")

print("\n=== does the flip survive as a PHYSICAL statement? check C/F decomposition ===")
for es in (6.5, 6.75, 7.0):
    r = X.solve_window(dom, nm, q_by[nm], hb, phi=X.PHI, e_scale=float(es))
    print(f"  es={es}: dS={r['dS_pot_ml']:.4f} = C({r['C_ml']:.4f}) - F({r['F_ml']:.4f})")
    print(f"      inc_B1={r['inc_B1_ml']:.4f} inc_B2={r['inc_B2_ml']:.4f} "
          f"displaced_raw={r['displaced_raw_ml']:.4f} pool={r['pool_window_ml']:.4f} "
          f"B1 status={r['status_B1']}")

print("\n=== the actual driver: x_ai - (M0-M1) turns negative? ===")
for es in (1, 3, 5, 6, 6.5, 6.75, 7, 10, 40):
    r = X.solve_window(dom, nm, q_by[nm], hb, phi=X.PHI, e_scale=float(es))
    net = r["x_ai_ml"] - (r["M0_ml"] - r["M1_ml"])
    print(f"  es={es:>5}: dM={r['M0_ml']-r['M1_ml']:>10.2f} x_ai={r['x_ai_ml']:>10.2f} "
          f"F={r['F_ml']:>10.2f}  net=x_ai-dM={net:>10.2f}  dS={r['dS_pot_ml']:>12.2f}")

print("\n=== E saturation: does E/day stop growing? (engine PUE cap) ===")
bl = cm.BASELINES[dom]
for es in (1, 5, 10, 40, 100):
    r = X.solve_window(dom, nm, q_by[nm], hb, phi=X.PHI, e_scale=float(es))
    print(f"  es={es:>5}: E_total={r['e_total_ml']:>12.1f} M0={r['M0_ml']:>12.1f} "
          f"M0/E={r['M0_ml']/max(r['e_total_ml'],1e-9):.6f}")
