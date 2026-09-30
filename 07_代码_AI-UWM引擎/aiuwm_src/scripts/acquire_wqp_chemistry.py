"""Acquire and normalize Water Quality Portal chemistry for G2 pilot inputs.

The utility keeps the raw WQP responses, hashes every response, and emits a
wide sample table compatible with ``run_g2_phreeqc_crosscheck.py``.  It is an
evidence-ingestion utility only: ambient/river observations are not silently
promoted to reclaimed-water observations or to a G2 PASS.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PARAMETERS: Mapping[str, str] = {
    "pH": "00400",
    "temperature_c": "00010",
    # Directly measured total dissolved solids are required for the
    # reduced-order cooling-water comparison.  Keep this separate from an
    # ion-sum proxy: the latter is a lower-bound screening quantity and must
    # never be silently substituted for TDS in a gate record.
    "tds_mg_l": "70300",
    "Ca_mg_l": "00915",
    "Mg_mg_l": "00925",
    "Na_mg_l": "00930",
    "Cl_mg_l": "00940",
    "SO4_mg_l": "00945",
    "alkalinity_mg_l_as_CaCO3": "00410",
    "Si_mg_l": "00955",
}
REQUIRED_OUTPUT = ("sample_id", "site_id", "date", *PARAMETERS)
OPTIONAL_OUTPUT = ("source_provenance", "observed_flag")
_SAFE_NAME = re.compile(r"[^A-Za-z0-9_.-]+")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _number(value: str, *, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric; got {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def _first_numeric(rows: Iterable[dict[str, str]], field: str) -> dict[str, str]:
    for row in rows:
        value = str(row.get("ResultMeasureValue", "")).strip()
        if not value:
            continue
        try:
            _number(value, field=field)
        except ValueError:
            continue
        return row
    raise ValueError(f"no numeric result for {field}")


def normalize_tables(tables: Mapping[str, Iterable[dict[str, str]]]) -> list[dict[str, str]]:
    """Join parameter tables by WQP ``ActivityIdentifier``.

    Duplicate results are retained in the raw files but the first numeric
    result for each activity/parameter is selected deterministically for the
    pilot table.  The manifest records that this is a screening normalization.
    """

    by_parameter: dict[str, dict[str, dict[str, str]]] = {}
    for parameter in PARAMETERS:
        grouped: dict[str, list[dict[str, str]]] = {}
        for row in tables.get(parameter, []):
            activity = str(row.get("ActivityIdentifier", "")).strip()
            if activity:
                grouped.setdefault(activity, []).append(dict(row))
        by_parameter[parameter] = {
            activity: _first_numeric(rows, parameter)
            for activity, rows in grouped.items()
        }

    common = set.intersection(*(set(values) for values in by_parameter.values()))
    normalized: list[dict[str, str]] = []
    for activity in sorted(common):
        anchor = by_parameter["pH"][activity]
        row = {
            "sample_id": activity,
            "site_id": str(anchor.get("MonitoringLocationIdentifier", "")).strip(),
            "date": str(anchor.get("ActivityStartDate", "")).strip(),
            "source_provenance": "Water Quality Portal / USGS activity record",
            "observed_flag": "true",
        }
        for parameter in PARAMETERS:
            source = by_parameter[parameter][activity]
            row[parameter] = str(source["ResultMeasureValue"]).strip()
        normalized.append(row)
    if not normalized:
        raise ValueError("no complete samples share all required WQP parameters")
    return normalized


def _fetch(url: str, output: Path) -> None:
    request = Request(
        url,
        headers={"User-Agent": "AI-UWM-R10 evidence acquisition", "Accept": "text/csv"},
    )
    with urlopen(request, timeout=120) as response:
        output.write_bytes(response.read())


def acquire(
    *,
    site_ids: Iterable[str],
    start_date: str,
    end_date: str,
    output_dir: Path,
    providers: str | None = None,
) -> dict[str, object]:
    sites = sorted({str(site).strip() for site in site_ids if str(site).strip()})
    if not sites:
        raise ValueError("at least one WQP site id is required")
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(exist_ok=True)
    tables: dict[str, list[dict[str, str]]] = {}
    sources: dict[str, dict[str, object]] = {}
    site_query = ";".join(sites)
    for parameter, pcode in PARAMETERS.items():
        query = {
            "siteid": site_query,
            "sampleMedia": "Water",
            "startDateLo": start_date,
            "startDateHi": end_date,
            "mimeType": "csv",
            "zip": "no",
        }
        # WQP exposes alkalinity inconsistently across providers; the
        # characteristic-name query is the stable fallback for this field.
        if parameter == "alkalinity_mg_l_as_CaCO3":
            query["characteristicName"] = "Alkalinity"
        else:
            query["pCode"] = pcode
        if providers:
            query["providers"] = providers
        url = "https://www.waterqualitydata.us/data/Result/search?" + urlencode(query)
        raw_path = raw_dir / f"{_SAFE_NAME.sub('_', parameter)}_p{pcode}.csv"
        _fetch(url, raw_path)
        with raw_path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise ValueError(f"WQP returned no rows for {parameter}")
        tables[parameter] = rows
        sources[parameter] = {"pcode": pcode, "url": url, "sha256": _sha256(raw_path), "row_count": len(rows)}

    normalized = normalize_tables(tables)
    normalized_path = output_dir / "wqp_chemistry_normalized.csv"
    with normalized_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[*REQUIRED_OUTPUT, *OPTIONAL_OUTPUT])
        writer.writeheader()
        writer.writerows(normalized)
    manifest = {
        "kind": "WQP_CHEMISTRY_INGESTION",
        "status": "PILOT_ONLY",
        "evidence_class": "E2_observed_ambient",
        "water_type_scope": "ambient_water_screening",
        "site_ids": sorted({row["site_id"] for row in normalized}),
        "sample_count": len(normalized),
        "date_span": {"start": min(row["date"] for row in normalized), "end": max(row["date"] for row in normalized)},
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "parameters": sources,
        "normalized_output": {"path": str(normalized_path.resolve()), "sha256": _sha256(normalized_path)},
        "gate_effect": "G2 remains NOT_READY: ambient observations are not reclaimed-water validation, reduced-model comparison and false-safe review are still required.",
    }
    manifest_path = output_dir / "wqp_chemistry_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-id", action="append", required=True)
    parser.add_argument("--start-date", default="01-01-2018")
    parser.add_argument("--end-date", default="12-31-2025")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--providers")
    args = parser.parse_args()
    manifest = acquire(site_ids=args.site_id, start_date=args.start_date, end_date=args.end_date, output_dir=args.output_dir, providers=args.providers)
    print(json.dumps({"status": manifest["status"], "sample_count": manifest["sample_count"], "output_dir": str(args.output_dir.resolve()), "gate_effect": manifest["gate_effect"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
