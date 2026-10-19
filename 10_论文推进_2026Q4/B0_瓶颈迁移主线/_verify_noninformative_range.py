# -*- coding: utf-8 -*-
"""核验"非 informative 约束的范围依赖"检验已写入，且数字有产物支撑。

断言：
  1. 扩展扫描产物存在（json + 两端 csv）；
  2. 两端各只剩 1 条从不失效，且均为 max_wwtw_utilization；
  3. HA/CO 的 wwtw 最大利用率 = 0.8992 / 0.8755（均 < 0.95）；
  4. 其余 5 条的首失效容量与表一致；
  5. 已排除 0 MW 伪影（reclaimed 首失效不再是 0）；
  6. 三处正文均已写入该检验。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
R2 = PROJ / "07_代码_AI-UWM引擎" / "aiuwm_src" / "validation_artifacts" / "r2"
J = HERE / "_noninformative_extended.json"
MS = HERE / "03_主稿_v2.md"
EN = HERE / "04_wr_manuscript_en.md"
SI = HERE / "05_wr_supplementary_en.md"

RES: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def main() -> None:
    ck("扩展 json 存在", J.exists(), str(J.name))
    for b in ("ha", "co"):
        f = R2 / b / "capacity_scan_4000mw.csv"
        ck(f"{b} 的 4000MW 扫描 csv 存在", f.exists(), f"{f.stat().st_size} B" if f.exists() else "缺失")

    if not J.exists():
        npass = sum(1 for _, ok, _ in RES if ok)
        print(f"通过 {npass}/{len(RES)}")
        return
    d = json.loads(J.read_text(encoding="utf-8"))

    for b in ("ha", "co"):
        never = [k for k, v in d[b].items() if v["first_fail_mw"] is None]
        ck(f"{b.upper()} 扩到 4000MW 后仅 1 条不失效", len(never) == 1, str(never))
        ck(f"{b.upper()} 不失效者为 max_wwtw_utilization",
           never == ["max_wwtw_utilization"], str(never))

    ck("HA wwtw 最大利用率 = 0.8992",
       abs(d["ha"]["max_wwtw_utilization"]["max_value"] - 0.8992) < 5e-4,
       str(d["ha"]["max_wwtw_utilization"]["max_value"]))
    ck("CO wwtw 最大利用率 = 0.8755",
       abs(d["co"]["max_wwtw_utilization"]["max_value"] - 0.8755) < 5e-4,
       str(d["co"]["max_wwtw_utilization"]["max_value"]))
    ck("两端 wwtw 利用率均 < 阈值 0.95",
       d["ha"]["max_wwtw_utilization"]["max_value"] < 0.95
       and d["co"]["max_wwtw_utilization"]["max_value"] < 0.95, "")

    expect = {
        "ha": {"system_reliability_fraction": 2050, "unmet_cooling_water_ml": 2300,
               "domestic_unmet_ml": 1850, "peak_capacity_ratio": 1750,
               "reclaimed_water_substitution_ratio": 1350},
        "co": {"system_reliability_fraction": 2550, "unmet_cooling_water_ml": 3000,
               "domestic_unmet_ml": 2350, "peak_capacity_ratio": 2300,
               "reclaimed_water_substitution_ratio": 2100},
    }
    for b, exp in expect.items():
        for k, v in exp.items():
            got = d[b][k]["first_fail_mw"]
            ck(f"{b.upper()} {k} 首失效 = {v}", got == float(v), str(got))

    ck("reclaimed 首失效不再是 0（已排除 0MW 伪影）",
       d["ha"]["reclaimed_water_substitution_ratio"]["first_fail_mw"] != 0.0, "")

    ms = MS.read_text(encoding="utf-8")
    en = EN.read_text(encoding="utf-8")
    si = SI.read_text(encoding="utf-8")
    ck("母稿含扫描范围边界检验", "扫描范围的边界检验" in ms, "")
    ck("母稿写明其一加强其一削弱", "加强" in ms and "削弱" in ms, "")
    ck("英文含 4000 MW 扩展说明", "4000 MW" in en and "range-dependent" in en, "")
    ck("SI 含 S5.1b", "S5.1b" in si, "")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"非 informative 范围依赖核验　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
