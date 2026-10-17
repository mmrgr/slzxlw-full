"""Probe 4: reconcile WP5 pool-convention dS vs WP4 fixed-pool dS."""
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
q = q_by[W.SAMPLE_IEUA]
bl = cm.BASELINES["ha"]

print("WP4 anchor ha|IEUA|ps=1: dS_WP4 = -7585.088415776312")
for phi in (0.2, 0.4, 0.6, 0.8):
    r = W.solve_dS("ha", W.SAMPLE_IEUA, q, phi=phi, pool_ml=bl["P0"],
                   gap_ml=bl["gap"], e_total_ml=bl["E_total"])
    print(f"  phi={phi}: WP5 dS={r['dS_pot_ml']:12.5f}  S_city_B2={r['S_city_B2_ml']:12.5f} "
          f"S_city_B1={r['S_city_B1_ml']:12.5f}  x_ai={r['x_ai_ml']:.4f} M0={r['M0_ml']:.4f}")

d = np.loadtxt if False else None
import pandas as pd
wp4 = pd.read_csv(HERE.parent / "A33_WP4_组成重构" / "wp4_results.csv", encoding="utf-8-sig")
sub = wp4[(wp4.domain == "ha") & (wp4["sample"] == W.SAMPLE_IEUA) & (wp4.pool_scale == 1.0)]
print("\nWP4 rows (ha|IEUA|ps=1):")
print(sub[["phi", "M0_ml", "M1_ml", "inc_B1_ml", "inc_B2_ml", "x_ai_ml",
           "C_ml", "F_ml", "dS_pot_ml", "reliable"]].to_string(index=False))
print("\nalgebraic relation check (WP5 - WP4 should equal -P0 + x_ai):")
for _, row in sub.iterrows():
    r = W.solve_dS("ha", W.SAMPLE_IEUA, q, phi=float(row["phi"]), pool_ml=bl["P0"],
                   gap_ml=bl["gap"], e_total_ml=bl["E_total"])
    lhs = r["dS_pot_ml"] - float(row["dS_pot_ml"])
    rhs = -bl["P0"] + r["x_ai_ml"]
    print(f"  phi={row['phi']}: LHS={lhs:12.5f} RHS={rhs:12.5f} diff={lhs-rhs:.3e} "
          f"| WP4 x_ai={row['x_ai_ml']:.5f} WP5 x_ai={r['x_ai_ml']:.5f} "
          f"WP4 M0={row['M0_ml']:.5f} WP5 M0={r['M0_ml']:.5f}")

print("\n=== co domain same check (P0_co=22413.98) ===")
sub = wp4[(wp4.domain == "co") & (wp4["sample"] == W.SAMPLE_IEUA) & (wp4.pool_scale == 1.0)]
blc = cm.BASELINES["co"]
for _, row in sub.iterrows():
    r = W.solve_dS("co", W.SAMPLE_IEUA, q, phi=float(row["phi"]), pool_ml=blc["P0"],
                   gap_ml=blc["gap"], e_total_ml=blc["E_total"])
    lhs = r["dS_pot_ml"] - float(row["dS_pot_ml"]); rhs = -blc["P0"] + r["x_ai_ml"]
    print(f"  phi={row['phi']}: LHS={lhs:12.5f} RHS={rhs:12.5f} diff={lhs-rhs:.3e}")

print("\n=== why is ls=0.3 jumpy? CoC floor saturating ===")
for ls in (0.25, 0.28, 0.30, 0.32, 0.35, 0.4):
    r = W.solve_dS("ha", W.SAMPLE_IEUA, q, phi=0.6, pool_ml=bl["P0"],
                   gap_ml=bl["gap"], e_total_ml=bl["E_total"], limit_scale=ls)
    print(f"  ls={ls}: dS={r['dS_pot_ml']:12.5f} CoC0={r['CoC0']:.6f} CoC1={r['CoC1']:.6f} "
          f"reliable={r['reliable']} {W.gate_reason(r)[:60]}")
