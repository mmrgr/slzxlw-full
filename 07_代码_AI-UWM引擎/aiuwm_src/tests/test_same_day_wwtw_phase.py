from __future__ import annotations

import copy
from pathlib import Path

import numpy as np
import pytest

from aiuwm.full_engine import FullAIUWMModel, load_project
from aiuwm.validation import ProjectValidationError


PROJECT = Path("examples/demo_full/project.json")


def _project(days: int = 2):
    project, timeseries = load_project(PROJECT)
    project = copy.deepcopy(project)
    timeseries = timeseries.iloc[:days].copy()
    project["simulation"]["end"] = str(timeseries["date"].iloc[-1].date())
    project["pipeline_events"] = []
    project["interventions"] = []
    return project, timeseries


def test_same_day_wwtw_phase_is_explicit_end_of_day_carryover_and_closes() -> None:
    project, timeseries = _project()
    project["same_day_wwtw_production"] = {
        "enabled": True,
        "mode": "end_of_day_diagnostic",
    }

    result = FullAIUWMModel(project, timeseries).run()
    daily = result.system_daily

    assert set(daily["same_day_wwtw_phase_status"]) == {"END_OF_DAY_CARRYOVER_ONLY"}
    assert (daily["same_day_wwtw_production_ml"] > 0.0).any()
    np.testing.assert_allclose(
        daily["same_day_wwtw_consumed_ml"], 0.0, atol=1e-12
    )
    np.testing.assert_allclose(
        daily["same_day_wwtw_carryover_ml"],
        daily["same_day_wwtw_production_ml"],
        atol=1e-12,
    )
    np.testing.assert_allclose(
        daily["same_day_wwtw_closure_residual_ml"], 0.0, atol=1e-12
    )
    np.testing.assert_allclose(
        daily["same_day_wwtw_storage_reconciliation_residual_ml"],
        0.0,
        atol=1e-12,
    )
    assert not daily["same_day_wwtw_feedback_to_data_center"].any()


def test_same_day_wwtw_phase_is_off_by_default() -> None:
    project, timeseries = _project(days=1)
    result = FullAIUWMModel(project, timeseries).run()
    assert "same_day_wwtw_phase_status" not in result.system_daily.columns


def test_same_day_wwtw_phase_rejects_unimplemented_feedback_mode() -> None:
    project, timeseries = _project(days=1)
    project["same_day_wwtw_production"] = {"enabled": True, "mode": "feedback"}
    with pytest.raises(ProjectValidationError, match="end_of_day_diagnostic"):
        FullAIUWMModel(project, timeseries)


def _add_ai_dc(project: dict) -> None:
    project["components"]["AI_DC1"] = {
        "kind": "data_center",
        "local_area": "LA1",
        "installed_it_capacity_mw": 500.0,
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


def test_same_day_co_current_mode_converges_and_closes_with_dc_feedback() -> None:
    project, timeseries = _project(days=1)
    _add_ai_dc(project)
    project["same_day_wwtw_production"] = {
        "enabled": True,
        "mode": "co_current_diagnostic",
    }

    result = FullAIUWMModel(project, timeseries).run()
    daily = result.system_daily.iloc[0]

    assert daily["same_day_wwtw_phase_status"] == "CO_CURRENT_DIAGNOSTIC_CONVERGED"
    assert bool(daily["same_day_wwtw_feedback_to_data_center"])
    assert daily["same_day_wwtw_data_center_consumed_ml"] > 0.0
    assert daily["same_day_wwtw_production_ml"] > 0.0
    np.testing.assert_allclose(
        daily["same_day_wwtw_closure_residual_ml"], 0.0, atol=1e-10
    )
    np.testing.assert_allclose(
        daily["same_day_wwtw_storage_reconciliation_residual_ml"],
        0.0,
        atol=1e-10,
    )
    dc = result.data_center_daily.iloc[0]
    assert dc["reclaimed_water_ml"] > 0.0
    np.testing.assert_allclose(dc["water_balance_residual_ml"], 0.0, atol=1e-10)


def test_same_day_co_current_without_dc_does_not_claim_dc_feedback() -> None:
    project, timeseries = _project(days=1)
    project["same_day_wwtw_production"] = {
        "enabled": True,
        "mode": "co_current_diagnostic",
    }

    result = FullAIUWMModel(project, timeseries).run()
    daily = result.system_daily.iloc[0]

    assert daily["same_day_wwtw_phase_status"] == "CO_CURRENT_DIAGNOSTIC_CONVERGED"
    assert daily["same_day_wwtw_data_center_consumed_ml"] == pytest.approx(0.0)
    assert not bool(daily["same_day_wwtw_feedback_to_data_center"])
    np.testing.assert_allclose(
        daily["same_day_wwtw_closure_residual_ml"], 0.0, atol=1e-10
    )
