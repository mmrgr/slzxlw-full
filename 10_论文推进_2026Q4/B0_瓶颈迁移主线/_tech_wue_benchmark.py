# -*- coding: utf-8 -*-
"""在模型上运行四种冷却技术，取其 WUE 与单位 MW 补水，与 Bowers 设计值对照。

【为什么要做】
Bowers 设计值给出冷却水 ≤0.5 AF/yr ≈ 617 m³/yr。若其 IT 容量为几 MW 量级，
则 WUE 会低到 0.01–0.07 L/kWh，明显低于工程上任何蒸发冷却技术。
这提示两种可能：
  (a) 该数字是"补充水"而非"全部冷却水"（例如大量使用空气冷却、仅高温补少量水）；
  (b) IT 容量远大于我的假设（但报告说 72 MW 是备用发电 designation）。

要判断是哪一种，必须看**模型自己在 dry/hybrid 档下**给出多少水耗——
如果模型的 dry 档也给出极低值，那 Bowers 数字就是自洽的。

【模型冷却技术档（来自 examples/cawcc_r2/ha/tech_*.json）】
  tech_evaporative / tech_efficient_evaporative / tech_hybrid /
  tech_dry / tech_dry_first / tech_liquid_to_air / tech_liquid_to_water
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
IT_MW = 10.0
YEAR_DAYS = 730.0


def main() -> None:
    base = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")

    print(f"{'技术档':<30}{'年补水 m³':>12}{'m³/d':>10}{'WUE L/kWh':>12}{'蒸发份额':>10}")
    print("-" * 76)
    rows = []
    for f in sorted(glob.glob(str(R2 / "ha" / "tech_*.json"))):
        name = Path(f).stem.replace("tech_", "")
        try:
            cfg = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"{name:<30} 读取失败 {e}")
            continue
        # 用 base 结构 + tech 覆盖
        trial = copy.deepcopy(base)
        # tech 文件通常是完整 project 或 patch，先判断
        if "components" in cfg and "AI_DC1" in cfg.get("components", {}):
            merge = copy.deepcopy(base)
            for cid, comp in cfg["components"].items():
                if cid in merge["components"]:
                    merge["components"][cid].update(comp)
            trial = merge
        else:
            trial["components"]["AI_DC1"].update(cfg)

        dc = next(v for v in trial["components"].values() if v.get("kind") == "data_center")
        dc["installed_it_capacity_mw"] = IT_MW
        dc.pop("capacity_schedule", None)

        try:
            res = FullAIUWMModel(trial, ts).run()
        except Exception as e:
            print(f"{name:<30} 运行失败 {str(e)[:40]}")
            continue

        d = res.data_center_daily
        # 找补水列
        mk = next((c for c in d.columns if "external_makeup" in c.lower()), None)
        if mk is None:
            mk = next((c for c in d.columns if "makeup" in c.lower()), None)
        if mk is None:
            print(f"{name:<30} 无补水列 ({[c for c in d.columns][:6]})")
            continue
        total_m3 = float(pd.to_numeric(d[mk], errors="coerce").sum())
        per_day = total_m3 / YEAR_DAYS
        kwh = IT_MW * 24.0 * YEAR_DAYS * 1000.0
        wue = (total_m3 * 1000.0) / kwh
        ev = next((c for c in d.columns if "evap" in c.lower()), None)
        ev_f = float(pd.to_numeric(d[ev], errors="coerce").mean()) if ev else float("nan")
        print(f"{name:<30}{total_m3:>12.1f}{per_day:>10.2f}{wue:>12.4f}{ev_f:>10.3f}")
        rows.append({"tech": name, "annual_m3": round(total_m3, 1),
                     "per_day_m3": round(per_day, 2), "wue": round(wue, 4)})

    print("\n=== 对照 Bowers 设计值 ===")
    print("  Bowers 冷却水 ≤0.5 AF/yr = 616.7 m³/yr，年日均 ≈1.69 m³/d")
    print("  若其 IT 容量为 10 MW，则 WUE ≈ 0.0070 L/kWh")
    print("  上表中最接近的档位：dry / dry_first")
    if rows:
        dry = [r for r in rows if "dry" in r["tech"]]
        if dry:
            print(f"  模型 dry 档：{dry[0]['annual_m3']} m³/yr @ {IT_MW} MW，"
                  f"WUE={dry[0]['wue']:.4f}")

    (Path(__file__).resolve().parent / "_tech_wue_benchmark.json").write_text(
        json.dumps({"it_mw": IT_MW, "rows": rows,
                    "bowers_design_m3_per_year": 616.7},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n产物：_tech_wue_benchmark.json")


if __name__ == "__main__":
    main()
