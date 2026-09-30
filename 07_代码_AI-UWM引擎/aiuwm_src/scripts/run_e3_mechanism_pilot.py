"""Run the read-only R10 E3 paired mechanism diagnostic.

The runner consumes one JSON manifest containing the four frozen states
``Q0/Ls``, ``Q1/Ls``, ``Q0/Ld`` and ``Q1/Ld``.  It only compares already
computed run tables; it never invokes or mutates the main model.  The default
mode is therefore an auditable ``PILOT_ONLY`` diagnostic.  ``--formal`` is a
hard gate and requires the independent G2/G3 audit plus explicit independent
review and coupled-run approval before the same calculations can be labelled
formal.

The manifest accepts CSV/JSON table paths, or inline ``rows`` lists.  Each
table must contain one row per ``date``/``dc_id`` pair and the four tables must
have exactly the same keys.  A common seed and provenance identifier must be
present either in the manifest/table metadata or in the rows.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]

try:
    from audit_g2_g3_evidence import audit
except ModuleNotFoundError:  # import as ``scripts.run_e3_mechanism_pilot``
    from scripts.audit_g2_g3_evidence import audit


STATES = ("Q0/Ls", "Q1/Ls", "Q0/Ld", "Q1/Ld")
Q_LEVELS = ("Q0", "Q1")
L_LEVELS = ("Ls", "Ld")

# Canonical names are deliberately explicit.  The aliases accommodate exports
# from the current engine while keeping the E3 contract independent of it.
ALIASES: dict[str, tuple[str, ...]] = {
    "ai_potable_ml": ("ai_potable_ml", "ai_potable", "ai_potable_water_ml", "AI_potable_ml", "AI_potable_water_ml", "potable_water_ml", "potable_delivered_ml"),
    "ai_reclaimed_ml": ("ai_reclaimed_ml", "ai_reclaimed", "ai_reclaimed_water_ml", "AI_reclaimed_ml", "AI_reclaimed_water_ml", "reclaimed_water_ml", "reclaimed_supply_ml"),
    "source_withdrawal_ml": ("source_withdrawal_ml", "source_withdrawal", "withdrawal_ml", "external_withdrawal_ml", "potable_withdrawal_ml"),
    "incumbent_potable_ml": ("incumbent_potable_ml", "incumbent_potable", "incumbent_potable_water_ml", "potable_water_ml", "incumbent_water_ml"),
    "energy_kwh": ("energy_kwh", "total_energy_kwh", "electricity_kwh", "energy"),
    "ghg_kgco2e": ("ghg_kgco2e", "ghg_kg_co2e", "carbon_kg_co2e", "ghg_caused_kg_co2e", "emissions_kgco2e", "ghg"),
    "cost": ("cost", "total_cost", "cost_usd", "operating_cost", "operational_cost_eur"),
    "unmet_ml": ("unmet_ml", "unmet_water_ml", "unmet_cooling_water_ml", "unmet_demand_ml", "unmet"),
    "sla": ("sla", "sla_reliability", "service_level", "reliability"),
    "coc": ("coc", "CoC", "cycles_of_concentration", "cycles_concentration"),
    "wwtw_inflow_ml": ("wwtw_inflow_ml", "wwtw_inflow", "wwtw_inflow_volume_ml"),
    "wwtw_treated_ml": ("wwtw_treated_ml", "wwtw_treated", "wwtw_treated_volume_ml"),
    "wwtw_peak_utilization": ("wwtw_peak_utilization", "peak_utilization", "wwtw_peak_utilisation"),
}

REQUIRED = (
    "ai_potable_ml", "ai_reclaimed_ml", "source_withdrawal_ml",
    "incumbent_potable_ml", "energy_kwh", "ghg_kgco2e", "cost", "unmet_ml", "sla",
)
OPTIONAL = ("coc", "wwtw_inflow_ml", "wwtw_treated_ml", "wwtw_peak_utilization")
QUALITY_ALIASES: dict[str, tuple[str, ...]] = {
    "tds_mg_l": ("tds_mg_l", "TDS_mg_l", "TDS", "quality_tds_mg_l"),
    "chloride_mg_l": ("chloride_mg_l", "Cl_mg_l", "chloride", "quality_chloride_mg_l"),
    "calcium_mg_l": ("calcium_mg_l", "Ca_mg_l", "calcium", "quality_calcium_mg_l"),
    "magnesium_mg_l": ("magnesium_mg_l", "Mg_mg_l", "magnesium", "quality_magnesium_mg_l"),
    "sulfate_mg_l": ("sulfate_mg_l", "SO4_mg_l", "sulfate", "quality_sulfate_mg_l"),
    "pH": ("pH", "ph", "quality_pH"),
}
BASELINE_ALIASES: dict[str, tuple[str, ...]] = {
    "ai_potable_ml": (
        "b2_ai_potable_ml", "b2_ai_potable_water_ml", "baseline_ai_potable_ml",
        "ai_potable_b2_ml", "B2_ai_potable_ml",
    ),
    "source_withdrawal_ml": (
        "b2_source_withdrawal_ml", "b2_source_withdrawal", "b2_source_ml", "baseline_source_withdrawal_ml",
        "source_withdrawal_b2_ml", "B2_source_withdrawal_ml",
    ),
    "incumbent_potable_ml": (
        "b2_incumbent_potable_ml", "b2_incumbent_potable_water_ml",
        "baseline_incumbent_potable_ml", "incumbent_potable_b2_ml",
    ),
}
BASELINE_REQUIRED = ("ai_potable_ml", "source_withdrawal_ml")
SEED_KEYS = ("seed", "run_seed", "random_seed", "common_seed")
PROVENANCE_KEYS = ("provenance_id", "provenance", "provenance_hash", "run_provenance", "source_provenance")
DATE_KEYS = ("date", "day", "day_id", "timestamp")
DC_KEYS = ("dc_id", "data_center_id", "data_center", "facility_id", "component_id")
SUM_METRICS = {
    "ai_potable_ml", "ai_reclaimed_ml", "source_withdrawal_ml", "incumbent_potable_ml",
    "energy_kwh", "ghg_kgco2e", "cost", "unmet_ml", "wwtw_inflow_ml", "wwtw_treated_ml",
}


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_hash(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _number(value: Any, *, field: str, nonnegative: bool = True) -> float:
    if isinstance(value, bool) or value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"{field} is missing")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} is not numeric") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} is not finite")
    if nonnegative and number < 0:
        raise ValueError(f"{field} must be non-negative")
    return number


def _first(row: Mapping[str, Any], aliases: Iterable[str]) -> tuple[str | None, Any]:
    for name in aliases:
        if name in row and row[name] not in (None, ""):
            return name, row[name]
    return None, None


def _read_rows_from_path(path: Path) -> tuple[list[dict[str, Any]], str]:
    if not path.is_file():
        raise FileNotFoundError(path)
    digest = _sha256(path)
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload if isinstance(payload, list) else payload.get("rows", payload.get("data")) if isinstance(payload, Mapping) else None
        if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
            raise ValueError(f"{path.name} must contain a list of mapping rows")
        return [dict(row) for row in rows], digest
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path.name} has no header")
        return [dict(row) for row in reader], digest


def _table_rows(spec: Any, base: Path) -> tuple[list[dict[str, Any]], str, dict[str, Any]]:
    metadata: dict[str, Any] = {}
    if isinstance(spec, str):
        path = Path(spec)
        path = path if path.is_absolute() else base / path
        rows, digest = _read_rows_from_path(path.resolve())
        metadata["path"] = str(path.resolve())
        return rows, digest, metadata
    if isinstance(spec, list):
        if any(not isinstance(row, Mapping) for row in spec):
            raise ValueError("inline table rows must be mappings")
        rows = [dict(row) for row in spec]
        return rows, _canonical_hash(rows), metadata
    if not isinstance(spec, Mapping):
        raise ValueError("table specification must be a path, rows list, or object")
    for key in ("seed", "run_seed", "random_seed", "provenance_id", "provenance", "source_provenance"):
        if key in spec:
            metadata[key] = spec[key]
    if "rows" in spec or "data" in spec:
        rows = spec.get("rows", spec.get("data"))
        if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
            raise ValueError("inline table rows must be mappings")
        rows = [dict(row) for row in rows]
        metadata["source"] = "inline"
        return rows, _canonical_hash(rows), metadata
    raw_path = spec.get("path", spec.get("file"))
    if raw_path is None:
        raise ValueError("table object requires path or rows")
    path = Path(str(raw_path))
    path = path if path.is_absolute() else base / path
    rows, digest = _read_rows_from_path(path.resolve())
    metadata["path"] = str(path.resolve())
    return rows, digest, metadata


def _manifest_specs(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    specs = payload.get("runs", payload.get("tables", payload.get("states")))
    if not isinstance(specs, Mapping):
        raise ValueError("input manifest requires a runs/tables/states mapping")
    return specs


def _metadata_value(payload: Mapping[str, Any], specs: Mapping[str, Any], key_names: Iterable[str]) -> str:
    for key in key_names:
        value = payload.get(key)
        if value not in (None, "") and not isinstance(value, Mapping):
            return _text(value)
    provenance = payload.get("provenance")
    if isinstance(provenance, Mapping):
        for key in key_names:
            value = provenance.get(key)
            if value not in (None, "") and not isinstance(value, Mapping):
                return _text(value)
        # A compact provenance object commonly uses ``id`` or ``hash``.
        if any(key in PROVENANCE_KEYS for key in key_names):
            for key in ("id", "identifier", "hash", "uri"):
                value = provenance.get(key)
                if value not in (None, "") and not isinstance(value, Mapping):
                    return _text(value)
    values: set[str] = set()
    for spec in specs.values():
        if isinstance(spec, Mapping):
            for key in key_names:
                value = spec.get(key)
                if value not in (None, "") and not isinstance(value, Mapping):
                    values.add(_text(value))
            if any(key in PROVENANCE_KEYS for key in key_names):
                value = spec.get("provenance")
                if isinstance(value, Mapping):
                    for key in ("id", "identifier", "hash", "uri"):
                        nested = value.get(key)
                        if nested not in (None, "") and not isinstance(nested, Mapping):
                            values.add(_text(nested))
    return next(iter(values)) if len(values) == 1 else ""


def _spec_metadata_values(spec: Mapping[str, Any], key_names: Iterable[str]) -> set[str]:
    values: set[str] = set()
    for key in key_names:
        value = spec.get(key)
        if value not in (None, "") and not isinstance(value, Mapping):
            values.add(_text(value))
        if key in PROVENANCE_KEYS and isinstance(value, Mapping):
            for nested_key in ("id", "identifier", "hash", "uri"):
                nested = value.get(nested_key)
                if nested not in (None, "") and not isinstance(nested, Mapping):
                    values.add(_text(nested))
    return values


def _row_metadata(rows: Iterable[Mapping[str, Any]], keys: Iterable[str]) -> set[str]:
    result: set[str] = set()
    for row in rows:
        for key in keys:
            value = row.get(key)
            if value not in (None, ""):
                result.add(_text(value))
    return result


def _date_dc(row: Mapping[str, Any], index: int) -> tuple[str, str]:
    _, date_value = _first(row, DATE_KEYS)
    _, dc_value = _first(row, DC_KEYS)
    if not _text(date_value) or not _text(dc_value):
        raise ValueError(f"row {index}: date and dc_id/data_center_id are required")
    return _text(date_value), _text(dc_value)


def _metric_column(row: Mapping[str, Any], metric: str) -> tuple[str | None, Any]:
    return _first(row, ALIASES[metric])


def _normalise_rows(rows: list[dict[str, Any]], label: str, common_seed: str, common_provenance: str) -> tuple[list[dict[str, Any]], list[str], set[tuple[str, str]]]:
    reasons: list[str] = []
    parsed: list[dict[str, Any]] = []
    keys: set[tuple[str, str]] = set()
    if not rows:
        return [], [f"{label} is empty"], keys
    for index, row in enumerate(rows, start=1):
        try:
            date_value, dc_id = _date_dc(row, index)
            key = (date_value, dc_id)
            if key in keys:
                raise ValueError(f"duplicate date/dc pair {date_value}/{dc_id}")
            values: dict[str, float] = {}
            for metric in REQUIRED:
                _, raw = _metric_column(row, metric)
                values[metric] = _number(raw, field=f"{label} row {index} {metric}", nonnegative=True)
            for metric in OPTIONAL:
                name, raw = _metric_column(row, metric)
                if name is not None:
                    values[metric] = _number(raw, field=f"{label} row {index} {metric}", nonnegative=True)
            quality: dict[str, float] = {}
            for quality_name, aliases in QUALITY_ALIASES.items():
                name, raw = _first(row, aliases)
                if name is not None:
                    quality[quality_name] = _number(raw, field=f"{label} row {index} {quality_name}", nonnegative=(quality_name != "pH"))
            values["water_quality"] = quality
            if values["sla"] > 1.0:
                raise ValueError(f"{label} row {index} sla must be in [0,1]")
            if "coc" in values and values["coc"] < 1.0:
                raise ValueError(f"{label} row {index} coc must be >=1")
            row_seed = _row_metadata([row], SEED_KEYS)
            row_provenance = _row_metadata([row], PROVENANCE_KEYS)
            if row_seed and common_seed and row_seed != {common_seed}:
                raise ValueError("row seed disagrees with common seed")
            if row_provenance and common_provenance and row_provenance != {common_provenance}:
                raise ValueError("row provenance disagrees with common provenance")
            # Preserve B2 values as a separate, optional baseline record.
            baseline: dict[str, float] = {}
            for metric, aliases in BASELINE_ALIASES.items():
                name, raw = _first(row, aliases)
                if name is not None:
                    baseline[metric] = _number(raw, field=f"{label} row {index} {name}", nonnegative=True)
            parsed.append({"date": date_value, "dc_id": dc_id, "values": values, "baseline": baseline})
            keys.add(key)
        except ValueError as exc:
            reasons.append(str(exc))
    return parsed, reasons, keys


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, float | str]:
    result: dict[str, float | str] = {}
    for metric in (*REQUIRED, *OPTIONAL):
        values = [float(row["values"][metric]) for row in rows if metric in row["values"]]
        if not values:
            result[metric] = "NA"
        elif metric in SUM_METRICS:
            result[metric] = sum(values)
        elif metric == "wwtw_peak_utilization":
            result[metric] = max(values)
        else:
            result[metric] = sum(values) / len(values)
    quality: dict[str, float] = {}
    for name in QUALITY_ALIASES:
        values = [float(row["values"]["water_quality"][name]) for row in rows if name in row["values"].get("water_quality", {})]
        if values:
            quality[name] = sum(values) / len(values)
    result["water_quality"] = quality
    return result


def _aggregate_baseline(rows: list[dict[str, Any]]) -> dict[str, float] | None:
    result: dict[str, float] = {}
    for metric in BASELINE_REQUIRED:
        values = [float(row["baseline"][metric]) for row in rows if metric in row["baseline"]]
        if not values:
            return None
        result[metric] = sum(values)
    for metric in BASELINE_ALIASES:
        if metric in result:
            continue
        values = [float(row["baseline"][metric]) for row in rows if metric in row["baseline"]]
        if values:
            result[metric] = sum(values)
    return result


def _subtract(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, float | str]:
    result: dict[str, float | str] = {}
    for metric in (*REQUIRED, *OPTIONAL):
        lhs, rhs = left.get(metric), right.get(metric)
        result[metric] = float(lhs) - float(rhs) if isinstance(lhs, (int, float)) and isinstance(rhs, (int, float)) else "NA"
    left_quality = left.get("water_quality", {})
    right_quality = right.get("water_quality", {})
    if isinstance(left_quality, Mapping) and isinstance(right_quality, Mapping):
        result["water_quality"] = {
            name: float(left_quality[name]) - float(right_quality[name])
            if name in left_quality and name in right_quality else "NA"
            for name in QUALITY_ALIASES
            if name in left_quality or name in right_quality
        }
    else:
        result["water_quality"] = {}
    return result


def _paired_rows(state_rows: Mapping[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Build a key-level paired trace for audit and reproducibility."""
    by_state = {
        state: {(row["date"], row["dc_id"]): row["values"] for row in rows}
        for state, rows in state_rows.items()
    }
    keys = sorted(set.intersection(*(set(values) for values in by_state.values()))) if by_state else set()
    result: list[dict[str, Any]] = []
    for date_value, dc_id in keys:
        values = {state: by_state[state][(date_value, dc_id)] for state in STATES}
        result.append({
            "date": date_value,
            "dc_id": dc_id,
            "states": values,
            "Delta_Q": {
                "Ls": _subtract(values["Q1/Ls"], values["Q0/Ls"]),
                "Ld": _subtract(values["Q1/Ld"], values["Q0/Ld"]),
            },
            "Delta_L": {
                "Q0": _subtract(values["Q0/Ld"], values["Q0/Ls"]),
                "Q1": _subtract(values["Q1/Ld"], values["Q1/Ls"]),
            },
        })
        result[-1]["Delta_QL"] = _subtract(result[-1]["Delta_Q"]["Ld"], result[-1]["Delta_Q"]["Ls"])
    return result


def _review_ok(path: Path | None, *, kind: str) -> tuple[bool, str]:
    if path is None:
        return False, f"formal E3 requires explicit {kind} approval"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return False, f"{kind} approval could not be read: {exc}"
    if not isinstance(payload, Mapping):
        return False, f"{kind} approval must be a JSON object"
    status = _text(payload.get("status", payload.get("decision", ""))).upper()
    reviewer = _text(payload.get("reviewer", payload.get("reviewer_id", payload.get("approved_by", ""))))
    scope = _text(payload.get("scope_status", payload.get("scope", ""))).upper()
    if status not in {"APPROVED", "PASS", "COMPLETE"} or not reviewer:
        return False, f"{kind} approval lacks approved status/reviewer"
    if scope and scope not in {"APPROVED", "IN_SCOPE", "IN-SCOPE", "PASS", "COMPLETE"}:
        return False, f"{kind} approval scope is not approved"
    return True, f"{kind} approval recorded"


def _gate_snapshot(repo_root: Path, experiment_root: Path | None) -> dict[str, Any]:
    try:
        audited = audit(repo_root, experiment_root)
    except Exception as exc:  # formal mode must fail closed if audit is unavailable
        return {"g2": {"status": "NOT_READY", "reason": f"audit unavailable: {exc}"}, "g3": {"status": "NOT_READY", "reason": f"audit unavailable: {exc}"}}
    return {
        name: {"status": audited.get(name, {}).get("status", "NOT_READY"), "reason": audited.get(name, {}).get("reason", "audit result missing")}
        for name in ("g2", "g3")
    }


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(
    input_manifest: Path,
    output: Path,
    *,
    formal: bool = False,
    repo_root: Path | None = None,
    experiment_root: Path | None = None,
    independent_review: Path | None = None,
    coupled_run_approval: Path | None = None,
    formal_review: Path | None = None,
) -> dict[str, Any]:
    """Run the E3 paired diagnostic and write an auditable manifest."""
    input_manifest = Path(input_manifest).resolve()
    output_arg = Path(output).resolve()
    output_dir = output_arg.parent if output_arg.suffix.lower() == ".json" else output_arg
    manifest_path = output_arg if output_arg.suffix.lower() == ".json" else output_dir / "manifest.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "kind": "R10_E3_MECHANISM_PILOT",
        "runner_version": "R10-E3-1.0",
        "status": "NOT_READY",
        "diagnostic_status": "NOT_RUN",
        "mode": "READ_ONLY",
        "pilot_only": not formal,
        "formal_requested": formal,
        "formal_run_performed": False,
        "execution_performed": False,
        "input_manifest": {"path": str(input_manifest), "sha256": _sha256(input_manifest) if input_manifest.is_file() else None},
        "tables": {},
        "baseline_inputs": {},
        "state_metrics": {},
        "deltas": {},
        "estimands": {},
        "paired_row_count": 0,
        "output_hashes": {},
        "reasons": [],
        "gate_statuses": {},
        "provenance": {"generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"), "main_model_integration": "READ_ONLY_BOUNDARY"},
        "gate_effect": "E3 remains a read-only pilot; no formal claim is made.",
    }
    # Perform the formal preflight before any table aggregation.  A formal
    # request with a missing gate/review must not calculate a diagnostic and
    # then merely discard it afterwards.
    formal_preflight_blocked = False
    formal_gate_snapshot: dict[str, Any] = {}
    if formal:
        repo = Path(repo_root or ROOT).resolve()
        experiment = Path(experiment_root).resolve() if experiment_root else None
        formal_gate_snapshot = _gate_snapshot(repo, experiment)
        payload["gate_statuses"] = {name: value["status"] for name, value in formal_gate_snapshot.items()}
        payload["gate_reasons"] = {name: value["reason"] for name, value in formal_gate_snapshot.items()}
        for name, value in formal_gate_snapshot.items():
            if value["status"] != "READY":
                payload["reasons"].append(f"{name.upper()} is {value['status']}")
        # A single review document is accepted as a compatibility shorthand
        # only when it carries the same approved scope for both decisions.
        independent_review = independent_review or formal_review
        coupled_run_approval = coupled_run_approval or formal_review
        review_ok, review_reason = _review_ok(Path(independent_review).resolve() if independent_review else None, kind="independent review")
        approval_ok, approval_reason = _review_ok(Path(coupled_run_approval).resolve() if coupled_run_approval else None, kind="coupled-run approval")
        if not review_ok:
            payload["reasons"].append(review_reason)
        if not approval_ok:
            payload["reasons"].append(approval_reason)
        for kind, path in (("independent_review", independent_review), ("coupled_run_approval", coupled_run_approval)):
            payload.setdefault("formal_evidence", {})[kind] = {
                "path": str(Path(path).resolve()) if path else None,
                "sha256": _sha256(Path(path).resolve()) if path and Path(path).is_file() else None,
            }
        formal_preflight_blocked = bool(payload["reasons"])
    state_rows: dict[str, list[dict[str, Any]]] = {}
    try:
        raw_manifest = json.loads(input_manifest.read_text(encoding="utf-8"))
        if not isinstance(raw_manifest, Mapping):
            raise ValueError("input manifest must be a JSON object")
        specs = _manifest_specs(raw_manifest)
        if set(specs) != set(STATES):
            missing = sorted(set(STATES) - set(specs))
            extra = sorted(set(specs) - set(STATES))
            raise ValueError(f"manifest must contain exactly four states; missing={missing}, extra={extra}")
        # Load all tables once before validation so a common seed/provenance
        # may be supplied in row columns as well as manifest metadata.
        raw_tables: dict[str, tuple[list[dict[str, Any]], str, dict[str, Any]]] = {}
        for state in STATES:
            raw_tables[state] = _table_rows(specs[state], input_manifest.parent)
        common_seed = _metadata_value(raw_manifest, specs, SEED_KEYS)
        common_provenance = _metadata_value(raw_manifest, specs, PROVENANCE_KEYS)
        row_seeds = {_text(value) for rows, _, _ in raw_tables.values() for value in _row_metadata(rows, SEED_KEYS)}
        row_provenance = {_text(value) for rows, _, _ in raw_tables.values() for value in _row_metadata(rows, PROVENANCE_KEYS)}
        if not common_seed and len(row_seeds) == 1:
            common_seed = next(iter(row_seeds))
        if not common_provenance and len(row_provenance) == 1:
            common_provenance = next(iter(row_provenance))
        if not common_seed:
            payload["reasons"].append("common seed is missing or inconsistent across manifest/table metadata and rows")
        if not common_provenance:
            payload["reasons"].append("common provenance is missing or inconsistent across manifest/table metadata and rows")
        if len(row_seeds) > 1:
            payload["reasons"].append("row seed is not common across the four states")
        if len(row_provenance) > 1:
            payload["reasons"].append("row provenance is not common across the four states")
        payload["provenance"].update({"common_seed": common_seed or None, "common_provenance": common_provenance or None})
        key_sets: dict[str, set[tuple[str, str]]] = {}
        for state in STATES:
            rows, digest, metadata = raw_tables[state]
            parsed, reasons, keys = _normalise_rows(rows, state, common_seed, common_provenance)
            if reasons:
                payload["reasons"].extend(reasons[:20])
                if len(reasons) > 20:
                    payload["reasons"].append(f"{state}: {len(reasons) - 20} additional row errors")
            state_rows[state] = parsed
            key_sets[state] = keys
            payload["tables"][state] = {"sha256": digest, "row_count": len(rows), **metadata}
        if key_sets and any(keys != key_sets[STATES[0]] for keys in key_sets.values()):
            payload["reasons"].append("paired date/dc keys are not identical across all four states")
        # A row-level metadata set must contain one common value whenever rows
        # provide it; this catches mixed seeds/provenance hidden by a manifest.
        for state, rows in state_rows.items():
            raw_spec = specs[state]
            source_rows = raw_tables[state][0]
            table_seed = _row_metadata(source_rows, SEED_KEYS)
            table_provenance = _row_metadata(source_rows, PROVENANCE_KEYS)
            if table_seed and common_seed and table_seed != {common_seed}:
                payload["reasons"].append(f"{state}: row seed disagrees with common seed")
            if table_provenance and common_provenance and table_provenance != {common_provenance}:
                payload["reasons"].append(f"{state}: row provenance disagrees with common provenance")
            if isinstance(raw_spec, Mapping) and any(value != common_seed for value in _spec_metadata_values(raw_spec, SEED_KEYS)):
                payload["reasons"].append(f"{state}: table seed disagrees with common seed")
            if isinstance(raw_spec, Mapping) and any(value != common_provenance for value in _spec_metadata_values(raw_spec, PROVENANCE_KEYS)):
                payload["reasons"].append(f"{state}: table provenance disagrees with common provenance")
        if not payload["reasons"] and not formal_preflight_blocked:
            payload["state_metrics"] = {state: _aggregate(state_rows[state]) for state in STATES}
            # Primary deltas, all defined on the same date/DC key set.
            payload["deltas"] = {
                "Delta_Q": {
                    "Ls": _subtract(payload["state_metrics"]["Q1/Ls"], payload["state_metrics"]["Q0/Ls"]),
                    "Ld": _subtract(payload["state_metrics"]["Q1/Ld"], payload["state_metrics"]["Q0/Ld"]),
                },
                "Delta_L": {
                    "Q0": _subtract(payload["state_metrics"]["Q0/Ld"], payload["state_metrics"]["Q0/Ls"]),
                    "Q1": _subtract(payload["state_metrics"]["Q1/Ld"], payload["state_metrics"]["Q1/Ls"]),
                },
            }
            payload["deltas"]["Delta_QL"] = _subtract(payload["deltas"]["Delta_Q"]["Ld"], payload["deltas"]["Delta_Q"]["Ls"])
            # Inline B2 fields are the preferred source.  If absent, accept a
            # separate b2 mapping in the manifest and aggregate the referenced
            # tables with the same two baseline metrics.
            b2 = raw_manifest.get("b2", raw_manifest.get("baselines", {}))
            b2_specs = b2 if isinstance(b2, Mapping) else {}
            for state in STATES:
                baseline = _aggregate_baseline(state_rows[state])
                if baseline is None and b2_specs:
                    candidate = b2_specs.get(state, b2_specs.get(state.split("/")[0]))
                    if candidate is not None:
                        b2_rows, b2_digest, b2_metadata = _table_rows(candidate, input_manifest.parent)
                        payload["baseline_inputs"][state] = {
                            "sha256": b2_digest,
                            "row_count": len(b2_rows),
                            **b2_metadata,
                        }
                        baseline_parsed: list[dict[str, Any]] = []
                        for row in b2_rows:
                            item: dict[str, Any] = {"baseline": {}}
                            for metric, aliases in BASELINE_ALIASES.items():
                                _, raw = _first(row, aliases)
                                if raw is not None:
                                    item["baseline"][metric] = _number(raw, field=f"B2 {state} {metric}")
                            baseline_parsed.append(item)
                        baseline = _aggregate_baseline(baseline_parsed)
                if baseline is None:
                    payload["estimands"][state] = {"S_AI": "NA", "S_city": "NA", "eta_transfer": "NA", "incumbent_potable_delta": "NA", "status": "NA_B2"}
                else:
                    current = payload["state_metrics"][state]
                    s_ai = baseline["ai_potable_ml"] - float(current["ai_potable_ml"])
                    s_city = baseline["source_withdrawal_ml"] - float(current["source_withdrawal_ml"])
                    eta: float | str = s_city / s_ai if s_ai > 0 else "NA"
                    incumbent_delta = (
                        baseline["incumbent_potable_ml"] - float(current["incumbent_potable_ml"])
                        if "incumbent_potable_ml" in baseline else "NA"
                    )
                    payload["estimands"][state] = {"S_AI": s_ai, "S_city": s_city, "eta_transfer": eta, "incumbent_potable_delta": incumbent_delta, "status": "DIAGNOSTIC"}
            payload["execution_performed"] = True
            paired_rows = _paired_rows(state_rows)
            payload["paired_row_count"] = len(paired_rows)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        payload["reasons"].append(f"input/validation error: {exc}")

    if formal:
        if formal_preflight_blocked or payload["reasons"]:
            payload["execution_performed"] = False
            payload["formal_run_performed"] = False
            payload["status"] = "NOT_READY"
            payload["diagnostic_status"] = "BLOCKED"
            payload["state_metrics"] = {}
            payload["deltas"] = {}
            payload["estimands"] = {}
            payload["reasons"].append("formal E3 run refused before paired mechanism calculation")
        else:
            # This utility remains a diagnostic even when a formal request is
            # admitted.  Formal publication claims belong to the reviewed
            # coupled run, not to this read-only table comparator.
            payload["status"] = "PILOT_ONLY"
            payload["diagnostic_status"] = "FORMAL_INPUT_ACCEPTED"
            payload["formal_run_performed"] = True
            payload["pilot_only"] = False
    elif payload["execution_performed"] and not payload["reasons"]:
        payload["status"] = "PILOT_ONLY"
        payload["diagnostic_status"] = "COMPLETED"
    elif payload["reasons"]:
        payload["status"] = "NOT_READY"
        payload["diagnostic_status"] = "BLOCKED"

    # Always emit deterministic output artifacts, including on validation
    # failure, so a reviewer can inspect and hash an unsuccessful attempt.
    state_path = output_dir / "state_metrics.json"
    delta_path = output_dir / "paired_deltas.json"
    paired_path = output_dir / "paired_rows.json"
    _write_json(state_path, {"state_metrics": payload["state_metrics"], "estimands": payload["estimands"]})
    _write_json(delta_path, payload["deltas"])
    _write_json(paired_path, paired_rows if payload.get("execution_performed") else [])
    payload["outputs"] = {"state_metrics": str(state_path.name), "paired_deltas": str(delta_path.name), "paired_rows": str(paired_path.name)}
    payload["output_hashes"] = {"state_metrics": _sha256(state_path), "paired_deltas": _sha256(delta_path), "paired_rows": _sha256(paired_path)}
    _write_json(manifest_path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", dest="input_manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--experiment-root", type=Path)
    parser.add_argument("--independent-review", type=Path)
    parser.add_argument("--coupled-run-approval", type=Path)
    parser.add_argument("--formal-review", type=Path, help="compatibility shorthand supplying both formal approvals")
    args = parser.parse_args()
    payload = run(args.input_manifest, args.output, formal=args.formal, repo_root=args.repo_root, experiment_root=args.experiment_root, independent_review=args.independent_review, coupled_run_approval=args.coupled_run_approval, formal_review=args.formal_review)
    print(json.dumps({"output": str(args.output.resolve()), "status": payload["status"], "reasons": payload["reasons"]}, ensure_ascii=False))
    return 0 if payload["status"] in {"PILOT_ONLY", "NOT_READY"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
