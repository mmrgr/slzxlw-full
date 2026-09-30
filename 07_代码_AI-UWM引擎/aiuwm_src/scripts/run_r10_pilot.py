"""Gate-safe R10 pilot preflight. This script never runs E3/E4 simulations."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from audit_g2_g3_evidence import audit
except ModuleNotFoundError:  # import when loaded as ``scripts.run_r10_pilot``
    from scripts.audit_g2_g3_evidence import audit


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_FIELDS = (
    "scenario_id", "counterfactual_group", "chemistry_state", "allocation_state",
    "adaptation_state", "weather_seed", "hydrology_seed", "workload_seed",
    "code_commit", "parameter_registry_version", "estimand", "status",
)
PARAMETER_FIELDS = (
    "parameter_id", "unit", "distribution", "lower", "upper",
    "correlation_group", "evidence_class", "source", "observation_population",
    "calibration_flag", "validation_flag", "version",
)


def _read_registry(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not set(required).issubset(reader.fieldnames):
            raise ValueError(f"{path.name}: missing required columns")
        rows = list(reader)
    if not rows or any(
        None in row or any(row.get(field) is None or not str(row[field]).strip() for field in required)
        for row in rows
    ):
        raise ValueError(f"{path.name}: empty or malformed required fields")
    return rows


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def preflight(
    repo_root: Path,
    scenario_id: str | None,
    mode: str | None,
    dry_run: bool,
    experiment_root: Path | None = None,
) -> dict[str, Any]:
    """Return a JSON-serializable decision without executing a model or estimand."""
    repo_root = repo_root.resolve()
    gate_audit = audit(repo_root, experiment_root.resolve() if experiment_root else None)
    gate_statuses = {gate: gate_audit[gate]["status"] for gate in ("g2", "g3")}
    result: dict[str, Any] = {
        "kind": "R10_DIAGNOSTIC_PREFLIGHT",
        "scenario_id": scenario_id,
        "mode": mode,
        "dry_run": dry_run,
        "execution_performed": False,
        "formal_e3_e4_eligible": False,
        "status": "REJECTED",
        "gate_statuses": gate_statuses,
        "gate_reasons": {gate: gate_audit[gate]["reason"] for gate in ("g2", "g3")},
        "provenance": {
            "repo_root": str(repo_root),
            "experiment_root": str(experiment_root.resolve()) if experiment_root else None,
            "parameter_registry": str(repo_root / "data" / "parameter_registry.csv"),
            "scenario_registry": str(repo_root / "data" / "scenario_registry.csv"),
            "registry_sha256": {},
            "scenario": None,
            "parameter_count": 0,
        },
        "formal_blockers": [],
        "rejection_reasons": [],
    }
    try:
        scenario_path = repo_root / "data" / "scenario_registry.csv"
        parameter_path = repo_root / "data" / "parameter_registry.csv"
        scenarios = _read_registry(scenario_path, SCENARIO_FIELDS)
        parameters = _read_registry(parameter_path, PARAMETER_FIELDS)
        result["provenance"]["registry_sha256"] = {
            "scenario_registry": _sha256(scenario_path),
            "parameter_registry": _sha256(parameter_path),
        }
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        result["rejection_reasons"].append(f"Registry invalid: {exc}")
        return result

    result["provenance"]["parameter_count"] = len(parameters)
    matches = [row for row in scenarios if row["scenario_id"] == scenario_id]
    if len(matches) != 1:
        result["rejection_reasons"].append(
            "Exactly one scenario_registry row must match --scenario-id."
        )
        return result
    scenario = matches[0]
    result["provenance"]["scenario"] = scenario
    if scenario["status"] not in {"not_ready", "diagnostic", "gate_pass", "gate_fail"}:
        result["rejection_reasons"].append("Unrecognized scenario status.")
    if scenario["chemistry_state"] not in {"Q0", "Q1"} or scenario["allocation_state"] not in {"Ls", "Ld", "legacy"} or scenario["adaptation_state"] not in {"A0", "A1", "A2", "A3"}:
        result["rejection_reasons"].append("Unrecognized scenario state.")
    version = scenario["parameter_registry_version"]
    if any(row["version"] != version for row in parameters):
        result["rejection_reasons"].append("Parameter registry version does not match scenario.")

    if scenario["status"] != "gate_pass":
        result["formal_blockers"].append(f"scenario status is {scenario['status']}")
    for gate, status in gate_statuses.items():
        if status != "READY":
            result["formal_blockers"].append(f"{gate.upper()} is {status}")
    # This script is a preflight only; formal approval remains outside its scope.
    result["formal_blockers"].append("G2/G3 independent evidence review and formal run approval are outside this preflight")
    if mode not in {"diagnostic", "daily-slice"}:
        result["rejection_reasons"].append("Explicit --mode diagnostic or --mode daily-slice is required.")
    if not dry_run:
        result["rejection_reasons"].append("Explicit --dry-run is required; this runner never executes E3/E4.")
    invocation_rejected = bool(result["rejection_reasons"])
    result["rejection_reasons"].extend(
        f"Formal run rejected: {blocker}" for blocker in result["formal_blockers"]
    )
    if not invocation_rejected:
        result["status"] = "DIAGNOSTIC_PREFLIGHT_ONLY"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--experiment-root", type=Path)
    parser.add_argument("--scenario-id")
    parser.add_argument("--mode", choices=("diagnostic", "daily-slice"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", help="accepted for CLI symmetry; output is always JSON")
    args = parser.parse_args()
    result = preflight(args.repo_root, args.scenario_id, args.mode, args.dry_run, args.experiment_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "DIAGNOSTIC_PREFLIGHT_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
