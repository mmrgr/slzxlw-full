# -*- coding: utf-8 -*-
"""核实：启用 quality_state 后 r* 机制是否真的消失？

【实测（1100 MW，D-HA）】
              CoC      r_eff     年补水 ML
r=0.5 False  5.0000  0.500000   30770.8
r=0.5 True   5.0000  0.500000   30770.8
r=0.7 False  4.3222  0.700000   31923.9
r=0.7 True   4.9991  0.700000   30772.2   ← 补水几乎不变
r=0.8 False  3.9568  0.755645   32764.8
r=0.8 True   4.9986  0.781105   30773.3
r=0.9 False  3.6484  0.743997   33655.1
r=0.9 True   4.9981  0.798036   30774.3

【惊人之处】
启用后 CoC 恒为 ~5（设计值），补水几乎恒定 → **阈值型反噬消失了**。

【必须查清的三件事】
1. 启用后 CoC 为何恒为设计值？
   可能：动态路径下，环路盐分被 blowdown 带走，稳态 CoC 由质量平衡决定，
        而 blowdown_quality_mg_l={TDS:1800} 或某些参数使稳态恰好接近 5。
   若如此，则"水质上限 L"根本没起作用 —— 这是一个**结构性问题**。

2. 这是否说明论文的 r* 机制依赖于"未启用动态盐分"这一设定？
   如果是，那是重大限制，必须披露。

3. 启用路径是否本身有缺陷（例如未正确实现限值约束）？

【本脚本】读启用后的逐日诊断列，判断 CoC=5 的来源。
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
OUT = HERE / "_quality_state_verify.txt"
lines: list[str] = []


def w(s: str = "") -> None:
    lines.append(str(s))


def main() -> None:
    proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")
    proj["components"]["AI_DC1"]["quality_state_enabled"] = True
    dc = proj["components"]["AI_DC1"]
    dc["water_sources"]["reclaimed"]["target_fraction"] = 0.9
    dc["water_sources"]["potable"]["target_fraction"] = 0.1
    dc["installed_it_capacity_mw"] = 1100.0
    dc.pop("capacity_schedule", None)
    res = FullAIUWMModel(proj, ts).run()
    d = res.data_center_daily

    w("=== 全部列 ===")
    for c in d.columns:
        w("  " + c)

    num = d.select_dtypes("number")
    w("\n=== 数值列统计 ===")
    w(f"{'列':<40}{'mean':>14}{'min':>12}{'max':>12}")
    for c in num.columns:
        w(f"{c:<40}{num[c].mean():>14.6f}{num[c].min():>12.6f}{num[c].max():>12.6f}")

    # 关键：环路盐分
    w("\n=== 与盐分/CoC 相关的列 ===")
    for c in d.columns:
        cl = c.lower()
        if any(k in cl for k in ("coc", "quality", "sal", "tds", "concentration",
                                 "blowdown", "evapor", "makeup")):
            w(f"  {c}: {d[c].head(3).tolist()}")

    Path(HERE / "_quality_state_verify.txt").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
