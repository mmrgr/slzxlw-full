"""Probe 6: surplus states, q sign reversal, and WP5 pool-convention vs fixed-pool."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wp5_common as W
import city_model as cm

_, q_by, primary, _ = W.load_primary_samples()
bl = cm.BASELINES["ha"]
elig = bl["P0"] + bl["gap"]

print("=== surplus regime: pool > elig (pool_scale>1.38 for ha) ===")
print(f"elig_ha = P0+gap = {elig:.2f}; P0 = {bl['P0']:.2f}")
print(f"{'pool_scale':>11} {'pool':>10} {'state':>9} {'C':>10} {'F':>11} {'dS':>11} {'push':>8}")
for ps in (0.5, 1.0, 1.38, 1.5, 2.0, 3.0, 4.0):
    pool = bl["P0"] * ps
    state = "surplus" if pool > elig else ("binding" if abs(pool - elig) < 1e-6 else "shortage")
    r = W.solve_dS("ha", W.SAMPLE_IEUA, q_by[W.SAMPLE_IEUA], phi=0.6, pool_ml=pool,
                   gap_ml=bl["gap"], e_total_ml=bl["E_total"])
    push = r["displaced_raw_ml"] - r["C_ml"]
    print(f"{ps:>11.2f} {pool:>10.1f} {state:>9} {r['C_ml']:>10.4f} {r['F_ml']:>11.4f} "
          f"{r['dS_pot_ml']:>11.4f} {push:>8.4f}")

print("\n=== surplus + large pool: does dS become positive? ===")
for ps in (2.0, 3.0, 5.0, 8.0, 12.0):
    for gap_scale in (0.2, 1.0, 3.0):
        pool = bl["P0"] * ps
        gap = bl["gap"] * gap_scale
        state = "surplus" if pool > (bl["P0"] + gap) else "shortage"
        r = W.solve_dS("ha", W.SAMPLE_IEUA, q_by[W.SAMPLE_IEUA], phi=0.6, pool_ml=pool,
                       gap_ml=gap, e_total_ml=bl["E_total"])
        print(f"  ps={ps:<5} gs={gap_scale:<4} {state:>8}: C={r['C_ml']:10.4f} "
              f"F={r['F_ml']:10.4f} dS={r['dS_pot_ml']:11.4f} "
              f"ok={r['reliable']} {W.gate_reason(r)[:30]}")

print("\n=== q sign convention check ===")
print("q = (CoC1-CoC0)/(CoC1*(CoC0-1)); q>0 <=> CoC1>CoC0 <=> 再生水更干净")
for samp in primary:
    for ls in (1.0, 2.0):
        r = W.solve_dS("ha", samp, q_by[samp], phi=0.6, pool_ml=bl["P0"],
                       gap_ml=bl["gap"], e_total_ml=bl["E_total"], limit_scale=ls)
        print(f"  {samp[:28]:<30} ls={ls}: CoC0={r['CoC0']:.4f} CoC1={r['CoC1']:.4f} "
              f"q={r['q']:+.5f} dS={r['dS_pot_ml']:11.4f}")

print("\n=== heatwave temperature sensitivity of dS (annual basis) ===")
for dt in (0, 2, 4, 6, 8):
    drv = dict(bl["drivers_rep"]); drv["temperature_c"] = float(drv["temperature_c"]) + dt
    r = W.solve_dS("ha", W.SAMPLE_IEUA, q_by[W.SAMPLE_IEUA], phi=0.6, pool_ml=bl["P0"],
                   gap_ml=bl["gap"], e_total_ml=bl["E_total"], drivers_rep=drv)
    print(f"  dT=+{dt}: dS={r['dS_pot_ml']:11.4f} CoC0={r['CoC0']:.4f} CoC1={r['CoC1']:.4f}")

print("\n=== limit_scale sign-flip threshold scan (ha, IEUA, phi=0.6) ===")
prev = None
for ls in np.arange(0.30, 1.01, 0.02):
    r = W.solve_dS("ha", W.SAMPLE_IEUA, q_by[W.SAMPLE_IEUA], phi=0.6, pool_ml=bl["P0"],
                   gap_ml=bl["gap"], e_total_ml=bl["E_total"], limit_scale=float(ls))
    s = W.sign_of(r["dS_pot_ml"])
    if prev is not None and s != prev and r["reliable"]:
        print(f"  SIGN FLIP at limit_scale={ls:.3f}: dS={r['dS_pot_ml']:.4f} "
              f"CoC0={r['CoC0']:.4f} CoC1={r['CoC1']:.4f} q={r['q']:+.5f}")
    prev = s
print("  (scan done)")

print("\n=== chemistry scale sign-flip threshold (ha, IEUA, phi=0.6) ===")
prev = None
for s in np.arange(1.0, 6.01, 0.1):
    r = W.solve_dS("ha", W.SAMPLE_IEUA, W.q_scaled(q_by[W.SAMPLE_IEUA], {k: float(s) for k in W.CORE}),
                   phi=0.6, pool_ml=bl["P0"], gap_ml=bl["gap"], e_total_ml=bl["E_total"])
    sg = W.sign_of(r["dS_pot_ml"])
    if prev is not None and sg != prev and r["reliable"]:
        print(f"  SIGN FLIP at chem x{s:.2f}: dS={r['dS_pot_ml']:.4f} CoC1={r['CoC1']:.4f} q={r['q']:+.5f}")
    prev = sg
print("  (scan done)")
