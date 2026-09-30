"""Standalone R10 E4 adaptation accounting.

This module is deliberately decoupled from :mod:`aiuwm.full_engine`.  It
evaluates engineering adaptations against an already computed daily cooling
ledger and makes every water, solute, energy, carbon, and cost term explicit.
The module is suitable for a small E4 pilot or an audit fixture; it does not
claim that the adaptation state has been coupled to the main model.

The four policies are:

``A0``
    No adaptation.  Reclaimed feed is used directly and no treatment sink is
    invented.
``A1``
    Chemical or side-stream treatment.  Per-solute removal, treatment energy,
    chemical cost, reject, and unreturned fractions are accounted for.
``A2``
    Membrane treatment.  Recovery determines permeate and reject volumes;
    rejection fractions determine solute fate.  Annualised CAPEX and OPEX are
    charged to the active cooling days.
``A3``
    Hybrid or dry heat rejection.  ``wet_fraction`` determines water demand;
    dry operation can add an explicit PUE and/or energy penalty.

All volumes use ML, solute masses use kg, energy uses kWh, and carbon uses
kgCO2e.  Costs are in the caller's currency units.  The result always keeps
numeric accounting for an infeasible strategy, while its E4 estimands
``E_adapt`` and ``C_adapt`` are the literal string ``"NA"``.  This prevents an
infeasible strategy from entering a ranking as zero or infinity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Iterable, Literal, Mapping, Sequence


AdaptationPolicy = Literal["A0", "A1", "A2", "A3"]
AdaptationStatus = Literal["feasible", "infeasible"]
NA = "NA"
_EPS = 1.0e-12


def _nonnegative(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be a finite non-negative number")
    return value


def _fraction(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be within [0, 1]")
    return value


def _mapping_numbers(values: Mapping[str, float] | None, name: str) -> dict[str, float]:
    if values is None:
        return {}
    if not isinstance(values, Mapping):
        raise TypeError(f"{name} must be a mapping")
    out: dict[str, float] = {}
    for key, value in values.items():
        text = str(key)
        out[text] = _nonnegative(value, f"{name}[{text!r}]")
    return out


@dataclass(frozen=True, slots=True)
class CoolingDayLedger:
    """One cooling-day demand and solute ledger.

    ``water_demand_ml`` is the gross service requirement.  ``reclaimed_supply_ml``
    is a non-fresh feed available to the adaptation transaction.  If
    ``freshwater_baseline_ml`` is omitted, the baseline withdrawal is the gross
    demand.  ``freshwater_available_ml`` is optional; omitting it means that
    freshwater fallback is unconstrained, while providing it allows SLA
    failures to be represented explicitly.

    ``solute_load_kg`` describes solute mass carried by the non-fresh feed.  A
    feed fraction is applied when the non-fresh feed is smaller than demand.
    This convention keeps the ledger closed without silently assigning
    solutes to an unobserved freshwater stream.
    """

    day_id: str
    water_demand_ml: float
    solute_load_kg: Mapping[str, float] = field(default_factory=dict)
    reclaimed_supply_ml: float = 0.0
    freshwater_baseline_ml: float | None = None
    freshwater_available_ml: float | None = None
    it_energy_kwh: float = 0.0
    service_required: bool = True

    def __post_init__(self) -> None:
        if not str(self.day_id):
            raise ValueError("day_id must be non-empty")
        _nonnegative(self.water_demand_ml, "water_demand_ml")
        _nonnegative(self.reclaimed_supply_ml, "reclaimed_supply_ml")
        if self.freshwater_baseline_ml is not None:
            _nonnegative(self.freshwater_baseline_ml, "freshwater_baseline_ml")
        if self.freshwater_available_ml is not None:
            _nonnegative(self.freshwater_available_ml, "freshwater_available_ml")
        _nonnegative(self.it_energy_kwh, "it_energy_kwh")
        _mapping_numbers(self.solute_load_kg, "solute_load_kg")

    @property
    def demand_ml(self) -> float:
        """Short alias used by ledger adapters."""

        return float(self.water_demand_ml)


# A readable alias for callers that use “record” rather than “ledger”.
CoolingDayRecord = CoolingDayLedger
AdaptationLedger = CoolingDayLedger


def cooling_ledger_from_data_center_daily(
    rows: Iterable[Mapping[str, Any]] | Any,
    *,
    freshwater_baseline_rows: Iterable[Mapping[str, Any]] | Any | None = None,
) -> tuple[CoolingDayLedger, ...]:
    """Create an E4 ledger from ``FullAIUWMModelResult.data_center_daily``.

    This is a read-only boundary adapter.  It exposes the main model's
    already-computed daily cooling transaction to the standalone E4 ledger;
    it does not feed adaptation decisions back into the model.  ``rows`` may
    be the pandas data frame emitted by the engine or an iterable of mapping
    rows (for example, records loaded from CSV/JSON).

    ``freshwater_baseline_rows`` may provide a separately simulated paired
    freshwater-only counterfactual (for example, B2). Rows are matched by
    date and data-centre ID and must match the adaptation rows exactly. When
    omitted, the ledger compares adaptation with the observed potable use in
    the same run; that is an incremental within-run reference and must not be
    reported as B2-to-B1 or city-scale savings. The gross service demand is
    ``external_makeup_ml``. If quality diagnostics are present, reclaimed-feed
    concentrations are converted to kg using the ML·mg/L unit identity.
    Missing quality diagnostics are represented by an empty solute ledger
    rather than an invented value.
    """

    def records(value: Iterable[Mapping[str, Any]] | Any) -> list[Mapping[str, Any]]:
        if hasattr(value, "to_dict") and callable(value.to_dict):
            value = value.to_dict(orient="records")
        if isinstance(value, Mapping):
            value = [value]
        output_rows = list(value)
        if any(not isinstance(row, Mapping) for row in output_rows):
            raise TypeError("data-center rows must be mappings")
        return output_rows

    source_rows = records(rows)
    baseline_by_key: dict[tuple[str, str], float] | None = None
    if freshwater_baseline_rows is not None:
        baseline_by_key = {}
        for index, raw in enumerate(records(freshwater_baseline_rows)):
            date = raw.get("date", raw.get("day"))
            data_center_id = raw.get("data_center_id", raw.get("component_id"))
            if date is None or data_center_id is None:
                raise ValueError("paired freshwater baseline rows require date and data_center_id")
            key = (str(date), str(data_center_id))
            if key in baseline_by_key:
                raise ValueError(f"duplicate freshwater baseline row: {key[0]}::{key[1]}")
            amount = raw.get("potable_water_ml", raw.get("external_withdrawal_ml"))
            if amount is None:
                raise ValueError(f"freshwater baseline row {index} lacks potable/external withdrawal")
            baseline_by_key[key] = _nonnegative(amount, f"freshwater_baseline_ml[{key!r}]")

    output: list[CoolingDayLedger] = []
    source_keys: set[tuple[str, str]] = set()
    for index, raw in enumerate(source_rows):
        if not isinstance(raw, Mapping):
            raise TypeError(f"data-center row {index} must be a mapping")

        def _value(*names: str, default: Any = None) -> Any:
            for name in names:
                if name in raw:
                    return raw[name]
            return default

        date = _value("date", "day", default=str(index))
        data_center_id = _value("data_center_id", "component_id", default=str(index))
        day_id = f"{date}::{data_center_id}"
        key = (str(date), str(data_center_id))
        if key in source_keys:
            raise ValueError(f"duplicate data-center daily row: {day_id}")
        source_keys.add(key)
        demand_ml = _value("external_makeup_ml", "gross_makeup_ml", "water_demand_ml", default=0.0)
        reclaimed_ml = _value("reclaimed_water_ml", "reclaimed_supply_ml", "reuse_delivered_ml", default=0.0)
        if baseline_by_key is None:
            baseline_ml = _value("potable_water_ml", "freshwater_baseline_ml", default=None)
        else:
            if key not in baseline_by_key:
                raise ValueError(f"paired freshwater baseline missing row: {day_id}")
            baseline_ml = baseline_by_key[key]
        it_energy_kwh = _value("it_energy_kwh", default=None)
        if it_energy_kwh is None:
            it_energy_kwh = float(_value("it_energy_mwh", default=0.0)) * 1000.0

        quality = _value("quality_reclaimed_source_mg_l", default={})
        solute_load: dict[str, float] = {}
        if isinstance(quality, Mapping):
            reclaimed_ml_float = float(reclaimed_ml)
            for name, concentration in quality.items():
                # 1 ML * 1 mg/L = 1 kg.
                concentration_value = _nonnegative(
                    concentration, f"quality_reclaimed_source_mg_l[{name!r}]"
                )
                solute_load[str(name)] = max(0.0, reclaimed_ml_float) * concentration_value
        explicit_solute = _value("solute_load_kg", default=None)
        if explicit_solute is not None:
            solute_load = _mapping_numbers(explicit_solute, "solute_load_kg")

        output.append(
            CoolingDayLedger(
                day_id=day_id,
                water_demand_ml=demand_ml,
                solute_load_kg=solute_load,
                reclaimed_supply_ml=reclaimed_ml,
                freshwater_baseline_ml=baseline_ml,
                freshwater_available_ml=_value("freshwater_available_ml", default=None),
                it_energy_kwh=it_energy_kwh,
                service_required=bool(_value("service_required", default=True)),
            )
        )
    if baseline_by_key is not None and source_keys != set(baseline_by_key):
        extra = sorted(set(baseline_by_key) - source_keys)
        raise ValueError(f"paired freshwater baseline has unmatched rows: {extra[:3]}")
    return tuple(output)


@dataclass(frozen=True, slots=True)
class AdaptationConfig:
    """Parameters for one R10 E4 adaptation policy."""

    policy: AdaptationPolicy
    city_saving_threshold_ml: float = 0.0
    min_sla_reliability: float = 1.0
    max_energy_kwh: float | None = None
    max_carbon_kg_co2e: float | None = None
    max_cost: float | None = None
    max_reject_ml: float | None = None

    # A1 chemical / side-stream treatment.
    solute_removal_fractions: Mapping[str, float] = field(default_factory=dict)
    side_stream_fraction: float = 1.0
    treatment_reject_fraction: float = 0.0
    treatment_unreturned_fraction: float = 0.0
    treatment_energy_kwh_per_ml: float = 0.0
    treatment_fixed_energy_kwh_per_day: float = 0.0
    chemical_cost_per_kg_removed: float = 0.0
    treatment_fixed_cost_per_day: float = 0.0

    # A2 membrane treatment.
    membrane_recovery_fraction: float = 1.0
    membrane_rejection_fractions: Mapping[str, float] = field(default_factory=dict)
    membrane_unreturned_fraction: float = 0.0
    membrane_energy_kwh_per_ml: float = 0.0
    membrane_capex: float = 0.0
    membrane_lifetime_years: float = 1.0
    membrane_annual_opex: float = 0.0

    # A3 hybrid / dry heat rejection.
    wet_fraction: float = 1.0
    extra_pue: float = 0.0
    extra_energy_kwh_per_ml_dry: float = 0.0
    extra_energy_kwh_per_ml_wet: float = 0.0

    # Common impact factors.
    energy_carbon_kg_per_kwh: float = 0.0
    energy_cost_per_kwh: float = 0.0

    def __post_init__(self) -> None:
        if self.policy not in {"A0", "A1", "A2", "A3"}:
            raise ValueError("policy must be one of A0, A1, A2, A3")
        _nonnegative(self.city_saving_threshold_ml, "city_saving_threshold_ml")
        _fraction(self.min_sla_reliability, "min_sla_reliability")
        for name in ("max_energy_kwh", "max_carbon_kg_co2e", "max_cost", "max_reject_ml"):
            value = getattr(self, name)
            if value is not None:
                _nonnegative(value, name)
        _mapping_fractions(self.solute_removal_fractions, "solute_removal_fractions")
        _fraction(self.side_stream_fraction, "side_stream_fraction")
        _fraction(self.treatment_reject_fraction, "treatment_reject_fraction")
        _fraction(self.treatment_unreturned_fraction, "treatment_unreturned_fraction")
        if self.treatment_reject_fraction + self.treatment_unreturned_fraction > 1.0 + _EPS:
            raise ValueError("treatment reject and unreturned fractions cannot exceed one")
        _nonnegative(self.treatment_energy_kwh_per_ml, "treatment_energy_kwh_per_ml")
        _nonnegative(self.treatment_fixed_energy_kwh_per_day, "treatment_fixed_energy_kwh_per_day")
        _nonnegative(self.chemical_cost_per_kg_removed, "chemical_cost_per_kg_removed")
        _nonnegative(self.treatment_fixed_cost_per_day, "treatment_fixed_cost_per_day")
        _fraction(self.membrane_recovery_fraction, "membrane_recovery_fraction")
        _mapping_fractions(self.membrane_rejection_fractions, "membrane_rejection_fractions")
        _fraction(self.membrane_unreturned_fraction, "membrane_unreturned_fraction")
        _nonnegative(self.membrane_energy_kwh_per_ml, "membrane_energy_kwh_per_ml")
        _nonnegative(self.membrane_capex, "membrane_capex")
        if not math.isfinite(float(self.membrane_lifetime_years)) or self.membrane_lifetime_years <= 0:
            raise ValueError("membrane_lifetime_years must be positive")
        _nonnegative(self.membrane_annual_opex, "membrane_annual_opex")
        _fraction(self.wet_fraction, "wet_fraction")
        _nonnegative(self.extra_pue, "extra_pue")
        _nonnegative(self.extra_energy_kwh_per_ml_dry, "extra_energy_kwh_per_ml_dry")
        _nonnegative(self.extra_energy_kwh_per_ml_wet, "extra_energy_kwh_per_ml_wet")
        _nonnegative(self.energy_carbon_kg_per_kwh, "energy_carbon_kg_per_kwh")
        _nonnegative(self.energy_cost_per_kwh, "energy_cost_per_kwh")

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "AdaptationConfig":
        """Construct a typed config from JSON-like policy parameters.

        A few concise aliases are accepted because E4 fixtures are often
        authored as CSV/JSON ledgers (``removal_fractions``, ``recovery`` and
        ``rejection_fractions``).
        """

        data = dict(values)
        if "policy" not in data:
            raise ValueError("adaptation config requires policy")
        aliases = {
            "removal_fractions": "solute_removal_fractions",
            "solute_removal_fraction": "solute_removal_fractions",
            "recovery": "membrane_recovery_fraction",
            "rejection_fractions": "membrane_rejection_fractions",
            "rejection_fraction": "membrane_rejection_fractions",
            "energy_kwh_per_ml": "treatment_energy_kwh_per_ml",
            "chemical_cost_per_kg": "chemical_cost_per_kg_removed",
            "annual_opex": "membrane_annual_opex",
            "pue_penalty": "extra_pue",
        }
        for old, new in aliases.items():
            if old in data and new not in data:
                data[new] = data.pop(old)
        return cls(**data)


def _mapping_fractions(values: Mapping[str, float] | None, name: str) -> dict[str, float]:
    if values is None:
        return {}
    if not isinstance(values, Mapping):
        raise TypeError(f"{name} must be a mapping")
    out: dict[str, float] = {}
    for key, value in values.items():
        text = str(key)
        out[text] = _fraction(value, f"{name}[{text!r}]")
    return out


@dataclass(frozen=True, slots=True)
class AdaptationDayResult:
    """Auditable daily result emitted by :func:`evaluate_adaptation`."""

    day_id: str
    demand_ml: float
    feed_ml: float
    permeate_ml: float
    reject_ml: float
    unreturned_ml: float
    freshwater_use_ml: float
    freshwater_baseline_ml: float
    freshwater_saving_ml: float
    unmet_water_ml: float
    service_ok: bool
    energy_kwh: float
    carbon_kg_co2e: float
    cost: float
    solute_in_kg: Mapping[str, float]
    solute_removed_kg: Mapping[str, float]
    solute_permeate_kg: Mapping[str, float]
    solute_reject_kg: Mapping[str, float]
    solute_unreturned_kg: Mapping[str, float]
    solute_closure_residual_kg: Mapping[str, float]


@dataclass(frozen=True, slots=True)
class AdaptationResult:
    """Aggregated adaptation accounting and E4 feasibility state."""

    policy: AdaptationPolicy
    status: AdaptationStatus
    infeasible_reasons: tuple[str, ...]
    freshwater_use_ml: float
    freshwater_baseline_ml: float
    freshwater_saving_ml: float
    freshwater_impact_ml: float
    unmet_water_ml: float
    sla_reliability: float
    energy_kwh: float
    carbon_kg_co2e: float
    cost: float
    annualized_capex_cost: float
    annualized_opex_cost: float
    reject_ml: float
    unreturned_ml: float
    reject_solute_kg: Mapping[str, float]
    unreturned_solute_kg: Mapping[str, float]
    removed_solute_kg: Mapping[str, float]
    solute_closure_residual_kg: Mapping[str, float]
    days: tuple[AdaptationDayResult, ...]
    provenance: Mapping[str, Any]

    @property
    def service_ok(self) -> bool:
        return self.sla_reliability >= 1.0 - _EPS

    @property
    def sla(self) -> float:
        """Alias for the service reliability fraction."""

        return self.sla_reliability

    @property
    def net_freshwater_saving_ml(self) -> float:
        """Alias used by the E3 estimand tables."""

        return self.freshwater_saving_ml

    @property
    def E_adapt(self) -> float | Literal["NA"]:
        """Minimum-energy estimand for this strategy, or ``NA`` if infeasible."""

        return self.energy_kwh if self.status == "feasible" else NA

    @property
    def C_adapt(self) -> float | Literal["NA"]:
        """Minimum-cost estimand for this strategy, or ``NA`` if infeasible."""

        return self.cost if self.status == "feasible" else NA

    @property
    def reject_mass_kg(self) -> Mapping[str, float]:
        """Physical reject plus the explicit unreturned solute stream."""

        return {
            name: self.reject_solute_kg.get(name, 0.0) + self.unreturned_solute_kg.get(name, 0.0)
            for name in set(self.reject_solute_kg) | set(self.unreturned_solute_kg)
        }


@dataclass(frozen=True, slots=True)
class AdaptationSetResult:
    """Cross-policy E4 selection with infeasible values kept as ``NA``."""

    results: tuple[AdaptationResult, ...]
    feasible_results: tuple[AdaptationResult, ...]
    status: AdaptationStatus
    E_adapt: float | Literal["NA"]
    C_adapt: float | Literal["NA"]
    minimum_energy_policy: AdaptationPolicy | None
    minimum_cost_policy: AdaptationPolicy | None
    pareto_results: tuple[AdaptationResult, ...]
    provenance: Mapping[str, Any]


def _coerce_ledger(ledger: Iterable[CoolingDayLedger | Mapping[str, Any]]) -> tuple[CoolingDayLedger, ...]:
    output: list[CoolingDayLedger] = []
    seen: set[str] = set()
    for index, row in enumerate(ledger):
        if isinstance(row, CoolingDayLedger):
            item = row
        elif isinstance(row, Mapping):
            data = dict(row)
            def first(*names: str, default: Any = None) -> Any:
                for name in names:
                    if name in data:
                        return data[name]
                return default

            day_id = first("day_id", "day", "date", "cooling_day", default=str(index))
            item = CoolingDayLedger(
                day_id=str(day_id),
                water_demand_ml=first("water_demand_ml", "cooling_demand_ml", "demand_ml", "water_ml", default=0.0),
                solute_load_kg=first("solute_load_kg", "solute_mass_kg", "solutes_kg", "solute_load", default={}),
                reclaimed_supply_ml=first("reclaimed_supply_ml", "reclaimed_ml", "reuse_supply_ml", "nonfresh_supply_ml", default=0.0),
                freshwater_baseline_ml=first("freshwater_baseline_ml", "baseline_freshwater_ml", default=None),
                freshwater_available_ml=first("freshwater_available_ml", "freshwater_cap_ml", default=None),
                it_energy_kwh=first("it_energy_kwh", "it_load_kwh", default=0.0),
                service_required=bool(first("service_required", "required", default=True)),
            )
        else:
            raise TypeError(f"ledger row {index} must be CoolingDayLedger or a mapping")
        if item.day_id in seen:
            raise ValueError(f"duplicate cooling day id: {item.day_id}")
        seen.add(item.day_id)
        output.append(item)
    return tuple(output)


def _coerce_config(
    config: AdaptationConfig | AdaptationPolicy | Mapping[str, Any] | None,
    *,
    policy: AdaptationPolicy | None,
    overrides: Mapping[str, Any],
) -> AdaptationConfig:
    if isinstance(config, AdaptationConfig):
        if policy is not None and policy != config.policy:
            raise ValueError("policy conflicts with config.policy")
        if overrides:
            data = {**{field: getattr(config, field) for field in config.__dataclass_fields__}, **dict(overrides)}
            return AdaptationConfig.from_mapping(data)
        return config
    if isinstance(config, Mapping):
        data = dict(config)
    else:
        data = {}
        if config is not None:
            data["policy"] = config
    if policy is not None:
        data["policy"] = policy
    data.update(overrides)
    if "policy" not in data:
        data["policy"] = "A0"
    return AdaptationConfig.from_mapping(data)


def _day_solute_input(day: CoolingDayLedger, feed_ml: float, gross_demand_ml: float) -> dict[str, float]:
    if feed_ml <= _EPS or gross_demand_ml <= _EPS:
        return {str(name): 0.0 for name in day.solute_load_kg}
    fraction = min(1.0, feed_ml / gross_demand_ml)
    return {str(name): _nonnegative(value, f"solute_load_kg[{name!r}]") * fraction for name, value in day.solute_load_kg.items()}


def _normalise_residual(
    values: Mapping[str, float],
    *,
    expected_names: set[str],
) -> dict[str, float]:
    names = expected_names | set(values)
    return {name: float(values.get(name, 0.0)) for name in sorted(names)}


def evaluate_adaptation(
    ledger: Iterable[CoolingDayLedger | Mapping[str, Any]],
    config: AdaptationConfig | AdaptationPolicy | Mapping[str, Any] | None = None,
    *,
    policy: AdaptationPolicy | None = None,
    provenance: Mapping[str, Any] | None = None,
    **overrides: Any,
) -> AdaptationResult:
    """Evaluate one A0--A3 strategy on a cooling-day ledger.

    The function is pure with respect to the ledger: it does not mutate input
    rows or any main-engine state.  ``config`` may be a typed config, policy
    string, or JSON-like mapping.  Keyword overrides are useful for small
    fixtures, e.g. ``policy="A1", solute_removal_fractions={"TDS": .8}``.
    """

    days = _coerce_ledger(ledger)
    cfg = _coerce_config(config, policy=policy, overrides=overrides)
    daily: list[AdaptationDayResult] = []
    totals: dict[str, float] = {
        "freshwater_use_ml": 0.0,
        "freshwater_baseline_ml": 0.0,
        "energy_kwh": 0.0,
        "carbon_kg_co2e": 0.0,
        "cost": 0.0,
        "reject_ml": 0.0,
        "unreturned_ml": 0.0,
        "unmet_water_ml": 0.0,
    }
    solute_totals: dict[str, dict[str, float]] = {
        "reject": {},
        "unreturned": {},
        "removed": {},
        "residual": {},
    }
    required_days = 0
    passing_days = 0
    annualized_capex = 0.0
    annualized_opex = 0.0

    def add_solute(target: dict[str, float], values: Mapping[str, float]) -> None:
        for name, value in values.items():
            target[name] = target.get(name, 0.0) + float(value)

    for day in days:
        gross_demand = float(day.water_demand_ml)
        baseline_fw = float(day.freshwater_baseline_ml if day.freshwater_baseline_ml is not None else gross_demand)
        target_demand = gross_demand * (cfg.wet_fraction if cfg.policy == "A3" else 1.0)
        feed_ml = min(float(day.reclaimed_supply_ml), target_demand)

        permeate_ml = feed_ml
        reject_ml = 0.0
        unreturned_ml = 0.0
        solute_input = _day_solute_input(day, feed_ml, gross_demand)
        solute_removed: dict[str, float] = {}
        solute_permeate: dict[str, float] = {}
        solute_reject: dict[str, float] = {}
        solute_unreturned: dict[str, float] = {}
        energy = 0.0
        direct_cost = 0.0

        if cfg.policy == "A0" or cfg.policy == "A3":
            solute_permeate = dict(solute_input)
            if cfg.policy == "A3":
                energy += day.it_energy_kwh * cfg.extra_pue
                energy += target_demand * cfg.extra_energy_kwh_per_ml_wet
                energy += max(0.0, gross_demand - target_demand) * cfg.extra_energy_kwh_per_ml_dry
        elif cfg.policy == "A1":
            treatment_feed = feed_ml * cfg.side_stream_fraction
            bypass_ml = feed_ml - treatment_feed
            reject_ml = treatment_feed * cfg.treatment_reject_fraction
            unreturned_ml = treatment_feed * cfg.treatment_unreturned_fraction
            treated_permeate_ml = treatment_feed - reject_ml - unreturned_ml
            permeate_ml = bypass_ml + treated_permeate_ml
            untreated_fraction = 0.0 if feed_ml <= _EPS else bypass_ml / feed_ml
            treated_fraction = 0.0 if feed_ml <= _EPS else treatment_feed / feed_ml
            for name, mass in solute_input.items():
                treated_input = mass * treated_fraction
                bypass_mass = mass * untreated_fraction
                removed = treated_input * cfg.solute_removal_fractions.get(name, 0.0)
                treated_residual = treated_input - removed
                solute_removed[name] = removed
                solute_permeate[name] = bypass_mass + (treated_residual * (0.0 if treatment_feed <= _EPS else treated_permeate_ml / treatment_feed))
                solute_reject[name] = treated_residual * cfg.treatment_reject_fraction
                solute_unreturned[name] = treated_residual * cfg.treatment_unreturned_fraction
            energy += treatment_feed * cfg.treatment_energy_kwh_per_ml
            if treatment_feed > _EPS or cfg.treatment_fixed_energy_kwh_per_day:
                energy += cfg.treatment_fixed_energy_kwh_per_day
            direct_cost += sum(solute_removed.values()) * cfg.chemical_cost_per_kg_removed
            if treatment_feed > _EPS or cfg.treatment_fixed_cost_per_day:
                direct_cost += cfg.treatment_fixed_cost_per_day
        else:  # A2 membrane
            permeate_ml = feed_ml * cfg.membrane_recovery_fraction
            reject_total_ml = feed_ml - permeate_ml
            unreturned_ml = reject_total_ml * cfg.membrane_unreturned_fraction
            reject_ml = reject_total_ml - unreturned_ml
            for name, mass in solute_input.items():
                removed = mass * cfg.membrane_rejection_fractions.get(name, 0.0)
                residual = mass - removed
                solute_removed[name] = removed
                solute_permeate[name] = residual * (0.0 if feed_ml <= _EPS else permeate_ml / feed_ml)
                solute_reject[name] = residual * (0.0 if feed_ml <= _EPS else reject_ml / feed_ml)
                solute_unreturned[name] = residual * (0.0 if feed_ml <= _EPS else unreturned_ml / feed_ml)
            energy += feed_ml * cfg.membrane_energy_kwh_per_ml
            if feed_ml > _EPS:
                direct_cost += 0.0

        # The treatment sink, rather than an implicit free resource, carries
        # all active treatment costs.  Annualised membrane ownership is spread
        # over the evaluated cooling days.
        if cfg.policy == "A2" and days:
            # ``annualized_*`` are reported as annual ownership costs.  The
            # evaluated cooling days carry a one-day share so that a short
            # ledger does not receive a full year's CAPEX/OPEX charge.
            annualized_capex = cfg.membrane_capex / cfg.membrane_lifetime_years
            annualized_opex = cfg.membrane_annual_opex
            direct_cost += (annualized_capex + annualized_opex) / 365.0

        freshwater_fallback = max(0.0, target_demand - permeate_ml)
        if day.freshwater_available_ml is None:
            freshwater_use = freshwater_fallback
        else:
            freshwater_use = min(freshwater_fallback, float(day.freshwater_available_ml))
        unmet = max(0.0, freshwater_fallback - freshwater_use)
        service_ok = unmet <= _EPS
        if day.service_required:
            required_days += 1
            if service_ok:
                passing_days += 1
        carbon = energy * cfg.energy_carbon_kg_per_kwh
        direct_cost += energy * cfg.energy_cost_per_kwh
        residual = {}
        all_names = set(solute_input) | set(solute_removed) | set(solute_permeate) | set(solute_reject) | set(solute_unreturned)
        for name in all_names:
            residual[name] = (
                solute_input.get(name, 0.0)
                - solute_removed.get(name, 0.0)
                - solute_permeate.get(name, 0.0)
                - solute_reject.get(name, 0.0)
                - solute_unreturned.get(name, 0.0)
            )
        row = AdaptationDayResult(
            day_id=day.day_id,
            demand_ml=target_demand,
            feed_ml=feed_ml,
            permeate_ml=permeate_ml,
            reject_ml=reject_ml,
            unreturned_ml=unreturned_ml,
            freshwater_use_ml=freshwater_use,
            freshwater_baseline_ml=baseline_fw,
            freshwater_saving_ml=baseline_fw - freshwater_use,
            unmet_water_ml=unmet,
            service_ok=service_ok,
            energy_kwh=energy,
            carbon_kg_co2e=carbon,
            cost=direct_cost,
            solute_in_kg=dict(solute_input),
            solute_removed_kg=dict(solute_removed),
            solute_permeate_kg=dict(solute_permeate),
            solute_reject_kg=dict(solute_reject),
            solute_unreturned_kg=dict(solute_unreturned),
            solute_closure_residual_kg=dict(residual),
        )
        daily.append(row)
        totals["freshwater_use_ml"] += freshwater_use
        totals["freshwater_baseline_ml"] += baseline_fw
        totals["energy_kwh"] += energy
        totals["carbon_kg_co2e"] += carbon
        totals["cost"] += direct_cost
        totals["reject_ml"] += reject_ml
        totals["unreturned_ml"] += unreturned_ml
        totals["unmet_water_ml"] += unmet
        add_solute(solute_totals["reject"], solute_reject)
        add_solute(solute_totals["unreturned"], solute_unreturned)
        add_solute(solute_totals["removed"], solute_removed)
        add_solute(solute_totals["residual"], residual)

    sla = 1.0 if required_days == 0 else passing_days / required_days
    saving = totals["freshwater_baseline_ml"] - totals["freshwater_use_ml"]
    reasons: list[str] = []
    if saving + _EPS < cfg.city_saving_threshold_ml:
        reasons.append("city_saving_threshold_not_met")
    if sla + _EPS < cfg.min_sla_reliability:
        reasons.append("sla_reliability_below_minimum")
    if cfg.max_energy_kwh is not None and totals["energy_kwh"] > cfg.max_energy_kwh + _EPS:
        reasons.append("energy_cap_exceeded")
    if cfg.max_carbon_kg_co2e is not None and totals["carbon_kg_co2e"] > cfg.max_carbon_kg_co2e + _EPS:
        reasons.append("carbon_cap_exceeded")
    if cfg.max_cost is not None and totals["cost"] > cfg.max_cost + _EPS:
        reasons.append("cost_cap_exceeded")
    if cfg.max_reject_ml is not None and totals["reject_ml"] > cfg.max_reject_ml + _EPS:
        reasons.append("reject_cap_exceeded")
    status: AdaptationStatus = "feasible" if not reasons else "infeasible"
    base_provenance = {
        "module": "aiuwm.adaptation",
        "contract": "R10-E4-A0-A3",
        "formula_version": "r10-e4-v1",
        "main_model_integration": "NOT_READY",
        "quality_evidence_default": "scenario_prior",
        "source": "caller_supplied_cooling_day_ledger",
        "evidence_type": "scenario_prior",
        "date_period": None,
        "uncertainty": "not estimated by standalone adapter",
        "units": {"volume": "ML", "solute": "kg", "energy": "kWh", "carbon": "kgCO2e"},
    }
    if provenance:
        base_provenance.update(dict(provenance))
    return AdaptationResult(
        policy=cfg.policy,
        status=status,
        infeasible_reasons=tuple(reasons),
        freshwater_use_ml=totals["freshwater_use_ml"],
        freshwater_baseline_ml=totals["freshwater_baseline_ml"],
        freshwater_saving_ml=saving,
        freshwater_impact_ml=totals["freshwater_use_ml"] - totals["freshwater_baseline_ml"],
        unmet_water_ml=totals["unmet_water_ml"],
        sla_reliability=sla,
        energy_kwh=totals["energy_kwh"],
        carbon_kg_co2e=totals["carbon_kg_co2e"],
        cost=totals["cost"],
        annualized_capex_cost=annualized_capex if cfg.policy == "A2" else 0.0,
        annualized_opex_cost=annualized_opex if cfg.policy == "A2" else 0.0,
        reject_ml=totals["reject_ml"],
        unreturned_ml=totals["unreturned_ml"],
        reject_solute_kg=dict(solute_totals["reject"]),
        unreturned_solute_kg=dict(solute_totals["unreturned"]),
        removed_solute_kg=dict(solute_totals["removed"]),
        solute_closure_residual_kg=dict(solute_totals["residual"]),
        days=tuple(daily),
        provenance=base_provenance,
    )


def _dominates(left: AdaptationResult, right: AdaptationResult) -> bool:
    """Return whether ``left`` is no worse in energy and cost and improves one."""

    return (
        left.energy_kwh <= right.energy_kwh + _EPS
        and left.cost <= right.cost + _EPS
        and (left.energy_kwh < right.energy_kwh - _EPS or left.cost < right.cost - _EPS)
    )


def evaluate_adaptation_set(
    ledger: Iterable[CoolingDayLedger | Mapping[str, Any]],
    configs: Iterable[AdaptationConfig | AdaptationPolicy | Mapping[str, Any]],
    *,
    provenance: Mapping[str, Any] | None = None,
) -> AdaptationSetResult:
    """Evaluate A0--A3 candidates and compute a feasible-only Pareto set.

    If no candidate meets the city saving/SLA/constraint gates, ``status`` is
    ``infeasible`` and both ``E_adapt`` and ``C_adapt`` are ``"NA"``.
    """

    frozen_ledger = tuple(ledger)
    results = tuple(evaluate_adaptation(frozen_ledger, config, provenance=provenance) for config in configs)
    feasible = tuple(result for result in results if result.status == "feasible")
    if feasible:
        energy_best = min(feasible, key=lambda result: (result.energy_kwh, result.policy))
        cost_best = min(feasible, key=lambda result: (result.cost, result.policy))
        pareto = tuple(
            result
            for result in feasible
            if not any(_dominates(other, result) for other in feasible if other is not result)
        )
        status: AdaptationStatus = "feasible"
        e_adapt: float | Literal["NA"] = energy_best.energy_kwh
        c_adapt: float | Literal["NA"] = cost_best.cost
        e_policy: AdaptationPolicy | None = energy_best.policy
        c_policy: AdaptationPolicy | None = cost_best.policy
    else:
        pareto = ()
        status = "infeasible"
        e_adapt = NA
        c_adapt = NA
        e_policy = None
        c_policy = None
    result_provenance = {
        "module": "aiuwm.adaptation",
        "contract": "R10-E4-A0-A3-set",
        "main_model_integration": "NOT_READY",
        "selection": "feasible-only; infeasible E_adapt/C_adapt are NA",
        "source": "caller_supplied_cooling_day_ledger",
        "evidence_type": "scenario_prior",
    }
    if provenance:
        result_provenance.update(dict(provenance))
    return AdaptationSetResult(
        results=results,
        feasible_results=feasible,
        status=status,
        E_adapt=e_adapt,
        C_adapt=c_adapt,
        minimum_energy_policy=e_policy,
        minimum_cost_policy=c_policy,
        pareto_results=pareto,
        provenance=result_provenance,
    )


# Explicit aliases make the contract discoverable without forcing callers to
# remember one spelling of “evaluate the candidate strategies”.
evaluate_adaptation_policies = evaluate_adaptation_set
run_adaptation_policies = evaluate_adaptation_set
run_adaptation = evaluate_adaptation
adaptation_summary = evaluate_adaptation_set


__all__ = [
    "AdaptationConfig",
    "AdaptationDayResult",
    "AdaptationPolicy",
    "AdaptationResult",
    "AdaptationSetResult",
    "CoolingDayLedger",
    "CoolingDayRecord",
    "AdaptationLedger",
    "cooling_ledger_from_data_center_daily",
    "evaluate_adaptation",
    "evaluate_adaptation_set",
    "evaluate_adaptation_policies",
    "run_adaptation_policies",
    "run_adaptation",
    "adaptation_summary",
]
