"""Probe 3: verify wp5_common against WP4 reference + calibrate Sobol size."""
from __future__ import annotations
import sys, time
from pathlib import Path
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wp5_common as W
import city_model as cm

samples, q_by, primary, banned = W.load_primary_samples()
print("authoritative samples:", list(q_by))
print("primary (COMPLETE):", primary)
print("banned:", banned)

q = q_by[W.SAMPLE_IEUA]

print("\n=== A) reproduce WP4 anchor: ha|IEUA|phi=0.6|ps=1 (WP4 dS=-7585.0884) ===")
r = W.solve_dS("ha", W.SAMPLE_IEUA, q, phi=0.6,
               pool_ml=cm.BASELINES["ha"]["P0"], gap_ml=cm.BASELINES["ha"]["gap"],
               e_total_ml=cm.BASELINES["ha"]["E_total"])
print(f"  WP5 dS={r['dS_pot_ml']:.4f}  predicted map dS-WP5 = dS_WP4 - P0 + x_ai = "
      f"{-7585.088415776312 - cm.BASELINES['ha']['P0'] + r['x_ai_ml']:.4f}")
print(f"  WP5 x_ai={r['x_ai_ml']:.4f} M0={r['M0_ml']:.4f} M1={r['M1_ml']:.4f} "
      f"C={r['C_ml']:.4f} gates={r['reliable']}")

print("\n=== B) gate survey on a stress grid (limited pool / extreme chemistry) ===")
bad = 0; tot = 0; reasons = {}
for dom in W.DOMS:
    bl = cm.BASELINES[dom]
    for samp in primary:
        for phi in (0.2, 0.4, 0.6, 0.8):
            for ps in (0.25, 0.5, 1.0, 2.0, 3.0):
                for ls in (0.3, 0.6, 1.0):
                    try:
                        rr = W.solve_dS(dom, samp, q_by[samp], phi=phi,
                                        pool_ml=bl["P0"] * ps, gap_ml=bl["gap"],
                                        e_total_ml=bl["E_total"], limit_scale=ls)
                    except Exception as e:
                        bad += 1; tot += 1
                        reasons["RAISE:" + type(e).__name__] = reasons.get("RAISE:" + type(e).__name__, 0) + 1
                        continue
                    tot += 1
                    if not rr["reliable"]:
                        bad += 1
                        k = W.gate_reason(rr) or "?"
                        reasons[k] = reasons.get(k, 0) + 1
print(f"  total={tot} unreliable={bad} ({100*bad/max(tot,1):.1f}%)")
for k, v in sorted(reasons.items(), key=lambda x: -x[1])[:12]:
    print(f"    {v:4d}  {k[:100]}")

print("\n=== C) sign range over the same grid (reliable only) ===")
vals = []
for dom in W.DOMS:
    bl = cm.BASELINES[dom]
    for samp in primary:
        for phi in (0.2, 0.4, 0.6, 0.8):
            for ps in (0.25, 0.5, 1.0, 2.0, 3.0):
                try:
                    rr = W.solve_dS(dom, samp, q_by[samp], phi=phi,
                                    pool_ml=bl["P0"] * ps, gap_ml=bl["gap"],
                                    e_total_ml=bl["E_total"])
                except Exception:
                    continue
                if rr["reliable"]:
                    vals.append(rr["dS_pot_ml"])
vals = np.array(vals)
print(f"  n={len(vals)} min={vals.min():.5g} max={vals.max():.5g} "
      f"n_neg={(vals < -W.ZERO_ABS).sum()} n_pos={(vals > W.ZERO_ABS).sum()}")

print("\n=== D) chemistry scale sweep (ha, IEUA, phi=0.6, ps=1) ===")
bl = cm.BASELINES["ha"]
for s in (0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0):
    try:
        rr = W.solve_dS("ha", W.SAMPLE_IEUA, W.q_scaled(q, {k: s for k in W.CORE}),
                        phi=0.6, pool_ml=bl["P0"], gap_ml=bl["gap"],
                        e_total_ml=bl["E_total"])
        print(f"  chem x{s:<5}: dS={rr['dS_pot_ml']:12.6g} CoC1={rr['CoC1']:.4f} "
              f"ok={rr['reliable']} {W.gate_reason(rr)[:60]}")
    except Exception as e:
        print(f"  chem x{s:<5}: RAISE {type(e).__name__}: {str(e)[:90]}")

print("\n=== E) limit_scale sweep incl. extended bounds ===")
for ls in (0.08, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0, 2.0, 4.0, 8.0):
    try:
        rr = W.solve_dS("ha", W.SAMPLE_IEUA, q, phi=0.6, pool_ml=bl["P0"],
                        gap_ml=bl["gap"], e_total_ml=bl["E_total"], limit_scale=ls)
        print(f"  ls={ls:<5}: dS={rr['dS_pot_ml']:12.6g} CoC0={rr['CoC0']:.4f} "
              f"CoC1={rr['CoC1']:.4f} ok={rr['reliable']} {W.gate_reason(rr)[:50]}")
    except Exception as e:
        print(f"  ls={ls:<5}: RAISE {type(e).__name__}: {str(e)[:80]}")

print("\n=== F) timing for one dS evaluation ===")
t0 = time.time()
for _ in range(20):
    W.solve_dS("ha", W.SAMPLE_IEUA, q, phi=0.6, pool_ml=bl["P0"],
               gap_ml=bl["gap"], e_total_ml=bl["E_total"])
print(f"  20 evals in {time.time()-t0:.3f}s => {(time.time()-t0)/20*1000:.1f} ms/eval")

print("\n=== G) timing with fresh cache vs shared cache ===")
q2 = q_by[W.SAMPLE_LADWP]
t0 = time.time()
cache = {}
for i in range(5):
    W.solve_dS("ha", W.SAMPLE_IEUA, q, phi=0.6, pool_ml=bl["P0"], gap_ml=bl["gap"],
               e_total_ml=bl["E_total"], cache=cache)
print(f"  shared cache 5 evals: {time.time()-t0:.3f}s")

print("\n=== H) does chemistry x20 produce distinct results across samples (cache key check)? ===")
for s in (0.5, 1.0, 2.0, 4.0):
    rr = W.solve_dS("ha", W.SAMPLE_IEUA, W.q_scaled(q, {k: s for k in W.CORE}),
                    phi=0.6, pool_ml=bl["P0"], gap_ml=bl["gap"], e_total_ml=bl["E_total"])
    rr2 = W.solve_dS("ha", W.SAMPLE_LADWP, W.q_scaled(q_by[W.SAMPLE_LADWP], {k: s for k in W.CORE}),
                     phi=0.6, pool_ml=bl["P0"], gap_ml=bl["gap"], e_total_ml=bl["E_total"])
    print(f"  x{s}: IEUA CoC1={rr['CoC1']:.5f} dS={rr['dS_pot_ml']:.5g} | "
          f"LADWP CoC1={rr2['CoC1']:.5f} dS={rr2['dS_pot_ml']:.5g}")
