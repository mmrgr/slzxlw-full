"""水—能—碳—社会联合指标（对应外部建议 7）。

建议 7 的验收目标：每项干预至少有**水、能、碳、社会可靠度**四类指标，
对每项干预报告 Pareto 前沿，**禁止只凭"节水"或"增加 MW"宣布干预优越**。

现状缺口（已核）：`intervention_cost_benefit.csv` 只有 CAWCC 增益、成本、
居民未满足量（社会），**缺能源与碳**。本脚本补齐，并把水足迹拆成
**直接（现场取水）** 与 **间接（源端电力耗水）** 两部分——这正是外部建议引用
的数据中心水研究反复强调的测量边界。

所有指标统一在 **baseline 的 CAWCC 容量点** 实测（与 `run_r2_cost_pareto.py`
第 280–302 行同口径），否则不同容量下不可比。

用法：
    PYTHONPATH=src python scripts/build_intervention_wec.py
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aiuwm.full_engine import FullAIUWMModel  # noqa: E402

R2 = ROOT / "examples" / "cawcc_r2"
OUTDIR = ROOT / "validation_artifacts" / "r2"
OUT = OUTDIR / "intervention_water_energy_carbon.csv"


def extract(result) -> dict:
    """从一次 run 提取四类指标。缺列时返回 None 而非崩溃，最后如实标 gap。"""
    sys_df = result.system_daily if getattr(result, "system_daily", None) is not None else pd.DataFrame()
    dc_df = (
        result.data_center_daily
        if getattr(result, "data_center_daily", None) is not None
        else pd.DataFrame()
    )
    area_df = result.area_daily if getattr(result, "area_daily", None) is not None else pd.DataFrame()

    def col(df: pd.DataFrame, name: str):
        return float(df[name].sum()) if not df.empty and name in df.columns else None

    direct = col(dc_df, "external_withdrawal_ml")          # AI 现场直接取水
    indirect = col(dc_df, "offsite_electricity_water_ml")  # 源端电力间接水足迹

    # 城市侧水足迹：送达 + 管网损失。降漏损类干预会直接反映在这一项上，
    # 而 AI 侧取水（上两项）对城市侧干预不敏感——这正是必须拆开报告的原因。
    delivered = col(sys_df, "delivered_ml")
    loss = col(sys_df, "loss_ml")
    city_total = None if (delivered is None or loss is None) else delivered + loss

    return {
        "AI直接取水_ML": direct,
        "AI间接水足迹_ML": indirect,
        "AI总水足迹_ML": None if (direct is None or indirect is None) else direct + indirect,
        "城市供给加损失_ML": city_total,
        "能耗_kWh": col(sys_df, "electricity_kwh"),
        "碳排_kgCO2e": col(sys_df, "ghg_net_kg_co2e"),
        "居民未满足量_ML": col(area_df, "unmet_domestic_ml"),
    }


def main() -> int:
    rows: list[dict] = []
    missing: set[str] = set()

    for domain in ("ha", "co"):
        project = json.loads((R2 / domain / "project.json").read_text(encoding="utf-8"))
        timeseries = pd.read_csv(R2 / domain / "timeseries.csv")
        specs = json.loads((R2 / "specs" / f"interventions_{domain}.json").read_text(encoding="utf-8"))
        marginal_path = OUTDIR / domain / "intervention_marginal.csv"
        if not marginal_path.exists():
            print(f"跳过 {domain}：缺少 {marginal_path}")
            continue
        marginal = pd.read_csv(marginal_path)
        baseline_cawcc = float(
            marginal.loc[marginal["intervention"] == "baseline", "maximum_safe_ai_capacity_mw"].iloc[0]
        )

        results: dict[str, dict] = {}
        for item in specs["interventions"]:
            trial = copy.deepcopy(project)
            for component in trial["components"].values():
                if component.get("kind") == "data_center":
                    component["installed_it_capacity_mw"] = baseline_cawcc
                    component.pop("capacity_schedule", None)
            for entry in item["set"]:
                target = trial
                parts = entry["path"].split(".")
                for part in parts[:-1]:
                    target = target[part]
                target[parts[-1]] = entry["value"]
            trial.pop("interventions", None)
            trial.pop("pipeline_events", None)
            metrics = extract(FullAIUWMModel(trial, timeseries).run())
            results[item["name"]] = metrics
            print(f"[{domain}] {item['name']} 已跑", flush=True)

        base = results.get("baseline", {})
        # 权衡判定必须用「相对变化」阈值。基线 CAWCC 是未受压工况点，
        # 多数城市侧干预对流量毫无影响、Δ 恰为 0；若仅凭 Δ<=0 就判"双赢"，
        # 会把"没变化"误报成"改善"。
        REL_TOL = 1e-4

        for name, metrics in results.items():
            row: dict = {"域": domain, "干预": name, "容量点_MW": baseline_cawcc}
            gain_row = marginal.loc[marginal["intervention"] == name]
            row["CAWCC增益_MW"] = (
                float(gain_row["maximum_safe_ai_capacity_mw"].iloc[0]) - baseline_cawcc
                if not gain_row.empty
                else None
            )
            for key, value in metrics.items():
                row[key] = value
                if value is None:
                    missing.add(key)
                    continue
                baseline_value = base.get(key)
                row[f"Δ{key}"] = (
                    None if baseline_value is None else round(value - baseline_value, 6)
                )
            rows.append(row)

        # 权衡标注：节水但增碳 / 增容量但恶化居民供水。
        # 只在「相对基线的变化幅度超过阈值」时才标注，避免把"无变化"误报为"改善"。
        for row in [r for r in rows if r["域"] == domain]:
            tags: list[str] = []

            def moved(key: str) -> bool | None:
                delta = row.get(f"Δ{key}")
                baseline_value = base.get(key)
                if delta is None or baseline_value is None:
                    return None
                if abs(float(baseline_value)) < 1e-12:
                    return None
                return abs(float(delta)) > REL_TOL * abs(float(baseline_value))

            d_city_water = row.get("Δ城市供给加损失_ML")
            d_ai_water = row.get("ΔAI总水足迹_ML")
            d_carbon = row.get("Δ碳排_kgCO2e")
            gain = row.get("CAWCC增益_MW")
            social = row.get("Δ居民未满足量_ML")

            carbon_moved = moved("碳排_kgCO2e")
            city_moved = moved("城市供给加损失_ML")

            if city_moved is True and carbon_moved is True:
                if (d_city_water or 0) < 0 and (d_carbon or 0) > 0:
                    tags.append("节水但增碳★权衡")
                elif (d_city_water or 0) > 0 and (d_carbon or 0) < 0:
                    tags.append("减碳但增取水★权衡")
                elif (d_city_water or 0) < 0 and (d_carbon or 0) < 0:
                    tags.append("水碳双赢")
            if carbon_moved is True and (d_carbon or 0) < 0:
                tags.append("碳排下降")
            if city_moved is True and (d_city_water or 0) < 0:
                tags.append("城市取水下降")
            if city_moved is False:
                tags.append("城市侧水足迹无变化")
            if d_ai_water is not None and abs(d_ai_water) > 1e-9:
                tags.append("AI水足迹变化")
            else:
                tags.append("AI水足迹无变化")
            if gain is not None and gain > 0 and social is not None and social > 1e-9:
                tags.append("增容量但恶化居民供水★权衡")
            row["权衡标记"] = "；".join(tags) if tags else "无显著变化"

    if not rows:
        print("未能生成任何行")
        return 1

    frame = pd.DataFrame(rows)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"\nwritten -> {OUT}  ({len(frame)} 行)")

    if missing:
        print(f"⚠️ 以下指标在模型中不可用，已如实留空：{sorted(missing)}")
    else:
        print("✅ 水/能/碳/社会四类指标全部可用")

    flagged = frame[frame["权衡标记"] != "无显著权衡"]
    print(f"\n检出存在权衡的干预 {len(flagged)} 项：")
    for _, row in flagged.iterrows():
        print(f"  [{row['域']}] {row['干预']}: {row['权衡标记']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
