"""Probe 8: locate exact NaN source in the Sobol path."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wp5_common as W
import city_model as cm
from wp5_morris_sobol import Evaluator, BOUNDS_STRESS

_, q_by, primary, _ = W.load_primary_samples()
names = ["limit_scale", "x_alkalinity", "phi", "gap_scale", "pool_scale", "e_scale", "dp_scale"]
bounds = {k: BOUNDS_STRESS[k] for k in names}
ev = Evaluator("ha", W.SAMPLE_IEUA, q_by[W.SAMPLE_IEUA], cm.BASELINES["ha"])

rng = np.random.default_rng(20261016)
a = rng.random((512, 7)); b = rng.random((512, 7))
low = np.array([bounds[n][0] for n in names])
span = np.array([bounds[n][1] - bounds[n][0] for n in names])
a, b = low + a * span, low + b * span
d = dict(zip(names, a[0]))
print("first row:", {k: round(float(v), 4) for k, v in d.items()})
r = ev.raw(d)
print("reliable:", None if r is None else r["reliable"],
      "reason:", "" if r is None else W.gate_reason(r))
print("n=", ev.n, "n_nan=", ev.n_nan, "n_raise=", ev.n_raise, "reasons=", ev.reasons)

print("\n--- now run the engine with a NON-NaN-emitting probe evaluator to isolate ---")
from aiuwm.sensitivity import sobol_sensitivity


def probe(p):
    return 1.0


s = sobol_sensitivity(probe, bounds, samples=32, seed=1)
print("constant evaluator:", s["S1"].tolist(), s["ST"].tolist())

ev2 = Evaluator("ha", W.SAMPLE_IEUA, q_by[W.SAMPLE_IEUA], cm.BASELINES["ha"])
s2 = sobol_sensitivity(ev2, bounds, samples=32, seed=1)
print("real evaluator samples=32:", s2[["parameter", "S1", "ST"]].round(5).to_dict("records"))
print("ev2 tallies: n=", ev2.n, "n_nan=", ev2.n_nan, "reasons=", ev2.reasons)

print("\n--- check: does the engine's `a` matrix get clamped? It uses low+u*span ---")
print("a range per param:", [(names[i], round(float(a[:, i].min()), 3),
                              round(float(a[:, i].max()), 3)) for i in range(7)])
