# -*- coding: utf-8 -*-
"""诊断 AI-UWM 数据中心补水的实际量级与单位，弄清 WUE ≈ 0.0017 的来源。

【疑点】
模型 evaporative 档在 10 MW 下给出年补水 290 m³/yr = 0.40 m³/d。
工程上蒸发冷却 10 MW IT 的补水应在 100–300 m³/d 量级（WUE 2–4 L/kWh）。
两者差约 1000 倍，必有一处理解错误：
  (a) data_center_daily 的补水列单位不是 m³/d？
  (b) installed_it_capacity_mw 的语义不是 IT 功率？
  (c) 冷却热负荷未被正确计算（heat_to_cooling_fraction 或 heat_basis）？
"""
from __future__ import annotations

import copy
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


def main() -> None:
    base = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")
    dc = next(v for v in base["components"].values() if v.get("kind") == "data_center")

    print("=== AI_DC1 关键配置 ===")
    for k in ("installed_it_capacity_mw", "heat_basis", "heat_to_cooling_fraction",
              "heat_rejection_temperature_coefficient", "technology"):
        print(f"  {k}: {dc.get(k)}")
    print(f"  cooling: {json.dumps({k: v for k, v in dc['cooling'].items() if k != 'technology_pue_adjustment'}, ensure_ascii=False)[:300]}")

    trial = copy.deepcopy(base)
    d2 = next(v for v in trial["components"].values() if v.get("kind") == "data_center")
    d2["installed_it_capacity_mw"] = 10.0
    d2.pop("capacity_schedule", None)
    res = FullAIUWMModel(trial, ts).run()
    d = res.data_center_daily

    print(f"\n=== data_center_daily 列（{len(d.columns)} 列）===")
    for c in d.columns:
        print("  ", c)

    print(f"\n=== 前 3 行的数值列 ===")
    num = d.select_dtypes("number")
    print(num.head(3).T.to_string())

    print(f"\n=== 各列的含义诊断（前 5 行均值）===")
    print(num.head(5).mean().to_string())
