"""Run the preregistered G3 facility leave-one-out diagnostic.

The runner consumes a daily table containing *observed* facility indicators and
out-of-sample model predictions.  It deliberately does not fit a model: model
fitting and calibration must happen before this script is called, and the
``prediction_training_facilities`` column makes the calibration/validation
separation auditable.  Missing provenance, insufficient time coverage, or a
synthetic table produces ``NOT_READY``.  A complete non-synthetic table whose
errors miss the preregistered limits produces ``FAIL``.  Only a complete table
with all leave-one-facility-out metrics inside the frozen limits can produce
``PASS``.

The command is intentionally stdlib-only so it can be used as a gate preflight.
It writes ``manifest.json`` and ``per_facility_metrics.csv`` under ``--output``
even when the result is ``NOT_READY``.  A generated diagnostic is not evidence
of a facility validation result; the G3 audit still requires a PASS manifest.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


GATE = "G3"
SPLIT = "leave-one-facility-out"
RUNNER_VERSION = "R10-G3-1.1"
MIN_FACILITIES = 3
MIN_MONTHS = 12
MIN_COVERAGE = 0.90

# These limits are frozen before a validation table is inspected.  They are
# deliberately exposed in the manifest so a later reviewer can compare a
# result with the preregistered analysis plan.
THRESHOLDS: dict[str, float] = {
    "wue_relative_error": 0.20,
    "makeup_relative_error": 0.20,
    "blowdown_relative_error": 0.25,
    "coc_absolute_error": 0.50,
    "coverage_fraction": MIN_COVERAGE,
}

CORE_COLUMNS = (
    "facility_id", "study_id", "date", "timezone", "source_uri", "meter_id",
    "it_energy_mwh", "facility_energy_mwh", "pue",
)
CONTEXT_ALIASES: dict[str, tuple[str, ...]] = {
    "dry_bulb_c": ("dry_bulb_c", "dry_bulb_temperature_c", "temperature_db_c"),
    "wet_bulb_c": ("wet_bulb_c", "wet_bulb_temperature_c", "temperature_wb_c"),
    "cooling_technology": ("cooling_technology", "cooling_tech", "technology"),
    "reclaimed_fraction": ("reclaimed_fraction", "reclaimed_water_fraction", "reclaimed_ratio"),
}
METRIC_ALIASES: dict[str, tuple[str, ...]] = {
    "wue_l_kwh_it": (
        "wue_l_kwh_it", "wue", "observed_wue_l_kwh_it", "observed_wue",
    ),
    "makeup_ml": (
        "makeup_ml", "cooling_makeup_ml", "external_makeup_ml",
        "gross_makeup_ml", "observed_makeup_ml", "observed_cooling_makeup_ml",
    ),
    "blowdown_ml": ("blowdown_ml", "observed_blowdown_ml"),
    "coc": ("coc", "cycles_of_concentration", "observed_coc"),
}
PREDICTED_ALIASES: dict[str, tuple[str, ...]] = {
    metric: tuple(dict.fromkeys(
        [f"predicted_{metric}", f"model_{metric}", f"simulated_{metric}", f"{metric}_predicted"]
        + [f"predicted_{alias}" for alias in aliases]
        + [f"model_{alias}" for alias in aliases]
        + [f"{alias}_predicted" for alias in aliases]
    ))
    for metric, aliases in METRIC_ALIASES.items()
}
PROVENANCE_ALIASES = {
    "synthetic_observed": ("synthetic_observed", "synthetic_flag", "is_synthetic"),
    "observed_flag": ("observed_flag", "is_observed"),
    "prediction_source": ("prediction_source", "model_source", "prediction_provenance"),
    "prediction_training_facilities": (
        "prediction_training_facilities", "training_facilities", "calibration_facilities",
    ),
    "quality_flag": ("quality_flag", "quality_status", "data_quality", "qa_status"),
}
SYNTHETIC_TOKENS = ("synthetic", "scenario", "demo", "generated", "fixture", "伪观测", "合成")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _first_column(fieldnames: Iterable[str], aliases: Iterable[str]) -> str | None:
    fields = set(fieldnames)
    for alias in aliases:
        if alias in fields:
            return alias
    return None


def _text(row: Mapping[str, str], column: str | None) -> str:
    return str(row.get(column, "") if column else "").strip()


def _number(value: Any, *, name: str, nonnegative: bool = False) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    if nonnegative and result < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return result


def _parse_date(value: str) -> date:
    text = value.strip()
    try:
        return date.fromisoformat(text)
    except ValueError:
        try:
            normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
            return datetime.fromisoformat(normalized).date()
        except ValueError as exc:
            raise ValueError(f"invalid ISO date or daily timestamp: {value!r}") from exc


def _relative_error(observed: list[float], predicted: list[float]) -> float:
    errors: list[float] = []
    for actual, estimate in zip(observed, predicted):
        denominator = max(abs(actual), 1e-12)
        errors.append(abs(estimate - actual) / denominator)
    return sum(errors) / len(errors) if errors else math.nan


def _mean_absolute_error(observed: list[float], predicted: list[float]) -> float:
    errors = [abs(estimate - actual) for actual, estimate in zip(observed, predicted)]
    return sum(errors) / len(errors) if errors else math.nan


def _month_count(days: Iterable[date]) -> int:
    return len({(value.year, value.month) for value in days})


def _elapsed_months(days: list[date]) -> int:
    """Count full calendar months over the inclusive observation interval."""
    start, stop = min(days), max(days) + timedelta(days=1)
    months = (stop.year - start.year) * 12 + stop.month - start.month
    anniversary_day = min(start.day, calendar.monthrange(stop.year, stop.month)[1])
    return months - int(stop.day < anniversary_day)


def _expected_days(days: list[date]) -> int:
    if not days:
        return 0
    return (max(days) - min(days)).days + 1


def _coverage(days: list[date]) -> float:
    expected = _expected_days(days)
    return len(set(days)) / expected if expected else 0.0


def _contains_synthetic(text: str) -> bool:
    lowered = text.strip().lower()
    return any(token in lowered for token in SYNTHETIC_TOKENS)


def _training_ids(value: str) -> set[str]:
    return {part.strip() for part in re.split(r"[,;|]", value) if part.strip()}


def _base_result(observations: Path, output: Path, *, status: str, reasons: list[str]) -> dict[str, Any]:
    return {
        "kind": "G3_FACILITY_HOLDOUT",
        "runner_version": RUNNER_VERSION,
        "gate": GATE,
        "status": status,
        "split": SPLIT,
        "leave_one_facility_out": True,
        "non_synthetic": False,
        "facility_count": 0,
        "min_months_per_facility": 0,
        "facility_ids": [],
        "study_ids": [],
        "thresholds": dict(THRESHOLDS),
        "metric_definitions": {
            "relative_error": "mean(abs(predicted-observed)/max(abs(observed),1e-12)) across daily pairs",
            "coc_absolute_error": "mean(abs(predicted-observed)) across daily pairs",
            "month_count": "completed calendar months over inclusive date interval, also requiring 12 distinct observed calendar months",
            "coverage": "unique observed days divided by days in inclusive date interval",
        },
        "input": {"path": str(observations.resolve()), "sha256": None, "row_count": 0},
        "outputs": {
            "per_facility_metrics": "per_facility_metrics.csv",
            "prediction_rows": "prediction_rows.csv",
            "row_counts": {"per_facility_metrics": 0, "prediction_rows": 0},
        },
        "coverage": {},
        "per_facility_metrics": "per_facility_metrics.csv",
        "holdout": {
            "facility_count": 0,
            "min_months_per_facility": 0,
            "leave_one_facility_out": True,
            "non_synthetic": False,
        },
        "reasons": reasons,
        "gate_effect": "G3 remains NOT_READY until an independent non-synthetic facility/study hold-out satisfies the frozen protocol.",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def _write_outputs(output: Path, payload: dict[str, Any], metrics: list[dict[str, Any]], prediction_rows: list[dict[str, Any]]) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    metric_fields = [
        "facility_id", "study_ids", "row_count", "month_count", "coverage_fraction",
        "wue_relative_error", "makeup_relative_error", "blowdown_relative_error",
        "coc_absolute_error", "thresholds_pass", "status", "reason",
    ]
    with (output / "per_facility_metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=metric_fields)
        writer.writeheader()
        for row in metrics:
            writer.writerow({name: row.get(name, "") for name in metric_fields})
    prediction_fields = ["facility_id", "study_id", "date", "metric", "observed", "predicted"]
    with (output / "prediction_rows.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=prediction_fields)
        writer.writeheader()
        for row in prediction_rows:
            writer.writerow({name: row.get(name, "") for name in prediction_fields})
    payload["outputs"]["row_counts"] = {
        "per_facility_metrics": len(metrics),
        "prediction_rows": len(prediction_rows),
    }
    payload["output_row_counts"] = dict(payload["outputs"]["row_counts"])
    payload["output_hashes"] = {
        "per_facility_metrics.csv": _sha256(output / "per_facility_metrics.csv"),
        "prediction_rows.csv": _sha256(output / "prediction_rows.csv"),
    }
    payload["output_row_counts"].update({
        "per_facility_metrics.csv": len(metrics),
        "prediction_rows.csv": len(prediction_rows),
    })
    payload["output_metadata"] = {
        name: {
            "path": name,
            "sha256": payload["output_hashes"][f"{name}.csv"],
            "row_count": payload["output_row_counts"][name],
        }
        for name in ("per_facility_metrics", "prediction_rows")
    }
    (output / "manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def run(observations: Path, output: Path, *, split: str = SPLIT) -> dict[str, Any]:
    """Run G3 and write a conservative manifest.

    The function returns a manifest for all ordinary data/provenance failures;
    only an operating-system error while writing the output is allowed to
    propagate.  This makes the result inspectable in automated gate checks.
    """
    observations = Path(observations).resolve()
    output = Path(output).resolve()
    reasons: list[str] = []
    payload = _base_result(observations, output, status="NOT_READY", reasons=reasons)
    metrics: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []
    if split != SPLIT:
        reasons.append(f"unsupported split {split!r}; only {SPLIT!r} is frozen")
        return _write_outputs(output, payload, metrics, prediction_rows)
    if not observations.exists():
        reasons.append(f"observation file does not exist: {observations}")
        return _write_outputs(output, payload, metrics, prediction_rows)
    try:
        payload["input"]["sha256"] = _sha256(observations)
        with observations.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = [str(value).strip() for value in (reader.fieldnames or []) if value is not None]
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        reasons.append(f"could not read CSV: {exc}")
        return _write_outputs(output, payload, metrics, prediction_rows)
    payload["input"]["row_count"] = len(rows)
    if not rows:
        reasons.append("observation file is empty")
        return _write_outputs(output, payload, metrics, prediction_rows)

    missing_core = [column for column in CORE_COLUMNS if column not in fields]
    context_columns = {
        key: _first_column(fields, aliases) for key, aliases in CONTEXT_ALIASES.items()
    }
    missing_core.extend(key for key, column in context_columns.items() if column is None)
    metric_columns: dict[str, str | None] = {
        metric: _first_column(fields, aliases) for metric, aliases in METRIC_ALIASES.items()
    }
    predicted_columns: dict[str, str | None] = {
        metric: _first_column(fields, aliases) for metric, aliases in PREDICTED_ALIASES.items()
    }
    missing_metrics = [metric for metric, column in metric_columns.items() if column is None]
    missing_predictions = [metric for metric, column in predicted_columns.items() if column is None]
    missing_core.extend(f"observed:{metric}" for metric in missing_metrics)
    missing_core.extend(f"predicted:{metric}" for metric in missing_predictions)
    provenance_columns = {
        key: _first_column(fields, aliases) for key, aliases in PROVENANCE_ALIASES.items()
    }
    missing_provenance = [
        key for key in (
            "synthetic_observed", "observed_flag", "prediction_source",
            "prediction_training_facilities", "quality_flag",
        )
        if provenance_columns[key] is None
    ]
    if missing_core:
        reasons.append("missing required columns: " + ", ".join(missing_core))
    if missing_provenance:
        reasons.append("missing provenance columns: " + ", ".join(missing_provenance))
    if missing_core or missing_provenance:
        return _write_outputs(output, payload, metrics, prediction_rows)

    parsed: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, date]] = set()
    facilities: set[str] = set()
    synthetic_rows: list[int] = []
    provenance_errors: list[str] = []
    malformed_rows: list[str] = []
    for index, row in enumerate(rows, start=2):
        facility = _text(row, "facility_id")
        study = _text(row, "study_id")
        source_uri = _text(row, "source_uri")
        meter_id = _text(row, "meter_id")
        if not facility or not study or not source_uri or not meter_id or not _text(row, "timezone"):
            malformed_rows.append(f"row {index}: facility/study/source_uri/meter_id/timezone must be non-empty")
            continue
        try:
            day = _parse_date(_text(row, "date"))
            it_energy = _number(row.get("it_energy_mwh"), name=f"it_energy_mwh row {index}")
            facility_energy = _number(row.get("facility_energy_mwh"), name=f"facility_energy_mwh row {index}")
            pue = _number(row.get("pue"), name=f"pue row {index}")
            if it_energy <= 0 or facility_energy < it_energy or pue < 1:
                raise ValueError("positive IT energy, facility energy >= IT energy and PUE >=1 required")
            if not math.isclose(pue, facility_energy / it_energy, rel_tol=0.01, abs_tol=0.001):
                raise ValueError("PUE differs from facility_energy_mwh/it_energy_mwh beyond 1% rounding allowance")
            dry_bulb = _number(row.get(context_columns["dry_bulb_c"]), name="dry_bulb_c")
            wet_bulb = _number(row.get(context_columns["wet_bulb_c"]), name="wet_bulb_c")
            reclaimed_fraction = _number(row.get(context_columns["reclaimed_fraction"]), name="reclaimed_fraction")
            if wet_bulb > dry_bulb or not 0 <= reclaimed_fraction <= 1:
                raise ValueError("wet bulb must not exceed dry bulb; reclaimed_fraction must be in [0,1]")
            if not _text(row, context_columns["cooling_technology"]):
                raise ValueError("cooling_technology must be non-empty")
            observed = {
                metric: _number(row.get(column), name=f"{metric} row {index}", nonnegative=(metric != "coc"))
                for metric, column in metric_columns.items()
            }
            predicted = {
                metric: _number(row.get(column), name=f"predicted {metric} row {index}", nonnegative=(metric != "coc"))
                for metric, column in predicted_columns.items()
            }
            if observed["coc"] < 1 or predicted["coc"] < 1:
                raise ValueError("observed and predicted CoC must be >=1")
            if observed["blowdown_ml"] > observed["makeup_ml"] or predicted["blowdown_ml"] > predicted["makeup_ml"]:
                raise ValueError("daily blowdown exceeds makeup; storage adjustment requires a different registered protocol")
        except ValueError as exc:
            malformed_rows.append(f"row {index}: {exc}")
            continue
        key = (facility, day)
        if key in seen_keys:
            malformed_rows.append(f"row {index}: duplicate facility/date {facility}/{day.isoformat()}")
            continue
        seen_keys.add(key)
        facilities.add(facility)
        synthetic_marker = _text(row, provenance_columns["synthetic_observed"])
        observed_flag = _text(row, provenance_columns["observed_flag"])
        quality_flag = _text(row, provenance_columns["quality_flag"]).lower()
        prediction_source = _text(row, provenance_columns["prediction_source"])
        training_facilities = _training_ids(_text(row, provenance_columns["prediction_training_facilities"]))
        if synthetic_marker.lower() not in {"false", "0", "no", "n"}:
            provenance_errors.append(f"row {index}: synthetic_observed must be an explicit false value")
        if observed_flag.lower() not in {"true", "1", "yes", "y"}:
            provenance_errors.append(f"row {index}: observed_flag must be an explicit true value")
        if quality_flag not in {"good", "valid", "ok", "pass", "accepted", "qa_pass", "quality_pass", "true", "1", "yes", "y"}:
            provenance_errors.append(f"row {index}: quality_flag must explicitly identify an accepted/valid observation")
        if (
            synthetic_marker.lower() in {"true", "1", "yes", "y"}
            or _contains_synthetic(source_uri)
            or _contains_synthetic(prediction_source)
            or _contains_synthetic(synthetic_marker)
            or observed_flag.lower() in {"false", "0", "no", "n"}
        ):
            synthetic_rows.append(index)
        parsed.append({
            "facility_id": facility, "study_id": study, "date": day,
            "source_uri": source_uri, "meter_id": meter_id,
            "observed": observed, "predicted": predicted,
            "prediction_source": prediction_source,
            "training_facilities": training_facilities,
            "quality_flag": quality_flag,
        })
    if malformed_rows:
        reasons.append("malformed or duplicate rows: " + "; ".join(malformed_rows[:8]))
        if len(malformed_rows) > 8:
            reasons.append(f"and {len(malformed_rows) - 8} additional malformed rows")
    if synthetic_rows:
        reasons.append(f"synthetic or non-observed provenance detected in {len(synthetic_rows)} row(s): {synthetic_rows[:8]}")
    if provenance_errors:
        reasons.append("invalid observation provenance: " + "; ".join(provenance_errors[:8]))
        if len(provenance_errors) > 8:
            reasons.append(f"and {len(provenance_errors) - 8} additional provenance errors")
    if len(parsed) != len(rows):
        reasons.append(f"only {len(parsed)} of {len(rows)} rows passed parsing")
    if not parsed:
        return _write_outputs(output, payload, metrics, prediction_rows)

    by_facility: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in parsed:
        by_facility[row["facility_id"]].append(row)
    facility_months = {
        facility: min(_month_count([row["date"] for row in facility_rows]), _elapsed_months([row["date"] for row in facility_rows]))
        for facility, facility_rows in by_facility.items()
    }
    facility_coverages = {
        facility: _coverage([row["date"] for row in facility_rows])
        for facility, facility_rows in by_facility.items()
    }
    payload["facility_count"] = len(by_facility)
    payload["min_months_per_facility"] = min(facility_months.values(), default=0)
    payload["facility_ids"] = sorted(by_facility)
    payload["study_ids"] = sorted({row["study_id"] for row in parsed})
    payload["holdout"].update({
        "facility_count": len(by_facility),
        "min_months_per_facility": payload["min_months_per_facility"],
    })
    payload["coverage"] = {
        "per_facility_months": facility_months,
        "per_facility_date_coverage": facility_coverages,
        "minimum_fraction": MIN_COVERAGE,
    }
    if len(by_facility) < MIN_FACILITIES:
        reasons.append(f"at least {MIN_FACILITIES} facilities are required; found {len(by_facility)}")
    short_months = {facility: count for facility, count in facility_months.items() if count < MIN_MONTHS}
    if short_months:
        reasons.append(f"each facility needs at least {MIN_MONTHS} complete calendar months; short facilities: {short_months}")
    low_coverage = {facility: value for facility, value in facility_coverages.items() if value < MIN_COVERAGE}
    if low_coverage:
        reasons.append(f"date coverage below {MIN_COVERAGE:.0%}: {low_coverage}")

    # Validate the held-out provenance before calculating any error summary.
    leakage: list[str] = []
    missing_prediction_source: list[str] = []
    fold_scopes: dict[str, set[str]] = {}
    study_facilities: dict[str, set[str]] = defaultdict(set)
    for row in parsed:
        study_facilities[row["study_id"]].add(row["facility_id"])
    mixed_studies = sorted(study for study, facility_set in study_facilities.items() if len(facility_set) > 1)
    if mixed_studies:
        leakage.extend(f"study:{study}:maps-to-multiple-facilities" for study in mixed_studies)
    for row in parsed:
        facility = row["facility_id"]
        if not row["prediction_source"]:
            missing_prediction_source.append(facility)
        if facility in row["training_facilities"]:
            leakage.append(facility)
        if not row["training_facilities"]:
            leakage.append(f"{facility}:empty-training-set")
        expected_training = set(by_facility) - {facility}
        if not expected_training.issubset(row["training_facilities"]):
            leakage.append(f"{facility}:missing-peer-training-facilities")
        unknown_training = row["training_facilities"] - set(by_facility)
        if unknown_training:
            leakage.append(f"{facility}:unknown-training-facilities:{','.join(sorted(unknown_training))}")
        if facility in fold_scopes and fold_scopes[facility] != row["training_facilities"]:
            leakage.append(f"{facility}:training-scope-changed-within-fold")
        fold_scopes[facility] = row["training_facilities"]
    payload["holdout"]["prediction_training_facilities"] = {
        facility: sorted(scope) for facility, scope in sorted(fold_scopes.items())
    }
    if missing_prediction_source:
        reasons.append("prediction_source is empty for facility(s): " + ", ".join(sorted(set(missing_prediction_source))))
    if leakage:
        reasons.append("calibration/validation separation cannot be verified; held-out facility leakage, incomplete peer training scope or inconsistent fold scope: " + ", ".join(sorted(set(leakage))))

    for facility, facility_rows in sorted(by_facility.items()):
        metric_values: dict[str, float] = {}
        for metric in METRIC_ALIASES:
            actual = [row["observed"][metric] for row in facility_rows]
            estimate = [row["predicted"][metric] for row in facility_rows]
            metric_values[metric] = _relative_error(actual, estimate) if metric != "coc" else _mean_absolute_error(actual, estimate)
            for row, observed, predicted in zip(facility_rows, actual, estimate):
                prediction_rows.append({
                    "facility_id": facility, "study_id": row["study_id"],
                    "date": row["date"].isoformat(), "metric": metric,
                    "observed": observed, "predicted": predicted,
                })
        threshold_pass = (
            facility_coverages[facility] >= MIN_COVERAGE
            and metric_values["wue_l_kwh_it"] <= THRESHOLDS["wue_relative_error"]
            and metric_values["makeup_ml"] <= THRESHOLDS["makeup_relative_error"]
            and metric_values["blowdown_ml"] <= THRESHOLDS["blowdown_relative_error"]
            and metric_values["coc"] <= THRESHOLDS["coc_absolute_error"]
        )
        row_reason = "" if threshold_pass else "one or more preregistered error/coverage thresholds exceeded"
        metrics.append({
            "facility_id": facility,
            "study_ids": "|".join(sorted({row["study_id"] for row in facility_rows})),
            "row_count": len(facility_rows),
            "month_count": facility_months[facility],
            "coverage_fraction": round(facility_coverages[facility], 8),
            "wue_relative_error": round(metric_values["wue_l_kwh_it"], 8),
            "makeup_relative_error": round(metric_values["makeup_ml"], 8),
            "blowdown_relative_error": round(metric_values["blowdown_ml"], 8),
            "coc_absolute_error": round(metric_values["coc"], 8),
            "thresholds_pass": threshold_pass,
            "status": "PASS" if threshold_pass else "FAIL",
            "reason": row_reason,
        })

    payload["non_synthetic"] = not synthetic_rows and not provenance_errors and not reasons_from_synthetic(reasons)
    payload["holdout"]["non_synthetic"] = payload["non_synthetic"]
    structural_blockers = bool(
        synthetic_rows or provenance_errors or malformed_rows or len(parsed) != len(rows)
        or len(by_facility) < MIN_FACILITIES or short_months or low_coverage
        or leakage or missing_prediction_source
    )
    if structural_blockers:
        payload["status"] = "NOT_READY"
    elif all(bool(row["thresholds_pass"]) for row in metrics):
        payload["status"] = "PASS"
        payload["gate_effect"] = "G3 facility hold-out completed under the frozen protocol; independent review is still required before formal E3/E4 unlock."
    else:
        payload["status"] = "FAIL"
        reasons.append("at least one complete facility hold-out misses a preregistered threshold")
    return _write_outputs(output, payload, metrics, prediction_rows)


def reasons_from_synthetic(reasons: Iterable[str]) -> bool:
    """Keep the non-synthetic flag conservative when only text is available."""
    return any("synthetic" in reason.lower() or "non-observed" in reason.lower() for reason in reasons)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--split", default=SPLIT, choices=(SPLIT,))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = run(args.observations, args.output, split=args.split)
    print(json.dumps({
        "output": str(args.output.resolve()),
        "status": payload["status"],
        "facility_count": payload["facility_count"],
        "min_months_per_facility": payload["min_months_per_facility"],
        "reasons": payload["reasons"],
    }, ensure_ascii=False))
    return 0 if payload["status"] in {"PASS", "FAIL", "NOT_READY"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
