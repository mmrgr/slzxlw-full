"""Build a bounded G3 lead from the public GSA cooling-tower evaluation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = {
    "facility_id",
    "study_id",
    "period_label",
    "period_days",
    "makeup_gal",
    "blowdown_gal",
    "drift_gal",
    "evaporation_gal",
    "heat_rejected_mmbtu",
    "water_per_heat_gal_per_mmbtu",
    "coc_water_balance",
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
    with normalized_csv.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        rows = list(reader)
    missing = sorted(REQUIRED_COLUMNS - fields)
    facilities = sorted({row.get("facility_id", "").strip() for row in rows if row.get("facility_id", "").strip()})
    total_days = sum(int(float(row["period_days"])) for row in rows) if not missing else 0
    payload: dict[str, Any] = {
        "artifact": "GSA_BLOWDOWN_RECOVERY_COOLING_FACILITY_CANDIDATE",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "CANDIDATE_REVIEW_REQUIRED",
        "evidence_class": "E2_public_cooling_facility_operations",
        "source_context": "GSA Green Proving Ground Lloyd D. George Courthouse cooling-tower BDR evaluation",
        "source_pdf": {"path": str(source_pdf), "sha256": _sha256(source_pdf), "bytes": source_pdf.stat().st_size},
        "normalized_csv": {"path": str(normalized_csv), "sha256": _sha256(normalized_csv), "rows": len(rows)},
        "coverage": {"facility_count": len(facilities), "facility_ids": facilities, "aggregate_period_count": len(rows), "aggregate_days": total_days},
        "observed_metrics": sorted(REQUIRED_COLUMNS - {"facility_id", "study_id", "period_label", "source_page"}),
        "formal_g3_eligible": False,
        "applicable_to": ["bounded cooling-tower makeup/blowdown/CoC prior", "G3 acquisition and protocol design"],
        "not_valid_for": ["formal leave-one-facility-out holdout", "data-center WUE validation", "12-month daily facility prediction"],
        "limitations": [
            "one courthouse facility and three aggregate periods totaling 102 days",
            "no IT energy, facility energy, PUE or WUE fields",
            "no model predictions or independent leave-one-facility-out review",
        ],
        "gate_effect": {"g3": "unchanged_NOT_READY", "g2": "unchanged_NOT_READY"},
    }
    if missing:
        payload["status"] = "INVALID_CANDIDATE"
        payload["missing_columns"] = missing
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
    print(json.dumps({"status": payload["status"], "facility_count": payload["coverage"]["facility_count"], "aggregate_days": payload["coverage"]["aggregate_days"], "formal_g3_eligible": payload["formal_g3_eligible"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
