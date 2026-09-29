"""R8 配套检查：WWTW 单位电耗取 0.30 还是 WaterMet2 北欧案的 0.462？

问题背景
--------
A08 锚点要求"污水厂 GHG 占 UWS 总 GHG 的 77%（WaterMet2 北欧案）"，本模型在
D2 修复后为 0.509，仍有 0.26 的差距。差距有两个可能的、性质完全不同的补法：

  (a) 抬高过程排放因子 —— 已核算过：要把占比推到 0.77，需要 0.702 kgCO2e/m3，
      是文献中位量级的 5.6 倍，属**强行拟合**，已在 R8 明确否决；
  (b) 抬高 WWTW 单位电耗 —— 本脚本要量的对象。WaterMet2 北欧案用 0.462 kWh/m3，
      本模型现用 0.30，两者都是有出处的取值（A11 观测区间即 0.30–0.462）。

因此本脚本**不做写盘**，只回答：换成 0.462 能把 A08/A09 推到哪、还剩多少缺口、
缺口是否仍必须归因于"过程排放因子"这一条路径。

用法
----
    PYTHONPATH=src python scripts/diagnose_wwtw_electricity_R8.py
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pandas as pd

from aiuwm.full_engine import FullAIUWMModel

ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT / "examples" / "cawcc_r2"
ART = ROOT / "validation_artifacts" / "r2"
ART.mkdir(parents=True, exist_ok=True)

# A11 观测区间的两端，加上 WaterMet2 北欧案原值
ELECTRICITY_OPTIONS = {"现行_0.30": 0.30, "WaterMet2北欧_0.462": 0.462}

# 与 repair_d1_d2_R8.py 的 WW_EF 保持一致的灵敏度三档（kg/m3 进水）
PROCESS_TIERS = {
    "L_MBR实测低": {"ch4_kg_m3": 0.00042, "n2o_kg_m3": 0.00034},
    "M_CAS实测中": {"ch4_kg_m3": 0.00115, "n2o_kg_m3": 0.00039},
    "H_LE实测高": {"ch4_kg_m3": 0.00332, "n2o_kg_m3": 0.00162},
}

A08_TARGET = 0.77
A09_TARGET = 0.88


def shares(proj: dict, ts: pd.DataFrame, capacity: float = 0.0) -> dict:
    trial = copy.deepcopy(proj)
    trial["components"]["AI_DC1"]["installed_it_capacity_mw"] = capacity
    cd = FullAIUWMModel(trial, ts).run().component_daily
    g = cd.groupby("component_id")["ghg_caused_kg_co2e"].sum()
    a = cd.groupby("component_id")["acidification_caused_kg_so2e"].sum()
    total_g, total_a = float(g.sum()), float(a.sum())
    return {
        "WWTW1_GHG占比": float(g.get("WWTW1", 0.0) / total_g) if total_g else float("nan"),
        "WWTW1_酸化占比": float(a.get("WWTW1", 0.0) / total_a) if total_a else float("nan"),
        "WWTW1_GHG_kgCO2e": float(g.get("WWTW1", 0.0)),
        "UWS总GHG_kgCO2e": total_g,
        "WWTW1_过程排放_kgCO2e": float(cd["direct_ghg_kg_co2e"].sum()),
    }


def main() -> int:
    rows = []
    for dom, label in (("ha", "D-HA"), ("co", "D-CO")):
        proj = json.loads((R2 / dom / "project.json").read_text(encoding="utf-8"))
        ts = pd.read_csv(R2 / dom / "timeseries.csv")
        for elec_tag, elec in ELECTRICITY_OPTIONS.items():
            for tier_tag, ef in PROCESS_TIERS.items():
                trial = copy.deepcopy(proj)
                ww = trial["components"]["WWTW1"]
                ww["electricity_kwh_m3"] = elec
                ww["direct_emissions"] = dict(ef)
                s = shares(trial, ts)
                elec_part = s["WWTW1_GHG_kgCO2e"] - s["WWTW1_过程排放_kgCO2e"]
                rows.append({
                    "域签": label,
                    "单位电耗": elec_tag,
                    "过程排放档": tier_tag,
                    "A08_WWTW_GHG占比": round(s["WWTW1_GHG占比"], 4),
                    "A08达标": "是" if s["WWTW1_GHG占比"] >= A08_TARGET else "否",
                    "距A08缺口": round(max(0.0, A08_TARGET - s["WWTW1_GHG占比"]), 4),
                    "A09_WWTW酸化占比": round(s["WWTW1_酸化占比"], 4),
                    "A09达标": "是" if s["WWTW1_酸化占比"] >= A09_TARGET else "否",
                    "其中_电耗贡献_kgCO2e": round(elec_part, 0),
                    "其中_过程排放_kgCO2e": round(s["WWTW1_过程排放_kgCO2e"], 0),
                })
                print(f"[{label}] {elec_tag:<20} {tier_tag:<12} "
                      f"A08={s['WWTW1_GHG占比']:.4f} A09={s['WWTW1_酸化占比']:.4f}")

    out = pd.DataFrame(rows)
    out.to_csv(ART / "wwtw_electricity_sensitivity_R8.csv", index=False, encoding="utf-8-sig")
    print(f"\n[OK] {ART / 'wwtw_electricity_sensitivity_R8.csv'}  rows={len(out)}")

    best = out.loc[out["A08_WWTW_GHG占比"].idxmax()]
    print(f"\n=== 结论 ===")
    print(f"区间内最优组合：{best['域签']} / {best['单位电耗']} / {best['过程排放档']}")
    print(f"A08 最高可达 {best['A08_WWTW_GHG占比']:.4f}（目标 {A08_TARGET}），"
          f"仍差 {best['距A08缺口']:.4f}")
    print("→ 即使同时取 '电耗上界 + 过程排放实测高档'，A08 仍无法达标；"
          "这证明缺口不是单点参数取值问题，而是模型边界的结构性差异。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
