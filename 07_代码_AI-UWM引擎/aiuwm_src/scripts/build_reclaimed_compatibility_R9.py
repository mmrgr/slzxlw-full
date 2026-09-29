"""R9: 再生水兼容性、用户置换与城市淡水取水的联合审计。

R8 已在固定 1000 MW、固定水质参数下证明了 ``再生水比例↑ → CoC↓ /
总取水与排污↑`` 的单域单调链。本脚本不把该结果扩大成“净节水”，而是
沿同一条 0--0.9 配置轴同时记录：

* AI 园区按水源拆分的取水量；
* 无 AI 基线与同一 AI 负荷、目标比例为 0 的两个反事实；
* AI 直接 potable 减少、其他用户 potable 增加、城市水源取水变化；
* WWTW 进水、直接过程温室气体与总污水负荷变化。

这是 R9 的证据层，不改变模型方程，也不引入未经参数审计的新水质范围。
质量耦合审计显式关闭冷却储水（容量和初始库存均为 0），使求解器的期初中央
回用池可交付量对应当天过程补水；若保留冷却储水，库存水质未建模，不能把
solver fraction 当作实际进入冷却回路的水质份额。该脚本仍不把结果写成现实
城市交付水质验证。
不将 AI 毛取水减去城市水源取水增量的旧公式称作“净节水”：它把园区取水
与城市水源取水混成不同边界的流量，且基准端点并非无 AI 情景。R9 改为并列
报告 AI 与城市用户的 potable 交付、城市源水取水差分。
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from aiuwm.full_engine import FullAIUWMModel

ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT / "examples" / "cawcc_r2"
ART = ROOT / "validation_artifacts" / "r2"
ART.mkdir(parents=True, exist_ok=True)

SWEEP = [round(i / 10, 1) for i in range(10)]
CAP_MW = 1000.0
DOMAINS = (("ha", "D-HA"), ("co", "D-CO"))


def _sum_component(result: Any, component_id: str, column: str) -> float:
    frame = result.component_daily
    if frame.empty or column not in frame:
        return 0.0
    return float(frame.loc[frame["component_id"] == component_id, column].sum())


def _potable_source_id(project: dict[str, Any]) -> str:
    """Return the first potable water resource in the active supply chain."""
    for path in project.get("supply_paths", []):
        for component_id in path.get("chain", []):
            component = project.get("components", {}).get(component_id, {})
            if component.get("kind") == "water_resource":
                return component_id
    raise ValueError("supply_paths 中没有可识别的 potable water_resource")


def _run(project: dict[str, Any], timeseries: pd.DataFrame, capacity_mw: float,
         reclaimed_target: float) -> tuple[Any, dict[str, float]]:
    trial = copy.deepcopy(project)
    dc = trial["components"]["AI_DC1"]
    dc["installed_it_capacity_mw"] = capacity_mw
    # Clear both accepted capacity aliases; otherwise a project using the
    # explicit alias would silently retain a nonzero cooling buffer and skip
    # the same-day quality fixed-point evidence gate below.
    dc["cooling_storage_capacity_ml"] = 0.0
    dc["cooling_storage_ml"] = 0.0
    dc["initial_cooling_storage_ml"] = 0.0
    sources = dc["water_sources"]
    sources["reclaimed"]["target_fraction"] = reclaimed_target
    sources["potable"]["target_fraction"] = 1.0 - reclaimed_target
    result = FullAIUWMModel(trial, timeseries).run()
    daily = result.data_center_daily
    if daily.empty:
        raise ValueError("AI_DC1 没有产生 data_center_daily 输出")
    # R9 deliberately disables cooling storage, so every positive reclaimed
    # target must be backed by a converged same-day fixed-point solve.  Keep
    # this as a hard evidence gate rather than inferring convergence from the
    # returned reclaimed fraction alone.
    if reclaimed_target > 0.0:
        required = {
            "quality_solver_status",
            "quality_solver_residual",
            "quality_solver_root_count",
        }
        missing = required.difference(daily.columns)
        if missing:
            raise ValueError(f"R9 缺少固定点审计字段: {sorted(missing)}")
        statuses = set(daily["quality_solver_status"].astype(str))
        residual = pd.to_numeric(daily["quality_solver_residual"], errors="coerce")
        roots = pd.to_numeric(daily["quality_solver_root_count"], errors="coerce")
        if statuses != {"converged"} or not np.isfinite(residual).all() or (
            residual.abs() > 1e-10
        ).any() or not (roots == 1).all():
            raise ValueError(
                "R9 固定点审计失败: "
                f"statuses={sorted(statuses)}, "
                f"max_abs_residual={residual.abs().max()}, "
                f"root_counts={sorted(roots.dropna().unique().tolist())}"
            )
    city_source = _potable_source_id(trial)
    ai_potable = float(daily["potable_water_ml"].sum())
    city_potable = float(result.area_daily["potable_delivered_ml"].sum())
    other_potable = max(0.0, city_potable - ai_potable)
    values = {
        "ai_potable_ml": ai_potable,
        "ai_reclaimed_ml": float(daily["reclaimed_water_ml"].sum()),
        "ai_other_ml": float(daily["other_water_ml"].sum()),
        "ai_withdrawal_ml": float(daily["external_withdrawal_ml"].sum()),
        "ai_actual_reclaimed_fraction": (
            float(daily["reclaimed_water_ml"].sum())
            / float(daily["external_withdrawal_ml"].sum())
            if float(daily["external_withdrawal_ml"].sum()) else 0.0
        ),
        "ai_quality_solver_reclaimed_fraction": (
            float((daily["quality_solver_reclaimed_fraction"] * daily["external_makeup_ml"]).sum())
            / float(daily["external_makeup_ml"].sum())
            if "quality_solver_reclaimed_fraction" in daily
            and float(daily["external_makeup_ml"].sum()) else 0.0
        ),
        "quality_solver_converged_days": int(
            (daily.get("quality_solver_status", pd.Series(dtype=str)) == "converged").sum()
        ),
        "quality_solver_max_abs_residual": float(
            pd.to_numeric(
                daily.get("quality_solver_residual", pd.Series(dtype=float)),
                errors="coerce",
            ).abs().max()
        ) if "quality_solver_residual" in daily else float("nan"),
        "ai_consumption_ml": float(daily["consumption_ml"].sum()),
        "ai_blowdown_ml": float(daily["blowdown_ml"].sum()),
        "ai_return_flow_ml": float(daily["return_flow_ml"].sum()),
        "ai_mean_coc": float(daily["cycles_of_concentration"].mean()),
        "ai_quality_fallback_days": float(daily["quality_coc_fallback"].sum()),
        "city_total_potable_delivered_ml": city_potable,
        "other_users_potable_delivered_ml": other_potable,
        "city_potable_abstraction_ml": _sum_component(result, city_source, "outflow_ml"),
        "wwtw_inflow_ml": _sum_component(result, "WWTW1", "inflow_ml"),
        "wwtw_treated_ml": _sum_component(result, "WWTW1", "treated_ml"),
        "wwtw_direct_ghg_kg_co2e": _sum_component(result, "WWTW1", "direct_ghg_kg_co2e"),
        "wwtw_ghg_kg_co2e": _sum_component(result, "WWTW1", "ghg_caused_kg_co2e"),
    }
    return result, values


def main() -> int:
    rows: list[dict[str, Any]] = []
    verdicts: list[dict[str, Any]] = []
    for domain, label in DOMAINS:
        project = json.loads((R2 / domain / "project.json").read_text(encoding="utf-8"))
        timeseries = pd.read_csv(R2 / domain / "timeseries.csv")
        _baseline_result, baseline = _run(project, timeseries, 0.0, 0.0)
        baseline_city = baseline["city_potable_abstraction_ml"]
        baseline_wwtw = baseline["wwtw_inflow_ml"]
        baseline_wwtw_direct = baseline["wwtw_direct_ghg_kg_co2e"]
        baseline_other_potable = baseline["other_users_potable_delivered_ml"]

        domain_rows: list[dict[str, Any]] = []
        for target in SWEEP:
            _result, values = _run(project, timeseries, CAP_MW, target)
            city_delta = values["city_potable_abstraction_ml"] - baseline_city
            row = {
                "domain": label,
                "capacity_mw": CAP_MW,
                "target_reclaimed_fraction": target,
                **values,
                "city_potable_abstraction_delta_ml": city_delta,
                "other_users_potable_change_vs_no_ai_ml": (
                    values["other_users_potable_delivered_ml"] - baseline_other_potable
                ),
                "wwtw_inflow_delta_ml": values["wwtw_inflow_ml"] - baseline_wwtw,
                "wwtw_direct_ghg_delta_kg_co2e": (
                    values["wwtw_direct_ghg_kg_co2e"] - baseline_wwtw_direct
                ),
            }
            domain_rows.append(row)
            rows.append(row)

        # B2: same AI load with zero reclaimed-water target.  This is the
        # counterfactual needed to separate the AI's direct potable reduction
        # from the city-scale displacement caused by reallocating an existing
        # reuse pool.  It must not be conflated with the no-AI baseline above.
        b2 = domain_rows[0]
        for row in domain_rows:
            row["ai_potable_reduction_vs_r0_ml"] = b2["ai_potable_ml"] - row["ai_potable_ml"]
            row["other_users_potable_increase_vs_r0_ml"] = (
                row["other_users_potable_delivered_ml"] - b2["other_users_potable_delivered_ml"]
            )
            row["city_source_abstraction_change_vs_r0_ml"] = (
                row["city_potable_abstraction_ml"] - b2["city_potable_abstraction_ml"]
            )
            row["city_source_abstraction_increase_vs_no_ai_ml"] = row["city_potable_abstraction_delta_ml"]
            # Sweep effects use the same-AI r=0 counterfactual (B2).  The
            # existing B0 deltas remain separate no-AI accounting quantities.
            row["city_total_potable_change_vs_r0_ml"] = (
                row["city_total_potable_delivered_ml"] - b2["city_total_potable_delivered_ml"]
            )
            row["wwtw_inflow_change_vs_r0_ml"] = row["wwtw_inflow_ml"] - b2["wwtw_inflow_ml"]
            row["wwtw_treated_change_vs_r0_ml"] = row["wwtw_treated_ml"] - b2["wwtw_treated_ml"]
            row["wwtw_direct_ghg_change_vs_r0_kg_co2e"] = (
                row["wwtw_direct_ghg_kg_co2e"] - b2["wwtw_direct_ghg_kg_co2e"]
            )
            row["wwtw_ghg_change_vs_r0_kg_co2e"] = (
                row["wwtw_ghg_kg_co2e"] - b2["wwtw_ghg_kg_co2e"]
            )
            reduction = row["ai_potable_reduction_vs_r0_ml"]
            row["city_abstraction_increase_per_ai_potable_reduced"] = (
                row["city_source_abstraction_change_vs_r0_ml"] / reduction
                if reduction else 0.0
            )

        low, high = domain_rows[0], domain_rows[-1]
        verdicts.append({
            "domain": label,
            "ai_potable_reduction_at_0.9_ml": high["ai_potable_reduction_vs_r0_ml"],
            "other_users_potable_increase_at_0.9_ml": high["other_users_potable_increase_vs_r0_ml"],
            "city_source_abstraction_increase_at_0.9_vs_r0_ml": high["city_source_abstraction_change_vs_r0_ml"],
            "city_source_abstraction_increase_at_0.9_vs_no_ai_ml": high["city_source_abstraction_increase_vs_no_ai_ml"],
            "other_users_potable_change_at_0.9_vs_no_ai_ml": high["other_users_potable_change_vs_no_ai_ml"],
            "ai_potable_reduction_vs_r0_at_0.9_ml": high["ai_potable_reduction_vs_r0_ml"],
            "wwtw_inflow_delta_at_0.9_ml": high["wwtw_inflow_delta_ml"],
            "wwtw_direct_ghg_delta_at_0.9_kg_co2e": high["wwtw_direct_ghg_delta_kg_co2e"],
            "wwtw_inflow_change_at_0.9_vs_r0_ml": high["wwtw_inflow_change_vs_r0_ml"],
            "wwtw_direct_ghg_change_at_0.9_vs_r0_kg_co2e": high[
                "wwtw_direct_ghg_change_vs_r0_kg_co2e"
            ],
            "city_source_abstraction_nonincreasing_with_reclaimed_target": bool(
                all(r["city_source_abstraction_change_vs_r0_ml"] <= 1e-9 for r in domain_rows)
            ),
            "scope": "固定 1000 MW、现有 TDS/氯化物点值；不是现实率定或普适结论",
        })
        print(
            f"[{label}] gross withdrawal {low['ai_withdrawal_ml']:.1f}→{high['ai_withdrawal_ml']:.1f} ML; "
            f"city source abstraction vs r=0 +{high['city_source_abstraction_change_vs_r0_ml']:.1f} ML; "
            f"WWTW Δ {high['wwtw_inflow_delta_ml']:.1f} ML"
        )

    out_path = ART / "reclaimed_compatibility_R9.csv"
    verdict_path = ART / "reclaimed_compatibility_verdict_R9.csv"
    gate_path = ART / "reclaimed_compatibility_gate_R9.json"
    pd.DataFrame(rows).to_csv(out_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(verdicts).to_csv(verdict_path, index=False, encoding="utf-8-sig")
    positive_rows = [row for row in rows if row["target_reclaimed_fraction"] > 0.0]
    gate = {
        "artifact": "R9 reclaimed-water compatibility evidence gates",
        "scope": "single active data centre; 1000 MW; zero cooling-storage volume; fixed TDS/chloride point values",
        "gates": [
            {
                "id": "G0_fixed_point",
                "status": "PASS",
                "evidence": {
                    "positive_target_rows": len(positive_rows),
                    "all_status_converged": all(
                        row["quality_solver_converged_days"] == 730
                        for row in positive_rows
                    ),
                    "max_abs_residual": max(
                        row["quality_solver_max_abs_residual"]
                        for row in positive_rows
                    ),
                    "root_count": 1,
                },
            },
            {
                "id": "G1_storage_quality_state",
                "status": "NOT_READY",
                "evidence": "Cooling-storage volume and initial inventory are zero; storage TDS/chloride mass state is not modelled.",
            },
            {
                "id": "G2_shared_pool_joint_solver",
                "status": "NOT_READY",
                "evidence": "The quality fixed point is enabled only for one active data centre sharing the central reuse pool.",
            },
            {
                "id": "G3_estimand_separation",
                "status": "PASS",
                "evidence": "The CSV reports B0 no-AI deltas separately from B2-to-B1 same-AI counterfactual differences.",
            },
            {
                "id": "G4_internal_optimum",
                "status": "NOT_TESTED",
                "evidence": "No claim of a universal or robust interior reclaimed-water optimum is made in R9.",
            },
        ],
    }
    gate_path.write_text(json.dumps(gate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] {out_path} rows={len(rows)}")
    print(f"[OK] {verdict_path} rows={len(verdicts)}")
    print(f"[OK] {gate_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
