"""Probe 5: F-convention audit between A13 and WP4/WP2, and F variants."""
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

print("F variants on ha|IEUA (pool=P0, gap=gap0):")
print(f"{'phi':>5} {'M0':>11} {'M1':>11} {'x_ai':>10} {'F_WP4':>11} {'F_A13':>11} "
      f"{'diff':>10} {'C':>8} {'dS_WP4':>11} {'dS_A13':>11}")
for phi in (0.2, 0.4, 0.6, 0.8):
    r = W.solve_dS("ha", W.SAMPLE_IEUA, q, phi=phi, pool_ml=bl["P0"],
                   gap_ml=bl["gap"], e_total_ml=bl["E_total"])
    M0, M1 = r["M0_ml"], r["M1_ml"]
    x = r["x_ai_ml"]; C = r["C_ml"]
    phi_eff = x / M1 if M1 > 1e-12 else 0.0
    F_wp4 = (M0 - M1) + x
    F_a13 = M0 - (1.0 - phi_eff) * M1
    print(f"{phi:>5} {M0:>11.4f} {M1:>11.4f} {x:>10.4f} {F_wp4:>11.4f} {F_a13:>11.4f} "
          f"{F_wp4-F_a13:>10.4f} {C:>8.3f} {C-F_wp4:>11.4f} {C-F_a13:>11.4f}")

print("\n>>> A13's F includes the reclaimed water 'phi_eff*M1' as offset; WP4's F does not.")
print(">>> F_WP4 - F_A13 = phi_eff*M1 - x_ai. Since x_ai = phi_eff*M1 in B2 by construction,")
print(">>> the two agree EXACTLY when the AI receives its full target fraction.")
for phi in (0.2, 0.4, 0.6, 0.8):
    r = W.solve_dS("ha", W.SAMPLE_IEUA, q, phi=phi, pool_ml=bl["P0"],
                   gap_ml=bl["gap"], e_total_ml=bl["E_total"])
    phi_eff = r["x_ai_ml"] / r["M1_ml"] if r["M1_ml"] > 1e-12 else 0.0
    print(f"  phi={phi}: x_ai={r['x_ai_ml']:.4f} phi_eff*M1={phi_eff*r['M1_ml']:.4f} "
          f"diff={r['x_ai_ml']-phi_eff*r['M1_ml']:.3e}  phi_eff={phi_eff:.6f} target={phi}")

print("\n=== where they DIVERGE: constrained pool (ps<1) ===")
for ps in (0.1, 0.25, 0.5, 1.0):
    pool = bl["P0"] * ps
    for phi in (0.6,):
        try:
            r = W.solve_dS("ha", W.SAMPLE_IEUA, q, phi=phi, pool_ml=pool,
                           gap_ml=bl["gap"], e_total_ml=bl["E_total"])
        except Exception as e:
            print(f"  ps={ps}: RAISE {e}"); continue
        if not r["reliable"]:
            print(f"  ps={ps}: UNRELIABLE {W.gate_reason(r)}"); continue
        M0, M1, x = r["M0_ml"], r["M1_ml"], r["x_ai_ml"]
        phi_eff = x / M1 if M1 > 1e-12 else 0.0
        F_wp4 = (M0 - M1) + x
        F_a13 = M0 - (1.0 - phi_eff) * M1
        print(f"  ps={ps}: M0={M0:.4f} M1={M1:.4f} x_ai={x:.4f} phi_eff={phi_eff:.4f} "
              f"F_WP4={F_wp4:.4f} F_A13={F_a13:.4f} diff={F_wp4-F_a13:.4f} "
              f"dS_WP4={r['C_ml']-F_wp4:.4f} dS_A13={r['C_ml']-F_a13:.4f}")
