"""Probe: dS_pot + cost. NOT a deliverable."""
from __future__ import annotations
import sys, time, json
from pathlib import Path
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
A10 = HERE.parent / "A10_敏感性与边界"
sys.path.insert(0, str(A10))
import city_model as cm
from aiuwm.data_center import calculate_data_center_plan

PANEL = "B_full"
IEUA = "IEUA RP-1 (2025, tertiary)"
LADWP = "LADWP AWPF (2012, RO product)"
samples = cm.load_samples()

def q_of(name, scale=1.0, override=None):
    row = samples[samples["source"] == name].iloc[0]
    q = {sp: float(row[sp]) for sp in cm.PANELS[PANEL] if sp in row.index and np.isfinite(row.get(sp, np.nan))}
    if override:
        q.update(override)
    return {k: v * scale for k, v in q.items()}


def solve(dom, name, q, phi, ps, coc_design=5.0, limit_scale=1.0, e_scale=1.0,
          gap_scale=1.0, t_scale=1.0, ai_target=None, pool_scale=None):
    bl = cm.BASELINES[dom]
    drv = dict(bl["drivers_rep"])
    drv["temperature_c"] = float(drv["temperature_c"]) * t_scale
    bl = dict(bl); bl["drivers_rep"] = drv
    pool = bl["P0"] * float(ps)
    gap = bl["gap"] * float(gap_scale)
    dp = 0.0
    cache = {}
    m0 = cm.m0_of(bl, PANEL, q, coc_design=coc_design, limit_scale=limit_scale, e_scale=e_scale)
    r2 = cm.solve_city(bl, PANEL, name, q, m0=m0, pool=pool, gap=gap, dp=dp,
                       ai_target=float(phi), coc_design=coc_design,
                       limit_scale=limit_scale, e_scale=e_scale, cache=cache)
    r1 = cm.solve_city(bl, PANEL, name, q, m0=m0, pool=pool, gap=gap, dp=dp,
                       ai_target=0.0, coc_design=coc_design,
                       limit_scale=limit_scale, e_scale=e_scale, cache=cache)
    M0, M1 = r1["M_ml"], r2["M_ml"]
    C = max(0.0, r2["inc_reclaimed_ml"] - r1["inc_reclaimed_ml"])
    x_ai = r2["x_ai_ml"]
    dS = C - ((M0 - M1) + x_ai)
    return dict(dS=dS, M0=M0, M1=M1, C=C, x_ai=x_ai, CoC0=r1["CoC_ai"], CoC1=r2["CoC_ai"],
                st2=r2["status"], st1=r1["status"], roots1=r1["roots"], roots2=r2["roots"],
                res2=r2["closure_residual_ml"], res1=r1["closure_residual_ml"])


t0 = time.time()
q = q_of(IEUA)
for phi in (0.0, 0.3, 0.6, 0.9):
    o = solve("ha", IEUA, q, phi, 1.0)
    print(f"phi={phi}: dS={o['dS']:.6g} CoC0={o['CoC0']:.4f} CoC1={o['CoC1']:.4f} "
          f"x_ai={o['x_ai']:.4g} M0={o['M0']:.6g} M1={o['M1']:.6g} st2={o['st2']} st1={o['st1']}")
print(f"[t] 4 evals (8 solves) in {time.time()-t0:.2f}s")

print("\n--- limit_scale sweep (ha, IEUA, phi=0.6, ps=1) ---")
for ls in (0.3, 0.5, 0.75, 1.0, 1.5, 2.5):
    try:
        o = solve("ha", IEUA, q, 0.6, 1.0, limit_scale=ls)
        print(f"ls={ls}: dS={o['dS']:.6g} CoC0={o['CoC0']:.4f} CoC1={o['CoC1']:.4f} st2={o['st2']}")
    except Exception as e:
        print(f"ls={ls}: RAISE {type(e).__name__}: {e}")

print("\n--- coc_design sweep ---")
for cd in (2.0, 3.0, 5.0, 8.0):
    try:
        o = solve("ha", IEUA, q, 0.6, 1.0, coc_design=cd)
        print(f"cd={cd}: dS={o['dS']:.6g} CoC0={o['CoC0']:.4f} CoC1={o['CoC1']:.4f} st2={o['st2']}")
    except Exception as e:
        print(f"cd={cd}: RAISE {type(e).__name__}: {e}")

print("\n--- e_scale sweep ---")
for es in (0.5, 0.75, 1.0, 1.25, 1.5, 2.0):
    o = solve("ha", IEUA, q, 0.6, 1.0, e_scale=es)
    print(f"es={es}: dS={o['dS']:.6g} CoC0={o['CoC0']:.4f} CoC1={o['CoC1']:.4f}")

print("\n--- gap_scale sweep ---")
for gs in (0.5, 1.0, 2.0, 4.0):
    o = solve("ha", IEUA, q, 0.6, 1.0, gap_scale=gs)
    print(f"gs={gs}: dS={o['dS']:.6g}")

print("\n--- t_scale sweep ---")
for ts in (0.8, 1.0, 1.2, 1.5, 1.8):
    o = solve("ha", IEUA, q, 0.6, 1.0, t_scale=ts)
    print(f"ts={ts}: dS={o['dS']:.6g} CoC0={o['CoC0']:.4f} CoC1={o['CoC1']:.4f}")

print("\n--- q chem scale sweep ---")
for qs in (0.25, 0.5, 1.0, 2.0, 4.0, 8.0):
    o = solve("ha", IEUA, q_of(IEUA, scale=qs), 0.6, 1.0)
    print(f"qs={qs}: dS={o['dS']:.6g} CoC1={o['CoC1']:.4f} st2={o['st2']}")

print("\n--- pools ---")
for ps in (0.5, 1.0, 2.0, 3.0):
    o = solve("ha", IEUA, q, 0.6, ps)
    print(f"ps={ps}: dS={o['dS']:.6g}")

print("\n--- LADWP ---")
for ps in (1.0, 2.0):
    o = solve("ha", LADWP, q_of(LADWP), 0.6, ps)
    print(f"ps={ps}: dS={o['dS']:.6g} CoC1={o['CoC1']:.4f} st2={o['st2']}")

print("\n--- co domain ---")
o = solve("co", IEUA, q, 0.6, 1.0)
print(f"co: dS={o['dS']:.6g}")

print(f"\n[t] total {time.time()-t0:.2f}s")
