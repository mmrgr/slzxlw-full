"""Audit the opt-in R10a single-data-centre quality vertical slice.

This audit runs two controlled treated-reuse quality scenarios through the
production engine.  It checks water/solute closure, solver convergence, and
the expected direction of the quality response (higher treated TDS must not
increase the quality-limited CoC).  The output is an internal model diagnostic;
it is deliberately not a G2 chemistry or G3 facility validation manifest.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aiuwm.full_engine import FullAIUWMModel, load_project


def _scenario(repo_root: Path, treated_tds_mg_l: float) -> dict[str, Any]:
    """Run a one-day, single-DC Q1 scenario with a declared treated output."""

    project_path = repo_root / "examples" / "ai_data_center" / "project.json"
    project, timeseries = load_project(project_path)
    project = copy.deepcopy(project)
    timeseries = timeseries.iloc[:1].copy()
    project["simulation"]["end"] = str(timeseries["date"].iloc[-1].date())

    dc = project["components"]["AI_DC1"]
    dc["quality_state_enabled"] = True
    dc["initial_cooling_storage_ml"] = 0.0
    dc["cooling_storage_ml"] = 0.0
    dc["cooling"].update(
        {
            "coc_mode": "quality_limited",
            "cycles_of_concentration": 8.0,
            "water_quality_limits": {"TDS": 1100.0},
        }
    )
    dc["water_sources"]["reclaimed"]["quality_mg_l"] = {"TDS": 900.0}
    dc["water_sources"]["potable"]["quality_mg_l"] = {"TDS": 200.0}
    reuse = project["components"]["CENTRAL_REUSE"]
    reuse["initial_ml"] = 100.0
    reuse["treatment_capacity_ml_day"] = 100.0
    reuse["quality_mg_l"] = {"TDS": float(treated_tds_mg_l)}
    reuse["quality_provenance"] = "treated_output"

    result = FullAIUWMModel(project, timeseries).run()
    row = result.data_center_daily.iloc[0]
    finite_columns = (
        "water_balance_residual_ml",
        "quality_solute_closure_residual_kg",
        "quality_process_solute_closure_residual_kg",
        "quality_partition_closure_TDS_kg",
        "quality_storage_water_balance_residual_ml",
        "quality_recovered_return_volume_residual_ml",
        "quality_recovered_return_mass_residual_kg",
        "cycles_of_concentration",
        "quality_process_TDS_mg_l",
    )
    metrics = {name: float(row[name]) for name in finite_columns}
    metrics["quality_solver_status"] = str(row["quality_solver_status"])
    metrics["quality_reclaimed_quality_provenance"] = str(
        row["quality_reclaimed_quality_provenance"]
    )
    return {
        "treated_tds_mg_l": float(treated_tds_mg_l),
        "metrics": metrics,
    }


def run_audit(repo_root: Path = ROOT, output_path: Path | None = None) -> dict[str, Any]:
    """Run the diagnostic and optionally write its JSON evidence artifact."""

    low = _scenario(repo_root, 100.0)
    high = _scenario(repo_root, 900.0)
    rows = (low, high)
    tolerance = 1e-9
    checks = {
        "all_metrics_finite": all(
            math.isfinite(float(value))
            for scenario in rows
            for key, value in scenario["metrics"].items()
            if key not in {"quality_solver_status", "quality_reclaimed_quality_provenance"}
        ),
        "solver_converged": all(
            scenario["metrics"]["quality_solver_status"] == "converged"
            for scenario in rows
        ),
        "quality_provenance_is_treated_output": all(
            scenario["metrics"]["quality_reclaimed_quality_provenance"]
            == "treated_output"
            for scenario in rows
        ),
        "water_and_solute_closure": all(
            abs(scenario["metrics"][name]) <= tolerance
            for scenario in rows
            for name in (
                "water_balance_residual_ml",
                "quality_solute_closure_residual_kg",
                "quality_process_solute_closure_residual_kg",
                "quality_partition_closure_TDS_kg",
                "quality_storage_water_balance_residual_ml",
                "quality_recovered_return_volume_residual_ml",
                "quality_recovered_return_mass_residual_kg",
            )
        ),
        "higher_tds_does_not_increase_quality_limited_coc": (
            low["metrics"]["cycles_of_concentration"]
            >= high["metrics"]["cycles_of_concentration"]
        ),
    }
    payload: dict[str, Any] = {
        "artifact": "R10a_single_dc_quality_invariants",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_INTERNAL_DIAGNOSTIC"
        if all(checks.values())
        else "FAIL_INTERNAL_DIAGNOSTIC",
        "gate_classification": "diagnostic_only",
        "formal_g2_or_g3_evidence": False,
        "scope": {
            "engine": "examples/ai_data_center/project.json",
            "days": 1,
            "data_centres": 1,
            "quality_inputs": "declared treated-output scenario values",
        },
        "checks": checks,
        "scenarios": list(rows),
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "research_2026" / "experiments" / "r10a_quality_invariants_2026-10-13.json",
    )
    args = parser.parse_args()
    payload = run_audit(args.repo_root.resolve(), args.output.resolve())
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS_INTERNAL_DIAGNOSTIC" else 1


if __name__ == "__main__":
    raise SystemExit(main())
