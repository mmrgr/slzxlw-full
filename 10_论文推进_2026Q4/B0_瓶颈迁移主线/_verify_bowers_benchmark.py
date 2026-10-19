# -*- coding: utf-8 -*-
"""核验"模型冷却技术档 × Bowers 设计值"的外部一致性。

【为什么这是一项有价值的检验】
论文此前的水侧参数（WUE、冷却技术）没有任何外部对照，参数包络表里多为"无锚点"。
本轮从 Item 7 社区报告（转引 Bowers Final EIR 2023-10）拿到一个**独立的官方设计值**：

  Bowers 项目：rooftop air-cooled chillers with adiabatic assistance
               冷却用再生水 ≤ 0.5 acre-foot/年 = 616.7 m³/yr

若其 IT 容量为 10 MW，则 WUE ≈ 0.007 L/kWh。
模型对应档位：dry = 0.000、dry_first = 0.398、hybrid = 0.606、evaporative = 2.205。

→ 0.007 落在 **dry 与 dry_first 之间**，与其 EIR 描述的"风冷为主、仅高温少量补水"一致。

【限制（必须声明）】
Bowers 的 IT 容量**未公开**。报告明确说 72 MW 是 CEC 的**备用发电 designation**，
"不应读作实测年电网需求"。故该对照只能做**量级/档位一致性检验**，
不能锁定 WUE 数值。IT 容量取不同值时 WUE 会变，但结论（落在 dry 侧）在
IT ∈ [1, 72] MW 全区间成立——这一点本脚本会验证。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
BM = HERE / "_tech_wue_benchmark.json"

RES: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> None:
    RES.append((name, bool(ok), detail))


def main() -> None:
    if not BM.exists():
        print("缺少 _tech_wue_benchmark.json")
        return
    d = json.loads(BM.read_text(encoding="utf-8"))
    rows = {r["tech"]: r for r in d["rows"]}

    # ---- 模型各档 WUE ----
    ck("dry 档 WUE = 0", abs(rows["dry"]["wue_l_per_kwh"]) < 1e-6,
       str(rows["dry"]["wue_l_per_kwh"]))
    ck("dry_first 档 WUE ≈ 0.40", abs(rows["dry_first"]["wue_l_per_kwh"] - 0.398) < 0.02,
       str(rows["dry_first"]["wue_l_per_kwh"]))
    ck("hybrid 档 WUE ≈ 0.61", abs(rows["hybrid"]["wue_l_per_kwh"] - 0.606) < 0.03,
       str(rows["hybrid"]["wue_l_per_kwh"]))
    ck("evaporative 档 WUE ≈ 2.21（工程常识 2–4 区间内）",
       2.0 <= rows["evaporative"]["wue_l_per_kwh"] <= 4.0,
       str(rows["evaporative"]["wue_l_per_kwh"]))
    ck("evaporative > hybrid > dry_first > dry（单调）",
       rows["evaporative"]["wue_l_per_kwh"] > rows["hybrid"]["wue_l_per_kwh"]
       > rows["dry_first"]["wue_l_per_kwh"] > rows["dry"]["wue_l_per_kwh"], "")

    # ---- Bowers 单位换算 ----
    ck("Bowers 0.5 AF = 616.7 m³", abs(d["bowers"]["m3_per_year"] - 616.7) < 0.2,
       str(d["bowers"]["m3_per_year"]))
    ck("Bowers @10 MW 的 WUE ≈ 0.0070", abs(d["bowers"]["wue_at_10mw"] - 0.0070) < 5e-4,
       str(d["bowers"]["wue_at_10mw"]))

    # ---- 关键断言：Bowers 落在 dry 与 dry_first 之间（对 IT 容量不敏感）----
    m3_yr = d["bowers"]["m3_per_year"]
    lo, hi = 0.0, rows["dry_first"]["wue_l_per_kwh"]
    print(f"\nBowers WUE 随 IT 容量假设的变化：")
    print(f"{'IT MW':>8}{'WUE L/kWh':>14}{'落在区间':>16}")
    ok_all = True
    for mw in (1, 2, 5, 10, 20, 50, 72):
        wue = (m3_yr * 1000.0) / (mw * 8760.0 * 1000.0)
        inside = lo - 1e-9 <= wue <= hi
        tag = "dry ↔ dry_first" if inside else ("低于 dry" if wue < lo else "高于 dry_first")
        if not inside:
            ok_all = False
        print(f"{mw:>8}{wue:>14.4f}{tag:>16}")
    ck("Bowers WUE 在 IT∈[1,72] MW 全区间落在 dry↔dry_first", ok_all,
       f"区间 [{lo}, {hi:.3f}]")

    # ---- 与 evaporative 档对比：说明"并非所有设施都是湿冷" ----
    ratio = rows["evaporative"]["wue_l_per_kwh"] / max(
        d["bowers"]["wue_at_10mw"], 1e-9)
    ck("Bowers 与湿冷档相差 ≥2 个数量级（支持'不能一律按湿冷建模'）",
       ratio > 100, f"湿冷/Bowers ≈ {ratio:.0f}×")

    npass = sum(1 for _, ok, _ in RES if ok)
    print(f"\n冷却技术档 × Bowers 一致性核验　通过 {npass}/{len(RES)}")
    for name, ok, detail in RES:
        print(("  ✅ " if ok else "  ❌ ") + name + (f"　[{detail}]" if detail else ""))
    sys.exit(0 if npass == len(RES) else 1)


if __name__ == "__main__":
    main()
