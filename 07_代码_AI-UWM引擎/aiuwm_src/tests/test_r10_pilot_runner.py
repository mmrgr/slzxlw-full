from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from scripts.audit_g2_g3_evidence import audit


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "run_r10_pilot.py"


def _write_csv(path: Path, row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path, *, status: str = "not_ready", version: str = "R10.1") -> Path:
    _write_csv(tmp_path / "data" / "scenario_registry.csv", {
        "scenario_id": "S1", "counterfactual_group": "paired-1", "chemistry_state": "Q1",
        "allocation_state": "Ls", "adaptation_state": "A0", "weather_seed": "101",
        "hydrology_seed": "201", "workload_seed": "301", "code_commit": "abc123",
        "parameter_registry_version": "R10.1", "estimand": "S_AI", "status": status,
    })
    _write_csv(tmp_path / "data" / "parameter_registry.csv", {
        "parameter_id": "source.reclaimed_tds", "unit": "mg/L", "distribution": "fixed",
        "lower": "650", "upper": "650", "correlation_group": "chemistry_q1",
        "evidence_class": "E0_assumption", "source": "pilot fixture",
        "observation_population": "scenario_prior", "calibration_flag": "false",
        "validation_flag": "false", "version": version,
    })
    return tmp_path


def _run(repo: Path, *args: str) -> tuple[int, dict]:
    process = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(repo), "--scenario-id", "S1", *args],
        capture_output=True, text=True, check=False,
    )
    assert not process.stderr
    return process.returncode, json.loads(process.stdout)


def test_default_rejects_not_ready_and_missing_g2_g3(tmp_path: Path) -> None:
    repo = _fixture(tmp_path)
    code, output = _run(repo)
    assert code == 2
    assert output["status"] == "REJECTED"
    assert output["gate_statuses"] == {"g2": "NOT_READY", "g3": "NOT_READY"}
    assert "scenario status is not_ready" in output["formal_blockers"]
    assert output["execution_performed"] is False
    assert output["formal_e3_e4_eligible"] is False


def test_explicit_diagnostic_dry_run_only_emits_preflight(tmp_path: Path) -> None:
    repo = _fixture(tmp_path)
    code, output = _run(repo, "--mode", "daily-slice", "--dry-run")
    assert code == 0
    assert output["status"] == "DIAGNOSTIC_PREFLIGHT_ONLY"
    assert output["provenance"]["scenario"]["code_commit"] == "abc123"
    assert output["provenance"]["parameter_count"] == 1
    assert output["provenance"]["registry_sha256"]["scenario_registry"].startswith("sha256:")
    assert output["provenance"]["registry_sha256"]["parameter_registry"].startswith("sha256:")
    assert output["formal_blockers"]
    assert output["execution_performed"] is False
    assert "estimand_values" not in output


def test_dry_run_flag_alone_and_mismatched_registry_are_rejected(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, version="R10.2")
    code, output = _run(repo, "--mode", "diagnostic", "--dry-run")
    assert code == 2
    assert "Parameter registry version does not match scenario." in output["rejection_reasons"]
    repo = _fixture(tmp_path)
    code, output = _run(repo, "--dry-run")
    assert code == 2
    assert any("--mode" in reason for reason in output["rejection_reasons"])


def test_candidate_inventory_does_not_upgrade_g2_g3(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, status="gate_pass")
    (repo / "independent.phrq").write_text("PHREEQC fixture", encoding="utf-8")
    (repo / "facility_observed.csv").write_text("sample,tds\n1,650\n", encoding="utf-8")
    gate_file = repo / "validation_artifacts" / "r2" / "reclaimed_compatibility_gate_R9.json"
    gate_file.parent.mkdir(parents=True)
    gate_file.write_text(json.dumps({"gates": [{"id": "G2_shared_pool_joint_solver", "status": "PASS"}]}))
    code, output = _run(repo, "--mode", "diagnostic", "--dry-run")
    assert code == 0
    assert output["gate_statuses"] == {"g2": "NOT_READY", "g3": "NOT_READY"}
    assert output["formal_e3_e4_eligible"] is False
    assert output["execution_performed"] is False
    assert output["formal_blockers"]
    audit_result = audit(repo)
    assert "independent.phrq" in audit_result["g2"]["phreeqc_or_independent_chemistry_files"]
    assert all(not item.endswith(".py") for item in audit_result["g2"]["phreeqc_or_independent_chemistry_files"])


def test_forged_complete_manifests_do_not_upgrade_gates(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, status="gate_pass")
    out = repo / "validation_artifacts"
    (out / "g2_phreeqc_crosscheck").mkdir(parents=True)
    (out / "g2_phreeqc_crosscheck" / "manifest.json").write_text(json.dumps({
        "gate": "G2", "status": "PASS", "independent_solver": {"name": "PHREEQC"},
        "database_hash": "sha256:chem", "sample_count": 4,
        "sample_level_crosscheck": True, "per_sample_outputs": "samples.csv",
        "false_safe_rate": 0.0,
    }), encoding="utf-8")
    (out / "g3_facility_holdout").mkdir(parents=True)
    (out / "g3_facility_holdout" / "manifest.json").write_text(json.dumps({
        "gate": "G3", "status": "PASS", "facility_count": 3,
        "min_months_per_facility": 12, "leave_one_facility_out": True,
        "non_synthetic": True, "per_facility_metrics": "metrics.csv",
    }), encoding="utf-8")
    code, output = _run(repo, "--mode", "diagnostic", "--dry-run")
    assert code == 0
    assert output["gate_statuses"] == {"g2": "NOT_READY", "g3": "NOT_READY"}
    assert output["formal_e3_e4_eligible"] is False
    assert output["execution_performed"] is False


def test_malformed_manifest_metrics_do_not_upgrade_gates(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, status="gate_pass")
    out = repo / "validation_artifacts"
    (out / "g2_phreeqc_crosscheck").mkdir(parents=True)
    (out / "g2_phreeqc_crosscheck" / "manifest.json").write_text(json.dumps({
        "gate": "G2", "status": "PASS", "independent_solver": {"name": "PHREEQC"},
        "database_hash": "sha256:chem", "sample_count": 0.5,
        "sample_level_crosscheck": True, "per_sample_outputs": "samples.csv",
        "false_safe_rate": 1.5,
    }), encoding="utf-8")
    (out / "g3_facility_holdout").mkdir(parents=True)
    (out / "g3_facility_holdout" / "manifest.json").write_text(json.dumps({
        "gate": "G3", "status": "PASS", "facility_count": 3.5,
        "min_months_per_facility": 12, "leave_one_facility_out": "true",
        "non_synthetic": "false", "per_facility_metrics": "metrics.csv",
    }), encoding="utf-8")
    code, output = _run(repo, "--mode", "diagnostic", "--dry-run")
    assert code == 0
    assert output["gate_statuses"] == {"g2": "NOT_READY", "g3": "NOT_READY"}
    assert output["formal_e3_e4_eligible"] is False


def test_verified_g2_manifest_can_become_ready(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, status="gate_pass")
    out = repo / "validation_artifacts" / "g2_phreeqc_crosscheck"
    out.mkdir(parents=True)
    database = out / "vitens.dat"
    database.write_text("independent database fixture\n", encoding="utf-8")
    samples = out / "samples.csv"
    _write_csv(samples, {"sample_id": "s1", "value": "1"})
    sample_rows = [
        {"sample_id": f"s{i}", "source_provenance": "external-measured", "observed_flag": "true",
         "quality_flag": "pass", "reduced_order_coc": "1.0", "phreeqc_coc": "0.8",
         "reduced_order_safe_at_one": "false", "phreeqc_safe_at_one": "false"}
        for i in range(1, 5)
    ]
    output_csv = out / "samples.csv.out.csv"
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sample_rows[0]))
        writer.writeheader()
        writer.writerows(sample_rows)
    manifest = {
        "gate": "G2", "status": "PASS", "independent_solver": {
            "name": "PHREEQC", "database_path": database.name, "database_hash": _sha256(database)},
        "database_hash": _sha256(database), "sample_count": 4,
        "sample_level_crosscheck": True, "per_sample_outputs": output_csv.name,
        "output_hashes": {"per_sample": _sha256(output_csv)}, "false_safe_rate": 0.0,
        "input": {"path": samples.name, "sha256": _sha256(samples), "row_count": 4},
        "independent_review": {"status": "APPROVED", "reviewer": "reviewer-1", "scope_status": "IN_SCOPE"},
    }
    # Keep the input row count consistent with the manifest while retaining a
    # minimal, independently hashed source table.
    with samples.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sample_id", "value"])
        writer.writeheader()
        writer.writerows({"sample_id": f"s{i}", "value": "1"} for i in range(1, 5))
    manifest["input"]["sha256"] = _sha256(samples)
    (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    result = audit(repo)
    assert result["g2"]["status"] == "READY"


def test_verified_g3_manifest_requires_real_rows_and_review(tmp_path: Path) -> None:
    repo = _fixture(tmp_path, status="gate_pass")
    out = repo / "validation_artifacts" / "g3_facility_holdout"
    out.mkdir(parents=True)
    input_csv = out / "observations.csv"
    fields = [
        "facility_id", "study_id", "date", "timezone", "source_uri", "meter_id",
        "it_energy_mwh", "facility_energy_mwh", "pue", "wue_l_kwh_it", "makeup_ml",
        "blowdown_ml", "coc", "predicted_wue_l_kwh_it", "predicted_makeup_ml",
        "predicted_blowdown_ml", "predicted_coc", "synthetic_observed", "observed_flag",
        "prediction_source", "prediction_training_facilities", "quality_flag",
    ]
    rows = []
    for facility in ("F1", "F2", "F3"):
        training = "F2,F3" if facility == "F1" else ("F1,F3" if facility == "F2" else "F1,F2")
        for month in range(1, 13):
            values = {field: "1" for field in fields}
            values.update({"facility_id": facility, "study_id": "study-1", "date": f"2025-{month:02d}-01",
                           "timezone": "UTC", "source_uri": "https://example.org/measured",
                           "meter_id": f"meter-{facility}", "prediction_training_facilities": training,
                           "synthetic_observed": "false", "observed_flag": "true",
                           "prediction_source": "external-model", "quality_flag": "pass"})
            rows.append(values)
    with input_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    metrics_csv = out / "per_facility_metrics.csv"
    metric_fields = ["facility_id", "row_count", "month_count", "coverage_fraction", "wue_relative_error",
                     "makeup_relative_error", "blowdown_relative_error", "coc_absolute_error", "thresholds_pass", "status"]
    with metrics_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=metric_fields)
        writer.writeheader()
        for facility in ("F1", "F2", "F3"):
            writer.writerow({"facility_id": facility, "row_count": 12, "month_count": 12,
                             "coverage_fraction": 1, "wue_relative_error": 0, "makeup_relative_error": 0,
                             "blowdown_relative_error": 0, "coc_absolute_error": 0,
                             "thresholds_pass": "true", "status": "PASS"})
    prediction_csv = out / "prediction_rows.csv"
    with prediction_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["facility_id", "study_id", "date", "metric", "observed", "predicted"])
        writer.writeheader()
        for row in rows:
            for metric in ("wue", "makeup", "blowdown", "coc"):
                writer.writerow({"facility_id": row["facility_id"], "study_id": row["study_id"],
                                 "date": row["date"], "metric": metric, "observed": 1, "predicted": 1})
    manifest = {
        "gate": "G3", "status": "PASS", "facility_count": 3, "min_months_per_facility": 12,
        "leave_one_facility_out": True, "non_synthetic": True,
        "input": {"path": input_csv.name, "sha256": _sha256(input_csv), "row_count": len(rows)},
        "outputs": {"per_facility_metrics": metrics_csv.name, "prediction_rows": prediction_csv.name},
        "output_row_counts": {"per_facility_metrics": 3, "prediction_rows": len(rows) * 4},
        "output_hashes": {"per_facility_metrics": _sha256(metrics_csv), "prediction_rows": _sha256(prediction_csv)},
        "independent_review": {"status": "APPROVED", "reviewer": "reviewer-1", "scope_status": "IN_SCOPE"},
    }
    (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    result = audit(repo)
    assert result["g3"]["status"] == "READY"
