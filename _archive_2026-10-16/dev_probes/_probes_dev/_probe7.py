"""Probe 7: why is Sobol 100% NaN, and why does x_alkalinity dominate?"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wp5_common as W
from wp5_morris_sobol import BOUNDS_STRESS
import city_model as cm

_, q_by, primary, _ = W.load_primary_samples()
q = q_by[W.SAMPLE_IEUA]

print("=== alkalinity is the ONLY binding species? check CoC per species limit ratio ===")
print(f"panel limits: {cm.PANELS[W.PANEL]}")
for nm in primary:
    print(f"  {nm}: {q_by[nm]}")
    for sp, lim in cm.PANELS[W.PANEL].items():
        v = q_by[nm].get(sp)
        if v:
            print(f"      {sp:<11} limit={lim:<7} conc={v:<9} limit/conc={lim/v:8.3f}")

print("\n=== CoC when scaling only one species (ha, IEUA, phi=0.6) ===")
bl = cm.BASELINES["ha"]
for sp in W.CORE:
    for s in (0.5, 1.0, 2.0, 3.0):
        qq = dict(q); qq[sp] = q[sp] * s
        try:
            r = W.solve_dS("ha", W.SAMPLE_IEUA, qq, phi=0.6, pool_ml=bl["P0"],
                           gap_ml=bl["gap"], e_total_ml=bl["E_total"])
            print(f"  {sp:<11} x{s:<4}: CoC0={r['CoC0']:.4f} CoC1={r['CoC1']:.4f} "
                  f"dS={r['dS_pot_ml']:11.4f} ok={r['reliable']}")
        except Exception as e:
            print(f"  {sp:<11} x{s:<4}: RAISE {str(e)[:70]}")

print("\n=== Sobol NaN: which parameters produce gate failure in the Saltelli design? ===")
names = list(BOUNDS_STRESS)
rng = np.random.default_rng(20261016)
a = rng.random((512, len(names))); b = rng.random((512, len(names)))
low = np.array([BOUNDS_STRESS[n][0] for n in names])
span = np.array([BOUNDS_STRESS[n][1] - BOUNDS_STRESS[n][0] for n in names])
a, b = low + a*span, low + b*span
from wp5_morris_sobol import Evaluator
ev = Evaluator("ha", W.SAMPLE_IEUA, q, bl)
bad = {}
vals = []
for row in np.vstack([a, b]):
    p = dict(zip(names, row))
    r = ev.raw(p)
    if r is None or not r["reliable"]:
        why = "RAISE" if r is None else W.gate_reason(r)
        bad[why] = bad.get(why, 0) + 1
    else:
        vals.append((r["dS_pot_ml"], dict(p)))
print(f"  bad = {sum(bad.values())}/1024; reasons = {bad}")

print("\n=== what distinguishes bad points? (compare param distributions) ===")
if vals:
    good_arr = pd.DataFrame([v[1] for v in vals])
    print("  good points: param means")
    print(good_arr.mean().round(3).to_string())
print("\n=== scan limit_scale x x_alkalinity in the 7-dim Sobol box (others at box middle) ===")
mid = {k: float(np.mean(v)) for k, v in BOUNDS_STRESS.items()}
for ls in np.linspace(*BOUNDS_STRESS["limit_scale"], 8):
    row = []
    for ak in np.linspace(*BOUNDS_STRESS["x_alkalinity"], 6):
        p = dict(mid); p["limit_scale"] = float(ls); p["x_alkalinity"] = float(ak)
        r = ev.raw(p)
        v = "GATE" if (r is None or not r["reliable"]) else f"{r['dS_pot_ml']:.0f}"
        row.append(f"{v:>10}")
    print(f"  ls={ls:6.3f}: " + " ".join(row))
print("  x_alkalinity:", " ".join(f"{v:>10.3f}" for v in np.linspace(*BOUNDS_STRESS["x_alkalinity"], 6)))

print("\n=== NaN diagnostic: is it no_convergence at extreme limit_scale? ===")
for ls in (0.4, 0.5, 0.6, 0.8, 1.0, 1.5, 2.0, 3.0):
    for ak in (0.5, 1.0, 2.0, 3.5):
        p = dict(mid); p["limit_scale"] = ls; p["x_alkalinity"] = ak
        r = ev.raw(p)
        if r is None:
            print(f"  ls={ls} ak={ak}: RAISE")
        elif not r["reliable"]:
            print(f"  ls={ls} ak={ak}: {W.gate_reason(r)[:70]} CoC0={r['CoC0']:.6f} CoC1={r['CoC1']:.6f}")
