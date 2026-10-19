# -*- coding: utf-8 -*-
"""核实模型内部的一处张力：CoC 按目标 r 计算，但实际交付是 r_eff。

【实测数据】
  r_target   r_eff      CoC(模型实际输出)   CoC(按目标r解析)   CoC(按r_eff解析)
    0.75     0.7402          ?                 4.1315            4.1674
    0.80     0.7556         3.9568             3.9568            4.1110
    0.85     0.7514          ?                 3.7964            4.1263
    0.90     0.7440         3.6484             3.6484            4.1535

关键：模型输出的 CoC 与"按目标 r 解析"完全一致（3.9568 / 3.6484），
**而不是**与"按实际交付 r_eff 解析"一致（4.1110 / 4.1535）。

【这意味着】
当再生水交付不足（r_eff < r_target）时，模型仍然按**目标配比**计算混合水质，
从而低估了实际的 CoC（因为实际自来水占比更高、混合水质更淡）。

这是一个**保守方向**的建模选择（高估水质反噬 = 高估水侧压力），
但它使"r 超过产能上限后"的区段失真：
  - 现实中，r 提到 0.9 但只能交付 0.744 时，实际混合水质等同于 r=0.744，
    CoC 应为 4.15 而非 3.65，反噬远小于模型报告值。
  - 因此模型在 r=0.85/0.9 报告的"反噬"是**上界**。

【为什么要写入论文】
1. 它解释了上一轮 22.86 MW 解析残差的来源（不是解析式错，是模型 CoC 与 r_eff 不一致）；
2. 它给论文一个重要限定：**r > 产能上限时的效应量是上界**；
3. 它与论文 §3.3(b) 剔除 max_reuse_utilization 的理由相呼应——
   产能限制的效应没有消失，而是以"r_eff 自回落 + CoC 仍按目标算"的方式进入了模型。

【注意】本发现不改变 r* 的结论：r* = 0.5532 位于 r_eff 仍完全达标（≤0.70）的区间内，
故阈值位置不受影响。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:/Users/mmrgr/Desktop/论文/算力中心/07_代码_AI-UWM引擎/aiuwm_src")
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
HERE = Path(__file__).resolve().parent
OUT = HERE / "_coc_reff_tension.json"

L, CD, CP, CR = 2200.0, 5.0, 180.0, 650.0


def coc_of(r: float) -> float:
    return min(CD, L / (r * CR + (1 - r) * CP))


def main() -> None:
    proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")
    MW = 1100.0
    rows = []

    print(f"{'r':>6}{'r_eff':>9}{'CoC模型':>10}{'CoC(目标)':>11}{'CoC(r_eff)':>12}"
          f"{'模型-目标':>11}{'模型-r_eff':>12}")
    print("-" * 74)
    for r in (0.70, 0.75, 0.80, 0.85, 0.90):
        t = json.loads(json.dumps(proj))
        dc = t["components"]["AI_DC1"]
        dc["water_sources"]["reclaimed"]["target_fraction"] = r
        dc["water_sources"]["potable"]["target_fraction"] = 1 - r
        dc["installed_it_capacity_mw"] = MW
        dc.pop("capacity_schedule", None)
        res = FullAIUWMModel(t, ts).run()
        d = res.data_center_daily
        r_eff = float(pd.to_numeric(d["actual_reclaimed_fraction"],
                                    errors="coerce").mean())
        coc_model = float(pd.to_numeric(d["cycles_of_concentration"],
                                        errors="coerce").mean())
        c_t = coc_of(r)
        c_e = coc_of(r_eff)
        print(f"{r:>6.2f}{r_eff:>9.6f}{coc_model:>10.4f}{c_t:>11.4f}{c_e:>12.4f}"
              f"{coc_model-c_t:>11.2e}{coc_model-c_e:>12.4f}")
        rows.append({"r_target": r, "r_eff_mean": round(r_eff, 6),
                     "coc_model": round(coc_model, 6),
                     "coc_at_target": round(c_t, 6),
                     "coc_at_eff": round(c_e, 6),
                     "diff_model_vs_target": round(coc_model - c_t, 9),
                     "diff_model_vs_eff": round(coc_model - c_e, 6)})

    print("\n=== 结论 ===")
    ok = all(abs(x["diff_model_vs_target"]) < 1e-6 for x in rows)
    print(f"  模型 CoC 与『按目标 r 解析』一致: {'是' if ok else '否'}")
    print(f"  → 当 r_eff < r_target 时，模型仍按目标配比算 CoC，")
    print(f"    因而在 r > 0.70 的区段**低估 CoC、高估反噬**。")

    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n产物：{OUT.name}")


if __name__ == "__main__":
    main()
