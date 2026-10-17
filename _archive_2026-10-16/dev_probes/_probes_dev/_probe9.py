"""Probe 9: verify the KeyError fix and Sobol now produces finite indices."""
from __future__ import annotations
import sys, time
from pathlib import Path
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wp5_common as W
import city_model as cm
from wp5_morris_sobol import Evaluator, BOUNDS_STRESS, sobol_guarded

_, q_by, primary, _ = W.load_primary_samples()

names = ["limit_scale", "x_alkalinity", "phi", "gap_scale", "pool_scale", "e_scale", "dp_scale"]
bounds = {k: BOUNDS_STRESS[k] for k in names}

print("=== full 12-dim Morris box, verify no KeyError ===")
ev = Evaluator("ha", W.SAMPLE_IEUA, q_by[W.SAMPLE_IEUA], cm.BASELINES["ha"])
p_full = {k: float(np.mean(v)) for k, v in BOUNDS_STRESS.items()}
r = ev.raw(p_full)
print("  full box point reliable:", None if r is None else r["reliable"])
r = ev.raw({k: BOUNDS_STRESS[k][0] for k in BOUNDS_STRESS})
print("  low corner reliable:", None if r is None else r["reliable"])
r = ev.raw({k: BOUNDS_STRESS[k][1] for k in BOUNDS_STRESS})
print("  high corner reliable:", None if r is None else r["reliable"], W.gate_reason(r) if r else "")
print("  tallies:", ev.summary())

print("\n=== Sobol subset (7 dims) now works? ===")
for n_samples in (64, 256):
    ev2 = Evaluator("ha", W.SAMPLE_IEUA, q_by[W.SAMPLE_IEUA], cm.BASELINES["ha"])
    t0 = time.time()
    s, sd = sobol_guarded(ev2, bounds, samples=n_samples, seed=20261016)
    dt = time.time() - t0
    print(f"  samples={n_samples}: {dt:.1f}s  verdict={sd['verdict'][:60]}")
    print(f"    nan={sd['n_nan']}/{sd['n_design_rows']}  gatefail={sd['n_gate_failures_during_design']}"
          f"  raises={sd['n_engine_raises_during_design']}")
    print(f"    {s[['parameter','S1','ST']].round(5).to_dict('records')}")

print("\n=== sobol_guarded must RAISE on a code defect, not swallow it ===")


class BrokenEvaluator:
    n_nan = 0
    n_raise = 0
    reasons = {}

    def __call__(self, p):
        raise KeyError("boom")


try:
    sobol_guarded(BrokenEvaluator(), bounds, samples=16, seed=1)
    print("  ✗ FAIL: KeyError was swallowed")
except KeyError as e:
    print(f"  ✓ PASS: KeyError propagated ({e}) -> code defect cannot masquerade as gate failure")
