"""R8：D2（污水处理过程排放缺失）的定量诊断与最小修复反演。

背景：`examples/cawcc_r2/{ha,co}/project.json` 的 WWTW1 没有 `direct_emissions`
字段，而 `full_engine._direct_wwtw_impacts()` 用 `direct.get("ch4_kg_m3", 0.0)`
等默认值 0 → **该组件的工艺过程排放恒为 0，全部 GHG 只来自电耗**。
后果：0 MW 无 AI 基线下 WWTW 占 UWS 已造成 GHG 的比仅为 0.30 量级，
而 WaterMet2 北欧案（锚点 A08）要求 >0.77。这直接压低了任何"改污水量"
干预的碳效应，也是历史上检不出"节水—增碳"权衡的机制原因。

修复路径是**纯配置**（引擎已支持 ch4_kg_m3 / n2o_kg_m3 / sludge_*），
本脚本负责把"需要多大"反演出来，并检查落在哪个文献区间。

产出：validation_artifacts/r2/wwtw_process_emission_inversion_R8.csv
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from aiuwm.full_engine import FullAIUWMModel

ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT / "examples" / "cawcc_r2"
ART = ROOT / "validation_artifacts" / "r2"

# 锚点：WaterMet2 北欧案 §S4 —— WWTW 对 UWS GHG 的贡献
A08_TARGET = 0.77
# 同一来源的结构分解：UWS 总 GHG 中 N2O（来自 WWTW）占 36%，CO2 约 50%
A08_N2O_SHARE_OF_TOTAL = 0.36
GWP = {"ch4": 25.0, "n2o": 298.0}  # IPCC 2006 GWP100，与 WaterMet2 同一套


def run_zero(project_file: Path, ts: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    proj = json.loads(project_file.read_text(encoding="utf-8"))
    proj["components"]["AI_DC1"]["installed_it_capacity_mw"] = 0.0
    res = FullAIUWMModel(proj, ts).run()
    return res.component_daily, res


def main() -> None:
    rows = []
    for dom, label in (("ha", "D-HA"), ("co", "D-CO")):
        ts = pd.read_csv(R2 / dom / "timeseries.csv")
        proj = json.loads((R2 / dom / "project.json").read_text(encoding="utf-8"))
        proj["components"]["AI_DC1"]["installed_it_capacity_mw"] = 0.0
        result = FullAIUWMModel(proj, ts).run()
        cd = result.component_daily

        print(f"\n=== {label} component_daily 列 ===")
        print(list(cd.columns))

        g = cd.groupby("component_id")
        ghg = g["ghg_caused_kg_co2e"].sum()
        total = ghg.sum()
        wwtw = float(ghg.get("WWTW1", 0.0))

        # WWTW 处理量：优先用 IPv flow 列，没有则退回 electricity 反演
        treated_ml = float("nan")
        for cand in ("inflow_ml", "throughput_ml", "treated_ml", "flow_ml", "activity_ml"):
            if cand in cd.columns:
                treated_ml = float(g[cand].sum().get("WWTW1", 0.0))
                break
        elec_col = "electricity_kwh" if "electricity_kwh" in cd.columns else None
        treated_recovered = float("nan")
        if elec_col:
            kwh = float(g[elec_col].sum().get("WWTW1", 0.0))
            ef = float(proj["components"]["WWTW1"]["electricity_kwh_m3"])
            treated_recovered = kwh / ef / 1e3  # kWh -> m3 -> ML

        share = wwtw / total if total else float("nan")

        # 反演：需要多大的过程排放 X 才能把 WWTW 占比抬到 target
        #   (wwtw + X) / (total + X) = target
        #   X = (target*total - wwtw) / (1 - target)
        need = (A08_TARGET * total - wwtw) / (1.0 - A08_TARGET)
        vol = treated_ml if pd.notna(treated_ml) else treated_recovered
        need_per_m3 = need / (vol * 1e3) if vol and pd.notna(vol) else float("nan")

        rows.append({
            "域签": label,
            "0MW基线UWS总已造成GHG_kgCO2e": round(total, 1),
            "WWTW1已造成GHG_kgCO2e": round(wwtw, 1),
            "WWTW1占比_现状": round(share, 4),
            "A08锚点下界": A08_TARGET,
            "缺口_相对百分比": round((share - A08_TARGET) / A08_TARGET * 100, 2),
            "WWTW1处理量_ML": None if pd.isna(vol) else round(vol, 1),
            "达标所需过程排放_kgCO2e": round(need, 1),
            "达标所需单位强度_kgCO2e每m3": None if pd.isna(need_per_m3) else round(need_per_m3, 4),
            "等效n2o_kg每m3": None if pd.isna(need_per_m3) else round(need_per_m3 / GWP["n2o"], 6),
        })

        print(f"\n--- {label} 0 MW 基线 分量 GHG（前 8）---")
        print(ghg.sort_values(ascending=False).head(8).round(1).to_string())

    out = pd.DataFrame(rows)
    out.to_csv(ART / "wwtw_process_emission_inversion_R8.csv",
               index=False, encoding="utf-8-sig")
    with pd.option_context("display.width", 260, "display.max_columns", 20):
        print("\n" + out.to_string(index=False))
    print(f"\n[OK] {ART / 'wwtw_process_emission_inversion_R8.csv'}")

    print("\n=== 组合口径结构校验 ===")
    for r in rows:
        need_total = r["达标所需单位强度_kgCO2e每m3"]
        if need_total is None:
            continue
        # WaterMet2：UWS 总 GHG 中 N2O(WWTW) 占 36%；WWTW 合计 >77%
        n2o_part_total = r["0MW基线UWS总已造成GHG_kgCO2e"] * A08_N2O_SHARE_OF_TOTAL
        print(f"{r['域签']}: 若按 N2O 单项占 UWS 总量 36% 反推，"
              f"N2O 过程排放应为 {n2o_part_total:,.0f} kgCO2e，"
              f"而达标 0.77 所需的总过程排放为 {r['达标所需过程排放_kgCO2e']:,.0f} kgCO2e")
        print(f"   → 两者之比 = {n2o_part_total / r['达标所需过程排放_kgCO2e']:.2f}"
              f"（若 >1 说明仅 N2O 一项就已超过达标所需，即 CH4 必须为 0 且电耗项需下调）")


if __name__ == "__main__":
    main()
