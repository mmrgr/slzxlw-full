# -*- coding: utf-8 -*-
"""核实：模型是否有质量求解器修正 CoC？上一轮"CoC 按目标算"的结论是否完整？

【上一轮结论】
模型 CoC = 按目标 r 解析值（差 ≤1e-15），而实际交付 r_eff < r，
故认为"模型按目标配比算 CoC，高估反噬"。

【本轮的疑问】
代码中 `_cycles_of_concentration` 支持 `source_fractions` 参数，
且下方有 `_coc_with_return_pool(fraction, initial_coc, fractions)` 这样的求解器。
若求解器在工作，CoC 应反映实际 fraction，而非目标。

但实测 CoC 与"按目标 r 解析"精确相等（1e-15）——这两件事矛盾。
可能：
  (a) 求解器未启用（quality_solver_status 不是 converged）；
  (b) 求解器启用了但收敛到目标值（因为 return pool 质量恰好补偿）；
  (c) CoC 是逐日先算、再平均，而 r_eff 也是平均 → 平均后恰好一致。

【方法】
读 data_center_daily 的 quality_solver_status / root_count / residual 列，
以及逐日的 target vs actual reclaimed fraction 与当日的 CoC，
判断求解器到底做了什么。
"""
from __future__ import annotations

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
OUT = HERE / "_solver_probe.txt"
lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(str(s))


def main() -> None:
    proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")

    for r in (0.80, 0.90):
        t = json.loads(json.dumps(proj))
        dc = t["components"]["AI_DC1"]
        dc["water_sources"]["reclaimed"]["target_fraction"] = r
        dc["water_sources"]["potable"]["target_fraction"] = 1 - r
        dc["installed_it_capacity_mw"] = 1100.0
        dc.pop("capacity_schedule", None)
        res = FullAIUWMModel(t, ts).run()
        d = res.data_center_daily

        w(f"\n{'='*86}\n r = {r}   MW = 1100\n{'='*86}")
        cols = [c for c in d.columns if any(k in c.lower() for k in
                ("quality_solver", "target_reclaimed", "actual_reclaimed",
                 "cycles_of_concentration", "quality_coc_fallback",
                 "quality_state", "quality_integration"))]
        w(f"相关列: {cols}")
        s = d[cols].copy()
        for c in cols:
            s[c] = pd.to_numeric(s[c], errors="coerce")

        for c in cols:
            if "status" in c or "state" in c:
                vc = d[c].astype(str).value_counts().to_dict()
                w(f"\n  {c} 取值分布: {vc}")
            else:
                w(f"  {c:<40} mean={s[c].mean():>14.6f} "
                  f"min={s[c].min():>12.6f} max={s[c].max():>12.6f}")

        # 逐日样本：交付不足的日子
        if "actual_reclaimed_fraction" in s.columns:
            short = s[s["actual_reclaimed_fraction"] < r - 1e-6]
            w(f"\n  交付不足天数: {len(short)} / {len(s)}")
            if len(short):
                w("\n  样本（前 5 天交付不足）：")
                show = [c for c in ("target_reclaimed_fraction", "actual_reclaimed_fraction",
                                    "cycles_of_concentration") if c in short.columns]
                w(short[show].head(5).to_string())

    OUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
