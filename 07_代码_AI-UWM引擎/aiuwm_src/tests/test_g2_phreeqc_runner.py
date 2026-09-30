from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.run_g2_phreeqc_crosscheck import _charge_balance_error_pct, _reduced_order_metrics, run


def test_reduced_order_metrics_uses_direct_tds_and_declares_limiting_indicator() -> None:
    metrics = _reduced_order_metrics({"tds_mg_l": "1000", "Cl_mg_l": "400"})

    assert metrics is not None
    assert metrics["reduced_order_coc"] == 1.25
    assert metrics["reduced_order_limiting_species"] == "chloride"
    assert metrics["reduced_order_safe_at_one"] is True


def test_reduced_order_metrics_does_not_substitute_missing_tds() -> None:
    assert _reduced_order_metrics({"Cl_mg_l": "10"}) is None


def test_charge_balance_is_explicit_screening_diagnostic() -> None:
    error = _charge_balance_error_pct({
        "Ca_mg_l": "40", "Mg_mg_l": "10", "Na_mg_l": "50",
        "Cl_mg_l": "60", "SO4_mg_l": "100",
        "alkalinity_mg_l_as_CaCO3": "120",
    })
    assert error is not None
    assert 0.0 <= error < 20.0


def test_phreeqc_runner_emits_pilot_manifest_without_opening_gate(tmp_path: Path) -> None:
    samples = tmp_path / "samples.csv"
    with samples.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "sample_id", "pH", "temperature_c", "Ca_mg_l", "Mg_mg_l", "Na_mg_l",
            "Cl_mg_l", "SO4_mg_l", "alkalinity_mg_l_as_CaCO3", "Si_mg_l",
            "source_provenance", "observed_flag",
        ])
        writer.writeheader()
        writer.writerow({
            "sample_id": "fixture-1", "pH": "7.5", "temperature_c": "25",
            "Ca_mg_l": "40", "Mg_mg_l": "10", "Na_mg_l": "50",
            "Cl_mg_l": "60", "SO4_mg_l": "100", "alkalinity_mg_l_as_CaCO3": "120",
            "Si_mg_l": "10", "source_provenance": "synthetic_fixture", "observed_flag": "false",
        })

    output = tmp_path / "manifest.json"
    payload = run(samples, output)

    assert payload["status"] == "PILOT_ONLY"
    assert payload["input"]["sample_count"] == 1
    assert payload["independent_solver"]["database_hash"].startswith("sha256:")
    assert payload["sample_level_crosscheck"] is False
    assert payload["false_safe_rate"] is None
    assert payload["gate_effect"].startswith("G2 remains NOT_READY:")
    assert json.loads(output.read_text(encoding="utf-8"))["gate"] == "G2"
