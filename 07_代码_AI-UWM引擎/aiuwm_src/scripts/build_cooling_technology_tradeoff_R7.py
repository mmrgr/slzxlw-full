"""R7 冷却技术阶梯上的水—能—碳权衡 + EU WUE 合规性判定。

背景：`intervention_water_energy_carbon.csv` 曾得出"未检出节水增碳权衡"的空结果。
本脚本证明：该空结果是**搜索空间受限**造成的——此前只在固定冷却技术下扫 IT 容量，
从未扫描冷却技术本身。`r2/{domain}/technology_comparison.csv` 中已存在完整的水—能前沿。

产出：validation_artifacts/r2/cooling_technology_tradeoff_R7.csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT / "examples" / "cawcc_r2"
ART = ROOT / "validation_artifacts" / "r2"

EU_LO, EU_HI, EU_MEAN = 0.07, 1.28, 0.58
GRID_EF = 0.35  # kgCO2e/kWh，取自 examples/cawcc_r2/{ha,co}/project.json


def sim_years(domain: str) -> float:
    p = json.loads((R2 / domain / "project.json").read_text(encoding="utf-8"))
    s = pd.Timestamp(p["simulation"]["start"])
    e = pd.Timestamp(p["simulation"]["end"])
    return (e - s).days / 365.25


def main() -> None:
    rows = []
    for dom, label in (("ha", "D-HA"), ("co", "D-CO")):
        df = pd.read_csv(ART / dom / "technology_comparison.csv")
        yrs = sim_years(dom)
        base = df.loc[df["technology"] == "evaporative"].iloc[0]
        base_e_kwh = base["facility_energy_mwh"] * 1e3 / yrs
        for _, r in df.iterrows():
            e_kwh = r["facility_energy_mwh"] * 1e3 / yrs
            de = e_kwh - base_e_kwh
            dwat = base["annual_withdrawal_ml"] - r["annual_withdrawal_ml"]  # ML/yr
            dco2 = de * GRID_EF  # kgCO2e/yr
            rows.append({
                "域签": label,
                "冷却技术": r["technology"],
                "湿冷份额": round(float(r["mean_wet_fraction"]), 4),
                "PUE": round(float(r["mean_pue"]), 4),
                "WUE_L_per_kWh": round(float(r["wue_l_kwh"]), 4),
                "EU观测区间0.07-1.28": "落在区间内" if EU_LO <= r["wue_l_kwh"] <= EU_HI
                                     else ("低于下界" if r["wue_l_kwh"] < EU_LO else "高出上限"),
                "距EU均值0.58偏差百分比": None if EU_MEAN == 0 else
                                     round((r["wue_l_kwh"] - EU_MEAN) / EU_MEAN * 100, 2),
                "年取水_ML": round(float(r["annual_withdrawal_ml"]), 2),
                "相对evaporative节水_ML每年": round(float(dwat), 2),
                "相对evaporative节水百分比": None if base["annual_withdrawal_ml"] == 0 else
                                        round(dwat / base["annual_withdrawal_ml"] * 100, 2),
                "设施能耗_MWh每年": round(e_kwh / 1e3, 2),
                "相对evaporative增能耗百分比": round(de / base_e_kwh * 100, 2),
                "相对evaporative增碳_kgCO2e每年": round(dco2, 0),
                # dwat 单位为 ML/yr = 1000 m3/yr，故比值即"每 1000 m3 节水的碳代价"
                "每千m3节水的碳代价_kgCO2e": None if dwat <= 0 else round(dco2 / dwat, 2),
                "每m3节水的碳代价_kgCO2e": None if dwat <= 0 else round(dco2 / dwat / 1e3, 3),
                "对照_A05供水碳强度倍率": None if dwat <= 0 else round((dco2 / dwat / 1e3) / 1.14, 2),
                "是否构成水能权衡": "是" if (dwat > 0 and de > 0) else
                                  ("双赢" if dwat > 0 and de <= 0 else "基准"),
            })
    out = pd.DataFrame(rows)
    cols = ["域签", "冷却技术", "湿冷份额", "PUE", "WUE_L_per_kWh",
            "EU观测区间0.07-1.28", "距EU均值0.58偏差百分比",
            "年取水_ML", "相对evaporative节水_ML每年", "相对evaporative节水百分比",
            "设施能耗_MWh每年", "相对evaporative增能耗百分比",
            "相对evaporative增碳_kgCO2e每年", "每千m3节水的碳代价_kgCO2e", "每m3节水的碳代价_kgCO2e", "对照_A05供水碳强度倍率", "是否构成水能权衡"]
    out = out[cols].sort_values(["域签", "WUE_L_per_kWh"], ascending=[True, False])
    out.to_csv(ART / "cooling_technology_tradeoff_R7.csv", index=False, encoding="utf-8-sig")
    with pd.option_context("display.width", 260, "display.max_columns", 20):
        print(out.to_string(index=False))
    print(f"\n[OK] {ART / 'cooling_technology_tradeoff_R7.csv'}  rows={len(out)}")
    print("\n=== 结论 ===")
    for label in ("D-HA", "D-CO"):
        s = out[(out["域签"] == label) & (out["是否构成水能权衡"] == "是")]
        if len(s):
            print(f"{label}: {len(s)} 条技术路径同时节水且增能耗 → 水—能权衡存在于模型中")
        else:
            print(f"{label}: 无异于 side-effect 的技术路径")


if __name__ == "__main__":
    main()
