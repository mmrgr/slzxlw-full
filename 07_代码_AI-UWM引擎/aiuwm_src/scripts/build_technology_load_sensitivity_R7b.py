"""R7b 冷却技术前沿的 IT 负荷稳健性检验。

背景：`r2/{domain}/technology_comparison.csv` 只在 750 MW 一处负荷上得到
（`run_r2.py:589`）。而 EU WUE 分级、WaterMet2 参数包络等外部锚点都不限定在
单一负荷；若技术之间的相对排序随负荷变化，§九 的前沿结论就不能泛化。

本脚本在 250 / 750 / 1500 MW 三档负荷上重跑七种冷却技术，输出：
  站点 WUE、PUE、湿冷份额、单位 IT 电量的设施能耗惩罚、以及全口径（站点 +
  源端间接水）节水率在三种 EWIF 下随负荷是否稳定。

不修改任何既有产物；新产物单独写 CSV。

产出：validation_artifacts/r2/technology_load_sensitivity_R7b.csv
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from aiuwm.full_engine import FullAIUWMModel

ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT / "examples" / "cawcc_r2"
ART = ROOT / "validation_artifacts" / "r2"

CAPACITIES = (250.0, 750.0, 1500.0)

# A20：电力水强度档位（L/kWh）
EWIF = {
    "项目现值": None,        # 从 project.json 读当前域值
    "GreenGrid_1.8": 1.80,
    "LBNL_4.52": 4.52,
}


def load_timeseries(domain: str) -> pd.DataFrame:
    """与 run_r2.py load_domain() 完全一致的时间序列入口。"""
    return pd.read_csv(R2 / domain / "timeseries.csv")


def sim_years(domain: str) -> float:
    p = json.loads((R2 / domain / "project.json").read_text(encoding="utf-8"))
    s = pd.Timestamp(p["simulation"]["start"])
    e = pd.Timestamp(p["simulation"]["end"])
    return (e - s).days / 365.25


def main() -> None:
    rows = []
    for dom, label in (("ha", "D-HA"), ("co", "D-CO")):
        ts = load_timeseries(dom)
        yrs = sim_years(dom)
        ewif_now = json.loads((R2 / dom / "project.json").read_text(
            encoding="utf-8"))["components"]["AI_DC1"][
            "offsite_electricity_water_intensity_l_kwh"]

        per_cap = {}
        for cap in CAPACITIES:
            for tech_file in sorted((R2 / dom).glob("tech_*.json")):
                tech = tech_file.stem.replace("tech_", "")
                proj = json.loads(tech_file.read_text(encoding="utf-8"))
                proj["components"]["AI_DC1"]["installed_it_capacity_mw"] = cap
                d = FullAIUWMModel(proj, ts).run().data_center_daily
                it_kwh = d["it_energy_mwh"].sum() * 1e3
                fac_kwh = d["facility_energy_mwh"].sum() * 1e3
                key = (cap, tech)
                per_cap[key] = {
                    "IT电量_kWh每年": it_kwh / yrs,
                    "设施电量_kWh每年": fac_kwh / yrs,
                    "站点取水_ML每年": d["external_withdrawal_ml"].sum() / yrs,
                    "站点耗水_ML每年": d["consumption_ml"].sum() / yrs,
                    "PUE": float(d["pue"].mean()),
                    "湿冷份额": float(d["wet_cooling_fraction"].mean()),
                }

        for (cap, tech), v in per_cap.items():
            base = per_cap[(cap, "evaporative")]
            it = v["IT电量_kWh每年"]
            fac = v["设施电量_kWh每年"]
            dFac = fac - base["设施电量_kWh每年"]
            dW = base["站点取水_ML每年"] - v["站点取水_ML每年"]
            row = {
                "域签": label,
                "IT容量_MW": cap,
                "冷却技术": tech,
                "PUE": round(v["PUE"], 4),
                "湿冷份额": round(v["湿冷份额"], 4),
                "站点WUE_L_per_kWhIT": round(v["站点取水_ML每年"] * 1e6 / it, 4) if it else None,
                "站点耗水强度_L_per_kWhIT": round(v["站点耗水_ML每年"] * 1e6 / it, 4) if it else None,
                "设施能耗惩罚_相对evaporative百分比": round(dFac / base["设施电量_kWh每年"] * 100, 2),
                "单位IT电量设施能耗惩罚_kWh_per_kWhIT": round(dFac / it, 4),
                "反转阈值EWIF_L_per_kWh": round(dW * 1e6 / dFac, 2) if dFac > 0 else None,
            }
            for name, fixed in EWIF.items():
                e = fixed if fixed is not None else ewif_now
                fb = base["站点取水_ML每年"] + base["设施电量_kWh每年"] * e / 1e6
                ft = v["站点取水_ML每年"] + fac * e / 1e6
                row[f"全口径节水百分比_{name}"] = (
                    None if tech == "evaporative" else round((fb - ft) / fb * 100, 2))
            rows.append(row)

    out = pd.DataFrame(rows).sort_values(["域签", "IT容量_MW", "站点WUE_L_per_kWhIT"],
                                         ascending=[True, True, False])
    out.to_csv(ART / "technology_load_sensitivity_R7b.csv",
               index=False, encoding="utf-8-sig")
    with pd.option_context("display.width", 320, "display.max_columns", 40):
        print(out.to_string(index=False))
    print(f"\n[OK] {ART / 'technology_load_sensitivity_R7b.csv'}  rows={len(out)}")

    print("\n=== 结论：跨负荷稳定性 ===")
    for col in ("反转阈值EWIF_L_per_kWh", "全口径节水百分比_GreenGrid_1.8",
                "全口径节水百分比_LBNL_4.52"):
        g = out[(out["冷却技术"] == "dry")].groupby("域签")[col]
        for label, s in g:
            vals = [x for x in s.tolist() if pd.notna(x)]
            print(f"  {col:<28} {label}: {vals}  极差={max(vals) - min(vals):.2f}")


if __name__ == "__main__":
    main()
