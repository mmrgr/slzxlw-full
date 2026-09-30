from __future__ import annotations

import csv
from datetime import date, timedelta
import json
from pathlib import Path

from scripts.run_g3_facility_holdout import run


def _write_table(path: Path, *, facilities: int = 3, days: int = 366, synthetic: bool = False, bad_prediction: bool = False) -> None:
    fields = [
        "facility_id", "study_id", "date", "timezone", "source_uri", "meter_id",
        "it_energy_mwh", "facility_energy_mwh", "pue", "wue_l_kwh_it",
        "dry_bulb_c", "wet_bulb_c", "cooling_technology", "reclaimed_fraction",
        "makeup_ml", "blowdown_ml", "coc", "predicted_wue_l_kwh_it",
        "predicted_makeup_ml", "predicted_blowdown_ml", "predicted_coc",
        "synthetic_observed", "observed_flag", "prediction_source",
        "prediction_training_facilities", "quality_flag",
    ]
    facility_ids = [f"F{index}" for index in range(1, facilities + 1)]
    start = date(2024, 1, 1)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for facility in facility_ids:
            training = ",".join(value for value in facility_ids if value != facility)
            for offset in range(days):
                day = start + timedelta(days=offset)
                writer.writerow({
                    "facility_id": facility,
                    "study_id": f"study-{facility}",
                    "date": day.isoformat(),
                    "timezone": "UTC",
                    "source_uri": f"https://example.org/meter/{facility}",
                    "meter_id": f"meter-{facility}",
                    "it_energy_mwh": "100",
                    "facility_energy_mwh": "120",
                    "pue": "1.2",
                    "dry_bulb_c": "30",
                    "wet_bulb_c": "20",
                    "cooling_technology": "cooling_tower",
                    "reclaimed_fraction": "0.5",
                    "wue_l_kwh_it": "1.0",
                    "makeup_ml": "10",
                    "blowdown_ml": "2",
                    "coc": "5",
                    "predicted_wue_l_kwh_it": "1.1" if not bad_prediction else "2.0",
                    "predicted_makeup_ml": "11",
                    "predicted_blowdown_ml": "2.3",
                    "predicted_coc": "5.2",
                    "synthetic_observed": "true" if synthetic else "false",
                    "observed_flag": "true",
                    "prediction_source": "external_loo_model",
                    "prediction_training_facilities": training,
                    "quality_flag": "good",
                })


def test_complete_non_synthetic_leave_one_facility_out_passes(tmp_path: Path) -> None:
    observations = tmp_path / "facility_daily.csv"
    output = tmp_path / "g3"
    _write_table(observations)

    payload = run(observations, output)

    assert payload["status"] == "PASS"
    assert payload["facility_count"] == 3
    assert payload["min_months_per_facility"] == 12
    assert payload["leave_one_facility_out"] is True
    assert payload["non_synthetic"] is True
    assert json.loads((output / "manifest.json").read_text(encoding="utf-8"))["status"] == "PASS"


def test_synthetic_rows_are_not_ready_even_when_metrics_pass(tmp_path: Path) -> None:
    observations = tmp_path / "synthetic_observed.csv"
    output = tmp_path / "g3"
    _write_table(observations, synthetic=True)

    payload = run(observations, output)

    assert payload["status"] == "NOT_READY"
    assert payload["non_synthetic"] is False
    assert any("synthetic" in reason for reason in payload["reasons"])


def test_missing_facility_coverage_fails_closed_with_reason(tmp_path: Path) -> None:
    observations = tmp_path / "facility_daily.csv"
    output = tmp_path / "g3"
    _write_table(observations, facilities=2, days=30)

    payload = run(observations, output)

    assert payload["status"] == "NOT_READY"
    assert any("at least 3 facilities" in reason for reason in payload["reasons"])
    assert any("calendar months" in reason for reason in payload["reasons"])


def test_complete_holdout_that_misses_threshold_is_fail(tmp_path: Path) -> None:
    observations = tmp_path / "facility_daily.csv"
    output = tmp_path / "g3"
    _write_table(observations, bad_prediction=True)

    payload = run(observations, output)

    assert payload["status"] == "FAIL"
    assert any("threshold" in reason for reason in payload["reasons"])


def _mutate_first_row(path: Path, **changes: str) -> None:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fields = list(rows[0])
    rows[0].update(changes)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_twelve_calendar_labels_without_twelve_full_months_are_not_ready(tmp_path: Path) -> None:
    observations = tmp_path / "facility_daily.csv"
    _write_table(observations, days=365)

    payload = run(observations, tmp_path / "g3")

    assert payload["status"] == "NOT_READY"
    assert payload["min_months_per_facility"] == 11
    assert any("complete calendar months" in reason for reason in payload["reasons"])


def test_quality_and_fold_scope_are_fail_closed(tmp_path: Path) -> None:
    observations = tmp_path / "facility_daily.csv"
    _write_table(observations)
    _mutate_first_row(observations, quality_flag="unknown")
    payload = run(observations, tmp_path / "g3_quality")
    assert payload["status"] == "NOT_READY"
    assert any("quality_flag" in reason for reason in payload["reasons"])

    _write_table(observations)
    _mutate_first_row(observations, prediction_training_facilities="F2")
    payload = run(observations, tmp_path / "g3_scope")
    assert payload["status"] == "NOT_READY"
    assert any("missing-peer-training-facilities" in reason for reason in payload["reasons"])


def test_inconsistent_energy_and_pue_are_not_accepted(tmp_path: Path) -> None:
    observations = tmp_path / "facility_daily.csv"
    _write_table(observations)
    _mutate_first_row(observations, facility_energy_mwh="130")

    payload = run(observations, tmp_path / "g3")

    assert payload["status"] == "NOT_READY"
    assert any("PUE differs" in reason for reason in payload["reasons"])
