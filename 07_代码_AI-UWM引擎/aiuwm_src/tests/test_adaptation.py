from __future__ import annotations

import math

import pytest

from aiuwm.adaptation import (
    AdaptationConfig,
    CoolingDayLedger,
    cooling_ledger_from_data_center_daily,
    evaluate_adaptation,
    evaluate_adaptation_set,
)


def _ledger() -> list[CoolingDayLedger]:
    return [
        CoolingDayLedger(
            "d1",
            water_demand_ml=100.0,
            reclaimed_supply_ml=100.0,
            solute_load_kg={"TDS": 10.0, "chloride": 2.0},
            it_energy_kwh=50.0,
        ),
        CoolingDayLedger(
            "d2",
            water_demand_ml=80.0,
            reclaimed_supply_ml=60.0,
            solute_load_kg={"TDS": 8.0, "chloride": 1.0},
            it_energy_kwh=40.0,
        ),
    ]


def test_a1_solute_and_water_closure_with_explicit_treatment_sinks() -> None:
    result = evaluate_adaptation(
        _ledger(),
        AdaptationConfig(
            policy="A1",
            solute_removal_fractions={"TDS": 0.8, "chloride": 0.5},
            treatment_reject_fraction=0.1,
            treatment_unreturned_fraction=0.05,
            treatment_energy_kwh_per_ml=0.2,
            treatment_fixed_energy_kwh_per_day=1.0,
            chemical_cost_per_kg_removed=3.0,
            treatment_fixed_cost_per_day=2.0,
        ),
    )

    assert result.status == "feasible"
    assert result.reject_ml == pytest.approx(16.0)
    assert result.unreturned_ml == pytest.approx(8.0)
    assert result.freshwater_use_ml == pytest.approx(44.0)
    assert result.freshwater_saving_ml == pytest.approx(136.0)
    assert result.energy_kwh == pytest.approx(34.0)
    assert result.cost > 0.0
    assert result.E_adapt == pytest.approx(result.energy_kwh)
    assert result.C_adapt == pytest.approx(result.cost)
    for residual in result.solute_closure_residual_kg.values():
        assert residual == pytest.approx(0.0, abs=1e-12)


def test_a2_reject_and_annualised_ownership_are_not_free() -> None:
    result = evaluate_adaptation(
        _ledger(),
        AdaptationConfig(
            policy="A2",
            membrane_recovery_fraction=0.75,
            membrane_rejection_fractions={"TDS": 0.9, "chloride": 0.8},
            membrane_energy_kwh_per_ml=0.1,
            membrane_capex=3650.0,
            membrane_lifetime_years=5.0,
            membrane_annual_opex=730.0,
            energy_cost_per_kwh=1.5,
        ),
    )

    assert result.reject_ml == pytest.approx(40.0)
    assert result.annualized_capex_cost == pytest.approx(730.0)
    assert result.annualized_opex_cost == pytest.approx(730.0)
    assert result.cost >= 8.0
    assert result.energy_kwh == pytest.approx(16.0)
    assert result.freshwater_use_ml == pytest.approx(60.0)
    for residual in result.solute_closure_residual_kg.values():
        assert residual == pytest.approx(0.0, abs=1e-12)


def test_a3_water_saving_and_pue_penalty_are_explicit() -> None:
    result = evaluate_adaptation(
        _ledger(),
        AdaptationConfig(
            policy="A3",
            wet_fraction=0.25,
            extra_pue=0.2,
            extra_energy_kwh_per_ml_dry=0.1,
            energy_carbon_kg_per_kwh=0.5,
        ),
    )

    assert result.freshwater_use_ml == pytest.approx(0.0)
    assert result.freshwater_saving_ml == pytest.approx(180.0)
    assert result.energy_kwh == pytest.approx((50.0 + 40.0) * 0.2 + (75.0 + 60.0) * 0.1)
    assert result.carbon_kg_co2e == pytest.approx(result.energy_kwh * 0.5)
    assert result.status == "feasible"


def test_no_strategy_meets_city_threshold_returns_na_estimands() -> None:
    ledger = [CoolingDayLedger("d1", water_demand_ml=10.0, reclaimed_supply_ml=0.0)]
    summary = evaluate_adaptation_set(
        ledger,
        [
            AdaptationConfig(policy="A0", city_saving_threshold_ml=1.0),
            AdaptationConfig(policy="A1", city_saving_threshold_ml=1.0, treatment_energy_kwh_per_ml=1.0),
            AdaptationConfig(policy="A2", city_saving_threshold_ml=1.0, membrane_energy_kwh_per_ml=1.0),
            AdaptationConfig(policy="A3", wet_fraction=1.0, city_saving_threshold_ml=1.0),
        ],
    )

    assert summary.status == "infeasible"
    assert summary.E_adapt == "NA"
    assert summary.C_adapt == "NA"
    assert summary.feasible_results == ()
    assert all(result.E_adapt == "NA" for result in summary.results)
    assert all(result.C_adapt == "NA" for result in summary.results)


def test_input_validation_and_provenance() -> None:
    with pytest.raises(ValueError, match=r"within \[0, 1\]"):
        AdaptationConfig(policy="A1", side_stream_fraction=1.1)
    with pytest.raises(ValueError, match="duplicate"):
        evaluate_adaptation(
            [
                {"day": "same", "water_demand_ml": 1.0},
                {"day": "same", "water_demand_ml": 1.0},
            ],
            "A0",
        )

    result = evaluate_adaptation([], "A0")
    assert result.provenance["main_model_integration"] == "NOT_READY"
    assert result.provenance["quality_evidence_default"] == "scenario_prior"
    assert math.isclose(result.freshwater_saving_ml, 0.0)


def test_main_model_data_center_rows_map_to_read_only_e4_ledger() -> None:
    ledger = cooling_ledger_from_data_center_daily(
        [
            {
                "date": "2030-01-01",
                "data_center_id": "DC1",
                "external_makeup_ml": 10.0,
                "reclaimed_water_ml": 4.0,
                "potable_water_ml": 6.0,
                "it_energy_mwh": 0.25,
                "quality_reclaimed_source_mg_l": {"TDS": 200.0},
            }
        ]
    )

    assert len(ledger) == 1
    row = ledger[0]
    assert row.day_id == "2030-01-01::DC1"
    assert row.water_demand_ml == pytest.approx(10.0)
    assert row.reclaimed_supply_ml == pytest.approx(4.0)
    assert row.freshwater_baseline_ml == pytest.approx(6.0)
    assert row.it_energy_kwh == pytest.approx(250.0)
    assert row.solute_load_kg["TDS"] == pytest.approx(800.0)

    # The adapter is intentionally read-only: evaluation remains a standalone
    # E4 calculation and does not mutate or promote the main-model gate.
    result = evaluate_adaptation(ledger, "A0")
    assert result.provenance["main_model_integration"] == "NOT_READY"


def test_paired_freshwater_baseline_is_distinct_from_same_run_potable_use() -> None:
    ledger = cooling_ledger_from_data_center_daily(
        [{
            "date": "2030-01-01", "data_center_id": "DC1",
            "external_makeup_ml": 10.0, "reclaimed_water_ml": 4.0,
            "potable_water_ml": 6.0,
        }],
        freshwater_baseline_rows=[{
            "date": "2030-01-01", "data_center_id": "DC1",
            "potable_water_ml": 12.0,
        }],
    )

    assert ledger[0].freshwater_baseline_ml == pytest.approx(12.0)
    result = evaluate_adaptation(ledger, "A0")
    assert result.freshwater_use_ml == pytest.approx(6.0)
    assert result.freshwater_saving_ml == pytest.approx(6.0)


def test_paired_freshwater_baseline_requires_exact_unique_day_dc_pairs() -> None:
    current = [{
        "date": "2030-01-01", "data_center_id": "DC1",
        "external_makeup_ml": 10.0, "reclaimed_water_ml": 4.0,
        "potable_water_ml": 6.0,
    }]
    with pytest.raises(ValueError, match="missing row"):
        cooling_ledger_from_data_center_daily(
            current,
            freshwater_baseline_rows=[{
                "date": "2030-01-02", "data_center_id": "DC1",
                "potable_water_ml": 12.0,
            }],
        )
    with pytest.raises(ValueError, match="duplicate"):
        cooling_ledger_from_data_center_daily(
            current,
            freshwater_baseline_rows=[
                {"date": "2030-01-01", "data_center_id": "DC1", "potable_water_ml": 12.0},
                {"date": "2030-01-01", "data_center_id": "DC1", "potable_water_ml": 12.0},
            ],
        )
