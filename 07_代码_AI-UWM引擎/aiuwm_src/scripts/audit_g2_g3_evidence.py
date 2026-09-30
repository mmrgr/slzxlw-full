"""Read-only inventory audit for the R10 G2/G3 evidence gates.

The audit never treats a generated/synthetic artifact as an observation.  It
only inventories files and provenance markers, then emits a conservative
``NOT_READY`` result when the independent chemistry or facility hold-out
evidence is absent.  It is intentionally stdlib-only so it can run before the
external validation toolchain is installed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from datetime import date
from pathlib import Path
from typing import Any, Iterable


PHREEQC_SUFFIXES = {".pqi", ".phrq", ".pqc", ".chem"}
PHREEQC_OUTPUT_SUFFIXES = {".csv", ".json", ".log", ".out", ".txt"}
PHREEQC_TOKENS = ("phreeqc", "pitzer", "reaktoro", "geochem")
OBSERVED_TOKENS = (
    "observed",
    "measured",
    "facility",
    "holdout",
    "hold-out",
    "实测",
    "现场",
    "观测",
    "留出",
)
SYNTHETIC_TOKENS = ("synthetic", "合成", "scenario_prior", "scenario-tuned", "情景")


def _iter_files(roots: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        files.extend(p for p in root.rglob("*") if p.is_file())
    return sorted(set(files))


def _rel(path: Path, roots: Iterable[Path]) -> str:
    for root in roots:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            continue
    return path.as_posix()


def _contains_tokens(path: Path, tokens: Iterable[str]) -> bool:
    name = path.name.lower()
    return any(token.lower() in name for token in tokens)


def _read_text(path: Path, limit: int = 250_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def _provenance_markers(files: Iterable[Path]) -> dict[str, int]:
    counts = {"synthetic_or_scenario": 0, "observed_marker": 0}
    for path in files:
        if path.suffix.lower() not in {".md", ".txt", ".csv", ".json", ".yaml", ".yml"}:
            continue
        text = _read_text(path).lower()
        if any(token.lower() in text for token in SYNTHETIC_TOKENS):
            counts["synthetic_or_scenario"] += 1
        if any(token.lower() in text for token in OBSERVED_TOKENS):
            counts["observed_marker"] += 1
    return counts


def _csv_header(path: Path) -> list[str]:
    try:
        with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
            return next(csv.reader(handle), [])
    except (OSError, csv.Error):
        return []


def _gate_manifest_candidates(repo_root: Path, experiment_root: Path | None, gate: str) -> list[Path]:
    """Find explicitly named validation manifests, never arbitrary evidence files."""
    roots = [repo_root / "validation_artifacts"]
    if experiment_root is not None:
        roots.extend((experiment_root / "validation_artifacts", experiment_root))
    tokens = (gate.lower(), "manifest")
    candidates: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.json"):
            normalized = path.as_posix().lower()
            if all(token in normalized for token in tokens):
                candidates.add(path)
        # The frozen runner output locations may use a generic manifest name.
        exact = root / ("g2_phreeqc_crosscheck" if gate == "G2" else "g3_facility_holdout") / "manifest.json"
        if exact.exists():
            candidates.add(exact)
    return sorted(candidates)


def _read_manifest(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(_read_text(path, limit=2_000_000))
    except (json.JSONDecodeError, OSError, TypeError):
        return None
    return payload if isinstance(payload, dict) else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _manifest_path(manifest: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = Path(value.strip())
    if not candidate.is_absolute():
        candidate = manifest.parent / candidate
    return candidate.resolve()


def _verified_file(manifest: Path, value: Any, expected_hash: Any) -> tuple[Path | None, str | None]:
    path = _manifest_path(manifest, value)
    if path is None:
        return None, "missing file reference"
    if not path.is_file():
        return None, f"referenced file does not exist: {path}"
    if not isinstance(expected_hash, str) or not expected_hash.startswith("sha256:"):
        return None, f"missing sha256 for referenced file: {path.name}"
    try:
        actual = _sha256(path)
    except OSError as exc:
        return None, f"cannot hash referenced file {path}: {exc}"
    if actual.lower() != expected_hash.lower():
        return None, f"sha256 mismatch for {path.name}"
    return path, None


def _review_ready(payload: dict[str, Any]) -> tuple[bool, str]:
    """Require an explicit, attributable independent review and scope decision."""
    review = payload.get("independent_review", payload.get("review"))
    if not isinstance(review, dict):
        return False, "independent_review record is missing"
    status = str(review.get("status", review.get("decision", ""))).strip().upper()
    if status not in {"APPROVED", "PASS", "COMPLETE"}:
        return False, "independent_review is not approved"
    reviewer = str(review.get("reviewer", review.get("reviewer_id", ""))).strip()
    if not reviewer:
        return False, "independent_review reviewer is missing"
    scope = review.get("scope_status", review.get("scope", payload.get("scope_status", "")))
    scope_text = str(scope).strip().upper()
    if scope_text not in {"APPROVED", "IN_SCOPE", "IN-SCOPE", "PASS", "COMPLETE"}:
        return False, "validation scope has not been approved"
    return True, "independent review and scope approval recorded"


def _csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]], str | None]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = [str(value).strip() for value in (reader.fieldnames or []) if value is not None]
            return fields, list(reader), None
    except (OSError, UnicodeError, csv.Error) as exc:
        return [], [], str(exc)


def _output_rows(path: Path) -> tuple[list[str], list[dict[str, Any]], str | None]:
    if path.suffix.lower() == ".csv":
        fields, rows, error = _csv_rows(path)
        return fields, rows, error
    try:
        payload = json.loads(_read_text(path, limit=20_000_000))
    except (json.JSONDecodeError, OSError, TypeError) as exc:
        return [], [], str(exc)
    if isinstance(payload, list):
        rows = [row for row in payload if isinstance(row, dict)]
    elif isinstance(payload, dict):
        rows = payload.get("rows", payload.get("results", []))
        if not isinstance(rows, list):
            rows = []
        rows = [row for row in rows if isinstance(row, dict)]
    else:
        rows = []
    fields = sorted({str(key) for row in rows for key in row})
    return fields, rows, None


def _finite_number(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _bool_marker(value: Any) -> bool | None:
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "pass", "ok"}:
        return True
    if text in {"false", "0", "no", "n", "fail"}:
        return False
    return None


def _quality_ok(row: dict[str, Any]) -> bool:
    for key in ("quality_flag", "quality_status", "quality", "data_quality"):
        if key in row:
            marker = str(row.get(key, "")).strip().lower()
            return marker in {"pass", "ok", "valid", "good", "true", "1", "accepted", "qa_pass", "quality_pass"}
    if "charge_balance_error_pct" in row:
        return _finite_number(row.get("charge_balance_error_pct"))
    return False


def _g2_manifest_check(paths: Iterable[Path]) -> tuple[bool, dict[str, Any] | None, str]:
    """Require a complete, sample-level independent chemistry validation record."""
    for path in paths:
        payload = _read_manifest(path)
        if payload is None or str(payload.get("status", "")).upper() != "PASS":
            continue
        gate = str(payload.get("gate", payload.get("gate_id", ""))).upper()
        if gate not in {"G2", "G2_CHEMISTRY", "G2_PHREEQC_CROSSCHECK"}:
            continue
        samples = payload.get("sample_count", payload.get("samples"))
        sample_count = samples if isinstance(samples, (int, float)) else 0
        solver = payload.get("independent_solver", payload.get("independent_chemistry_solver"))
        solver = solver if isinstance(solver, dict) else {}
        database_hash = payload.get("database_hash", solver.get("database_hash"))
        database_ref = solver.get("database_path", solver.get("database_file"))
        sample_check = payload.get("sample_level_crosscheck", False)
        if isinstance(sample_check, dict):
            sample_check = str(sample_check.get("status", "")).upper() == "PASS" or bool(sample_check.get("complete"))
        outputs = payload.get("per_sample_outputs", payload.get("per_sample_output"))
        if outputs is None and isinstance(payload.get("outputs"), dict):
            outputs = payload["outputs"].get("per_sample")
        false_safe = payload.get("false_safe_rate")
        if false_safe is None and isinstance(payload.get("metrics"), dict):
            false_safe = payload["metrics"].get("false_safe_rate")
        review_ok, review_reason = _review_ready(payload)
        sample_count_valid = (
            isinstance(sample_count, (int, float))
            and not isinstance(sample_count, bool)
            and math.isfinite(sample_count)
            and sample_count >= 1
            and float(sample_count).is_integer()
        )
        false_safe_valid = (
            isinstance(false_safe, (int, float))
            and not isinstance(false_safe, bool)
            and math.isfinite(false_safe)
            and 0.0 <= float(false_safe) <= 1.0
        )
        if not all((sample_count_valid, bool(solver), bool(database_hash), bool(database_ref), bool(sample_check), false_safe_valid, review_ok)):
            continue
        database_path, database_error = _verified_file(path, database_ref, database_hash)
        output_hashes = payload.get("output_hashes", {})
        output_hash = output_hashes.get("per_sample", output_hashes.get("sample_level")) if isinstance(output_hashes, dict) else None
        output_path, output_error = _verified_file(path, outputs, output_hash)
        if database_path is None or output_path is None:
            continue
        fields, output_rows, parse_error = _output_rows(output_path)
        required = {"sample_id", "source_provenance", "observed_flag", "reduced_order_coc", "phreeqc_coc", "reduced_order_safe_at_one", "phreeqc_safe_at_one"}
        if parse_error or not output_rows or not required.issubset(fields) or len(output_rows) != int(sample_count):
            continue
        if any(not str(row.get("sample_id", "")).strip() or not str(row.get("source_provenance", "")).strip()
               or _bool_marker(row.get("observed_flag")) is not True
               or not _quality_ok(row)
               or not all(_finite_number(row.get(key)) for key in ("reduced_order_coc", "phreeqc_coc"))
               for row in output_rows):
            continue
        false_safe_count = sum(
            _bool_marker(row.get("reduced_order_safe_at_one")) is True
            and _bool_marker(row.get("phreeqc_safe_at_one")) is False
            for row in output_rows
        )
        if abs(float(false_safe) - false_safe_count / len(output_rows)) > 1e-9:
            continue
        input_meta = payload.get("input") if isinstance(payload.get("input"), dict) else {}
        input_path, input_error = _verified_file(path, input_meta.get("path"), input_meta.get("sha256"))
        if input_path is None:
            continue
        input_fields, input_rows, input_parse_error = _csv_rows(input_path)
        input_ids = {str(row.get("sample_id", "")).strip() for row in input_rows}
        output_ids = {str(row.get("sample_id", "")).strip() for row in output_rows}
        if (input_parse_error or "sample_id" not in input_fields or len(input_rows) != int(sample_count)
                or input_meta.get("row_count", input_meta.get("sample_count")) != int(sample_count)
                or input_ids != output_ids or "" in input_ids):
            continue
        return True, {"path": str(path), "manifest": payload}, "Complete sample-level G2 validation manifest passed."
    return False, None, "No complete PASS G2 manifest with verified input/output hashes, chemistry provenance/quality rows, independent review, and false-safe statistic was found."


def _g3_manifest_check(paths: Iterable[Path]) -> tuple[bool, dict[str, Any] | None, str]:
    """Require the frozen minimum of three facilities and twelve months each."""
    for path in paths:
        payload = _read_manifest(path)
        if payload is None or str(payload.get("status", "")).upper() != "PASS":
            continue
        gate = str(payload.get("gate", payload.get("gate_id", ""))).upper()
        if gate not in {"G3", "G3_FACILITY_HOLDOUT", "G3_HOLDOUT"}:
            continue
        holdout = payload.get("holdout") if isinstance(payload.get("holdout"), dict) else {}
        facility_count = payload.get("facility_count", payload.get("facilities", holdout.get("facility_count")))
        if isinstance(facility_count, list):
            facility_count = len(facility_count)
        months = payload.get("min_months_per_facility", payload.get("minimum_months", holdout.get("min_months_per_facility")))
        loo = payload.get("leave_one_facility_out", payload.get("leave_one_out", holdout.get("leave_one_facility_out")))
        non_synthetic = payload.get("non_synthetic", holdout.get("non_synthetic", False))
        metrics = payload.get("per_facility_metrics", payload.get("facility_metrics"))
        prediction_rows = None
        if isinstance(payload.get("outputs"), dict):
            metrics = payload["outputs"].get("per_facility_metrics", metrics)
            prediction_rows = payload["outputs"].get("prediction_rows")
        prediction_rows = payload.get("prediction_rows", prediction_rows)
        facility_count_valid = (
            isinstance(facility_count, (int, float))
            and not isinstance(facility_count, bool)
            and math.isfinite(facility_count)
            and facility_count >= 3
            and float(facility_count).is_integer()
        )
        months_valid = (
            isinstance(months, (int, float))
            and not isinstance(months, bool)
            and math.isfinite(months)
            and months >= 12
            and float(months).is_integer()
        )
        review_ok, _ = _review_ready(payload)
        if not all((facility_count_valid, months_valid, loo is True, non_synthetic is True,
                    isinstance(metrics, str), isinstance(prediction_rows, str), review_ok)):
            continue
        input_meta = payload.get("input") if isinstance(payload.get("input"), dict) else {}
        input_path, _ = _verified_file(path, input_meta.get("path"), input_meta.get("sha256"))
        output_hashes = payload.get("output_hashes", {})
        metric_hash = (output_hashes.get("per_facility_metrics") or output_hashes.get("per_facility_metrics.csv")) if isinstance(output_hashes, dict) else None
        prediction_hash = (output_hashes.get("prediction_rows") or output_hashes.get("prediction_rows.csv")) if isinstance(output_hashes, dict) else None
        metrics_path, _ = _verified_file(path, metrics, metric_hash)
        prediction_path, _ = _verified_file(path, prediction_rows, prediction_hash)
        if input_path is None or metrics_path is None or prediction_path is None:
            continue
        fields, rows, input_error = _csv_rows(input_path)
        metric_fields, metric_rows, metric_error = _csv_rows(metrics_path)
        pred_fields, pred_rows, pred_error = _csv_rows(prediction_path)
        required_input = {"facility_id", "study_id", "date", "timezone", "source_uri", "meter_id",
                          "synthetic_observed", "observed_flag", "prediction_source", "prediction_training_facilities"}
        required_metrics = {"facility_id", "row_count", "month_count", "coverage_fraction",
                            "wue_relative_error", "makeup_relative_error", "blowdown_relative_error",
                            "coc_absolute_error", "thresholds_pass", "status"}
        if input_error or metric_error or pred_error or not required_input.issubset(fields) or not required_metrics.issubset(metric_fields):
            continue
        expected_rows = input_meta.get("row_count")
        if not isinstance(expected_rows, (int, float)) or int(expected_rows) != len(rows) or len(rows) == 0:
            continue
        facilities: dict[str, list[date]] = {}
        invalid_input = False
        for row in rows:
            facility = str(row.get("facility_id", "")).strip()
            try:
                day = date.fromisoformat(str(row.get("date", "")).strip()[:10])
            except ValueError:
                invalid_input = True
                break
            if not facility or not all(str(row.get(key, "")).strip() for key in ("study_id", "timezone", "source_uri", "meter_id", "prediction_source", "prediction_training_facilities")):
                invalid_input = True
                break
            if _bool_marker(row.get("synthetic_observed")) is not False or _bool_marker(row.get("observed_flag")) is not True or not _quality_ok(row):
                invalid_input = True
                break
            training = {part.strip() for part in re.split(r"[,;|]", str(row.get("prediction_training_facilities", ""))) if part.strip()}
            if not training or facility in training:
                invalid_input = True
                break
            facilities.setdefault(facility, []).append(day)
        if invalid_input or len(facilities) != int(facility_count) or len(metric_rows) != len(facilities):
            continue
        if any(len({(day.year, day.month) for day in days}) < 12 or
               ((max(days).year - min(days).year) * 12 + max(days).month - min(days).month + 1) < 12
               for days in facilities.values()):
            continue
        metric_ids = {str(row.get("facility_id", "")).strip() for row in metric_rows}
        output_counts = payload.get("output_row_counts")
        if not isinstance(output_counts, dict) and isinstance(payload.get("outputs"), dict):
            output_counts = payload["outputs"].get("row_counts")
        if not isinstance(output_counts, dict) or output_counts.get("per_facility_metrics") != len(metric_rows) or output_counts.get("prediction_rows") != len(pred_rows):
            continue
        actual_min_months = min(len({(day.year, day.month) for day in days}) for days in facilities.values())
        if metric_ids != set(facilities) or len(pred_rows) < len(rows) * 4 or actual_min_months < int(months):
            continue
        if any(str(row.get("status", "")).upper() != "PASS" or _bool_marker(row.get("thresholds_pass")) is not True
               or not all(_finite_number(row.get(key)) for key in ("coverage_fraction", "wue_relative_error", "makeup_relative_error", "blowdown_relative_error", "coc_absolute_error"))
               for row in metric_rows):
            continue
        return True, {"path": str(path), "manifest": payload}, "Complete G3 facility hold-out manifest passed."
    return False, None, "No complete PASS G3 manifest with verified input/output hashes, facility/month structure, provenance/quality rows, and independent review was found."


def audit(repo_root: Path, experiment_root: Path | None = None) -> dict[str, Any]:
    roots = [repo_root]
    if experiment_root is not None:
        roots.append(experiment_root)
    files = _iter_files(roots)

    validation_roots = [root / "validation_artifacts" for root in roots]
    phreeqc_files = []
    for path in files:
        suffix = path.suffix.lower()
        is_solver_input = suffix in PHREEQC_SUFFIXES
        is_validation_output = (
            suffix in PHREEQC_OUTPUT_SUFFIXES
            and _contains_tokens(path, PHREEQC_TOKENS)
            and any(path.is_relative_to(root) for root in validation_roots if root.exists())
        )
        if is_solver_input or is_validation_output:
            phreeqc_files.append(path)

    candidate_external = []
    for path in files:
        if path.suffix.lower() not in {".csv", ".json", ".parquet", ".xlsx", ".xls", ".txt"}:
            continue
        if _contains_tokens(path, OBSERVED_TOKENS):
            candidate_external.append(path)

    synthetic_candidates = []
    for path in candidate_external:
        normalized = path.as_posix().lower()
        # ``create_demo_inputs.py`` writes examples/demo_full/observed.csv from
        # a model run plus noise; the filename alone must never upgrade it to
        # an observation.
        is_demo_output = "/examples/demo" in normalized or normalized.endswith("/synthetic_observed.csv")
        if _contains_tokens(path, SYNTHETIC_TOKENS) or is_demo_output:
            synthetic_candidates.append(path)
    non_synthetic_candidates = [path for path in candidate_external if path not in synthetic_candidates]

    registry = repo_root / "data" / "parameter_registry.csv"
    registry_rows = 0
    registry_prior_rows = 0
    if registry.exists():
        try:
            with registry.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            registry_rows = len(rows)
            registry_prior_rows = sum(
                row.get("observation_population", "").strip().lower() == "scenario_prior"
                for row in rows
            )
        except (OSError, csv.Error):
            pass

    scenario = repo_root / "data" / "scenario_registry.csv"
    scenario_rows = 0
    scenario_not_ready_rows = 0
    if scenario.exists():
        try:
            with scenario.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            scenario_rows = len(rows)
            scenario_not_ready_rows = sum(
                row.get("status", "").strip().lower() == "not_ready" for row in rows
            )
        except (OSError, csv.Error):
            pass

    r9_gate = repo_root / "validation_artifacts" / "r2" / "reclaimed_compatibility_gate_R9.json"
    r9_g2_status = None
    if r9_gate.exists():
        try:
            payload = json.loads(_read_text(r9_gate))
            for gate in payload.get("gates", []):
                if gate.get("id") == "G2_shared_pool_joint_solver":
                    r9_g2_status = gate.get("status")
                    break
        except json.JSONDecodeError:
            pass

    g2_ready, g2_manifest, g2_reason = _g2_manifest_check(
        _gate_manifest_candidates(repo_root, experiment_root, "G2")
    )
    g3_ready, g3_manifest, g3_reason = _g3_manifest_check(
        _gate_manifest_candidates(repo_root, experiment_root, "G3")
    )
    return {
        "audit": "R10 G2/G3 evidence inventory",
        "repo_root": str(repo_root),
        "experiment_root": str(experiment_root) if experiment_root else None,
        "g2": {
            "status": "READY" if g2_ready else "NOT_READY",
            "phreeqc_or_independent_chemistry_files": [_rel(p, roots) for p in phreeqc_files],
            "r9_joint_gate_status": r9_g2_status,
            "validation_manifest": g2_manifest,
            "reason": g2_reason,
        },
        "g3": {
            "status": "READY" if g3_ready else "NOT_READY",
            "candidate_external_files": [_rel(p, roots) for p in candidate_external],
            "synthetic_or_scenario_candidates": [_rel(p, roots) for p in synthetic_candidates],
            "non_synthetic_candidate_files": [_rel(p, roots) for p in non_synthetic_candidates],
            "validation_manifest": g3_manifest,
            "reason": g3_reason,
        },
        "provenance": _provenance_markers(files),
        "registries": {
            "parameter_rows": registry_rows,
            "scenario_prior_rows": registry_prior_rows,
            "scenario_rows": scenario_rows,
            "scenario_not_ready_rows": scenario_not_ready_rows,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--experiment-root", type=Path)
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args()
    result = audit(args.repo_root.resolve(), args.experiment_root.resolve() if args.experiment_root else None)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
