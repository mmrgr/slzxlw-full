# -*- coding: utf-8 -*-
"""诊断 WUE 量级（结果写文件，避免控制台编码问题）。"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:/Users/mmrgr/Desktop/论文/算力中心/07_代码_AI-UWM引擎/aiuwm_src")
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
OUT = Path(__file__).resolve().parent / "_diag_wue.txt"
lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(str(s))


def main() -> None:
    base = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")
    dc = next(v for v in base["components"].values() if v.get("kind") == "data_center")

    w("=== AI_DC1 关键配置 ===")
    for k in ("installed_it_capacity_mw", "heat_basis", "heat_to_cooling_fraction",
              "heat_rejection_temperature_coefficient", "technology"):
        w(f"  {k}: {dc.get(k)}")
    cool = {k: v for k, v in dc["cooling"].items() if k != "technology_pue_adjustment"}
    w(f"  cooling: {json.dumps(cool, ensure_ascii=False)}")

    trial = copy.deepcopy(base)
    d2 = next(v for v in trial["components"].values() if v.get("kind") == "data_center")
    d2["installed_it_capacity_mw"] = 10.0
    d2.pop("capacity_schedule", None)
    res = FullAIUWMModel(trial, ts).run()
    d = res.data_center_daily

    w(f"\n=== data_center_daily 列（{len(d.columns)}）===")
    for c in d.columns:
        w(f"  {c}")

    num = d.select_dtypes("number")
    w(f"\n=== 各数值列前 5 行均值 ===")
    w(num.head(5).mean().to_string())

    w(f"\n=== 各数值列全程合计 ===")
    w(num.sum().to_string())

    OUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
