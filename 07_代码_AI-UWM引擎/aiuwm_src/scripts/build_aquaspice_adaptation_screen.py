"""Summarize the public AquaSPICE cooling-treatment pilot for E4 screening.

The output is a provenance-preserving E2 parameter screen. It reports measured
flow, feed TDS, permeate TDS and pH ranges from the supplied CSV files, but it
does not invent treatment energy, cost, corrosion or facility-validation
parameters. The result is therefore unsuitable for a formal G2/G3 gate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FILES = (
    "BACF_CTMU_Enhanced.csv",
    "RO_CTMU_Enhanced.csv",
    "RO_CTBD.csv",
    "UF_CTMU_Enhanced.csv",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _number(row: dict[str, str], name: str) -> float | None:
    value = row.get(name, "")
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _quantiles(values: list[float]) -> dict[str, float | int]:
    if not values:
        return {"count": 0, "median": None, "q05": None, "q95": None}
    ordered = sorted(values)

    def percentile(q: float) -> float:
        index = (len(ordered) - 1) * q
        lower = math.floor(index)
        upper = math.ceil(index)
        if lower == upper:
            return ordered[lower]
        weight = index - lower
        return ordered[lower] * (1.0 - weight) + ordered[upper] * weight

    return {
        "count": len(ordered),
        "median": percentile(0.5),
        "q05": percentile(0.05),
        "q95": percentile(0.95),
    }


def _summarize_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        rows = list(reader)
        columns = list(reader.fieldnames or [])
    result: dict[str, Any] = {
        "path": str(path),
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
        "row_count": len(rows),
        "columns": columns,
        "time_start": rows[0].get("Time") if rows else None,
        "time_end": rows[-1].get("Time") if rows else None,
    }
    if path.name.startswith("RO_"):
        fields = (
            "RO_C_Feed_TDS",
            "RO_C_Perm",
            "RO_Perm_Flow",
            "RO_Conc_Flow",
            "RO_Feed_Flow_ultrasonic",
            "RO_Feed_pH",
            "RO_Feed_T",
            "RO_Y",
        )
        result["measurements"] = {
            field: _quantiles([value for value in (_number(row, field) for row in rows) if value is not None])
            for field in fields
        }
        perm = [_number(row, "RO_Perm_Flow") for row in rows]
        conc = [_number(row, "RO_Conc_Flow") for row in rows]
        flow_recovery = [
            p / (p + c)
            for p, c in zip(perm, conc)
            if p is not None and c is not None and p + c > 0.0
        ]
        feed_tds = [_number(row, "RO_C_Feed_TDS") for row in rows]
        perm_tds = [_number(row, "RO_C_Perm") for row in rows]
        tds_rejection = [
            1.0 - p / f
            for p, f in zip(perm_tds, feed_tds)
            if p is not None and f is not None and f > 0.0
        ]
        result["derived_screening_metrics"] = {
            "flow_recovery_fraction": _quantiles(flow_recovery),
            "tds_rejection_fraction": _quantiles(tds_rejection),
        }
    return result


def summarize_dataset(data_root: Path, output_path: Path | None = None) -> dict[str, Any]:
    data_root = data_root.resolve()
    file_summaries = []
    missing = []
    for name in FILES:
        path = data_root / name
        if not path.is_file():
            missing.append(name)
            continue
        file_summaries.append(_summarize_file(path))
    payload: dict[str, Any] = {
        "artifact": "AquaSPICE_E2_adaptation_parameter_screen",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "PASS_E2_SCREEN" if not missing and file_summaries else "INCOMPLETE_E2_SCREEN",
        "evidence_class": "E2_public_pilot",
        "dataset_root": str(data_root),
        "files": file_summaries,
        "missing_files": missing,
        "applicable_to": ["A1/A2 treatment flow and TDS parameter screening"],
        "not_valid_for": [
            "formal G2 chemistry cross-validation",
            "G3 facility holdout",
            "data-centre-specific energy or cost calibration",
            "microbial, corrosion or field-scale scaling safety",
        ],
        "unmeasured_or_unresolved": [
            "treatment energy and carbon",
            "chemical and capital costs",
            "complete ion panel and alkalinity",
            "data-centre operating conditions",
        ],
        "gate_effect": {
            "g2": "unchanged_NOT_READY",
            "g3": "unchanged_NOT_READY",
            "e4": "diagnostic_parameter_screen_only",
        },
    }
    if output_path is not None:
        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = summarize_dataset(args.data_root, args.output)
    print(json.dumps({"status": payload["status"], "files": len(payload["files"]), "output": str(args.output.resolve())}, ensure_ascii=False))
    return 0 if payload["status"] == "PASS_E2_SCREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
