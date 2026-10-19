# -*- coding: utf-8 -*-
"""解释：为什么 D-CO 端联合口径的降幅（750 MW）远大于 D-HA（400 MW）？

【事实】
HA：政策约束阈值 ≥0.65；r=0.6 时联合 1150、r=0.7 时 1100、r=0.8 时 900、r=0.9 时 800
CO：政策约束阈值 ≥0.40；r=0.6 时联合 1200、r=0.7 时 1000、r=0.8 时 850、r=0.9 时 700

两者都是"提高 r 目标 → 政策约束更易失效"的自指效应，但 CO 端更剧烈。

【假设 1：CO 的政策阈值更低（0.40 vs 0.65），所以更早被 r 超过】
  HA: r 从 0.65 起才可能违约 → r=0.6 时还没违约，故 r=0.6 联合仍 1150（纯物理值）
  CO: r 从 0.40 起就可能违约 → r=0.6 已超阈值很多，故 r=0.6 联合掉到 1200
  这解释了"更早起效"，但不解释"降得更深"。

【假设 2：CO 端的瓶颈在电网，而政策约束与电网约束的失效先后关系不同】
  CO 纯物理首失效 = 电网（1500 MW）
  CO 联合首失效在 r≥0.6 时 = 政策约束
  若政策约束在 1200 就失效，而电网要到 1500，则政策约束成为新的、更早的瓶颈。
  
【检验方式】
读 constraint_boundaries / rstar_boundaries_by_r 产物，看 CO 端各 r 下
政策约束的首失效容量，以及它与纯物理首失效（电网 1500）的差距。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"


def main() -> None:
    for name in ("rstar_boundaries_by_r.csv", "rstar_physical_boundaries_by_r.csv"):
        f = R2 / name
        if not f.exists():
            print(f"缺失 {name}")
            continue
        d = pd.read_csv(f, encoding="utf-8-sig")
        print(f"\n{'='*78}\n{name}  列: {list(d.columns)}\n{'='*78}")
        # 只看政策约束与电网约束
        for dom in ("ha", "co"):
            sub = d[d[d.columns[0]] == dom] if d.columns[0] in ("domain", "域") else d
            if sub.empty:
                continue
            print(f"\n  --- {dom.upper()} ---")
            cols = [c for c in d.columns if c in
                    ("target_r", "constraint", "first_failed_capacity_mw", "informative")]
            if not cols:
                cols = list(d.columns)[:6]
            s = sub[cols]
            # 筛政策 / 电网
            if "constraint" in cols:
                s = s[s["constraint"].astype(str).str.contains(
                    "reclaimed_water_substitution|grid_connection", na=False, regex=True)]
            print(s.to_string(index=False))


if __name__ == "__main__":
    main()
