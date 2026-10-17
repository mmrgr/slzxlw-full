"""探针: 在细网格上取引擎的 M(phi)/CoC(phi) 曲线, 并测运行成本.

只读运行主模型, 不写回任何仓库目录, 不改变门禁.
"""
from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2] / "07_代码_AI-UWM引擎" / "aiuwm_src"
sys.path.insert(0, str(REPO / "src"))

from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = REPO / "examples" / "cawcc_r2"
CAP_MW = 1000.0
GRID = [round(i / 20, 3) for i in range(0, 19)]  # 0.00 .. 0.90 step .05


def run(project, timeseries, target):
    trial = copy.deepcopy(project)
    dc = trial["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = CAP_MW
    dc["cooling_storage_capacity_ml"] = 0.0
    dc["cooling_storage_ml"] = 0.0
    dc["initial_cooling_storage_ml"] = 0.0
    dc["water_sources"]["reclaimed"]["target_fraction"] = target
    dc["water_sources"]["potable"]["target_fraction"] = 1.0 - target
    res = FullAIUWMModel(trial, timeseries).run()
    d = res.data_center_daily
    return {
        "M": float(d["external_withdrawal_ml"].sum()),
        "potable": float(d["potable_water_ml"].sum()),
        "reclaimed": float(d["reclaimed_water_ml"].sum()),
        "phi_actual": float(d["reclaimed_water_ml"].sum()) / float(d["external_withdrawal_ml"].sum()),
        "coc": float(d["cycles_of_concentration"].mean()),
        "evap": float(d["evaporation_ml"].sum()) if "evaporation_ml" in d else np.nan,
        "wwtw_treated": float(res.component_daily.loc[res.component_daily["component_id"] == "WWTW1", "treated_ml"].sum()),
        "city_potable": float(res.area_daily["potable_delivered_ml"].sum()),
    }


def main():
    for domain in ("ha", "co"):
        project = json.loads((R2 / domain / "project.json").read_text(encoding="utf-8"))
        ts = pd.read_csv(R2 / domain / "timeseries.csv")
        rows = []
        t0 = time.time()
        for g in GRID:
            r = run(project, ts, g)
            r["f_requested"] = g
            rows.append(r)
        dt = time.time() - t0
        df = pd.DataFrame(rows)[["f_requested", "phi_actual", "M", "potable", "reclaimed", "coc", "evap", "wwtw_treated", "city_potable"]]
        print(f"===== {domain.upper()}  运行 {len(GRID)} 个情景耗时 {dt:.1f}s")
        print(df.round(1).to_string(index=False))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
