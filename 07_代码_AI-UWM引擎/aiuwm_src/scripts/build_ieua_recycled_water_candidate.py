"""Build a traceable candidate from an official IEUA recycled-water report.

The report supplies a direct utility aggregate with a cooling-relevant ion
panel, but it summarizes monthly averages rather than sample-level records and
does not report temperature.  It is therefore useful for plausibility bounds
and acquisition planning, not a formal G2 PASS manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_METRICS = {
    "pH": "pH",
    "temperature_c": "temperature_c",
    "tds_mg_l": "tds_mg_l",
    "chloride_mg_l": "chloride_mg_l",
    "calcium_mg_l": "calcium_mg_l",
    "magnesium_mg_l": "magnesium_mg_l",
    "sodium_mg_l": "sodium_mg_l",
    "sulfate_mg_l": "sulfate_mg_l",
    "alkalinity_mg_l_as_caco3": "alkalinity_mg_l_as_caco3",
    "silica_mg_l": "silica_mg_l",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def build_candidate(normalized_csv: Path, source_pdf: Path, output: Path | None = None) -> dict[str, Any]:
    normalized_csv = normalized_csv.resolve()
    source_pdf = source_pdf.resolve()
    table = pd.read_csv(normalized_csv)
    metrics = set(table["metric"].astype(str))
    coverage = {
        name: {
            "observed": metric in metrics,
            "rows": int((table["metric"] == metric).sum()),
            "units": sorted({str(value) for value in table.loc[table["metric"] == metric, "units"]}),
        }
        for name, metric in REQUIRED_METRICS.items()
    }
    complete = all(item["observed"] for item in coverage.values())
    payload: dict[str, Any] = {
        "artifact": "IEUA_RP1_2025_RECLAIMED_WATER_CANDIDATE",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "CANDIDATE_REVIEW_REQUIRED",
        "evidence_class": "E2_public_reclaimed_water_aggregate",
        "source_context": "IEUA RP-1 direct recycled-water report",
        "source_pdf": {"path": str(source_pdf), "sha256": _sha256(source_pdf), "bytes": source_pdf.stat().st_size},
        "normalized_csv": {"path": str(normalized_csv), "sha256": _sha256(normalized_csv), "rows": int(len(table))},
        "aggregation": "Monthly-average summary with average/minimum/maximum columns; not individual samples.",
        "coverage": coverage,
        "required_panel_complete": complete,
        "formal_g2_eligible": False,
        "applicable_to": ["direct reclaimed-water plausibility bounds", "cooling chemistry prior screening", "future G2 acquisition planning"],
        "not_valid_for": [
            "formal G2 chemistry cross-validation",
            "temperature-dependent PHREEQC validation",
            "facility holdout validation",
            "sample-level uncertainty estimation",
        ],
        "limitations": [
            "temperature is absent from the public report",
            "the report aggregates monthly averages and does not provide row-level samples",
            "measurement uncertainty and charge-balance inputs are not reported",
        ],
        "gate_effect": {"g2": "unchanged_NOT_READY", "g3": "unchanged_NOT_READY"},
    }
    if output is not None:
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--normalized-csv", type=Path, required=True)
    parser.add_argument("--source-pdf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_candidate(args.normalized_csv, args.source_pdf, args.output)
    print(json.dumps({"status": payload["status"], "required_panel_complete": payload["required_panel_complete"], "formal_g2_eligible": payload["formal_g2_eligible"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
