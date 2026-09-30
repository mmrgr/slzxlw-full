from __future__ import annotations

import csv
import json
from pathlib import Path

import scripts.run_e4_adaptation_pilot as pilot
from scripts.run_e4_adaptation_pilot import run


def _write_daily(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "date", "data_center_id", "external_makeup_ml", "reclaimed_water_ml",
            "potable_water_ml", "it_energy_mwh", "quality_reclaimed_source_mg_l",
        ])
        writer.writeheader()
        writer.writerow({
            "date": "2030-01-01", "data_center_id": "DC1",
            "external_makeup_ml": "10", "reclaimed_water_ml": "4",
            "potable_water_ml": "6", "it_energy_mwh": "0.25",
            "quality_reclaimed_source_mg_l": '{"TDS": 200}',
        })


def test_read_only_pilot_evaluates_a0_to_a3_and_hashes_outputs(tmp_path: Path) -> None:
    source = tmp_path / "data_center_daily.csv"
    output = tmp_path / "e4"
    _write_daily(source)

    payload = run(source, output, repo_root=tmp_path)

    assert payload["status"] == "NOT_READY"
    assert payload["diagnostic_status"] == "READ_ONLY"
    assert payload["execution_mode"] == "READ_ONLY_DIAGNOSTIC"
    assert payload["main_model_integration"] == "READ_ONLY_BOUNDARY"
    assert payload["execution_performed"] is True
    assert len(payload["results"]) == 4
    assert payload["selection"]["summary_rows"] == 4
    assert payload["selection"]["daily_rows"] == 4
    assert payload["output_hashes"]["summary"].startswith("sha256:")
    assert payload["input"]["sha256"].startswith("sha256:")

    summary = (output / "adaptation_summary.csv").read_text(encoding="utf-8")
    assert "A0" in summary and "A3" in summary
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "NOT_READY"
    assert manifest["diagnostic_status"] == "READ_ONLY"


def test_csv_python_mapping_repr_is_decoded_without_execution(tmp_path: Path) -> None:
    source = tmp_path / "data_center_daily.csv"
    source.write_text(
        "date,data_center_id,external_makeup_ml,reclaimed_water_ml,potable_water_ml,quality_reclaimed_source_mg_l\n"
        "2030-01-01,DC1,10,4,6,\"{'TDS': 200}\"\n",
        encoding="utf-8",
    )

    payload = run(source, tmp_path / "repr", repo_root=tmp_path)

    assert payload["execution_performed"] is True


def test_formal_request_is_refused_before_adaptation_when_gates_not_ready(tmp_path: Path) -> None:
    source = tmp_path / "data_center_daily.csv"
    output = tmp_path / "formal"
    _write_daily(source)

    payload = run(source, output, repo_root=tmp_path, formal=True)

    assert payload["status"] == "NOT_READY"
    assert payload["execution_performed"] is False
    assert payload["formal_run_performed"] is False
    assert payload["gate_statuses"] == {"g2": "NOT_READY", "g3": "NOT_READY"}
    assert any("formal E4 run refused" in reason for reason in payload["reasons"])
    assert payload["results"] == []


def test_formal_request_stays_blocked_without_coupled_feedback_review(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "data_center_daily.csv"
    baseline = tmp_path / "freshwater_baseline.csv"
    _write_daily(source)
    baseline.write_text(
        "date,data_center_id,potable_water_ml\n2030-01-01,DC1,12\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        pilot,
        "audit",
        lambda *_args: {
            "g2": {"status": "READY", "reason": "fixture"},
            "g3": {"status": "READY", "reason": "fixture"},
        },
    )

    payload = run(source, tmp_path / "formal_review_missing", freshwater_baseline=baseline, repo_root=tmp_path, formal=True)

    assert payload["gate_statuses"] == {"g2": "READY", "g3": "READY"}
    assert payload["status"] == "NOT_READY"
    assert payload["execution_performed"] is False
    assert any("coupling approval" in reason for reason in payload["reasons"])


def test_infeasible_estimands_are_na_in_summary(tmp_path: Path) -> None:
    source = tmp_path / "data_center_daily.json"
    source.write_text(json.dumps({"data_center_daily": [{
        "date": "2030-01-01", "data_center_id": "DC1",
        "external_makeup_ml": 10.0, "reclaimed_water_ml": 0.0,
        "freshwater_available_ml": 0.0,
    }]}), encoding="utf-8")
    config = tmp_path / "configs.json"
    config.write_text(json.dumps([
        {"policy": "A0", "min_sla_reliability": 1.0},
        {"policy": "A1", "min_sla_reliability": 1.0},
        {"policy": "A2", "min_sla_reliability": 1.0},
        {"policy": "A3", "min_sla_reliability": 1.0},
    ]), encoding="utf-8")

    payload = run(source, tmp_path / "na", config=config, repo_root=tmp_path)

    assert payload["selection"]["status"] == "infeasible"
    assert payload["selection"]["E_adapt"] == "NA"
    assert payload["selection"]["C_adapt"] == "NA"
    rows = list(csv.DictReader((tmp_path / "na" / "adaptation_summary.csv").open(encoding="utf-8")))
    assert len(rows) == 4
    assert {row["E_adapt"] for row in rows} == {"NA"}
    assert {row["C_adapt"] for row in rows} == {"NA"}
