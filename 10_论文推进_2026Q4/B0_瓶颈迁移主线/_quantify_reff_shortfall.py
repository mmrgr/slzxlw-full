# -*- coding: utf-8 -*-
"""核实并量化"高 r 时再生水交付不足"这一发现。

【数据（D-HA，1100 MW，730 天）】
  r=0.7: r_eff = 0.700000，未达标 0/730 天        → 交付完全兑现
  r=0.8: r_eff = 0.755645，未达标 620/730 天      → 86% 的天数短缺
  r=0.9: r_eff = 0.743997，未达标 730/730 天      → 全部短缺，且 r_eff 反而下降

【为什么重要】
论文 §5.7 的核心论证是"提高 r 会因水质反噬而推高补水需求"。
但模型里还有一个**并行机制**：当 r 超过再生水产能上限时，
实际交付比例 r_eff 不再等于目标 r，**自回落到约 0.74–0.76 的平台上**。

这意味着：
1. 论文 §5.7 计算的"反噬"是在 r_eff < r 的条件下发生的，
   而解析式（用目标 r 计算 CoC）因此**系统性高估了 CoC 的下降幅度**；
2. 这正是上一轮 CAWCC 解析残差的根源（预测偏低，因为按目标 r 算的 CoC 太低）；
3. **更重要的是**：`max_reuse_utilization` 被论文 §3.3(b) 剔除
   （理由："300 ML 储池使日尺度处理速率达铭牌属正常调蓄"），
   但这里显示的是**再生水量（产能×分流比）不足**，不是处理速率不足。
   论文把产能约束的效应**部分隐藏在了 r_eff 的自回落里**。

【本脚本量化】
1. 各 r 下的 r_eff 平台值与未达标天数；
2. 用 r_eff 而非 r 重算 CoC，检验是否能解释上一轮的 22.86 MW 残差；
3. 报出 r_eff 开始偏离目标的临界 r。
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
OUT = HERE / "_reff_shortfall.json"
lines: list[str] = []

L, CD, CP, CR = 2200.0, 5.0, 180.0, 650.0


def w(s: str = "") -> None:
    lines.append(str(s))


def coc_of(r: float) -> float:
    return min(CD, L / (r * CR + (1 - r) * CP))


def f_of(r: float) -> float:
    c = coc_of(r)
    return c / (c - 1.0)


def main() -> None:
    proj = json.loads((R2 / "ha" / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / "ha" / "timeseries.csv")
    MW = 1100.0

    rows = []
    w(f"{'r_target':>9}{'r_eff':>10}{'未达标天数':>11}{'CoC(目标r)':>12}"
      f"{'CoC(r_eff)':>12}{'f(目标)':>10}{'f(r_eff)':>10}")
    w("-" * 78)
    for r in (0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9):
        t = json.loads(json.dumps(proj))
        dc = t["components"]["AI_DC1"]
        dc["water_sources"]["reclaimed"]["target_fraction"] = r
        dc["water_sources"]["potable"]["target_fraction"] = 1 - r
        dc["installed_it_capacity_mw"] = MW
        dc.pop("capacity_schedule", None)
        res = FullAIUWMModel(t, ts).run()
        d = res.data_center_daily
        ar = pd.to_numeric(d["actual_reclaimed_fraction"], errors="coerce")
        r_eff = float(ar.mean())
        short = int((ar < r - 1e-6).sum())
        w(f"{r:>9.2f}{r_eff:>10.6f}{short:>11d}{coc_of(r):>12.4f}"
          f"{coc_of(r_eff):>12.4f}{f_of(r):>10.4f}{f_of(r_eff):>10.4f}")
        rows.append({"r_target": r, "r_eff_mean": round(r_eff, 6),
                     "n_short_days": short,
                     "coc_target": round(coc_of(r), 4),
                     "coc_eff": round(coc_of(r_eff), 4),
                     "f_target": round(f_of(r), 4),
                     "f_eff": round(f_of(r_eff), 4)})

    # 用 r_eff 重算 A/f 预测
    w("\n\n=== 用 r_eff 替代目标 r 重算解析预测（A=1500）===")
    caw = pd.read_csv(ROOT / "validation_artifacts" / "r2"
                      / "rstar_physical_cawcc_by_r.csv", encoding="utf-8-sig")
    caw = caw[caw["domain"] == "ha"].set_index("target_r")["physical_cawcc_mw"]
    w(f"{'r':>6}{'实测CAWCC':>11}{'预测(目标r)':>13}{'预测(r_eff)':>13}{'残差(目标)':>12}{'残差(r_eff)':>13}")
    w("-" * 70)
    for x in rows:
        r = x["r_target"]
        if r not in caw.index:
            continue
        obs = float(caw[r])
        p_t = 1500.0 / x["f_target"]
        p_e = 1500.0 / x["f_eff"]
        w(f"{r:>6.2f}{obs:>11.0f}{p_t:>13.1f}{p_e:>13.1f}"
          f"{obs-p_t:>12.1f}{obs-p_e:>13.1f}")

    (HERE / "_reff_shortfall.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(HERE / "_reff_shortfall.txt").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
