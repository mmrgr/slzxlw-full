"""Probe 2: heatwave / drought mechanisms + gate behaviour."""
from __future__ import annotations
import sys, time
from pathlib import Path
import numpy as np, pandas as pd
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
import importlib.util as ilu
spec = ilu.spec_from_file_location("wp", HERE / "_probe.py")
# avoid re-running probe main; just re-declare helpers
A10 = HERE.parent / "A10_敏感性与边界"
sys.path.insert(0, str(A10))
import city_model as cm
from aiuwm.data_center import calculate_data_center_plan
from aiuwm.reclaimed_allocation import solve_joint_quality_allocation, JointQualityRequest

PANEL = "B_full"
IEUA = "IEUA RP-1 (2025, tertiary)"
samples = cm.load_samples()


def q_of(name):
    row = samples[samples["source"] == name].iloc[0]
    return {sp: float(row[sp]) for sp in cm.PANELS[PANEL]
            if sp in row.index and np.isfinite(row.get(sp, np.nan))}


q = q_of(IEUA)

# ---- engine-level: what does temperature do to evaporation / PUE? ----
print("=== engine: T/humidity -> evaporation, PUE, wet_fraction (ha, B_full, no reclaimed) ===")
comp = cm.base_comp(cm.BASELINES["ha"], PANEL, 0.0)
print(f"comp heat_basis={comp['cooling'].get('heat_basis')} "
      f"tech={comp['cooling'].get('technology')} "
      f"pue_mode={comp.get('pue_mode')} tempco={comp.get('temperature_coefficient')}")
for T, RH in [(10, 60), (20, 50), (30, 40), (38, 30), (43, 20), (45, 15)]:
    drv = dict(cm.BASELINES["ha"]["drivers_rep"])
    drv["temperature_c"] = float(T); drv["relative_humidity"] = float(RH)
    p = calculate_data_center_plan(comp, cm.BASELINES["ha"]["date_rep"], drv)
    print(f"T={T:>4} RH={RH:>3}: pue={p.pue:.4f} wb={p.wet_bulb_temperature_c:.2f} "
          f"wetf={p.wet_cooling_fraction:.3f} evap={p.evaporation_ml:.1f} ext={p.external_makeup_ml:.1f}")

# ---- drought: reduce reclaimed availability at fixed everything else ----
print("\n=== drought: reclaimed availability vs outcome (ha, phi=0.6, ps=1) ===")
bl0 = cm.BASELINES["ha"]
pool = bl0["P0"] * 1.0
gap = bl0["gap"]
m0 = cm.m0_of(bl0, PANEL, q)
for frac in (1.0, 0.75, 0.5, 0.35, 0.25, 0.15, 0.05):
    cache = {}
    for phi in (0.6, 0.0):
        try:
            r = cm.solve_city(bl0, PANEL, IEUA, q, m0=m0, pool=pool * frac, gap=gap,
                              dp=0.0, ai_target=phi, cache=cache)
            if phi == 0.6:
                r2 = r
            else:
                r1 = r
        except Exception as e:
            print(f"frac={frac} phi={phi}: RAISE {type(e).__name__}: {e}")
            r1 = r2 = None
            break
    if r1 is None:
        continue
    M0, M1 = r1["M_ml"], r2["M_ml"]
    C = max(0.0, r2["inc_reclaimed_ml"] - r1["inc_reclaimed_ml"])
    x = r2["x_ai_ml"]
    dS = C - ((M0 - M1) + x)
    print(f"frac={frac:<5} dS={dS:12.6g} x_ai={x:9.5g} M0={M0:9.5g} M1={M1:9.5g} "
          f"C={C:8.5g} inc_B1={r1['inc_reclaimed_ml']:9.5g} st1={r1['status']} st2={r2['status']}")

# ---- heatwave via e_scale and t_scale with gate tracking ----
print("\n=== heatwave: e_scale with gates (ha, IEUA, phi=0.6, ps=1) ===")
for es in (1.0, 1.2, 1.4, 1.6, 2.0, 3.0, 5.0):
    cache = {}
    bl = dict(bl0)
    try:
        m0e = cm.m0_of(bl, PANEL, q, e_scale=es)
        out = []
        for phi in (0.6, 0.0):
            r = cm.solve_city(bl, PANEL, IEUA, q, m0=m0e, pool=pool, gap=gap, dp=0.0,
                              ai_target=phi, e_scale=es, cache=cache)
            out.append(r)
        r2, r1 = out
        M0, M1 = r1["M_ml"], r2["M_ml"]
        C = max(0.0, r2["inc_reclaimed_ml"] - r1["inc_reclaimed_ml"])
        dS = C - ((M0 - M1) + r2["x_ai_ml"])
        sens = dS / es
        print(f"es={es:<4} dS={dS:12.6g} dS/es={sens:11.6g} CoC0={r1['CoC_ai']:.4f} "
              f"CoC1={r2['CoC_ai']:.4f} st1={r1['status']} st2={r2['status']}")
    except Exception as e:
        print(f"es={es}: RAISE {type(e).__name__}: {e}")

print("\n=== heatwave: t_scale with gates ===")
for ts in (1.0, 1.1, 1.2, 1.3, 1.5, 1.8):
    bl = dict(bl0); drv = dict(bl0["drivers_rep"])
    drv["temperature_c"] = float(drv["temperature_c"]) * ts
    bl["drivers_rep"] = drv
    cache = {}
    out = []
    for phi in (0.6, 0.0):
        r = cm.solve_city(bl, PANEL, IEUA, q, m0=cm.m0_of(bl, PANEL, q), pool=pool,
                          gap=gap, dp=0.0, ai_target=phi, cache=cache)
        out.append(r)
    r2, r1 = out
    M0, M1 = r1["M_ml"], r2["M_ml"]
    C = max(0.0, r2["inc_reclaimed_ml"] - r1["inc_reclaimed_ml"])
    dS = C - ((M0 - M1) + r2["x_ai_ml"])
    print(f"ts={ts:<4} dS={dS:12.6g} CoC0={r1['CoC_ai']:.4f} CoC1={r2['CoC_ai']:.4f} "
          f"M0={M0:.6g} st2={r2['status']}")

# ---- real observed heatwave/drought windows in the timeseries ----
print("\n=== observed extremes in cawcc_r2 timeseries ===")
for dom in ("ha", "co"):
    ts = pd.read_csv(cm.R2 / dom / "timeseries.csv", parse_dates=["date"])
    print(f"--- {dom}: n={len(ts)} {ts.date.min().date()}..{ts.date.max().date()}")
    print(f"    T: median={ts.temperature_c.median():.2f} p95={ts.temperature_c.quantile(.95):.2f} "
          f"max={ts.temperature_c.max():.2f}")
    print(f"    RH: median={ts.relative_humidity_pct.median():.1f}")
    print(f"    reservoir_inflow_ml: min={ts.reservoir_inflow_ml.min():.2f} "
          f"p05={ts.reservoir_inflow_ml.quantile(.05):.2f} median={ts.reservoir_inflow_ml.median():.2f} "
          f"max={ts.reservoir_inflow_ml.max():.2f}")
    print(f"    rainfall: min={ts.rainfall_mm.min():.2f} max={ts.rainfall_mm.max():.2f} "
          f"n_dry={(ts.rainfall_mm <= 0.1).sum()}")
    idx = ts.temperature_c.idxmax()
    print(f"    hottest day: {ts.loc[idx,'date'].date()} T={ts.loc[idx,'temperature_c']:.2f} "
          f"RH={ts.loc[idx,'relative_humidity_pct']:.1f} inflow={ts.loc[idx,'reservoir_inflow_ml']:.2f}")
    # 37-day rolling mean
    roll = ts.temperature_c.rolling(37).mean()
    j = roll.idxmax()
    print(f"    hottest 37d window ending {ts.loc[j,'date'].date()} meanT={roll[j]:.2f}; "
          f"T scale vs all-mean = {roll[j]/ts.temperature_c.mean():.4f}")
    rin = ts.reservoir_inflow_ml.rolling(37).mean()
    k = rin.idxmin()
    print(f"    driest 37d window ending {ts.loc[k,'date'].date()} mean inflow={rin[k]:.2f}; "
          f"ratio to median-of-rolling = {rin[k]/rin.median():.4f}")
    print(f"    reservoir inflow annual totals: "
          f"{ts.groupby(ts.date.dt.year).reservoir_inflow_ml.sum().round(1).to_dict()}")
