"""Register downloaded external evidence without changing R10 gate states.

The registry is deliberately metadata-only: it records a public dataset's
license, DOI, file hashes, shape and time span. It does not turn a pilot
cooling-tower dataset into data-centre facility validation or PHREEQC evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _inspect_csv(path: Path) -> dict[str, Any]:
    import pandas as pd

    frame = pd.read_csv(path, sep=";", low_memory=False)
    result: dict[str, Any] = {
        "file": path.name,
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
        "rows": int(len(frame)),
        "columns": [str(column) for column in frame.columns],
        "delimiter": ";",
    }
    if "Time" in frame.columns and len(frame):
        parsed = pd.to_datetime(frame["Time"], dayfirst=True, errors="coerce")
        result["time_start"] = parsed.min().isoformat() if parsed.notna().any() else None
        result["time_end"] = parsed.max().isoformat() if parsed.notna().any() else None
        result["time_parse_failures"] = int(parsed.isna().sum())
    if "Stream" in frame.columns:
        result["streams"] = sorted(frame["Stream"].dropna().astype(str).unique().tolist())
    return result


def register(dataset_root: Path, output: Path) -> dict[str, Any]:
    dataset_root = dataset_root.resolve()
    files = sorted(dataset_root.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {dataset_root}")
    records = [_inspect_csv(path) for path in files]
    payload = {
        "kind": "EXTERNAL_EVIDENCE_REGISTRY",
        "registry_version": "R10.1",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "dataset": {
            "name": "AquaSPICE pilot testing: cooling-tower water minimization",
            "doi": "10.17632/249yhxbcvj.1",
            "landing_page": "https://data.mendeley.com/datasets/249yhxbcvj/1",
            "license": "CC BY 4.0",
            "source_type": "public pilot cooling-tower treatment dataset",
            "evidence_class": "E2_public_pilot",
            "applicable_to": ["adaptation_parameter_screening", "cooling_tower_treatment_accounting"],
            "not_valid_for": ["data_center_facility_holdout", "independent_phreeqc_crosscheck"],
        },
        "dataset_root": str(dataset_root),
        "files": records,
        "gate_effect": {
            "g2": "unchanged_NOT_READY",
            "g3": "unchanged_NOT_READY",
            "reason": "Pilot cooling-tower data do not provide independent PHREEQC outputs or >=3 data-centre facilities with leave-one-facility-out validation.",
        },
    }
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = register(args.dataset_root, args.output)
    print(json.dumps({"output": str(args.output.resolve()), "file_count": len(payload["files"]), "g2": payload["gate_effect"]["g2"], "g3": payload["gate_effect"]["g3"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
