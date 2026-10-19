# -*- coding: utf-8 -*-
"""用 Bowers 项目环评设计值校验模型的水耗量级。

【一手数据（Item 7 社区报告 p.60-61，引自 Final EIR 2023-10，pp.3-14 与 4.18-2）】
  Bowers 项目冷却技术：rooftop **air-cooled** chillers with **adiabatic** assistance（高温时）
  冷却用再生水：≤ 0.5 acre-foot/年 = 162,926 gal ≈ 616.7 m³
  自来水：约 2 acre-foot/年 = 651,702 gal ≈ 2,467 m³（含约 1 AF 景观）
  年日均冷却水：约 446 gal/day ≈ 1.69 m³/day

  报告同时给出 CEC 的 72 MW 备用发电 designation，但明确"不应读作实测年电网需求"。
  故不能直接把 72 MW 当作 IT 容量。

【本脚本做什么】
1. 单位换算核对（1 AF = 325,851 gal = 1,233.48 m³）；
2. 在"多个可能的 IT 容量"假设下，算出该项目的 WUE（L/kWh）与日补水（m³/d per MW）；
3. 与 AI-UWM 模型的技术参数比较（tech_dry / tech_hybrid / tech_evaporative）；
4. 得出：该案例落在模型的哪一档冷却技术上，以及模型是否高估/低估水耗。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
OUT = HERE / "_bowers_benchmark.json"

AF_TO_GAL = 325_851.0
AF_TO_M3 = 1233.48
GAL_TO_M3 = 0.00378541
DAY_PER_YEAR = 365.0
HOURS_PER_YEAR = 8760.0


def main() -> None:
    cool_af = 0.5
    potable_af = 2.0
    cool_m3 = cool_af * AF_TO_M3
    potable_m3 = potable_af * AF_TO_M3
    cool_gal = cool_af * AF_TO_GAL
    potable_gal = potable_af * AF_TO_GAL

    print("=== 单位换算核对 ===")
    print(f"  0.5 AF = {cool_gal:,.0f} gal（原文 162,926）→ 差 {cool_gal-162926:+.0f}")
    print(f"  2.0 AF = {potable_gal:,.0f} gal（原文 651,702）→ 差 {potable_gal-651702:+.0f}")
    print(f"  1.0 AF = {AF_TO_GAL:,.0f} gal（原文 325,851）→ 一致" if AF_TO_GAL == 325851 else "")
    print(f"  冷却 {cool_af} AF = {cool_m3:,.1f} m³/yr")
    print(f"  自来水 {potable_af} AF = {potable_m3:,.1f} m³/yr")
    daily_cool_m3 = cool_m3 / DAY_PER_YEAR
    print(f"  冷却日均 = {daily_cool_m3:.2f} m³/d（原文约 446 gal/d = "
          f"{446*GAL_TO_M3:.2f} m³/d）")

    # ---- 在若干 IT 容量假设下算 WUE ----
    print(f"\n=== 单位 IT 容量水耗（冷却用水 {cool_m3:.1f} m³/yr）===")
    print(f"{'IT 容量 (MW)':>14}{'WUE (L/kWh)':>14}{'补水 (m³/d/MW)':>18}{'年满负荷 h':>12}")
    rows = []
    for mw in (1.0, 5.0, 10.0, 20.0, 50.0, 72.0):
        # 年 IT 电量 = MW × 8760 h × 1000 kWh/MWh
        mwh = mw * HOURS_PER_YEAR
        kwh = mwh * 1000.0
        # 1 m³ = 1000 L
        wue = (cool_m3 * 1000.0) / kwh
        per_mw_day = daily_cool_m3 / mw
        print(f"{mw:>14.0f}{wue:>14.4f}{per_mw_day:>18.4f}{HOURS_PER_YEAR:>12.0f}")
        rows.append({"it_mw": mw, "wue_l_per_kwh": round(wue, 4),
                     "makeup_m3_per_day_per_mw": round(per_mw_day, 4)})

    # ---- 与模型技术档对比 ----
    print(f"\n=== 与 AI-UWM 冷却技术档对比 ===")
    print("  模型口径：WUE = 补水(m³/d) × 1000 / (IT_MW × 24 × 1000)  [L/kWh]")
    print("  典型档位（工程惯例量级，非本文设定值）：")
    print("    evaporative（湿冷）    WUE ≈ 2.0–4.0 L/kWh")
    print("    hybrid / adiabatic     WUE ≈ 0.5–1.5 L/kWh")
    print("    dry（风冷）            WUE ≈ 0.0–0.2 L/kWh")
    print()
    for r in rows:
        w = r["wue_l_per_kwh"]
        if w < 0.25:
            band = "dry（风冷）档"
        elif w < 1.6:
            band = "hybrid / adiabatic 档"
        elif w < 4.5:
            band = "evaporative（湿冷）档"
        else:
            band = "超出常见湿冷档（说明 IT 容量假设过小）"
        print(f"  若 IT={r['it_mw']:>5.0f} MW → WUE={w:>7.4f} L/kWh → 落在 {band}")

    print(f"\n=== 关键判读 ===")
    print("  该项目的冷却技术被 EIR 明确描述为 air-cooled + adiabatic assistance，")
    print("  即**风冷为主、高温时段绝热辅助**——与模型的 tech_dry_first / 混合档对应。")
    print("  其冷却水耗极低（≤0.5 AF/yr ≈ 617 m³/yr），说明：")
    print("    (1) 并非所有 Santa Clara 数据中心都是湿冷——模型用单一 evaporative 设定会高估水耗；")
    print("    (2) 该案例不能用于锚定 WUE 数值，因为**IT 容量未公开**（72 MW 是备用发电 designation，")
    print("        报告明确禁止读作年电网需求）；")
    print("    (3) 但可用于**定性校验**：模型的 dry/hybrid 档应能产出同量级（<1 AF/yr）的冷却水耗。")

    OUT.write_text(json.dumps({
        "source": "Item 7 Post Meeting Material.pdf pp.60-61，转引 Bowers Final EIR (2023-10) pp.3-14, 4.18-2",
        "cooling_recycled_af_per_year": cool_af,
        "potable_af_per_year": potable_af,
        "cooling_m3_per_year": round(cool_m3, 1),
        "daily_cooling_m3": round(daily_cool_m3, 2),
        "wue_by_capacity": rows,
        "note": ("IT 容量未公开，故 WUE 无法唯一定值；72 MW 为 CEC 备用发电 designation，"
                 "报告明确不得读作年电网需求。仅用于定性校验而非数值锚定。"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n产物：{OUT.name}")


if __name__ == "__main__":
    main()
