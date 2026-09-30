"""Deterministic reclaimed-water allocation primitives.

This module is intentionally independent of :mod:`aiuwm.full_engine`.  It
implements the R10a allocation contract on an *already computed* reclaimed
water supply.  ``available_supply_ml`` is the total supply available to this
allocation transaction before any incumbent claims are reserved for the
shared policy.  It is the dedicated pool size for the dedicated policy.  The
total reuse production or storage volume is not a valid substitute unless it
has first been converted to this transaction-level supply.

Two policies are exposed:

``allocate_shared_surplus``
    Protect incumbent reclaimed-water claims first.  If the available supply is large
    enough, the remaining amount is shared pro-rata over incremental demand.
    If it is too small even for incumbent claims, incumbent claims are
    reduced pro-rata and no incremental claim is served.  The latter rule is
    deterministic and avoids an input-order tie break.

``allocate_dedicated_incremental``
    Allocate only per-consumer dedicated incremental offers.  Dedicated
    offers do not take water from incumbents.  If the offers exceed the
    dedicated pool supply, they are reduced pro-rata, again independent of input
    order.

The solver reports both potable volume displaced by reclaimed water and
potable fallback caused by an incumbent shortfall.  A result contains a
scenario identifier and an explicit closure residual so it can be persisted
and audited before integration into the main model.  The shared incumbent-first
policy has an opt-in daily slice in ``full_engine``; dedicated incremental
allocation remains ``NOT_READY`` there because its independent source ledger
has not been integrated.  Quality feedback for the shared slice remains an
explicit ``NOT_READY`` coupling gate outside the isolated joint solver.
``solve_joint_quality_allocation`` is the bounded multi-data-centre
co-current prerequisite.  It is intentionally callback based: the caller
must provide the actual quality-limited plan for each trial allocation, so no
quality state is invented by the allocator itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Callable, Iterable, Literal, Mapping


AllocationPolicy = Literal["shared_incumbent_first", "dedicated_incremental"]


@dataclass(frozen=True, slots=True)
class JointQualityRequest:
    """One incremental consumer in a shared quality/allocation solve.

    ``target_reclaimed_fraction`` is the maximum fraction of that consumer's
    *actual* external makeup which may be supplied by the shared pool.  The
    external makeup is supplied by the evaluator at each trial allocation;
    this is what makes the allocation a co-current fixed point rather than a
    one-pass pro-rata split.

    ``incumbent_reclaimed_ml`` is protected before incremental demand.  It is
    normally zero for a new data centre, while existing municipal claims can
    be represented without changing the allocator contract.
    """

    consumer_id: str
    target_reclaimed_fraction: float
    incumbent_reclaimed_ml: float = 0.0
    max_reclaimed_ml: float = float("inf")
    potable_baseline_ml: float = 0.0


@dataclass(frozen=True, slots=True)
class JointPlanEvaluation:
    """Evaluator output for one trial reclaimed allocation.

    A caller may calculate this with :func:`aiuwm.data_center.calculate_data_center_plan`
    or with an equivalent quality model.  ``quality_solver_residual`` is kept
    separate from the allocation residual so a converged water split cannot
    mask a failed quality fixed point.
    """

    external_makeup_ml: float
    cycles_of_concentration: float = float("nan")
    reclaimed_quality_mg_l: Mapping[str, float] = field(default_factory=dict)
    quality_solver_status: str = "converged"
    quality_solver_residual: float = 0.0


@dataclass(frozen=True, slots=True)
class JointQualityAllocation:
    """Final per-consumer state from a joint quality/allocation solve."""

    consumer_id: str
    reclaimed_allocated_ml: float
    reclaimed_capacity_ml: float
    reclaimed_fraction: float
    external_makeup_ml: float
    cycles_of_concentration: float
    reclaimed_quality_mg_l: Mapping[str, float]
    fixed_point_residual_ml: float
    quality_solver_status: str
    quality_solver_residual: float


@dataclass(frozen=True, slots=True)
class JointQualityAllocationResult:
    """Auditable result of the isolated multi-DC joint solver.

    The result is ``READY_JOINT_CO_CURRENT`` only when a unique fixed point is
    found and every evaluator reports a converged quality solve.  Any other
    state remains explicitly ``NOT_READY_JOINT_QUALITY_ALLOCATION`` so the
    main model cannot accidentally promote a volume-only ledger to E3.
    """

    scenario_id: str
    policy: Literal["shared_incumbent_first"]
    available_supply_ml: float
    incumbent_requested_ml: float
    incumbent_allocated_ml: float
    incremental_budget_ml: float
    total_allocated_ml: float
    unallocated_supply_ml: float
    closure_residual_ml: float
    status: str
    quality_integration_status: str
    iterations: int
    root_count: int
    max_fixed_point_residual_ml: float
    allocations: tuple[JointQualityAllocation, ...]


JointPlanEvaluator = Callable[[JointQualityRequest, float], JointPlanEvaluation]


@dataclass(frozen=True, slots=True)
class AllocationRequest:
    """One consumer's daily reclaimed-water request.

    Parameters are volumes in ML/day (or another common volume unit).  The
    same request type is accepted by both policies:

    ``demand_ml``
        Maximum reclaimed volume the consumer can use in this scenario.
    ``incumbent_reclaimed_ml``
        Existing reclaimed-water claim.  Shared allocation protects this
        claim before serving incremental demand.  Dedicated allocation does
        not draw it from the shared pool.
    ``dedicated_supply_ml``
        Dedicated incremental offer for this consumer.  It is used only by
        :func:`allocate_dedicated_incremental` and is clipped at incremental
        demand.
    ``potable_baseline_ml``
        Potable volume that reclaimed water can displace for this consumer.
        It caps the reported ``potable_volume_displaced_ml``.  Under the
        shared policy, it also caps potable fallback caused by an unserved
        incumbent claim.
    """

    consumer_id: str
    demand_ml: float
    incumbent_reclaimed_ml: float = 0.0
    dedicated_supply_ml: float = 0.0
    potable_baseline_ml: float = 0.0


@dataclass(frozen=True, slots=True)
class ConsumerAllocation:
    """Auditable allocation for one consumer."""

    consumer_id: str
    requested_ml: float
    incumbent_requested_ml: float
    incumbent_allocated_ml: float
    incremental_requested_ml: float
    incremental_allocated_ml: float
    total_allocated_ml: float
    unmet_reclaimed_ml: float
    potable_volume_displaced_ml: float
    displaced_incumbent_potable_ml: float


@dataclass(frozen=True, slots=True)
class AllocationResult:
    """Result and conservation diagnostics for one allocation scenario."""

    scenario_id: str
    policy: AllocationPolicy
    available_supply_ml: float
    total_allocated_ml: float
    unallocated_supply_ml: float
    closure_residual_ml: float
    preserved_incumbent_reclaimed_ml: float
    displaced_incumbent_potable_ml: float
    potable_volume_displaced_ml: float
    allocations: tuple[ConsumerAllocation, ...]

    @property
    def overdraw_ml(self) -> float:
        """Positive supply overdraw (always zero for a valid result)."""

        return max(0.0, self.total_allocated_ml - self.available_supply_ml)

    @property
    def available_surplus_ml(self) -> float:
        """Backward-compatible alias; use :attr:`available_supply_ml`."""

        return self.available_supply_ml

    @property
    def unallocated_surplus_ml(self) -> float:
        """Backward-compatible alias; use :attr:`unallocated_supply_ml`."""

        return self.unallocated_supply_ml


def allocate_shared_surplus(
    scenario_id: str,
    available_supply_ml: float,
    requests: Iterable[AllocationRequest],
) -> AllocationResult:
    """Allocate available shared supply incumbent-first, then pro-rata.

    Existing claims are fulfilled before incremental requests.  When the
    available supply cannot cover all existing claims, those claims are
    reduced proportionally and incremental demand receives zero.  Every
    result is sorted by ``consumer_id``; changing the input order therefore
    cannot change the policy outcome.
    """

    normalized = _normalize_inputs(scenario_id, available_supply_ml, requests)
    available = float(available_supply_ml)
    incumbent_total = math.fsum(item.incumbent_reclaimed_ml for item in normalized)

    if incumbent_total <= available:
        incumbent_allocations = {
            item.consumer_id: item.incumbent_reclaimed_ml for item in normalized
        }
        incremental_capacity = {
            item.consumer_id: max(0.0, item.demand_ml - item.incumbent_reclaimed_ml)
            for item in normalized
        }
        incremental_budget = max(0.0, available - incumbent_total)
        incremental_allocations = _pro_rata(
            incremental_budget, incremental_capacity
        )
    else:
        # Incumbents have priority, but a shortage must remain order
        # independent.  Pro-rata reduction is the only deterministic policy
        # available without an additional, explicit priority field.
        incumbent_allocations = _pro_rata(available, {
            item.consumer_id: item.incumbent_reclaimed_ml for item in normalized
        })
        incremental_allocations = {item.consumer_id: 0.0 for item in normalized}

    return _build_result(
        scenario_id=scenario_id,
        policy="shared_incumbent_first",
        available_supply_ml=available,
        requests=normalized,
        incumbent_allocations=incumbent_allocations,
        incremental_allocations=incremental_allocations,
    )


def solve_joint_quality_allocation(
    scenario_id: str,
    available_supply_ml: float,
    requests: Iterable[JointQualityRequest],
    evaluator: JointPlanEvaluator,
    *,
    max_iterations: int = 200,
    tolerance_ml: float = 1e-10,
    quality_tolerance: float = 1e-10,
    damping: float = 0.5,
    root_tolerance_ml: float = 1e-8,
) -> JointQualityAllocationResult:
    """Solve shared-pool allocation and quality demand as one fixed point.

    For a trial reclaimed allocation ``x_i``, ``evaluator`` returns the
    actual external makeup ``E_i`` and quality-solver diagnostics.  The
    incremental capacity is ``target_i * E_i`` (optionally capped by
    ``max_reclaimed_ml``), after which incumbent claims are reserved and the
    remaining supply is allocated pro-rata.  The map is iterated with bounded
    damping from several deterministic starts (zero, incumbent-only, the
    first allocation map and two scaled first-map points).  A single common root is required; disagreement
    between starts is reported as ``non_unique`` rather than silently
    selecting one result.

    This function is deliberately independent of :class:`FullAIUWMModel`.
    It gives the main model a reviewable prerequisite for multi-DC integration
    while keeping legacy and one-DC paths unchanged.
    """

    normalized = _normalize_joint_inputs(scenario_id, available_supply_ml, requests)
    if not callable(evaluator):
        raise TypeError("evaluator must be callable")
    if not isinstance(max_iterations, int) or max_iterations <= 0:
        raise ValueError("max_iterations must be a positive integer")
    _validate_nonnegative_finite("tolerance_ml", tolerance_ml)
    _validate_nonnegative_finite("quality_tolerance", quality_tolerance)
    if not isinstance(damping, (int, float)) or not math.isfinite(float(damping)):
        raise ValueError("damping must be finite")
    damping = float(damping)
    if not 0.0 < damping <= 1.0:
        raise ValueError("damping must be in (0, 1]")
    _validate_nonnegative_finite("root_tolerance_ml", root_tolerance_ml)

    available = float(available_supply_ml)
    incumbent_requested = math.fsum(
        item.incumbent_reclaimed_ml for item in normalized
    )
    if incumbent_requested <= available:
        incumbent_allocated = {
            item.consumer_id: item.incumbent_reclaimed_ml for item in normalized
        }
    else:
        incumbent_allocated = _pro_rata(
            available,
            {item.consumer_id: item.incumbent_reclaimed_ml for item in normalized},
        )
    incumbent_total_allocated = math.fsum(incumbent_allocated.values())

    def evaluate_all(
        allocations: Mapping[str, float],
    ) -> tuple[dict[str, JointPlanEvaluation], dict[str, float]]:
        evaluations: dict[str, JointPlanEvaluation] = {}
        capacities: dict[str, float] = {}
        for request in normalized:
            trial = max(0.0, float(allocations.get(request.consumer_id, 0.0)))
            value = evaluator(request, trial)
            if not isinstance(value, JointPlanEvaluation):
                raise TypeError(
                    "evaluator must return JointPlanEvaluation values"
                )
            _validate_joint_evaluation(request.consumer_id, value)
            evaluations[request.consumer_id] = value
            capacity = min(
                value.external_makeup_ml * request.target_reclaimed_fraction,
                request.max_reclaimed_ml,
            )
            # Protect an incumbent claim even if a trial quality state would
            # otherwise lower the target capacity; the resulting shortfall is
            # visible through the shared-pool incumbent allocation itself.
            capacities[request.consumer_id] = max(
                request.incumbent_reclaimed_ml, capacity
            )
        return evaluations, capacities

    def map_allocation(
        capacities: Mapping[str, float],
    ) -> dict[str, float]:
        incremental_budget = max(0.0, available - incumbent_total_allocated)
        incremental_capacities = {
            request.consumer_id: max(
                0.0,
                float(capacities.get(request.consumer_id, 0.0))
                - request.incumbent_reclaimed_ml,
            )
            for request in normalized
        }
        incremental = _pro_rata(incremental_budget, incremental_capacities)
        return {
            request.consumer_id: min(
                float(capacities.get(request.consumer_id, 0.0)),
                float(incumbent_allocated.get(request.consumer_id, 0.0))
                + incremental.get(request.consumer_id, 0.0),
            )
            for request in normalized
        }

    def iterate(
        initial: Mapping[str, float],
    ) -> tuple[
        bool,
        int,
        dict[str, float],
        dict[str, JointPlanEvaluation],
        dict[str, float],
        float,
    ]:
        current = {
            request.consumer_id: max(
                0.0, float(initial.get(request.consumer_id, 0.0))
            )
            for request in normalized
        }
        last_evaluations: dict[str, JointPlanEvaluation] = {}
        last_capacities: dict[str, float] = {}
        residual = float("inf")
        for iteration in range(1, max_iterations + 1):
            last_evaluations, last_capacities = evaluate_all(current)
            mapped = map_allocation(last_capacities)
            residual = max(
                (abs(mapped[item.consumer_id] - current[item.consumer_id])
                 for item in normalized),
                default=0.0,
            )
            if residual <= tolerance_ml:
                # Re-evaluate at the undamped fixed point so reported plan
                # diagnostics correspond exactly to reported allocations.
                final_evaluations, final_capacities = evaluate_all(mapped)
                final_map = map_allocation(final_capacities)
                final_residual = max(
                    (abs(final_map[item.consumer_id] - mapped[item.consumer_id])
                     for item in normalized),
                    default=0.0,
                )
                return (
                    final_residual <= tolerance_ml,
                    iteration,
                    mapped,
                    final_evaluations,
                    final_capacities,
                    final_residual,
                )
            current = {
                item.consumer_id: current[item.consumer_id]
                + damping * (mapped[item.consumer_id] - current[item.consumer_id])
                for item in normalized
            }
        return False, max_iterations, current, last_evaluations, last_capacities, residual

    zero_start = {item.consumer_id: 0.0 for item in normalized}
    incumbent_start = dict(incumbent_allocated)
    first_evaluations, first_capacities = evaluate_all(zero_start)
    first_start = map_allocation(first_capacities)
    starts = [zero_start, incumbent_start, first_start]
    for scale in (0.25, 0.5):
        starts.append(
            {
                item.consumer_id: scale * first_start[item.consumer_id]
                for item in normalized
            }
        )
    roots: list[
        tuple[
            dict[str, float],
            dict[str, JointPlanEvaluation],
            dict[str, float],
            int,
            float,
        ]
    ] = []
    max_iterations_seen = 0
    for start in starts:
        converged, iterations, allocation, evaluations, capacities, residual = iterate(
            start
        )
        max_iterations_seen = max(max_iterations_seen, iterations)
        if converged:
            if not any(
                max(
                    abs(allocation[item.consumer_id] - prior[0][item.consumer_id])
                    for item in normalized
                )
                <= root_tolerance_ml
                for prior in roots
            ):
                roots.append((allocation, evaluations, capacities, iterations, residual))

    root_count = len(roots)
    quality_ready = False
    chosen_allocation: dict[str, float]
    chosen_evaluations: dict[str, JointPlanEvaluation]
    chosen_capacities: dict[str, float]
    chosen_iterations = max_iterations_seen
    chosen_residual = float("inf")
    if root_count == 1:
        (
            chosen_allocation,
            chosen_evaluations,
            chosen_capacities,
            chosen_iterations,
            chosen_residual,
        ) = roots[0]
        quality_ready = all(
            value.quality_solver_status in {"converged", "ready"}
            and abs(value.quality_solver_residual) <= quality_tolerance
            for value in chosen_evaluations.values()
        )
        status = "converged_unique" if quality_ready else "quality_not_converged"
    elif root_count > 1:
        # A root ambiguity is a scientific failure even when each root closes
        # volume; selecting one would make downstream E3 estimates arbitrary.
        chosen_allocation, chosen_evaluations, chosen_capacities, chosen_iterations, chosen_residual = roots[0]
        status = "non_unique"
    else:
        # Preserve the deterministic incumbent transaction even when the
        # incremental quality map does not converge.  The result remains
        # NOT_READY, but it does not erase a protected claim from the audit
        # ledger merely because the quality root failed.
        chosen_allocation = dict(incumbent_allocated)
        chosen_evaluations, chosen_capacities = evaluate_all(chosen_allocation)
        status = "no_convergence"

    allocations: list[JointQualityAllocation] = []
    for request in normalized:
        consumer_id = request.consumer_id
        value = chosen_evaluations[consumer_id]
        allocated = max(0.0, float(chosen_allocation.get(consumer_id, 0.0)))
        external = value.external_makeup_ml
        fraction = allocated / external if external > 0.0 else 0.0
        capacity = chosen_capacities.get(consumer_id, 0.0)
        mapped_allocated = map_allocation(chosen_capacities).get(consumer_id, 0.0)
        allocations.append(
            JointQualityAllocation(
                consumer_id=consumer_id,
                reclaimed_allocated_ml=allocated,
                reclaimed_capacity_ml=capacity,
                reclaimed_fraction=fraction,
                external_makeup_ml=external,
                cycles_of_concentration=value.cycles_of_concentration,
                reclaimed_quality_mg_l=dict(value.reclaimed_quality_mg_l),
                fixed_point_residual_ml=allocated - mapped_allocated,
                quality_solver_status=value.quality_solver_status,
                quality_solver_residual=value.quality_solver_residual,
            )
        )
    total_allocated = math.fsum(item.reclaimed_allocated_ml for item in allocations)
    unallocated = max(0.0, available - total_allocated)
    closure = available - total_allocated - unallocated
    integration_status = (
        "READY_JOINT_CO_CURRENT"
        if status == "converged_unique" and quality_ready
        else "NOT_READY_JOINT_QUALITY_ALLOCATION"
    )
    return JointQualityAllocationResult(
        scenario_id=scenario_id,
        policy="shared_incumbent_first",
        available_supply_ml=available,
        incumbent_requested_ml=incumbent_requested,
        incumbent_allocated_ml=incumbent_total_allocated,
        incremental_budget_ml=max(0.0, available - incumbent_total_allocated),
        total_allocated_ml=total_allocated,
        unallocated_supply_ml=unallocated,
        closure_residual_ml=closure,
        status=status,
        quality_integration_status=integration_status,
        iterations=chosen_iterations,
        root_count=root_count,
        max_fixed_point_residual_ml=chosen_residual,
        allocations=tuple(allocations),
    )


def allocate_dedicated_incremental(
    scenario_id: str,
    available_supply_ml: float,
    requests: Iterable[AllocationRequest],
) -> AllocationResult:
    """Allocate dedicated incremental offers without incumbent displacement.

    Only ``dedicated_supply_ml`` up to each consumer's incremental demand is
    eligible.  If eligible offers exceed the shared scenario surplus, they
    are scaled pro-rata.  This keeps the result order-independent while
    preserving the dedicated policy's defining property: no incumbent claim
    is taken from the shared pool.
    """

    normalized = _normalize_inputs(scenario_id, available_supply_ml, requests)
    available = float(available_supply_ml)
    incremental_capacity = {
        item.consumer_id: min(
            item.dedicated_supply_ml,
            max(0.0, item.demand_ml - item.incumbent_reclaimed_ml),
        )
        for item in normalized
    }
    incremental_allocations = _pro_rata(available, incremental_capacity)
    incumbent_allocations = {item.consumer_id: 0.0 for item in normalized}

    return _build_result(
        scenario_id=scenario_id,
        policy="dedicated_incremental",
        available_supply_ml=available,
        requests=normalized,
        incumbent_allocations=incumbent_allocations,
        incremental_allocations=incremental_allocations,
    )


def _normalize_inputs(
    scenario_id: str,
    available_supply_ml: float,
    requests: Iterable[AllocationRequest],
) -> tuple[AllocationRequest, ...]:
    if not isinstance(scenario_id, str) or not scenario_id.strip():
        raise ValueError("scenario_id must be a non-empty string")
    _validate_volume("available_supply_ml", available_supply_ml)
    if available_supply_ml < 0.0:
        raise ValueError("available_supply_ml cannot be negative")

    raw_requests = tuple(requests)
    if any(not isinstance(item, AllocationRequest) for item in raw_requests):
        raise TypeError("requests must contain AllocationRequest values")
    normalized = tuple(sorted(raw_requests, key=lambda item: item.consumer_id))
    seen: set[str] = set()
    for item in normalized:
        if not isinstance(item.consumer_id, str) or not item.consumer_id.strip():
            raise ValueError("consumer_id must be a non-empty string")
        if item.consumer_id in seen:
            raise ValueError(f"duplicate consumer_id: {item.consumer_id}")
        seen.add(item.consumer_id)
        for name in (
            "demand_ml",
            "incumbent_reclaimed_ml",
            "dedicated_supply_ml",
            "potable_baseline_ml",
        ):
            value = getattr(item, name)
            _validate_volume(f"{item.consumer_id}.{name}", value)
            if value < 0.0:
                raise ValueError(f"{item.consumer_id}.{name} cannot be negative")
        if item.incumbent_reclaimed_ml > item.demand_ml:
            raise ValueError(
                f"{item.consumer_id}.incumbent_reclaimed_ml cannot exceed demand_ml"
            )
    return normalized


def _normalize_joint_inputs(
    scenario_id: str,
    available_supply_ml: float,
    requests: Iterable[JointQualityRequest],
) -> tuple[JointQualityRequest, ...]:
    if not isinstance(scenario_id, str) or not scenario_id.strip():
        raise ValueError("scenario_id must be a non-empty string")
    _validate_nonnegative_finite("available_supply_ml", available_supply_ml)
    raw_requests = tuple(requests)
    if any(not isinstance(item, JointQualityRequest) for item in raw_requests):
        raise TypeError("requests must contain JointQualityRequest values")
    normalized = tuple(sorted(raw_requests, key=lambda item: item.consumer_id))
    seen: set[str] = set()
    for item in normalized:
        if not isinstance(item.consumer_id, str) or not item.consumer_id.strip():
            raise ValueError("consumer_id must be a non-empty string")
        if item.consumer_id in seen:
            raise ValueError(f"duplicate consumer_id: {item.consumer_id}")
        seen.add(item.consumer_id)
        target = float(item.target_reclaimed_fraction)
        if not math.isfinite(target) or not 0.0 <= target <= 1.0:
            raise ValueError(
                f"{item.consumer_id}.target_reclaimed_fraction must be between 0 and 1"
            )
        for name, value in (
            ("incumbent_reclaimed_ml", item.incumbent_reclaimed_ml),
            ("potable_baseline_ml", item.potable_baseline_ml),
        ):
            _validate_nonnegative_finite(f"{item.consumer_id}.{name}", value)
        max_reclaimed = float(item.max_reclaimed_ml)
        if math.isnan(max_reclaimed) or max_reclaimed < 0.0:
            raise ValueError(
                f"{item.consumer_id}.max_reclaimed_ml must be non-negative or infinity"
            )
        if item.incumbent_reclaimed_ml > max_reclaimed:
            raise ValueError(
                f"{item.consumer_id}.incumbent_reclaimed_ml cannot exceed max_reclaimed_ml"
            )
    return normalized


def _validate_nonnegative_finite(name: str, value: float) -> None:
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite and non-negative")
    if float(value) < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")


def _validate_joint_evaluation(
    consumer_id: str, value: JointPlanEvaluation
) -> None:
    _validate_nonnegative_finite(
        f"{consumer_id}.external_makeup_ml", value.external_makeup_ml
    )
    coc = float(value.cycles_of_concentration)
    if not math.isnan(coc) and (not math.isfinite(coc) or coc < 0.0):
        raise ValueError(
            f"{consumer_id}.cycles_of_concentration must be finite and non-negative, or NaN"
        )
    if not isinstance(value.quality_solver_status, str):
        raise ValueError(f"{consumer_id}.quality_solver_status must be a string")
    if not isinstance(value.reclaimed_quality_mg_l, Mapping):
        raise ValueError(f"{consumer_id}.reclaimed_quality_mg_l must be a mapping")
    for name, concentration in value.reclaimed_quality_mg_l.items():
        _validate_nonnegative_finite(
            f"{consumer_id}.reclaimed_quality_mg_l[{name}]", concentration
        )
    if not isinstance(value.quality_solver_residual, (int, float)) or not math.isfinite(
        float(value.quality_solver_residual)
    ):
        raise ValueError(
            f"{consumer_id}.quality_solver_residual must be finite"
        )
    if float(value.quality_solver_residual) < 0.0:
        raise ValueError(
            f"{consumer_id}.quality_solver_residual cannot be negative"
        )


def _validate_volume(name: str, value: float) -> None:
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{name} must be a finite number")


def _pro_rata(budget: float, capacities: dict[str, float]) -> dict[str, float]:
    """Return order-independent proportional allocations capped by capacity."""

    budget = max(0.0, float(budget))
    ordered = tuple(sorted(capacities.items()))
    total_capacity = math.fsum(max(0.0, float(value)) for _, value in ordered)
    if total_capacity <= 0.0 or budget <= 0.0:
        return {consumer_id: 0.0 for consumer_id, _ in ordered}
    if budget >= total_capacity:
        return {
            consumer_id: max(0.0, float(capacity))
            for consumer_id, capacity in ordered
        }
    ratio = budget / total_capacity
    allocations = {
        consumer_id: max(0.0, float(capacity)) * ratio
        for consumer_id, capacity in ordered
    }
    # Floating-point multiplication can make the sum exceed the budget by a
    # few ulps.  Remove any excess deterministically from the final sorted
    # claimant so the no-overdraw invariant is strict at result level.
    excess = math.fsum(allocations.values()) - budget
    if excess > 0.0:
        for consumer_id, _ in reversed(ordered):
            reducible = min(allocations[consumer_id], excess)
            allocations[consumer_id] -= reducible
            excess -= reducible
            if excess <= 0.0:
                break
    return allocations


def _build_result(
    *,
    scenario_id: str,
    policy: AllocationPolicy,
    available_supply_ml: float,
    requests: tuple[AllocationRequest, ...],
    incumbent_allocations: dict[str, float],
    incremental_allocations: dict[str, float],
) -> AllocationResult:
    rows: list[ConsumerAllocation] = []
    for item in requests:
        incumbent_allocated = min(
            item.incumbent_reclaimed_ml,
            max(0.0, float(incumbent_allocations.get(item.consumer_id, 0.0))),
        )
        incremental_requested = max(0.0, item.demand_ml - item.incumbent_reclaimed_ml)
        incremental_allocated = min(
            incremental_requested,
            max(0.0, float(incremental_allocations.get(item.consumer_id, 0.0))),
        )
        total_allocated = incumbent_allocated + incremental_allocated
        unmet = max(0.0, item.demand_ml - total_allocated)
        displaced_potable = min(total_allocated, item.potable_baseline_ml)
        incumbent_shortfall = max(0.0, item.incumbent_reclaimed_ml - incumbent_allocated)
        # Dedicated supply is incremental and leaves the incumbent pool
        # untouched.  Its zero incumbent allocation is therefore not a
        # shortfall and must not be counted as displaced potable demand.
        displaced_incumbent_potable = (
            min(incumbent_shortfall, item.potable_baseline_ml)
            if policy == "shared_incumbent_first"
            else 0.0
        )
        rows.append(
            ConsumerAllocation(
                consumer_id=item.consumer_id,
                requested_ml=item.demand_ml,
                incumbent_requested_ml=item.incumbent_reclaimed_ml,
                incumbent_allocated_ml=incumbent_allocated,
                incremental_requested_ml=incremental_requested,
                incremental_allocated_ml=incremental_allocated,
                total_allocated_ml=total_allocated,
                unmet_reclaimed_ml=unmet,
                potable_volume_displaced_ml=displaced_potable,
                displaced_incumbent_potable_ml=displaced_incumbent_potable,
            )
        )

    total_allocated = math.fsum(row.total_allocated_ml for row in rows)
    unallocated = max(0.0, float(available_supply_ml) - total_allocated)
    # The residual is intentionally retained instead of rounded away.  It
    # exposes floating-point drift to a caller's chosen closure tolerance.
    residual = float(available_supply_ml) - total_allocated - unallocated
    preserved_incumbent = math.fsum(row.incumbent_allocated_ml for row in rows)
    if policy == "dedicated_incremental":
        # The dedicated transaction leaves the incumbent pool untouched.  A
        # caller can use this value to prove that dedicated supply was
        # preserved instead of silently treating it as zero allocation.
        preserved_incumbent = math.fsum(row.incumbent_requested_ml for row in rows)
    return AllocationResult(
        scenario_id=scenario_id,
        policy=policy,
        available_supply_ml=float(available_supply_ml),
        total_allocated_ml=total_allocated,
        unallocated_supply_ml=unallocated,
        closure_residual_ml=residual,
        preserved_incumbent_reclaimed_ml=preserved_incumbent,
        displaced_incumbent_potable_ml=math.fsum(
            row.displaced_incumbent_potable_ml for row in rows
        ),
        potable_volume_displaced_ml=math.fsum(
            row.potable_volume_displaced_ml for row in rows
        ),
        allocations=tuple(rows),
    )


__all__ = [
    "AllocationPolicy",
    "AllocationRequest",
    "ConsumerAllocation",
    "AllocationResult",
    "JointQualityRequest",
    "JointPlanEvaluation",
    "JointQualityAllocation",
    "JointQualityAllocationResult",
    "allocate_shared_surplus",
    "solve_joint_quality_allocation",
    "allocate_dedicated_incremental",
]
