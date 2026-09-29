"""R8：D1（厂外电力水强度）与 D2（污水处理过程排放缺失）的联合修复。

设计前提（已验证）
------------------
CAWCC 的 11 条约束（system_reliability_fraction / domestic_unmet_ml /
unmet_cooling_water_ml / max_*_utilization / max_source_abstraction_ratio /
reclaimed_water_substitution_ratio / peak_capacity_ratio /
max_local_connection_ratio / max_daily_average_grid_connection_ratio）
**全部基于水流量与利用率，没有一条引用 ghg_* 或 offsite_electricity_water_ml**。
因此修复 D1/D2 在结构上不可能改变任何容量阈值。

本脚本的写操作只对 AI_DC1.offsite_electricity_water_intensity_l_kwh、
WWTW1.electricity_kwh_m3 与 WWTW1.direct_emissions 生效，**先验证、后落盘**：只有当新老配置在各关键容量点上的
约束数值逐位一致时，才真正写入 project.json。

外部锚点（本轮新增，均带来源）
----------------------------
D1 电力水强度 EWIF（A20）
    HA → 4.52 L/kWh = LBNL 2024 间接水足迹反演值（观测上界）
    CO → 1.80 L/kWh = Green Grid White Paper #35（美国平均）
    保留原有的 HA > CO 域间强弱关系，但现在两端都有出处；原值 0.40/0.18 无来源。

D2 污水处理厂「全流程直接排放」实测（A21）
    以 g/CH4 per m3 进水 与 g/N2O per m3 进水 给出，均为全流程实测：
      L 低（MBR 膜法，全流程实测）   CH4 0.42  g/m3、N2O 0.34  g/m3
      M 中（常规活性污泥法 CAS）     CH4 1.15  g/m3、N2O 0.39  g/m3   ★默认
      H 高（Ludzack-Ettinger 工艺）  CH4 3.32  g/m3、N2O 1.62  g/m3
    来源：同一张综述表内的三组全流程实测（Masuda et al. 2015；Daelman et al. 2013；
    MBR 全流程多点采样研究）。另有 Mannina et al. 2019 情景模拟给出 0.140–0.940
    kgCO2e/m3，作为上限背景参考。

GWP：保持 IPCC 2006 GWP100（CO2=1、CH4=25、N2O=298），与 WaterMet2 完全一致，
     保证锚点 A08 可比；同时在配置里显式写出，避免依赖引擎默认值被日后改动。
     痏注意：原文用 AR5 GWP 报告的合计值与本 Rob 口径会有小幅差异，属预期。

产出：validation_artifacts/r2/d1_d2_repair_verification_R8.csv
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pandas as pd

from aiuwm.ai_capacity import scan_ai_capacity
from aiuwm.full_engine import FullAIUWMModel

ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT / "examples" / "cawcc_r2"
ART = ROOT / "validation_artifacts" / "r2"

# --- A20：每个域的新 EWIF -------------------------------------------------
# 两域统一取 Green Grid WP#35 记载的美国平均 1.80 L/kWh：
#   · 原值的 HA/CO 差异（0.40 vs 0.18）本身无文献出处，属臆造对比，撤回；
#     HA/CO 的域间差异由气候与水资源条件承载（时间序列与约束），不靠 EWIF 拆分。
#   · 4.52（LBNL 2024）作为**灵敏度上界**而非基线配置，避免全篇建在极端值上。
NEW_EWIF = {"ha": 1.80, "co": 1.80}

# 修复前的原始取值。脚本可重复运行；若只看"文件中上一状态"，
# 第二次运行起基线图景会失真，因此这里显式重建原始状态作为对照基准。
OLD_EWIF = {"ha": 0.40, "co": 0.18}

# R8 修复前 WWTW 的单位电耗。该字段后来从 0.30 更新为 0.462 kWh/m3；
# 若不在历史对照中显式回退，修复前/后差分会把 D2 排放修复与电耗更新混在一起。
OLD_WWTW_ELECTRICITY_KWH_M3 = 0.30

# --- A21：WWTW 全流程直接排放三档（kg/m3 进水） ---------------------------
# 注意：键名必须与 full_engine._direct_wwtw_impacts() 读取的一致。
# 该处用 direct.get("ch4_kg_m3") / direct.get("n2o_kg_m3")，写成 "ch4" 会静默取 0。
WW_EF = {
    "L_MBR实测低": {"ch4_kg_m3": 0.00042, "n2o_kg_m3": 0.00034},
    "M_CAS实测中": {"ch4_kg_m3": 0.00115, "n2o_kg_m3": 0.00039},
    "H_LE实测高": {"ch4_kg_m3": 0.00332, "n2o_kg_m3": 0.00162},
}
DEFAULT_TIER = "M_CAS实测中"

GWP100 = {"co2": 1, "ch4": 25, "n2o": 298}
PROBE_CAPS = {"ha": [1100.0, 1150.0, 1300.0], "co": [1400.0, 1450.0, 1500.0]}


def load(domain: str) -> tuple[dict, pd.DataFrame]:
    proj = json.loads((R2 / domain / "project.json").read_text(encoding="utf-8"))
    ts = pd.read_csv(R2 / domain / "timeseries.csv")
    return proj, ts


def original(domain: str) -> dict:
    """重建 R8 修复前的原始配置（与当前文件状态无关）。"""
    proj, _ = load(domain)
    proj["components"]["AI_DC1"]["offsite_electricity_water_intensity_l_kwh"] = OLD_EWIF[domain]
    proj["components"]["WWTW1"]["electricity_kwh_m3"] = OLD_WWTW_ELECTRICITY_KWH_M3
    proj["components"]["WWTW1"].pop("direct_emissions", None)
    proj.pop("characterisation", None)
    return proj


def patched(domain: str, tier: str = DEFAULT_TIER) -> dict:
    proj, _ = load(domain)
    proj["components"]["AI_DC1"]["offsite_electricity_water_intensity_l_kwh"] = NEW_EWIF[domain]
    proj["components"]["WWTW1"]["direct_emissions"] = dict(WW_EF[tier])
    proj["characterisation"] = {"gwp100": dict(GWP100)}
    return proj


def wwtw_share(proj: dict, ts: pd.DataFrame, capacity: float) -> dict:
    trial = copy.deepcopy(proj)
    trial["components"]["AI_DC1"]["installed_it_capacity_mw"] = capacity
    cd = FullAIUWMModel(trial, ts).run().component_daily
    g = cd.groupby("component_id")["ghg_caused_kg_co2e"].sum()
    return {
        "UWS总已造成GHG_kgCO2e": float(g.sum()),
        "WWTW1_kgCO2e": float(g.get("WWTW1", 0.0)),
        "WWTW1占比": float(g.get("WWTW1", 0.0) / g.sum()) if g.sum() else float("nan"),
        "WWTW1过程排放_kgCO2e": float(cd["direct_ghg_kg_co2e"].sum()),
    }


def main() -> int:
    rows = []
    write_ok = True

    for dom, label in (("ha", "D-HA"), ("co", "D-CO")):
        proj = original(dom)      # 修复前原始状态作为对照基准
        ts = pd.read_csv(R2 / dom / "timeseries.csv")
        new_proj = patched(dom)   # 修复后目标状态
        old_ewif = OLD_EWIF[dom]
        old_direct = "（缺失→0）"

        # ---- 校验 1：CAWCC 约束数值必须逐位一致 -------------------------
        for cap in PROBE_CAPS[dom]:
            old_cap = copy.deepcopy(proj)
            old_cap["components"]["AI_DC1"]["installed_it_capacity_mw"] = cap
            new_cap = copy.deepcopy(new_proj)
            new_cap["components"]["AI_DC1"]["installed_it_capacity_mw"] = cap
            a = scan_ai_capacity(old_cap, ts, capacities_mw=[cap])
            b = scan_ai_capacity(new_cap, ts, capacities_mw=[cap])
            # 只比对 specs/constraints_<domain>.json 中明确列出的那 11 条约束。
            # 不要用"所有数值列"做比对——足迹类指标（间接水、系统碳）在 D1/D2
            # 修复下本应改变，否则会永远 FAIL（本脚本第一版就犯了这个错）。
            spec_keys = list(json.loads(
                (R2 / "specs" / f"constraints_{dom}.json").read_text(
                    encoding="utf-8"))["constraints"].keys())
            shared = [c for c in spec_keys if c in a.columns and c in b.columns]
            missing = [c for c in spec_keys if c not in a.columns]
            diffs = []
            for c in shared:
                d = abs(float(a[c].iloc[0]) - float(b[c].iloc[0]))
                if d > 1e-9:
                    diffs.append((c, d))
            ok = not diffs
            write_ok &= ok
            rows.append({
                "域签": label, "IT容量_MW": cap, "校验": "CAWCC约束数值一致性",
                "比较列数": len(shared),
                "最大偏差": 0.0 if ok else max(d for _, d in diffs),
                "不一致列": "" if ok else ",".join(c for c, _ in diffs),
                "结论": ("PASS" if ok else "FAIL")
                        + (f"（{len(missing)} 条约束不在输出列中）" if missing else ""),
            })

        # ---- 校验 2：0 MW 基线 WWTW 占比（三档 vs 修复前） --------------
        before = wwtw_share(proj, ts, 0.0)
        for tier, ef in WW_EF.items():
            tier_proj = patched(dom, tier)
            after = wwtw_share(tier_proj, ts, 0.0)
            rows.append({
                "域签": label, "IT容量_MW": 0.0,
                "校验": f"0MW基线WWTW占比@{tier}",
                "比较列数": 1,
                "最大偏差": round(after["WWTW1占比"] - before["WWTW1占比"], 4),
                "不一致列": f"修复前{before['WWTW1占比']:.4f} → 修复后{after['WWTW1占比']:.4f}",
                "结论": f"A08下界0.77 {'达成' if after['WWTW1占比'] >= 0.77 else '未达成'}",
            })

        # ---- 校验 3：AI 侧间接水占总水足迹比（EWIF 修复前后） -----------
        for tag, proj_variant in (("修复前", proj), ("修复后", new_proj)):
            trial = copy.deepcopy(proj_variant)
            trial["components"]["AI_DC1"]["installed_it_capacity_mw"] = 1000.0
            dcd = FullAIUWMModel(trial, ts).run().data_center_daily
            site = float(dcd["external_withdrawal_ml"].sum())
            off = float(dcd["offsite_electricity_water_ml"].sum())
            rows.append({
                "域签": label, "IT容量_MW": 1000.0,
                "校验": f"间接水占AI总水足迹比（{tag}）",
                "比较列数": 1,
                "最大偏差": round(off / (site + off), 4) if (site + off) else None,
                "不一致列": f"EWIF={proj_variant['components']['AI_DC1']['offsite_electricity_water_intensity_l_kwh']}"
                          f"；场地{site:,.0f} ML / 源端{off:,.0f} ML",
                "结论": f"间接占比 {off / (site + off) * 100:.1f}%" if (site + off) else "无流量",
            })

        print(f"\n=== {label} ===")
        print(f"  EWIF: {old_ewif} → {NEW_EWIF[dom]}")
        print(f"  WWTW1.direct_emissions: {old_direct or '（缺失→0）'} → {WW_EF[DEFAULT_TIER]}")

    out = pd.DataFrame(rows)
    out.to_csv(ART / "d1_d2_repair_verification_R8.csv",
               index=False, encoding="utf-8-sig")
    with pd.option_context("display.width", 280, "display.max_columns", 20,
                           "display.max_colwidth", 60):
        print("\n" + out.to_string(index=False))
    print(f"\n[OK] {ART / 'd1_d2_repair_verification_R8.csv'}  rows={len(out)}")

    fails = out[out["结论"] == "FAIL"]
    print(f"\n=== 写盘判定 ===  失败项 {len(fails)} 条")
    if len(fails) or not write_ok:
        print("❌ CAWCC 约束在新配置下发生变化，已终止修复（未写入任何文件）")
        return 1

    for dom in ("ha", "co"):
        path = R2 / dom / "project.json"
        proj = json.loads(path.read_text(encoding="utf-8"))
        proj["components"]["AI_DC1"]["offsite_electricity_water_intensity_l_kwh"] = NEW_EWIF[dom]
        proj["components"]["WWTW1"]["direct_emissions"] = dict(WW_EF[DEFAULT_TIER])
        proj["characterisation"] = {"gwp100": dict(GWP100)}
        path.write_text(json.dumps(proj, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
