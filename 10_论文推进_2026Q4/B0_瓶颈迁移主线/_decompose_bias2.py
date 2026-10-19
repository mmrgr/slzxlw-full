# -*- coding: utf-8 -*-
"""核查 r=0.8→0.9 时"自来水用量反而上升"这一非单调现象。

【现象（1100 MW 固定）】
  r=0.5: 自来水 21.08, 再生水 21.08
  r=0.7: 自来水 13.12, 再生水 30.62
  r=0.8: 自来水 11.11, 再生水 33.78
  r=0.9: 自来水 11.98, 再生水 34.14   ← 自来水反弹

若 (1−r)·M 单调下降，自来水不应反弹。反弹说明 M 增长得比 (1−r) 下降更快，
或**实际交付的再生水比例 r_eff < 目标 r**（再生水不够），使自来水补足缺口。

【检验】
读 data_center_daily 的：
  - target_reclaimed_fraction（目标）
  - actual_reclaimed_fraction / quality_solver_reclaimed_fraction（实际交付）
  - gross_makeup_ml / external_makeup_ml / potable_water_ml
在 r=0.8 与 0.9 下逐日比较，看 r_eff 是否掉下来。
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
OUT = HERE / "_bias_decompose2.txt"
lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(str(s))


def main() -> None:
    proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")
    MW = 1100.0

    for r in (0.7, 0.8, 0.9):
        t = json.loads(json.dumps(proj))
        dc = t["components"]["AI_DC1"]
        dc["water_sources"]["reclaimed"]["target_fraction"] = r
        dc["water_sources"]["potable"]["target_fraction"] = 1 - r
        dc["installed_it_capacity_mw"] = MW
        dc.pop("capacity_schedule", None)
        res = FullAIUWMModel(t, ts).run()
        d = res.data_center_daily

        w(f"\n{'='*80}\n r = {r}   MW = {MW:.0f}\n{'='*80}")
        cols = ["target_reclaimed_fraction", "actual_reclaimed_fraction",
                "gross_makeup_ml", "external_makeup_ml", "potable_water_ml",
                "reclaimed_water_ml", "cycles_of_concentration",
                "quality_coc_fallback"]
        cols = [c for c in cols if c in d.columns]
        w(f"列: {cols}")
        s = d[cols].apply(pd.to_numeric, errors="coerce")
        w("\n=== 全程统计 ===")
        for c in cols:
            w(f"  {c:<34} mean={s[c].mean():>12.6f}  sum={s[c].sum():>14.4f}  "
              f"min={s[c].min():>10.4f}  max={s[c].max():>10.4f}")
        # 实际交付比例
        if "actual_reclaimed_fraction" in s.columns:
            ar = s["actual_reclaimed_fraction"]
            w(f"\n  实际交付 r_eff: mean={ar.mean():.6f} "
              f"(< 目标 {r} 的天数: {(ar < r - 1e-6).sum()} / {len(ar)})")
        # CoC fallback
        if "quality_coc_fallback" in s.columns:
            w(f"  quality_coc_fallback 触发天数: {int(s['quality_coc_fallback'].fillna(0).sum())}")
        # 自来水/再生水
        if "potable_water_ml" in s.columns:
            w(f"  自来水占比 = {s['potable_water_ml'].sum()/ (s['potable_water_ml'].sum()+s['reclaimed_water_ml'].sum()):.6f}")

    OUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
