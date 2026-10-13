"""Normalize a public reclaimed-water ion table as a gate-safe G2 candidate.

The Figshare table contains one reclaimed-water row and one brackish-water
comparison row from an irrigation study.  This script preserves the raw hash,
normalizes the major-ion units, and computes a transparent charge-balance
diagnostic.  It deliberately does not promote the data to formal G2 evidence:
the study is not a cooling-tower study, has no temperature or uncertainty
fields, and does not provide independent PHREEQC results or replicated facility
samples.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


CANONICAL_COLUMNS = (
    "water_resource",
    "ec_us_cm",
    "ph",
    "na_mmol_l",
    "k_mmol_l",
    "hco3_mmol_l",
    "cl_mmol_l",
    "ca_mmol_l",
    "mg_mmol_l",
    "so4_mmol_l",
    "sar",
    "tn_mg_l",
    "tp_mg_l",
    "pb_mg_l",
    "cu_mg_l",
    "zn_mg_l",
    "cd_mg_l",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _charge_balance(row: dict[str, Any]) -> dict[str, Any]:
    cations = (
        (_finite(row.get("na_mmol_l")) or 0.0)
        + (_finite(row.get("k_mmol_l")) or 0.0)
        + 2.0 * (_finite(row.get("ca_mmol_l")) or 0.0)
        + 2.0 * (_finite(row.get("mg_mmol_l")) or 0.0)
    )
    anions = (
        (_finite(row.get("hco3_mmol_l")) or 0.0)
        + (_finite(row.get("cl_mmol_l")) or 0.0)
        + 2.0 * (_finite(row.get("so4_mmol_l")) or 0.0)
    )
    denominator = 0.5 * (cations + anions)
    percent = 100.0 * (cations - anions) / denominator if denominator else None
    return {
        "cation_meq_l": cations,
        "anion_meq_l": anions,
        "charge_balance_percent": percent,
        "status": "REVIEW_REQUIRED" if percent is None or abs(percent) > 5.0 else "PASS_SCREEN",
    }


def _sample_suffix(resource: str) -> str:
    plain = html.unescape(re.sub(r"<[^>]+>", "", resource))
    plain = re.sub(r"[^A-Za-z0-9]+", "_", plain).strip("_")
    return plain or "UNKNOWN"


def normalize_frame(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Normalize a table whose columns are already in the source order."""
    if len(frame.columns) != len(CANONICAL_COLUMNS):
        raise ValueError(f"Expected {len(CANONICAL_COLUMNS)} columns; got {len(frame.columns)}")
    normalized: list[dict[str, Any]] = []
    for index, values in frame.iterrows():
        row = {name: values.iloc[position] for position, name in enumerate(CANONICAL_COLUMNS)}
        resource = str(row["water_resource"]).strip()
        if not resource or resource.lower() == "nan":
            raise ValueError(f"Row {index} has no water-resource label")
        output = {
            "sample_id": f"FIGSHARE-28948753-{_sample_suffix(resource)}",
            "water_resource": resource,
            "ec_us_cm": _finite(row["ec_us_cm"]),
            "ph": _finite(row["ph"]),
            "na_mmol_l": _finite(row["na_mmol_l"]),
            "k_mmol_l": _finite(row["k_mmol_l"]),
            "hco3_mmol_l": _finite(row["hco3_mmol_l"]),
            "cl_mmol_l": _finite(row["cl_mmol_l"]),
            "ca_mmol_l": _finite(row["ca_mmol_l"]),
            "mg_mmol_l": _finite(row["mg_mmol_l"]),
            "so4_mmol_l": _finite(row["so4_mmol_l"]),
            "sar": _finite(row["sar"]),
            "tn_mg_l": _finite(row["tn_mg_l"]),
            "tp_mg_l": _finite(row["tp_mg_l"]),
            "pb_mg_l": None if str(row["pb_mg_l"]).strip().upper() == "ND" else _finite(row["pb_mg_l"]),
            "cu_mg_l": None if str(row["cu_mg_l"]).strip().upper() == "ND" else _finite(row["cu_mg_l"]),
            "zn_mg_l": None if str(row["zn_mg_l"]).strip().upper() == "ND" else _finite(row["zn_mg_l"]),
            "cd_mg_l": None if str(row["cd_mg_l"]).strip().upper() == "ND" else _finite(row["cd_mg_l"]),
        }
        output["charge_balance"] = _charge_balance(output)
        normalized.append(output)
    return normalized


def build_candidate(raw_path: Path, output_json: Path, output_csv: Path) -> dict[str, Any]:
    raw_path = raw_path.resolve()
    # The source is an old binary XLS file; xlrd is intentionally an ingestion-only dependency.
    frame = pd.read_excel(raw_path, header=0, engine="xlrd")
    frame.columns = list(CANONICAL_COLUMNS)
    rows = normalize_frame(frame)
    payload: dict[str, Any] = {
        "artifact": "FIGSHARE_RECLAIMED_WATER_G2_CANDIDATE",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": {
            "article_id": 28948753,
            "file_id": 54279751,
            "title": "Physicochemical properties and ion concentrations of reclaimed water (RW) and brackish water (BW)",
            "doi": "10.1371/journal.pone.0322846.t002",
            "landing_page": "https://plos.figshare.com/articles/dataset/Physicochemical_properties_and_ion_concentrations_of_reclaimed_water_RW_and_brackish_water_BW_/28948753",
            "download_url": "https://ndownloader.figshare.com/files/54279751",
            "metadata_path": str(raw_path.parent / "source_metadata.json"),
            "license": "CC BY 4.0",
            "raw_path": str(raw_path),
            "raw_sha256": _sha256(raw_path),
            "raw_bytes": raw_path.stat().st_size,
        },
        "rows": rows,
        "sample_count": len(rows),
        "evidence_class": "E2_public_reclaimed_water_table",
        "status": "CANDIDATE_REVIEW_REQUIRED",
        "formal_g2_eligible": False,
        "applicable_to": ["major-ion plausibility screening", "charge-balance review", "scenario-prior bounding"],
        "not_valid_for": [
            "formal G2 chemistry cross-validation",
            "data-centre cooling-water representation",
            "facility holdout or time-series validation",
            "temperature-dependent PHREEQC comparison",
        ],
        "limitations": [
            "one reclaimed-water row from an irrigation study",
            "no sampling date, treatment-stage metadata, temperature, TDS, or analytical uncertainty in the table",
            "independent PHREEQC results and cooling-tower operating context are absent",
            "the brackish-water comparison row has a charge-balance review flag; the reclaimed-water row passes this screen",
        ],
        "gate_effect": {
            "g2": "unchanged_NOT_READY",
            "g3": "unchanged_NOT_READY",
        },
    }
    output_json = output_json.resolve()
    output_csv = output_csv.resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(rows).to_csv(output_csv, index=False)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-xls", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()
    payload = build_candidate(args.raw_xls, args.output_json, args.output_csv)
    print(json.dumps({"status": payload["status"], "sample_count": payload["sample_count"], "formal_g2_eligible": payload["formal_g2_eligible"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
