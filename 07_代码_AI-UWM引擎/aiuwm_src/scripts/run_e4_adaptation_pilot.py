"""Run the read-only R10 E4 A0--A3 adaptation diagnostic.

The input is an exported ``data_center_daily`` table from the main model.  A
paired freshwater-only table can be supplied to make the reference explicit.
The adapter evaluates the four standalone adaptation policies, writes a
machine-readable summary and preserves the main-model boundary as
``status=NOT_READY`` and ``main_model_integration=READ_ONLY_BOUNDARY``.

This utility has two deliberately separate modes.  The default diagnostic
mode is useful for checking accounting and produces an auditable pilot even
when external gates are unavailable.  ``--formal`` requests a formal run and
is rejected before evaluation unless the G2 and G3 evidence audit both return
``READY`` and a reviewed coupled main-model implementation exists.  This
read-only runner currently has no such implementation and cannot promote
itself to a gate PASS.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from audit_g2_g3_evidence import audit
except ModuleNotFoundError:  # import as ``scripts.run_e4_adaptation_pilot``
    from scripts.audit_g2_g3_evidence import audit

from aiuwm.adaptation import (
    AdaptationConfig,
    AdaptationSetResult,
    AdaptationResult,
    cooling_ledger_from_data_center_daily,
    evaluate_adaptation_set,
)


POLICIES = ("A0", "A1", "A2", "A3")

# Policy-only defaults are intentionally neutral.  Treatment, recovery,
# energy, cost, SLA and saving assumptions belong in a versioned caller config
# rather than being silently invented by this runner.
DEFAULT_CONFIGS: tuple[dict[str, Any], ...] = tuple({"policy": policy} for policy in POLICIES)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _read_rows(path: Path) -> list[dict[str, Any]]:
    """Load CSV or JSON rows without applying model transformations."""

    if not path.is_file():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict):
            rows = payload.get("rows", payload.get("data_center_daily"))
        else:
            rows = None
        if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
            raise ValueError(f"{path.name} must contain a list of mapping rows")
        return [dict(row) for row in rows]
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path.name} has no header")
        return [dict(row) for row in reader]


def _decode_mapping_fields(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Decode JSON mappings embedded in CSV cells for the adapter boundary."""

    decoded: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        for name in ("quality_reclaimed_source_mg_l", "solute_load_kg"):
            value = item.get(name)
            if isinstance(value, str) and value.strip():
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError as exc:
                    # pandas' CSV export uses Python's single-quoted repr for
                    # object-valued cells.  literal_eval accepts that stable
                    # representation without executing arbitrary code.
                    try:
                        parsed = ast.literal_eval(value)
                    except (ValueError, SyntaxError) as fallback_exc:
                        raise ValueError(f"{name} must be a JSON object when supplied as text") from fallback_exc
                if not isinstance(parsed, Mapping):
                    raise ValueError(f"{name} must decode to a JSON object")
                item[name] = dict(parsed)
        decoded.append(item)
    return decoded


def _validate_rows(
    rows: list[Mapping[str, Any]], *, label: str, baseline: bool = False
) -> list[str]:
    reasons: list[str] = []
    if not rows:
        return [f"{label} is empty"]
    for index, row in enumerate(rows):
        if not any(name in row for name in ("date", "day")):
            reasons.append(f"{label} row {index} lacks date/day")
        if not any(name in row for name in ("data_center_id", "component_id")):
            reasons.append(f"{label} row {index} lacks data_center_id/component_id")
        required_water = (
            ("potable_water_ml", "external_withdrawal_ml")
            if baseline
            else ("external_makeup_ml", "gross_makeup_ml", "water_demand_ml")
        )
        if not any(name in row for name in required_water):
            reasons.append(
                f"{label} row {index} lacks "
                + ("potable/external withdrawal" if baseline else "external/gross/water demand")
            )
        if len(reasons) >= 10:
            reasons.append("additional input errors omitted")
            break
    return reasons


def _load_configs(path: Path | None) -> tuple[dict[str, Any], ...]:
    if path is None:
        return DEFAULT_CONFIGS
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("configs", payload.get("policies"))
    if not isinstance(payload, list) or any(not isinstance(item, Mapping) for item in payload):
        raise ValueError("config JSON must be a list of policy objects or {configs: [...]}")
    configs = tuple(dict(item) for item in payload)
    policies = tuple(str(config.get("policy", "")) for config in configs)
    if set(policies) != set(POLICIES) or len(configs) != len(POLICIES):
        raise ValueError("config JSON must contain exactly one config for each of A0, A1, A2 and A3")
    return configs


def _number_or_na(value: Any) -> float | str:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
        return float(value)
    return "NA"


def _result_row(result: AdaptationResult) -> dict[str, Any]:
    return {
        "policy": result.policy,
        "status": result.status,
        "E_adapt": _number_or_na(result.E_adapt),
        "C_adapt": _number_or_na(result.C_adapt),
        "freshwater_use_ml": result.freshwater_use_ml,
        "freshwater_baseline_ml": result.freshwater_baseline_ml,
        "freshwater_saving_ml": result.freshwater_saving_ml,
        "unmet_water_ml": result.unmet_water_ml,
        "sla_reliability": result.sla_reliability,
        "energy_kwh": result.energy_kwh,
        "carbon_kg_co2e": result.carbon_kg_co2e,
        "cost": result.cost,
        "reject_ml": result.reject_ml,
        "unreturned_ml": result.unreturned_ml,
        "infeasible_reasons": ";".join(result.infeasible_reasons),
    }


def _daily_rows(result: AdaptationResult) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for day in result.days:
        rows.append({
            "policy": result.policy,
            "day_id": day.day_id,
            "demand_ml": day.demand_ml,
            "feed_ml": day.feed_ml,
            "permeate_ml": day.permeate_ml,
            "reject_ml": day.reject_ml,
            "unreturned_ml": day.unreturned_ml,
            "freshwater_use_ml": day.freshwater_use_ml,
            "freshwater_baseline_ml": day.freshwater_baseline_ml,
            "freshwater_saving_ml": day.freshwater_saving_ml,
            "unmet_water_ml": day.unmet_water_ml,
            "service_ok": day.service_ok,
            "energy_kwh": day.energy_kwh,
            "carbon_kg_co2e": day.carbon_kg_co2e,
            "cost": day.cost,
            "solute_closure_residual_kg": json.dumps(dict(day.solute_closure_residual_kg), ensure_ascii=False, sort_keys=True),
        })
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _gate_snapshot(repo_root: Path, experiment_root: Path | None) -> dict[str, Any]:
    audited = audit(repo_root, experiment_root)
    return {
        "g2": {
            "status": audited.get("g2", {}).get("status", "NOT_READY"),
            "reason": audited.get("g2", {}).get("reason", "audit result missing"),
        },
        "g3": {
            "status": audited.get("g3", {}).get("status", "NOT_READY"),
            "reason": audited.get("g3", {}).get("reason", "audit result missing"),
        },
    }


def _formal_review_ok(path: Path | None) -> tuple[bool, str]:
    """Validate the separate coupling approval required by a formal run."""

    if path is None:
        return False, "formal E4 requires an explicit reviewed coupling approval"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return False, f"formal coupling approval could not be read: {exc}"
    if not isinstance(payload, Mapping):
        return False, "formal coupling approval must be a JSON object"
    status = str(payload.get("status", payload.get("decision", ""))).strip().upper()
    reviewer = str(payload.get("reviewer", payload.get("reviewer_id", ""))).strip()
    scope = str(payload.get("scope_status", payload.get("scope", ""))).strip().upper()
    integration = str(payload.get("main_model_integration", "")).strip().upper()
    if status not in {"APPROVED", "PASS", "COMPLETE"} or not reviewer:
        return False, "formal coupling approval lacks approved status/reviewer"
    if scope not in {"APPROVED", "IN_SCOPE", "IN-SCOPE", "PASS", "COMPLETE"}:
        return False, "formal coupling approval scope is not approved"
    if integration not in {"COUPLED_FEEDBACK", "FORMAL_COUPLED"}:
        return False, "formal coupling approval does not approve coupled feedback integration"
    return True, "formal coupling approval recorded"


def _base_manifest(
    input_path: Path,
    output: Path,
    *,
    baseline_path: Path | None,
    config_path: Path | None,
    formal_requested: bool,
    gates: dict[str, Any],
) -> dict[str, Any]:
    return {
        "kind": "R10_E4_ADAPTATION_PILOT",
        "runner_version": "R10-E4-1.0",
        "status": "NOT_READY",
        "diagnostic_status": "READ_ONLY",
        "main_model_integration": "READ_ONLY_BOUNDARY",
        "gate": "E4",
        "formal_requested": formal_requested,
        "formal_run_performed": False,
        "execution_performed": False,
        "execution_mode": "READ_ONLY_DIAGNOSTIC",
        "gate_statuses": {name: value["status"] for name, value in gates.items()},
        "gate_reasons": {name: value["reason"] for name, value in gates.items()},
        "input": {"path": str(input_path.resolve()), "sha256": None, "row_count": 0, "kind": "main_model_data_center_daily"},
        "paired_freshwater_baseline": None if baseline_path is None else {"path": str(baseline_path.resolve()), "sha256": None, "row_count": 0},
        "config": {"path": None if config_path is None else str(config_path.resolve()), "sha256": None, "source": "policy_only_defaults" if config_path is None else "caller_supplied"},
        "formal_review": None,
        "policies": list(POLICIES),
        "results": [],
        "selection": None,
        "outputs": {"summary": "adaptation_summary.csv", "daily": "adaptation_daily.csv"},
        "output_hashes": {},
        "reasons": [],
        "provenance": {
            "adapter": "aiuwm.adaptation.cooling_ledger_from_data_center_daily",
            "evaluation": "aiuwm.adaptation.evaluate_adaptation_set",
            "contract": "R10-E4-A0-A3",
            "units": {"volume": "ML", "energy": "kWh", "carbon": "kgCO2e", "cost": "caller-defined"},
            "comparison_scope": "within-run or paired freshwater baseline; no city-scale claim",
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        },
        "gate_effect": "E4 remains NOT_READY until G2/G3 evidence audit is READY and the main-model boundary is formally reviewed.",
    }


def run(
    data_center_daily: Path,
    output: Path,
    *,
    freshwater_baseline: Path | None = None,
    config: Path | None = None,
    formal_review: Path | None = None,
    repo_root: Path | None = None,
    experiment_root: Path | None = None,
    formal: bool = False,
) -> dict[str, Any]:
    """Evaluate an E4 pilot and write an auditable manifest.

    ``formal=True`` is a hard gate: no adaptation calculation occurs unless
    both independent evidence audits are READY.  Ordinary diagnostic mode
    remains read-only and is intentionally labelled NOT_READY.
    """

    input_path = Path(data_center_daily).resolve()
    output = Path(output).resolve()
    baseline_path = Path(freshwater_baseline).resolve() if freshwater_baseline else None
    config_path = Path(config).resolve() if config else None
    formal_review_path = Path(formal_review).resolve() if formal_review else None
    repo = Path(repo_root or ROOT).resolve()
    experiment = Path(experiment_root).resolve() if experiment_root else None
    gates = _gate_snapshot(repo, experiment)
    payload = _base_manifest(input_path, output, baseline_path=baseline_path, config_path=config_path, formal_requested=formal, gates=gates)
    payload["provenance"]["baseline_mode"] = (
        "paired_freshwater_counterfactual" if baseline_path is not None else "within_run_potable_use"
    )
    if formal_review_path is not None:
        payload["formal_review"] = {
            "path": str(formal_review_path),
            "sha256": _sha256(formal_review_path) if formal_review_path.is_file() else None,
        }
    output.mkdir(parents=True, exist_ok=True)

    try:
        payload["input"]["sha256"] = _sha256(input_path)
        source_rows = _decode_mapping_fields(_read_rows(input_path))
        payload["input"]["row_count"] = len(source_rows)
        if baseline_path is not None:
            payload["paired_freshwater_baseline"]["sha256"] = _sha256(baseline_path)
            baseline_rows = _decode_mapping_fields(_read_rows(baseline_path))
            payload["paired_freshwater_baseline"]["row_count"] = len(baseline_rows)
        else:
            baseline_rows = None
        input_reasons = _validate_rows(source_rows, label="data_center_daily")
        if baseline_rows is not None:
            input_reasons.extend(_validate_rows(baseline_rows, label="freshwater_baseline", baseline=True))
        configs = _load_configs(config_path)
        if config_path is not None:
            payload["config"]["sha256"] = _sha256(config_path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        input_reasons = [f"input/configuration error: {exc}"]
        configs = ()
        baseline_rows = None

    payload["reasons"].extend(input_reasons)
    gate_blockers = [f"{name.upper()} is {value['status']}" for name, value in gates.items() if value["status"] != "READY"]
    if formal:
        if baseline_path is None:
            gate_blockers.append("formal E4 requires a paired freshwater baseline")
        review_ok, review_reason = _formal_review_ok(formal_review_path)
        if not review_ok:
            gate_blockers.append(review_reason)
        # This runner is intentionally a read-only adapter.  Even a future
        # G2/G3 PASS cannot turn it into a coupled feedback solver by itself.
        # A reviewed main-model integration must replace this blocker before
        # any formal E4 execution is enabled.
        gate_blockers.append(
            "main-model E4 feedback coupling is NOT_READY; this runner only executes a read-only diagnostic"
        )
    if formal and gate_blockers:
        payload["reasons"].extend(gate_blockers)
        payload["reasons"].append("formal E4 run refused before adaptation evaluation")
    elif not payload["reasons"]:
        try:
            ledger = cooling_ledger_from_data_center_daily(source_rows, freshwater_baseline_rows=baseline_rows)
            evaluated: AdaptationSetResult = evaluate_adaptation_set(
                ledger,
                [AdaptationConfig.from_mapping(item) for item in configs],
                provenance={
                    "main_model_integration": "READ_ONLY_BOUNDARY",
                    "runner": "run_e4_adaptation_pilot",
                    "formal_requested": formal,
                },
            )
            summary_rows = [_result_row(result) for result in evaluated.results]
            daily_rows = [row for result in evaluated.results for row in _daily_rows(result)]
            _write_csv(output / "adaptation_summary.csv", summary_rows)
            _write_csv(output / "adaptation_daily.csv", daily_rows)
            payload["results"] = summary_rows
            payload["selection"] = {
                "status": evaluated.status,
                "E_adapt": _number_or_na(evaluated.E_adapt),
                "C_adapt": _number_or_na(evaluated.C_adapt),
                "minimum_energy_policy": evaluated.minimum_energy_policy,
                "minimum_cost_policy": evaluated.minimum_cost_policy,
                "feasible_policies": [result.policy for result in evaluated.feasible_results],
                "summary_rows": len(summary_rows),
                "daily_rows": len(daily_rows),
            }
            payload["execution_performed"] = True
            payload["formal_run_performed"] = bool(formal)
            # The standalone adapter is never a formal E4 result.  Keep the
            # gate-facing status NOT_READY while exposing that accounting was
            # executed in the read-only diagnostic boundary.
            payload["status"] = "NOT_READY"
            payload["output_hashes"] = {
                "summary": _sha256(output / "adaptation_summary.csv"),
                "daily": _sha256(output / "adaptation_daily.csv"),
            }
        except (TypeError, ValueError, KeyError) as exc:
            payload["reasons"].append(f"adaptation evaluation failed: {exc}")
    if not payload["execution_performed"]:
        _write_csv(output / "adaptation_summary.csv", [])
        _write_csv(output / "adaptation_daily.csv", [])
        payload["output_hashes"] = {
            "summary": _sha256(output / "adaptation_summary.csv"),
            "daily": _sha256(output / "adaptation_daily.csv"),
        }
    (output / "manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-center-daily", type=Path, required=True)
    parser.add_argument("--freshwater-baseline", type=Path)
    parser.add_argument("--config", type=Path, help="JSON list with one policy config for each A0--A3")
    parser.add_argument("--formal-review", type=Path, help="reviewed coupled-feedback approval JSON required by --formal")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--experiment-root", type=Path)
    parser.add_argument("--formal", action="store_true", help="request formal E4; hard-blocked unless G2/G3 are READY")
    args = parser.parse_args()
    payload = run(
        args.data_center_daily,
        args.output,
        freshwater_baseline=args.freshwater_baseline,
        config=args.config,
        formal_review=args.formal_review,
        repo_root=args.repo_root,
        experiment_root=args.experiment_root,
        formal=args.formal,
    )
    print(json.dumps({
        "output": str(args.output.resolve()),
        "status": payload["status"],
        "execution_performed": payload["execution_performed"],
        "gate_statuses": payload["gate_statuses"],
        "reasons": payload["reasons"],
    }, ensure_ascii=False))
    if args.formal and not payload["formal_run_performed"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
