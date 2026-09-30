from __future__ import annotations

import math

import pytest

from aiuwm.reclaimed_allocation import (
    AllocationRequest,
    JointPlanEvaluation,
    JointQualityRequest,
    allocate_dedicated_incremental,
    allocate_shared_surplus,
    solve_joint_quality_allocation,
)


def _by_id(result):
    return {row.consumer_id: row for row in result.allocations}


def test_shared_protects_incumbents_then_allocates_incremental_pro_rata() -> None:
    requests = [
        AllocationRequest(
            "dc-b", demand_ml=12.0, incumbent_reclaimed_ml=4.0, potable_baseline_ml=12.0
        ),
        AllocationRequest(
            "dc-a", demand_ml=20.0, incumbent_reclaimed_ml=10.0, potable_baseline_ml=20.0
        ),
    ]

    result = allocate_shared_surplus("Q1A0-shared", 24.0, requests)
    rows = _by_id(result)

    assert result.scenario_id == "Q1A0-shared"
    assert result.policy == "shared_incumbent_first"
    assert rows["dc-a"].incumbent_allocated_ml == pytest.approx(10.0)
    assert rows["dc-b"].incumbent_allocated_ml == pytest.approx(4.0)
    assert rows["dc-a"].incremental_allocated_ml == pytest.approx(10.0 * 10.0 / 18.0)
    assert rows["dc-b"].incremental_allocated_ml == pytest.approx(8.0 * 10.0 / 18.0)
    assert result.total_allocated_ml == pytest.approx(24.0)
    assert result.unallocated_supply_ml == pytest.approx(0.0)
    assert result.closure_residual_ml == pytest.approx(0.0, abs=1e-12)
    assert result.overdraw_ml == 0.0
    assert result.displaced_incumbent_potable_ml == pytest.approx(0.0)


def test_shared_shortage_reduces_incumbents_pro_rata_and_reports_potable_fallback() -> None:
    result = allocate_shared_surplus(
        "Q1A0-short",
        4.0,
        [
            AllocationRequest("inc-b", demand_ml=10.0, incumbent_reclaimed_ml=6.0, potable_baseline_ml=10.0),
            AllocationRequest("inc-a", demand_ml=10.0, incumbent_reclaimed_ml=4.0, potable_baseline_ml=10.0),
        ],
    )
    rows = _by_id(result)

    assert rows["inc-a"].incumbent_allocated_ml == pytest.approx(1.6)
    assert rows["inc-b"].incumbent_allocated_ml == pytest.approx(2.4)
    assert all(row.incremental_allocated_ml == 0.0 for row in rows.values())
    assert result.displaced_incumbent_potable_ml == pytest.approx(6.0)
    assert result.potable_volume_displaced_ml == pytest.approx(4.0)
    assert result.total_allocated_ml <= result.available_supply_ml
    assert result.closure_residual_ml == pytest.approx(0.0, abs=1e-12)


def test_shared_result_is_independent_of_request_order() -> None:
    requests = [
        AllocationRequest("z", demand_ml=9.0, incumbent_reclaimed_ml=1.0),
        AllocationRequest("a", demand_ml=7.0, incumbent_reclaimed_ml=2.0),
        AllocationRequest("m", demand_ml=12.0, incumbent_reclaimed_ml=3.0),
    ]
    forward = allocate_shared_surplus("order", 11.0, requests)
    reverse = allocate_shared_surplus("order", 11.0, list(reversed(requests)))

    assert forward.allocations == reverse.allocations
    assert forward.total_allocated_ml == reverse.total_allocated_ml
    assert forward.closure_residual_ml == reverse.closure_residual_ml


def test_dedicated_supply_is_incremental_and_does_not_displace_incumbents() -> None:
    result = allocate_dedicated_incremental(
        "Q1A0-dedicated",
        9.0,
        [
            AllocationRequest(
                "dc-b",
                demand_ml=12.0,
                incumbent_reclaimed_ml=5.0,
                dedicated_supply_ml=6.0,
                potable_baseline_ml=12.0,
            ),
            AllocationRequest(
                "dc-a",
                demand_ml=10.0,
                incumbent_reclaimed_ml=4.0,
                dedicated_supply_ml=8.0,
                potable_baseline_ml=10.0,
            ),
        ],
    )
    rows = _by_id(result)

    # Eligible dedicated requests are 6 and 6, so a 9 ML pool is split 4.5/4.5.
    assert rows["dc-a"].incumbent_allocated_ml == 0.0
    assert rows["dc-b"].incumbent_allocated_ml == 0.0
    assert rows["dc-a"].incremental_allocated_ml == pytest.approx(4.5)
    assert rows["dc-b"].incremental_allocated_ml == pytest.approx(4.5)
    assert result.displaced_incumbent_potable_ml == pytest.approx(0.0)
    assert result.preserved_incumbent_reclaimed_ml == pytest.approx(9.0)
    assert result.potable_volume_displaced_ml == pytest.approx(9.0)
    assert result.total_allocated_ml == pytest.approx(9.0)
    assert result.overdraw_ml == 0.0


def test_invalid_or_overdraw_inputs_are_rejected_or_clipped() -> None:
    with pytest.raises(ValueError, match="negative"):
        allocate_shared_surplus("bad", -1.0, [])
    with pytest.raises(ValueError, match="duplicate"):
        allocate_shared_surplus(
            "bad",
            2.0,
            [AllocationRequest("same", demand_ml=1.0), AllocationRequest("same", demand_ml=1.0)],
        )
    with pytest.raises(ValueError, match="cannot exceed"):
        allocate_shared_surplus(
            "bad",
            2.0,
            [AllocationRequest("bad-demand", demand_ml=1.0, incumbent_reclaimed_ml=2.0)],
        )

    # A dedicated offer can exceed the pool, but the result cannot overdraw it.
    result = allocate_dedicated_incremental(
        "clip",
        1.0,
        [AllocationRequest("dc", demand_ml=100.0, dedicated_supply_ml=100.0)],
    )
    assert result.total_allocated_ml == pytest.approx(1.0)
    assert result.total_allocated_ml <= result.available_supply_ml
    assert math.isclose(result.closure_residual_ml, 0.0, abs_tol=1e-12)


def test_joint_quality_allocation_converges_unique_and_is_permutation_invariant() -> None:
    requests = [
        JointQualityRequest("DC_B", target_reclaimed_fraction=0.8),
        JointQualityRequest("DC_A", target_reclaimed_fraction=0.8),
    ]

    def evaluate(request: JointQualityRequest, reclaimed_ml: float) -> JointPlanEvaluation:
        external = 10.0 + 0.1 * reclaimed_ml
        return JointPlanEvaluation(
            external_makeup_ml=external,
            cycles_of_concentration=4.0 + reclaimed_ml / 100.0,
            reclaimed_quality_mg_l={"TDS": 600.0 + reclaimed_ml},
        )

    forward = solve_joint_quality_allocation("joint", 10.0, requests, evaluate)
    reverse = solve_joint_quality_allocation("joint", 10.0, reversed(requests), evaluate)

    assert forward.status == "converged_unique"
    assert forward.quality_integration_status == "READY_JOINT_CO_CURRENT"
    assert forward.root_count == 1
    assert forward.iterations > 0
    assert abs(forward.closure_residual_ml) <= 1e-12
    assert forward.allocations == reverse.allocations
    assert sum(item.reclaimed_allocated_ml for item in forward.allocations) == pytest.approx(10.0)
    assert all(item.reclaimed_fraction > 0.0 for item in forward.allocations)
    assert all(item.quality_solver_status == "converged" for item in forward.allocations)


def test_joint_quality_allocation_requires_quality_convergence() -> None:
    request = JointQualityRequest("DC_A", target_reclaimed_fraction=1.0)

    def evaluate(_request: JointQualityRequest, _reclaimed_ml: float) -> JointPlanEvaluation:
        return JointPlanEvaluation(
            external_makeup_ml=5.0,
            reclaimed_quality_mg_l={"TDS": 1000.0},
            quality_solver_status="not_converged",
            quality_solver_residual=1.0,
        )

    result = solve_joint_quality_allocation("quality_gate", 3.0, [request], evaluate)
    assert result.status == "quality_not_converged"
    assert result.quality_integration_status == "NOT_READY_JOINT_QUALITY_ALLOCATION"
    assert result.root_count == 1
    assert result.total_allocated_ml == pytest.approx(3.0)


def test_joint_quality_allocation_protects_incumbents_before_incremental_pool() -> None:
    requests = [
        JointQualityRequest("incumbent", target_reclaimed_fraction=0.5, incumbent_reclaimed_ml=6.0),
        JointQualityRequest("DC_A", target_reclaimed_fraction=1.0),
    ]

    def evaluate(_request: JointQualityRequest, _reclaimed_ml: float) -> JointPlanEvaluation:
        return JointPlanEvaluation(external_makeup_ml=10.0)

    result = solve_joint_quality_allocation("incumbent", 8.0, requests, evaluate)
    rows = {item.consumer_id: item for item in result.allocations}
    assert rows["incumbent"].reclaimed_allocated_ml == pytest.approx(6.0)
    assert rows["DC_A"].reclaimed_allocated_ml == pytest.approx(2.0)
    assert result.incumbent_allocated_ml == pytest.approx(6.0)
    assert result.incremental_budget_ml == pytest.approx(2.0)
    assert abs(result.closure_residual_ml) <= 1e-12


def test_joint_quality_allocation_keeps_incumbent_ledger_when_root_does_not_converge() -> None:
    requests = [
        JointQualityRequest("incumbent", target_reclaimed_fraction=1.0, incumbent_reclaimed_ml=2.0),
        JointQualityRequest("DC_A", target_reclaimed_fraction=1.0),
    ]

    def evaluate(_request: JointQualityRequest, reclaimed_ml: float) -> JointPlanEvaluation:
        return JointPlanEvaluation(external_makeup_ml=100.0 + 100.0 * reclaimed_ml)

    result = solve_joint_quality_allocation(
        "no_root", 4.0, requests, evaluate, max_iterations=1
    )
    rows = {item.consumer_id: item for item in result.allocations}
    assert result.status == "no_convergence"
    assert result.quality_integration_status == "NOT_READY_JOINT_QUALITY_ALLOCATION"
    assert rows["incumbent"].reclaimed_allocated_ml == pytest.approx(2.0)


def test_joint_quality_allocation_rejects_nonfinite_quality_diagnostics() -> None:
    request = JointQualityRequest("DC_A", target_reclaimed_fraction=1.0)

    def evaluate(_request: JointQualityRequest, _reclaimed_ml: float) -> JointPlanEvaluation:
        return JointPlanEvaluation(
            external_makeup_ml=5.0,
            cycles_of_concentration=float("inf"),
        )

    with pytest.raises(ValueError, match="cycles_of_concentration"):
        solve_joint_quality_allocation("invalid_quality", 3.0, [request], evaluate)
