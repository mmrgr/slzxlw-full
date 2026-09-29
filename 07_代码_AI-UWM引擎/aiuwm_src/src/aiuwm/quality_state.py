"""Small, auditable water-quality state primitives.

This module is intentionally not wired into :mod:`full_engine` yet.  It
defines the units and mass bookkeeping needed before cooling-storage quality
can be coupled to the R9 fixed point.  ``1 ML * 1 mg/L = 1 kg`` exactly, so
the representation avoids hidden litre-to-kilogram conversions.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Mapping


def _nonnegative(value: float, name: str) -> float:
    value = float(value)
    if not isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and non-negative")
    return value


def _fraction(value: float, name: str) -> float:
    value = float(value)
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")
    return value


@dataclass(frozen=True)
class QualityState:
    """A well-mixed water volume and dissolved-solute masses.

    Volumes are ML, masses are kg, and concentrations returned by
    :meth:`concentrations_mg_l` are mg/L.  Missing solutes are treated as zero
    mass; callers should supply every indicator that is relevant to a gate.
    """

    volume_ml: float
    mass_kg: Mapping[str, float]

    def __post_init__(self) -> None:
        object.__setattr__(self, "volume_ml", _nonnegative(self.volume_ml, "volume_ml"))
        clean = {
            str(name): _nonnegative(value, f"mass_kg[{name}]")
            for name, value in self.mass_kg.items()
        }
        object.__setattr__(self, "mass_kg", clean)

    @classmethod
    def from_concentrations(
        cls, volume_ml: float, concentrations_mg_l: Mapping[str, float]
    ) -> "QualityState":
        volume = _nonnegative(volume_ml, "volume_ml")
        return cls(
            volume,
            {
                str(name): volume * _nonnegative(value, f"concentration[{name}]")
                for name, value in concentrations_mg_l.items()
            },
        )

    def concentrations_mg_l(self) -> dict[str, float]:
        if self.volume_ml == 0.0:
            return {name: 0.0 for name in self.mass_kg}
        return {
            name: mass / self.volume_ml for name, mass in self.mass_kg.items()
        }


def mix_quality_states(states: Iterable[QualityState]) -> QualityState:
    """Mix well-stirred states while conserving each solute mass."""

    volume = 0.0
    mass: dict[str, float] = {}
    for state in states:
        volume += state.volume_ml
        for name, value in state.mass_kg.items():
            mass[name] = mass.get(name, 0.0) + value
    return QualityState(volume, mass)


def withdraw_quality_state(
    state: QualityState, volume_ml: float
) -> tuple[QualityState, QualityState]:
    """Withdraw a well-mixed volume and return ``(withdrawn, remaining)``."""

    volume = _nonnegative(volume_ml, "volume_ml")
    if volume > state.volume_ml + 1e-12:
        raise ValueError("withdrawal exceeds state volume")
    volume = min(volume, state.volume_ml)
    fraction = volume / state.volume_ml if state.volume_ml else 0.0
    withdrawn_mass = {
        name: value * fraction for name, value in state.mass_kg.items()
    }
    remaining_mass = {
        name: value - withdrawn_mass[name]
        for name, value in state.mass_kg.items()
    }
    return QualityState(volume, withdrawn_mass), QualityState(
        state.volume_ml - volume, remaining_mass
    )


@dataclass(frozen=True)
class SolutePartition:
    """One-day salt ledger for a blowdown stream.

    Internal recovery returns part of the blowdown to the cooling loop.  The
    configured removal fraction removes solute from that recovered stream.
    The remainder is split between sewer return and an explicitly tracked
    unreturned loss.  Evaporation carries no dissolved-solute mass.
    """

    blowdown_mass_kg: Mapping[str, float]
    recovered_return_mass_kg: Mapping[str, float]
    removed_mass_kg: Mapping[str, float]
    sewer_return_mass_kg: Mapping[str, float]
    unreturned_mass_kg: Mapping[str, float]
    residual_kg: Mapping[str, float]


def partition_blowdown_solutes(
    concentrations_mg_l: Mapping[str, float],
    blowdown_ml: float,
    internal_recovery_fraction: float,
    removal_fraction_by_solute: Mapping[str, float] | None = None,
    return_fraction: float = 1.0,
) -> SolutePartition:
    """Partition blowdown solute mass and return per-solute closure residuals."""

    volume = _nonnegative(blowdown_ml, "blowdown_ml")
    recovery = _fraction(internal_recovery_fraction, "internal_recovery_fraction")
    return_fraction = _fraction(return_fraction, "return_fraction")
    removal_fraction_by_solute = removal_fraction_by_solute or {}
    blowdown: dict[str, float] = {}
    recovered_return: dict[str, float] = {}
    removed: dict[str, float] = {}
    sewer: dict[str, float] = {}
    unreturned: dict[str, float] = {}
    residual: dict[str, float] = {}
    for name, concentration in concentrations_mg_l.items():
        mass = volume * _nonnegative(concentration, f"concentration[{name}]")
        removal = _fraction(
            removal_fraction_by_solute.get(name, 0.0),
            f"removal_fraction_by_solute[{name}]",
        )
        recovered_mass = mass * recovery
        removed_mass = recovered_mass * removal
        recovered_to_loop = recovered_mass - removed_mass
        returnable = mass - recovered_mass
        sewer_mass = returnable * return_fraction
        unreturned_mass = returnable - sewer_mass
        blowdown[name] = mass
        recovered_return[name] = recovered_to_loop
        removed[name] = removed_mass
        sewer[name] = sewer_mass
        unreturned[name] = unreturned_mass
        residual[name] = mass - (
            recovered_to_loop + removed_mass + sewer_mass + unreturned_mass
        )
    return SolutePartition(
        blowdown, recovered_return, removed, sewer, unreturned, residual
    )
