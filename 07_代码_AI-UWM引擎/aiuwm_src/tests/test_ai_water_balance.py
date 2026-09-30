from __future__ import annotations

import copy
from pathlib import Path

import numpy as np
import pytest
from collections import defaultdict

from aiuwm.full_engine import FullAIUWMModel, load_project
from aiuwm.validation import ProjectValidationError


PROJECT = Path("examples/demo_full/project.json")


def ai_project(days: int = 5, capacity_mw: float = 500.0):
    project, timeseries = load_project(PROJECT)
    project = copy.deepcopy(project)
    timeseries = timeseries.iloc[:days].copy()
    project["simulation"]["end"] = str(timeseries["date"].iloc[-1].date())
    project["pipeline_events"] = []
    project["interventions"] = []
    project["components"]["AI_DC1"] = {
        "kind": "data_center",
        "local_area": "LA1",
        "installed_it_capacity_mw": capacity_mw,
        "load_factor": 0.75,
        "pue_mode": "dynamic",
        "base_pue": 1.2,
        "temperature_coefficient": 0.003,
        "min_pue": 1.05,
        "max_pue": 1.6,
        "cooling_storage_ml": 2.0,
        "initial_cooling_storage_ml": 2.0,
        "cooling": {
            "technology": "evaporative",
            "cycles_of_concentration": 5.0,
            "drift_fraction_of_makeup": 0.0002,
            "blowdown_return_fraction": 1.0,
            "internal_recovery_fraction": 0.0,
            "blowdown_quality_mg_l": {"TDS": 1600.0},
        },
        "water_sources": {
            "reclaimed": {
                "component_id": "CENTRAL_REUSE",
                "target_fraction": 0.70,
                "priority": 1,
            },
            "potable": {"target_fraction": 0.30, "priority": 2},
        },
        "water_fallback": True,
        "priority_class": "ai_data_center",
    }
    return project, timeseries


def test_zero_ai_capacity_is_exact_baseline() -> None:
    baseline, timeseries = ai_project(capacity_mw=0.0)
    without_ai = copy.deepcopy(baseline)
    without_ai["components"].pop("AI_DC1")
    baseline_result = FullAIUWMModel(without_ai, timeseries).run()
    ai_result = FullAIUWMModel(baseline, timeseries).run()
    np.testing.assert_allclose(
        ai_result.system_daily["water_demand_ml"],
        baseline_result.system_daily["water_demand_ml"],
        atol=0.0,
    )
    assert (ai_result.data_center_daily["external_withdrawal_ml"] == 0).all()


def test_ai_is_supplied_by_real_reuse_and_potable_and_returns_to_wwtw() -> None:
    project, timeseries = ai_project()
    result = FullAIUWMModel(project, timeseries).run()
    dc = result.data_center_daily
    assert len(dc) == len(timeseries)
    assert dc["it_energy_mwh"].sum() > 0
    assert dc["external_withdrawal_ml"].sum() > 0
    assert dc["reclaimed_water_ml"].sum() > 0
    assert (
        dc["reclaimed_water_ml"]
        <= dc["external_withdrawal_ml"] * dc["target_reclaimed_fraction"] + 1e-10
    ).all()
    np.testing.assert_allclose(dc["water_balance_residual_ml"], 0.0, atol=1e-9)
    sewer = result.component_daily[result.component_daily.component_id == "SEWER1"]
    without_ai = copy.deepcopy(project)
    without_ai["components"].pop("AI_DC1")
    baseline = FullAIUWMModel(without_ai, timeseries).run()
    baseline_sewer = baseline.component_daily[
        baseline.component_daily.component_id == "SEWER1"
    ]
    assert sewer["inflow_ml"].sum() > baseline_sewer["inflow_ml"].sum()
    tds = result.pollutant_daily[
        (result.pollutant_daily.component_id == "AI_DC1")
        & (result.pollutant_daily.pollutant == "TDS")
    ]
    assert tds["mass_kg"].sum() > 0


def test_main_result_exposes_read_only_e4_a0_boundary() -> None:
    project, timeseries = ai_project(days=1)
    result = FullAIUWMModel(project, timeseries).run()

    diagnostic = result.e4_adaptation_diagnostic()
    assert diagnostic["status"] == "NOT_READY"
    assert diagnostic["policy"] == "A0"
    assert diagnostic["main_model_integration"] == "READ_ONLY_BOUNDARY"
    assert diagnostic["paired_freshwater_baseline_required"] is True

    ledger = result.to_e4_ledger()
    assert len(ledger) == len(result.data_center_daily)
    assert diagnostic["a0_accounting"]["within_run_baseline_ml"] == pytest.approx(
        sum(day.freshwater_baseline_ml for day in ledger)
    )


def test_reclaimed_supply_is_limited_by_reuse_storage() -> None:
    project, timeseries = ai_project(days=1)
    project["components"]["CENTRAL_REUSE"]["initial_ml"] = 0.25
    project["components"]["CENTRAL_REUSE"]["treatment_capacity_ml_day"] = 0.25
    result = FullAIUWMModel(project, timeseries).run()
    assert result.data_center_daily.iloc[0]["reclaimed_water_ml"] <= 0.25 + 1e-12


def test_opt_in_shared_allocation_is_permutation_invariant_and_audited() -> None:
    def run(reverse: bool):
        project, timeseries = ai_project(days=1, capacity_mw=300.0)
        project["reuse_allocation_mode"] = "shared_incumbent_first"
        project["components"]["CENTRAL_REUSE"]["initial_ml"] = 100.0
        project["components"]["CENTRAL_REUSE"]["treatment_capacity_ml_day"] = 100.0
        first = project["components"].pop("AI_DC1")
        second = copy.deepcopy(first)
        ordered = [("AI_A", first), ("AI_B", second)]
        if reverse:
            ordered.reverse()
        project["components"].update(ordered)
        return FullAIUWMModel(project, timeseries).run()

    forward = run(False)
    reverse = run(True)
    forward_dc = forward.data_center_daily.set_index("data_center_id")
    reverse_dc = reverse.data_center_daily.set_index("data_center_id")
    for component_id in ("AI_A", "AI_B"):
        np.testing.assert_allclose(
            forward_dc.loc[component_id, "reclaimed_water_ml"],
            reverse_dc.loc[component_id, "reclaimed_water_ml"],
            atol=1e-12,
        )
        assert (
            forward_dc.loc[component_id, "quality_integration_status"]
            == "NOT_READY_JOINT_QUALITY_ALLOCATION"
        )
    area_row = forward.area_daily.iloc[0]
    assert area_row["reuse_allocation_policy"] == "shared_incumbent_first"
    assert area_row["reuse_allocation_closure_residual_ml"] == 0.0
    assert area_row["reuse_allocation_displaced_incumbent_potable_ml"] >= 0.0


def test_multi_dc_quality_allocation_is_joint_and_carries_treated_quality() -> None:
    project, timeseries = ai_project(days=1, capacity_mw=300.0)
    project["reuse_allocation_mode"] = "shared_incumbent_first"
    reuse = project["components"]["CENTRAL_REUSE"]
    reuse["initial_ml"] = 100.0
    reuse["treatment_capacity_ml_day"] = 100.0
    reuse["quality_mg_l"] = {"TDS": 700.0}
    reuse["quality_provenance"] = "treated_output"
    template = project["components"].pop("AI_DC1")
    for component_id in ("AI_A", "AI_B"):
        dc = copy.deepcopy(template)
        dc["quality_state_enabled"] = True
        dc["initial_cooling_storage_ml"] = 0.0
        dc["cooling_storage_ml"] = 0.0
        dc["cooling"].update(
            {
                "coc_mode": "quality_limited",
                "cycles_of_concentration": 8.0,
                "water_quality_limits": {"TDS": 1100.0},
            }
        )
        dc["water_sources"]["reclaimed"]["quality_mg_l"] = {"TDS": 900.0}
        dc["water_sources"]["potable"]["quality_mg_l"] = {"TDS": 200.0}
        project["components"][component_id] = dc

    result = FullAIUWMModel(project, timeseries).run()
    dc_rows = result.data_center_daily.set_index("data_center_id")
    assert set(dc_rows["quality_integration_status"]) == {"READY_JOINT_CO_CURRENT"}
    assert set(dc_rows["quality_reclaimed_quality_provenance"]) == {"treated_output"}
    assert all(
        row == {"TDS": 700.0}
        for row in dc_rows["quality_reclaimed_source_mg_l"]
    )
    assert all(dc_rows["quality_solver_status"] == "converged")
    assert (dc_rows["cycles_of_concentration"] < 8.0).all()
    np.testing.assert_allclose(
        dc_rows["quality_solver_reclaimed_fraction"],
        dc_rows["reclaimed_water_ml"] / dc_rows["external_makeup_ml"],
        atol=1e-12,
    )
    assert dc_rows["reclaimed_water_ml"].sum() <= reuse["initial_ml"] + 1e-10
    np.testing.assert_allclose(dc_rows["water_balance_residual_ml"], 0.0, atol=1e-9)
    np.testing.assert_allclose(
        dc_rows["quality_process_solute_closure_residual_kg"], 0.0, atol=1e-9
    )
    area_row = result.area_daily.iloc[0]
    assert "joint-quality" in area_row["reuse_allocation_scenario_id"]
    assert area_row["reuse_allocation_closure_residual_ml"] == 0.0


def test_multi_dc_joint_slice_carries_recovered_return_to_next_day() -> None:
    project, timeseries = ai_project(days=2, capacity_mw=300.0)
    project["reuse_allocation_mode"] = "shared_incumbent_first"
    reuse = project["components"]["CENTRAL_REUSE"]
    reuse["initial_ml"] = 100.0
    reuse["treatment_capacity_ml_day"] = 100.0
    reuse["quality_mg_l"] = {"TDS": 100.0}
    reuse["quality_provenance"] = "treated_output"
    template = project["components"].pop("AI_DC1")
    for component_id in ("AI_A", "AI_B"):
        dc = copy.deepcopy(template)
        dc["quality_state_enabled"] = True
        dc["initial_cooling_storage_ml"] = 0.0
        dc["cooling_storage_ml"] = 0.0
        dc["cooling"].update(
            {
                "coc_mode": "quality_limited",
                "cycles_of_concentration": 8.0,
                "water_quality_limits": {"TDS": 1100.0},
                "internal_recovery_fraction": 0.5,
            }
        )
        dc["water_sources"]["reclaimed"]["quality_mg_l"] = {"TDS": 900.0}
        dc["water_sources"]["potable"]["quality_mg_l"] = {"TDS": 200.0}
        project["components"][component_id] = dc

    result = FullAIUWMModel(project, timeseries).run()
    rows = result.data_center_daily.sort_values(["date", "data_center_id"])
    day_two = rows[rows["date"] == rows["date"].max()]
    assert set(day_two["quality_integration_status"]) == {"READY_JOINT_CO_CURRENT"}
    assert (day_two["quality_recovered_return_volume_start_ml"] > 0.0).all()
    np.testing.assert_allclose(day_two["water_balance_residual_ml"], 0.0, atol=1e-9)
    np.testing.assert_allclose(
        day_two["quality_process_solute_closure_residual_kg"], 0.0, atol=1e-9
    )


def test_multi_dc_joint_slice_is_invariant_to_component_order() -> None:
    def run(reverse: bool):
        project, timeseries = ai_project(days=1, capacity_mw=300.0)
        project["reuse_allocation_mode"] = "shared_incumbent_first"
        reuse = project["components"]["CENTRAL_REUSE"]
        reuse["initial_ml"] = 100.0
        reuse["treatment_capacity_ml_day"] = 100.0
        reuse["quality_mg_l"] = {"TDS": 100.0}
        reuse["quality_provenance"] = "treated_output"
        template = project["components"].pop("AI_DC1")
        entries = []
        for component_id in ("AI_A", "AI_B"):
            dc = copy.deepcopy(template)
            dc["quality_state_enabled"] = True
            dc["initial_cooling_storage_ml"] = 0.0
            dc["cooling_storage_ml"] = 0.0
            dc["cooling"].update(
                {
                    "coc_mode": "quality_limited",
                    "cycles_of_concentration": 8.0,
                    "water_quality_limits": {"TDS": 1100.0},
                }
            )
            dc["water_sources"]["reclaimed"]["quality_mg_l"] = {"TDS": 900.0}
            dc["water_sources"]["potable"]["quality_mg_l"] = {"TDS": 200.0}
            entries.append((component_id, dc))
        if reverse:
            entries.reverse()
        project["components"].update(entries)
        return FullAIUWMModel(project, timeseries).run()

    forward = run(False).data_center_daily.set_index("data_center_id")
    reverse = run(True).data_center_daily.set_index("data_center_id")
    for component_id in ("AI_A", "AI_B"):
        np.testing.assert_allclose(
            forward.loc[component_id, [
                "external_makeup_ml",
                "reclaimed_water_ml",
                "cycles_of_concentration",
            ]].to_numpy(dtype=float),
            reverse.loc[component_id, [
                "external_makeup_ml",
                "reclaimed_water_ml",
                "cycles_of_concentration",
            ]].to_numpy(dtype=float),
            atol=1e-12,
        )
    assert set(forward["quality_integration_status"]) == {"READY_JOINT_CO_CURRENT"}


def test_dedicated_mode_is_rejected_until_incremental_source_is_integrated() -> None:
    project, timeseries = ai_project(days=1)
    project["reuse_allocation_mode"] = "dedicated_incremental"
    with pytest.raises(ProjectValidationError, match="reuse_allocation_mode"):
        FullAIUWMModel(project, timeseries)


def test_quality_solver_is_explicitly_disabled_when_cooling_storage_has_no_quality_state(
    monkeypatch,
) -> None:
    project, timeseries = ai_project(days=1)
    dc = project["components"]["AI_DC1"]
    dc["cooling"].update({
        "coc_mode": "quality_limited",
        "water_quality_limits": {"TDS": 1800.0},
    })
    dc["water_sources"]["reclaimed"]["quality"] = {"TDS": 700.0}
    dc["water_sources"]["potable"]["quality"] = {"TDS": 200.0}

    import aiuwm.full_engine as full_engine

    calls = []
    original = full_engine.calculate_data_center_plan

    def wrapped(*args, **kwargs):
        calls.append(kwargs.get("reclaimed_available_ml"))
        return original(*args, **kwargs)

    monkeypatch.setattr(full_engine, "calculate_data_center_plan", wrapped)
    result = FullAIUWMModel(project, timeseries).run()
    row = result.data_center_daily.iloc[0]

    assert calls == [None]
    assert row["storage_start_ml"] > 0.0
    assert row["quality_solver_status"] == "not_applicable"


def test_no_fallback_preserves_unmet_water_and_other_source_is_accounted() -> None:
    project, timeseries = ai_project(days=1)
    project["components"]["CENTRAL_REUSE"]["initial_ml"] = 0.0
    project["components"]["AI_DC1"]["water_fallback"] = False
    limited = FullAIUWMModel(project, timeseries).run().data_center_daily.iloc[0]
    assert limited["unmet_cooling_water_ml"] > 0

    project, timeseries = ai_project(days=1)
    sources = project["components"]["AI_DC1"]["water_sources"]
    sources["reclaimed"]["target_fraction"] = 0.4
    sources["potable"]["target_fraction"] = 0.3
    sources["other"] = {"target_fraction": 0.3, "available_ml_day": 100}
    supplied = FullAIUWMModel(project, timeseries).run().data_center_daily.iloc[0]
    assert supplied["other_water_ml"] > 0
    assert abs(supplied["water_balance_residual_ml"]) < 1e-9


def test_opt_in_quality_storage_carries_solutes_and_closes() -> None:
    project, timeseries = ai_project(days=2)
    dc = project["components"]["AI_DC1"]
    dc["quality_state_enabled"] = True
    dc["cooling_storage_quality_mg_l"] = {"TDS": 900.0, "chloride": 250.0}
    dc["water_sources"]["reclaimed"]["quality"] = {"TDS": 700.0, "chloride": 180.0}
    dc["water_sources"]["potable"]["quality"] = {"TDS": 200.0, "chloride": 40.0}
    model = FullAIUWMModel(project, timeseries)
    result = model.run()
    rows = result.data_center_daily
    assert set(rows["quality_state_status"]) == {"ENABLED_DYNAMIC_STORAGE"}
    np.testing.assert_allclose(
        rows["quality_solute_closure_residual_kg"], 0.0, atol=1e-9
    )
    np.testing.assert_allclose(
        rows["quality_storage_water_balance_residual_ml"], 0.0, atol=1e-9
    )
    assert model.data_center_quality_storage["AI_DC1"].volume_ml >= 0.0
    assert rows["quality_process_TDS_mg_l"].max() > 0.0


def test_single_dc_quality_solver_uses_treated_reuse_output_quality() -> None:
    def run(output_tds: float):
        project, timeseries = ai_project(days=1)
        dc = project["components"]["AI_DC1"]
        dc["quality_state_enabled"] = True
        dc["initial_cooling_storage_ml"] = 0.0
        dc["cooling_storage_ml"] = 0.0
        dc["cooling"].update({
            "coc_mode": "quality_limited",
            "cycles_of_concentration": 8.0,
            "water_quality_limits": {"TDS": 1100.0},
        })
        dc["water_sources"]["reclaimed"]["quality_mg_l"] = {"TDS": 900.0}
        dc["water_sources"]["potable"]["quality_mg_l"] = {"TDS": 200.0}
        reuse = project["components"]["CENTRAL_REUSE"]
        reuse["initial_ml"] = 100.0
        reuse["treatment_capacity_ml_day"] = 100.0
        reuse["quality_mg_l"] = {"TDS": output_tds}
        reuse["quality_provenance"] = "treated_output"
        row = FullAIUWMModel(project, timeseries).run().data_center_daily.iloc[0]
        return row

    treated = run(100.0)
    concentrated = run(900.0)
    assert treated["quality_solver_status"] == "converged"
    assert treated["quality_reclaimed_quality_provenance"] == "treated_output"
    assert treated["quality_reclaimed_source_mg_l"]["TDS"] == 100.0
    assert treated["cycles_of_concentration"] > concentrated["cycles_of_concentration"]
    np.testing.assert_allclose(
        treated["quality_process_solute_closure_residual_kg"], 0.0, atol=1e-9
    )
    np.testing.assert_allclose(
        treated["quality_partition_closure_TDS_kg"], 0.0, atol=1e-9
    )


def test_single_dc_carries_recovered_return_into_next_quality_plan() -> None:
    def run(internal_recovery: float):
        project, timeseries = ai_project(days=3)
        dc = project["components"]["AI_DC1"]
        dc["quality_state_enabled"] = True
        dc["initial_cooling_storage_ml"] = 0.0
        dc["cooling_storage_ml"] = 0.0
        dc["cooling"].update({
            "coc_mode": "quality_limited",
            "cycles_of_concentration": 8.0,
            "water_quality_limits": {"TDS": 1100.0},
            "internal_recovery_fraction": internal_recovery,
        })
        dc["water_sources"]["reclaimed"]["quality_mg_l"] = {"TDS": 900.0}
        dc["water_sources"]["potable"]["quality_mg_l"] = {"TDS": 200.0}
        reuse = project["components"]["CENTRAL_REUSE"]
        reuse["initial_ml"] = 100.0
        reuse["treatment_capacity_ml_day"] = 100.0
        reuse["quality_mg_l"] = {"TDS": 100.0}
        return FullAIUWMModel(project, timeseries).run().data_center_daily

    with_return = run(0.5)
    without_return = run(0.0)
    assert with_return.loc[1, "quality_recovered_return_volume_start_ml"] > 0.0
    np.testing.assert_allclose(
        with_return["quality_recovered_return_volume_residual_ml"], 0.0, atol=1e-12
    )
    np.testing.assert_allclose(
        with_return["quality_recovered_return_partition_closure_kg"], 0.0, atol=1e-9
    )
    np.testing.assert_allclose(
        with_return["quality_recovered_return_mass_residual_kg"], 0.0, atol=1e-9
    )
    assert (
        with_return.loc[2, "cycles_of_concentration"]
        < without_return.loc[2, "cycles_of_concentration"]
    )


def test_declared_reuse_quality_defaults_to_scenario_prior() -> None:
    project, timeseries = ai_project(days=1)
    dc = project["components"]["AI_DC1"]
    dc["quality_state_enabled"] = True
    dc["initial_cooling_storage_ml"] = 0.0
    dc["cooling_storage_ml"] = 0.0
    dc["cooling"].update({
        "coc_mode": "quality_limited",
        "cycles_of_concentration": 8.0,
        "water_quality_limits": {"TDS": 1100.0},
    })
    dc["water_sources"]["reclaimed"]["quality_mg_l"] = {"TDS": 900.0}
    dc["water_sources"]["potable"]["quality_mg_l"] = {"TDS": 200.0}
    reuse = project["components"]["CENTRAL_REUSE"]
    reuse["initial_ml"] = 100.0
    reuse["treatment_capacity_ml_day"] = 100.0
    reuse["quality_mg_l"] = {"TDS": 100.0}
    row = FullAIUWMModel(project, timeseries).run().data_center_daily.iloc[0]
    assert row["quality_reclaimed_quality_provenance"] == "scenario_prior"


def test_shortage_allocation_supports_resident_proportional_and_ai_first() -> None:
    def state():
        return {
            "demand": {"domestic": 10.0, "data_center::AI": 10.0},
            "remaining": {"domestic": 10.0, "data_center::AI": 10.0},
            "potable_delivered": defaultdict(float),
            "minimum_service_fractions": {},
        }

    resident = state()
    FullAIUWMModel._allocate_potable_to_demands(resident, 10, None, "resident_first")
    assert resident["potable_delivered"]["domestic"] == 10
    proportional = state()
    FullAIUWMModel._allocate_potable_to_demands(proportional, 10, None, "proportional")
    assert proportional["potable_delivered"]["domestic"] == 5
    ai_first = state()
    FullAIUWMModel._allocate_potable_to_demands(ai_first, 10, None, "ai_first")
    assert ai_first["potable_delivered"]["data_center::AI"] == 10
