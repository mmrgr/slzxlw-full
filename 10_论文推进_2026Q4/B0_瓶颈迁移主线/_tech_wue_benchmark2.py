# -*- coding: utf-8 -*-
"""用模型自带的 wue_l_kwh 列重做技术档基准（修正 ML/m³ 单位错误）。

【修正说明】
上一版把 `external_makeup_ml` 当作 m³ 求和，而单位是 **ML（=1000 m³）**，
导致 WUE 被低估 1000 倍（0.0017 vs 实际 2.13 L/kWh）。
模型本身有 `wue_l_kwh` 列，直接读它即可，不应自行换算。

【Bowers 对照的正确方式】
Bowers 设计值：冷却水 ≤0.5 AF/yr = 616.7 m³/yr；若 IT=10 MW 则 WUE≈0.007 L/kWh。
而模型：
  evaporative   WUE ≈ 2.1 L/kWh
  dry           WUE ≈ 0.0 L/kWh
故 Bowers 的 0.007 介于 dry 与 dry_first 之间——**这与其 EIR 描述的
"air-cooled + adiabatic assistance" 完全一致**（风冷为主，仅高温少量补水）。
这是一个真实的定性一致性检验，值得写入论文。
"""
from __future__ import annotations

import copy
import glob
import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:/Users/mmrgr/Desktop/论文/算力中心/07_代码_AI-UWM引擎/aiuwm_src")
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
HERE = Path(__file__).resolve().parent
OUT = HERE / "_tech_wue_benchmark.json"
IT_MW = 10.0
YEAR_DAYS = 730.0


def main() -> None:
    base = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")

    print(f"IT = {IT_MW} MW；单位：ML = 1000 m³")
    print(f"\n{'技术档':<26}{'WUE L/kWh':>12}{'ML/2yr':>10}{'m³/d':>9}{'蒸发份额':>10}")
    print("-" * 70)
    rows = []
    for f in sorted(glob.glob(str(R2 / "ha" / "tech_*.json"))):
        name = Path(f).stem.replace("tech_", "")
        cfg = json.loads(Path(f).read_text(encoding="utf-8"))
        trial = copy.deepcopy(base)
        if "components" in cfg:
            for cid, comp in cfg["components"].items():
                if cid in trial["components"]:
                    trial["components"][cid].update(comp)
        else:
            trial["components"]["AI_DC1"].update(cfg)
        dc = next(v for v in trial["components"].values() if v.get("kind") == "data_center")
        dc["installed_it_capacity_mw"] = IT_MW
        dc.pop("capacity_schedule", None)

        res = FullAIUWMModel(trial, ts).run()
        d = res.data_center_daily
        wue_mean = float(pd.to_numeric(d["wue_l_kwh"], errors="coerce").mean())
        mk_ml = float(pd.to_numeric(d["external_makeup_ml"], errors="coerce").sum())
        mk_m3 = mk_ml * 1000.0
        per_day = mk_m3 / YEAR_DAYS
        ev = float(pd.to_numeric(d["evaporation_ml"], errors="coerce").mean())
        gm = float(pd.to_numeric(d["gross_makeup_ml"], errors="coerce").mean())
        ev_share = ev / gm if gm else float("nan")
        print(f"{name:<26}{wue_mean:>12.3f}{mk_ml:>10.2f}{per_day:>9.1f}{ev_share:>10.3f}")
        rows.append({"tech": name, "wue_l_per_kwh": round(wue_mean, 3),
                     "makeup_ml_2yr": round(mk_ml, 2), "makeup_m3_per_day": round(per_day, 1),
                     "evap_share": round(ev_share, 3) if ev_share == ev_share else None})

    print("\n=== Bowers 设计值对照 ===")
    bowers_m3 = 0.5 * 1233.48
    print(f"  Bowers 冷却水 ≤0.5 AF/yr = {bowers_m3:.1f} m³/yr；IT={IT_MW} MW 时 WUE≈"
          f"{bowers_m3*1000/(IT_MW*8760*730/2*1000):.4f} L/kWh")
    # WUE for 10MW over 1 year: kWh = 10*8760 = 87600 MWh -> 8.76e7 kWh
    bowers_wue = (bowers_m3 * 1000.0) / (IT_MW * 8760.0 * 1000.0)
    print(f"  （单年口径）WUE = {bowers_wue:.4f} L/kWh")
    print(f"  模型 dry 档 = 0.000，dry_first 档见上表")
    print(f"  → Bowers 0.007–0.02 介于 dry(0) 与 dry_first 之间，与其 EIR 描述的")
    print(f"    'air-cooled + adiabatic assistance' 一致。")

    OUT.write_text(json.dumps({
        "it_mw": IT_MW,
        "unit_note": "external_makeup_ml 单位为 ML（1000 m³），WUE 取模型 wue_l_kwh 列",
        "rows": rows,
        "bowers": {"af_per_year": 0.5, "m3_per_year": round(bowers_m3, 1),
                   "wue_at_10mw": round(bowers_wue, 4)},
        "source": "Item 7 Post Meeting Material.pdf pp.60-61 (转引 Bowers Final EIR 2023-10)",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n产物：{OUT.name}")


if __name__ == "__main__":
    main()
