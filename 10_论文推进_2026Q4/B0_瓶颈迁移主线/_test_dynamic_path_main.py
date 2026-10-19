# -*- coding: utf-8 -*-
"""关键检验：改用动态盐分路径重跑主结论，r* 判据是否仍然成立？

【为什么这是最关键的问题】
上一轮披露：论文跑在 legacy volume-only 路径，启用动态路径后 r=0.9 的 CoC
从 3.6484 升到 4.9981，年补水变幅从 9.37% 降到 0.0114%。

审稿人必然问：
  "那你的 r* 判据在动态路径下还成立吗？"

这个问题有两种可能答案：
  A. 成立但减弱 → 论文结论稳健，只需报告量级变化
  B. 不成立 → 机制是 legacy 路径的产物，论文需要重大改写

【检验设计】
在 D-HA 端点上，启用 quality_state=True，然后用 50 MW 网格扫 CAWCC(r)：
  r ∈ {0.0, 0.5, 0.6, 0.7, 0.8, 0.9}
比较：
  - 纯物理 CAWCC 随 r 的变化（legacy vs dynamic）
  - 阈值型响应是否仍存在（r 0.5→0.8 取水增幅）
  - r* = 0.5532 处是否仍有拐点（CoC 是否在 r* 后开始下降）

注意：动态路径下 CoC 若恒为 5.0，则 r* 后也不会下降 →
      "阈值型响应"在取水量上消失，但**解析判据 r* 本身仍可计算**。
      需要区分"判据是否有效"与"后果是否显著"。
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

from aiuwm.ai_capacity import find_ai_carrying_capacity  # noqa: E402
from run_r2 import daily_constraints, scan_with_mean  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
HERE = Path(__file__).resolve().parent
OUT = HERE / "_dynamic_path_cawcc.json"
CAP = list(np.arange(0, 2001, 50, dtype=float))
R_GRID = [0.0, 0.5, 0.6, 0.7, 0.8, 0.9]


def main() -> None:
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")
    cons = json.loads((R2 / "specs" / "constraints_ha.json").read_text(encoding="utf-8"))
    day = daily_constraints(cons)
    phys = {k: v for k, v in day.items() if k != "reclaimed_water_substitution_ratio"}

    out = {}
    for mode, enable in (("legacy", False), ("dynamic", True)):
        print(f"\n{'='*80}\n[{mode}]  quality_state_enabled = {enable}\n{'='*80}")
        print(f"{'r':>5}{'CoC':>10}{'CAWCC':>9}{'首失效约束':>36}{'总取水ML':>13}")
        print("-" * 78)
        rows = []
        for r in R_GRID:
            proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
            dc = proj["components"]["AI_DC1"]
            if enable:
                dc["quality_state_enabled"] = True
            dc["water_sources"]["reclaimed"]["target_fraction"] = r
            dc["water_sources"]["potable"]["target_fraction"] = 1 - r
            scan = scan_with_mean(proj, ts, CAP)
            pos = scan[scan["ai_capacity_mw"] >= 50].reset_index(drop=True)
            got = find_ai_carrying_capacity(pos, {"constraints": phys})
            caw = float(got["maximum_safe_ai_capacity_mw"])
            lim = str(got["limiting_constraint"])
            # CoC 与总取水：取 CAWCC 点（若无则取中点）
            at = scan[np.isclose(scan["ai_capacity_mw"], caw)]
            if at.empty:
                at = scan[scan["ai_capacity_mw"] == 1000.0]
            coc = float(at["coc_mean"].iloc[0]) if "coc_mean" in at.columns else None
            tot = float(at["total_withdrawal_ml"].iloc[0])
            coc_s = "None" if coc is None else f"{coc:.4f}"
            print(f"{r:>5.1f}{coc_s:>10}{caw:>9.0f}{lim[:34]:>36}{tot:>13.1f}")
            rows.append({"r": r, "coc": (None if coc is None else round(coc, 4)),
                         "cawcc": caw,
                         "limiting": lim, "total_withdrawal_ml": round(tot, 1)})
        out[mode] = rows

    (HERE / "_dynamic_path_cawcc.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*80}\n对比\n{'='*80}")
    print(f"{'r':>5}{'CAWCC legacy':>14}{'CAWCC dynamic':>15}{'差':>8}")
    print("-" * 44)
    for a, b in zip(out["legacy"], out["dynamic"]):
        print(f"{a['r']:>5.1f}{a['cawcc']:>14.0f}{b['cawcc']:>15.0f}"
              f"{b['cawcc']-a['cawcc']:>8.0f}")
    print(f"\n产物：_dynamic_path_cawcc.json")


if __name__ == "__main__":
    main()
