from __future__ import annotations

import math

import pytest

from aiuwm.quality_state import (
    QualityState,
    mix_quality_states,
    partition_blowdown_solutes,
    withdraw_quality_state,
)


def test_mix_and_withdraw_conserve_two_solute_masses() -> None:
    first = QualityState.from_concentrations(10.0, {"TDS": 700.0, "chloride": 100.0})
    second = QualityState.from_concentrations(5.0, {"TDS": 1_300.0, "chloride": 300.0})
    mixed = mix_quality_states([first, second])
    assert mixed.volume_ml == 15.0
    assert mixed.concentrations_mg_l() == {"TDS": 900.0, "chloride": 166.66666666666666}

    withdrawn, remaining = withdraw_quality_state(mixed, 6.0)
    for solute in ("TDS", "chloride"):
        assert math.isclose(
            withdrawn.mass_kg[solute] + remaining.mass_kg[solute],
            mixed.mass_kg[solute],
            abs_tol=1e-12,
        )
    assert withdrawn.volume_ml + remaining.volume_ml == mixed.volume_ml


def test_blowdown_solute_partition_closes_with_removal_and_unreturned_loss() -> None:
    partition = partition_blowdown_solutes(
        {"TDS": 1_800.0, "chloride": 500.0},
        blowdown_ml=10.0,
        internal_recovery_fraction=0.4,
        removal_fraction_by_solute={"TDS": 0.25, "chloride": 1.0},
        return_fraction=0.5,
    )
    for solute, residual in partition.residual_kg.items():
        assert abs(residual) <= 1e-12
        assert partition.blowdown_mass_kg[solute] >= 0.0
    assert partition.removed_mass_kg["chloride"] > partition.removed_mass_kg["TDS"]
    assert partition.unreturned_mass_kg["TDS"] > 0.0


def test_blowdown_removal_fraction_boundaries() -> None:
    no_removal = partition_blowdown_solutes(
        {"TDS": 1_000.0}, 1.0, 0.5, {"TDS": 0.0}
    )
    full_removal = partition_blowdown_solutes(
        {"TDS": 1_000.0}, 1.0, 0.5, {"TDS": 1.0}
    )
    assert no_removal.removed_mass_kg["TDS"] == 0.0
    assert full_removal.recovered_return_mass_kg["TDS"] == 0.0


def test_quality_state_rejects_negative_or_overdrawn_values() -> None:
    with pytest.raises(ValueError):
        QualityState.from_concentrations(-1.0, {"TDS": 1.0})
    state = QualityState.from_concentrations(1.0, {"TDS": 1.0})
    with pytest.raises(ValueError):
        withdraw_quality_state(state, 2.0)
