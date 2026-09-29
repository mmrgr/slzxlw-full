"""R7b 全口径水足迹前沿：站点水 + 源端间接水，联合 EU WUE 与电网碳强度包络。

为什么必须做这一步
------------------
`cooling_technology_tradeoff_R7.csv` 的"节水百分比"只用了 `annual_withdrawal_ml`
（场站取水）。但缺陷 D1 已确认 `offsite_electricity_water_intensity_l_kwh`
被低估 91–96%，源端间接水通道被削弱约一个量级。若干冷却技术的能耗惩罚
（+4.6%~+15.4%）会通过这条被削弱的通道产生反向耗水，站点 WUE 口径
根本看不到它。Green Grid 记载的"干冷却省现场水却抬高流域总耗水"争议，
必须换成全口径（站点 + 源端）才能判定。

本脚本不重跑引擎，只对既有 `r2/{domain}/technology_comparison.csv` 做代数外推：
    W_indirect[ML/yr] = E_facility[kWh/yr] x EWIF[L/kWh] / 1e6
    F_total[ML/yr]    = W_site + W_indirect
    ΔCO2[kg/yr]       = (E_tech - E_base)[kWh/yr] x EF[kgCO2e/kWh]
    全口径碳代价    = ΔCO2 / (F_base - F_tech)

并给出**反转阈值 EWIF***：使全口径节水归零所需的电网水强度
    EWIF* = ΔW_site x 1e6 / ΔE_facility
把 EWIF* 与观测包络（1.8 / 4.52）比较，即可直接判定" Green Grid 式反转
在本参数域内是否可能发生"——这是可证伪的，而不是叙事。

外部锚点（本轮新增，均带来源）
----------------------------
A19  电网全生命周期碳强度包络
     IPCC WGIII AR5 Annex III Table A.III.2（生命周期排放，gCO2eq/kWh，
     min/median/max）：陆上风电 7.0/11/56、水电 1.0/24/2200、核电 3.7/12/110、
     光伏(地面) 18/48/180、气电 CCGT 410/490/650、煤电 PC 740/820/910。
     → 本报告采用三档：0.011（可再生主导）/ 0.35（项目现值）/ 0.820（煤电中位数）
A20  电力水强度 EWIF
     1.8 L/kWh  = Green Grid White Paper #35（美国平均）
     4.52 L/kWh = LBNL 2024 间接水反演值

产出：validation_artifacts/r2/total_water_footprint_frontier_R7b.csv
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

# A20：电力水强度档位（L/kWh）
EWIF_TIERS = [
    ("项目现值", None),      # None = 从 project.json 读当前域值
    ("GreenGrid_1.8", 1.80),
    ("LBNL_4.52", 4.52),
]

# A19：电网碳强度档位（kgCO2e/kWh）
EF_TIERS = [
    ("可再生主导_0.011", 0.011),
    ("项目现值_0.350", 0.350),
    ("煤电主导_0.820", 0.820),
]
EF_SOURCE = {
    "可再生主导_0.011": "IPCC AR5 A.III.2 陆上风电生命周期中位数 11 gCO2eq/kWh",
    "项目现值_0.350": "项目当前取值，落在 IPCC 包络内（气电 490 与煤电 820 之下）",
    "煤电主导_0.820": "IPCC AR5 A.III.2 煤电 PC 生命周期中位数 820 gCO2eq/kWh",
}


def project_value(domain: str, key: str) -> float:
    p = json.loads((R2 / domain / "project.json").read_text(encoding="utf-8"))
    return float(p["components"]["AI_DC1"][key])


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
        ewif_now = project_value(dom, "offsite_electricity_water_intensity_l_kwh")

        # 年化：withdrawal/consumption 已年化；facility_energy_mwh 为全期累计
        d = df.copy()
        d["E_kwh_yr"] = d["facility_energy_mwh"] * 1e3 / yrs
        d["C_site_ml_yr"] = d["annual_consumption_ml"]
        base = d.loc[d["technology"] == "evaporative"].iloc[0]

        for _, r in d.iterrows():
            de = r["E_kwh_yr"] - base["E_kwh_yr"]                    # kWh/yr
            dw_site = base["annual_withdrawal_ml"] - r["annual_withdrawal_ml"]
            dc_site = base["C_site_ml_yr"] - r["C_site_ml_yr"]       # ML/yr

            # 反转阈值：使全口径节水归零所需的电网水强度（L/kWh）
            ewif_star = None
            if de > 0:
                ewif_star = dw_site * 1e6 / de

            for ewif_name, ewif_fixed in EWIF_TIERS:
                ewif = ewif_fixed if ewif_fixed is not None else ewif_now
                f_base = base["annual_withdrawal_ml"] + base["E_kwh_yr"] * ewif / 1e6
                f_tech = r["annual_withdrawal_ml"] + r["E_kwh_yr"] * ewif / 1e6
                dF = f_base - f_tech                                  # ML/yr 全口径节水
                pct_site = (dw_site / base["annual_withdrawal_ml"] * 100
                            if base["annual_withdrawal_ml"] else None)
                pct_full = (dF / f_base * 100) if f_base else None

                for ef_name, ef in EF_TIERS:
                    dco2 = de * ef
                    rows.append({
                        "域签": label,
                        "冷却技术": r["technology"],
                        "PUE": round(float(r["mean_pue"]), 4),
                        "站点WUE_L_per_kWhIT": round(float(r["wue_l_kwh"]), 4),
                        "EWIF档位": ewif_name,
                        "EWIF_L_per_kWh": round(ewif, 4),
                        "电网碳强度档位": ef_name,
                        "EF_kgCO2e_per_kWh": ef,
                        "年设施能耗_kWh": round(float(r["E_kwh_yr"]), 0),
                        "站点取水_ML每年": round(float(r["annual_withdrawal_ml"]), 2),
                        "源端间接水_ML每年": round(float(r["E_kwh_yr"] * ewif / 1e6), 2),
                        "全口径水足迹_ML每年": round(float(f_tech), 2),
                        "站点口径节水百分比": None if pct_site is None else round(pct_site, 2),
                        "全口径节水百分比": None if pct_full is None else round(pct_full, 2),
                        "站点口径高估倍数": None if (pct_full in (None, 0) or pct_site is None)
                                          else round(pct_site / pct_full, 2),
                        "相对evaporative增碳_kgCO2e每年": round(dco2, 0),
                        "全口径每m3节水碳代价_kgCO2e": None if dF <= 0 else round(dco2 / dF / 1e3, 3),
                        "对照_供水碳强度1.14倍率": None if dF <= 0 else round(dco2 / dF / 1e3 / 1.14, 2),
                        "反转阈值EWIF_L_per_kWh": None if ewif_star is None else round(ewif_star, 2),
                        "EWIF是否足以反转": (None if ewif_star is None
                                       else ("是" if ewif >= ewif_star else "否")),
                    })

    out = pd.DataFrame(rows)
    out.to_csv(ART / "total_water_footprint_frontier_R7b.csv",
               index=False, encoding="utf-8-sig")

    print(f"[OK] {ART / 'total_water_footprint_frontier_R7b.csv'}  rows={len(out)}")

    # ---- 聚焦结论：GreenGrid_1.8 x 项目现值 EF=0.35 -----------------------
    print("\n=== 表一：全口径前沿（EWIF=1.8 Green Grid，EF=0.35）===")
    s = out[(out["EWIF档位"] == "GreenGrid_1.8") & (out["电网碳强度档位"] == "项目现值_0.350")]
    with pd.option_context("display.width", 300, "display.max_columns", 30):
        print(s[["域签", "冷却技术", "站点WUE_L_per_kWhIT", "站点取水_ML每年",
                 "源端间接水_ML每年", "全口径水足迹_ML每年",
                 "站点口径节水百分比", "全口径节水百分比", "站点口径高估倍数",
                 "全口径每m3节水碳代价_kgCO2e", "反转阈值EWIF_L_per_kWh",
                 "EWIF是否足以反转"]].to_string(index=False))

    print("\n=== 表二：干冷却在三种 EWIF 下的真实全口径节水（HA/CO）===")
    s2 = out[(out["冷却技术"] == "dry") & (out["电网碳强度档位"] == "项目现值_0.350")]
    with pd.option_context("display.width", 300, "display.max_columns", 30):
        print(s2[["域签", "EWIF档位", "站点口径节水百分比", "全口径节水百分比",
                  "站点口径高估倍数", "全口径每m3节水碳代价_kgCO2e",
                  "反转阈值EWIF_L_per_kWh", "EWIF是否足以反转"]].to_string(index=False))

    print("\n=== 表三：每 m3 全口径节水的碳代价在电网碳强度包络上的跨度（dry）===")
    s3 = out[(out["冷却技术"] == "dry") & (out["EWIF档位"] == "LBNL_4.52")]
    with pd.option_context("display.width", 300, "display.max_columns", 30):
        print(s3[["域签", "电网碳强度档位", "EF_kgCO2e_per_kWh",
                  "全口径节水百分比", "全口径每m3节水碳代价_kgCO2e",
                  "对照_供水碳强度1.14倍率"]].to_string(index=False))

    print("\n=== 结论 ===")
    for label in ("D-HA", "D-CO"):
        sub = out[(out["域签"] == label) & (out["EWIF是否足以反转"] == "是")]
        star = out[(out["域签"] == label)]["反转阈值EWIF_L_per_kWh"].dropna().unique()
        print(f"{label}: 发生全口径反转的组合数 = {len(sub)}；"
              f"反转阈值 EWIF* 集合 = {sorted(star)}")
    print("\n注：EWIF* > 4.52（观测上界）意味着在已知电力水强度包络内，"
          "干/混合冷却不可能抬高全流域总耗水——站点 WUE 口径却会显示 100% 节水。")


if __name__ == "__main__":
    sys.exit(main())
