from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def _rows(name: str) -> list[dict[str, str]]:
    with (ROOT / "data" / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_parameter_registry_fixture_matches_schema() -> None:
    schema = json.loads((ROOT / "data" / "parameter_registry_schema.json").read_text(encoding="utf-8"))
    rows = _rows("parameter_registry.csv")
    assert rows
    assert set(schema["required_fields"]).issubset(rows[0])
    assert all(row["lower"] and row["upper"] for row in rows)
    assert all(row["version"] == schema["schema_version"] for row in rows)


def test_scenario_registry_has_paired_not_ready_q_l_a_fixture() -> None:
    schema = json.loads((ROOT / "data" / "scenario_registry_schema.json").read_text(encoding="utf-8"))
    rows = _rows("scenario_registry.csv")
    assert len(rows) == 16
    assert set(schema["required_fields"]).issubset(rows[0])
    assert {row["chemistry_state"] for row in rows} == {"Q0", "Q1"}
    assert {row["allocation_state"] for row in rows} == {"Ls", "Ld"}
    assert {row["adaptation_state"] for row in rows} == {"A0", "A1", "A2", "A3"}
    assert {row["status"] for row in rows} == {"not_ready"}
    assert len({(row["weather_seed"], row["hydrology_seed"], row["workload_seed"]) for row in rows}) == 1
