"""Inventory a public recycled-water utility sampling page without opening G2.

The California SDWIS page is direct utility effluent evidence with laboratory
methods and repeated sampling dates, but it does not expose a complete
cooling-relevant panel.  This script snapshots the page's analyte coverage and
never imputes pH, temperature, TDS or silica from other measurements.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_ANALYTES = {
    "pH": (r"^PH$",),
    "temperature_c": (r"TEMPERATURE",),
    "tds_mg_l": (r"TOTAL DISSOLVED SOLIDS|^TDS$",),
    "chloride": (r"^CHLORIDE$",),
    "calcium": (r"^CALCIUM$",),
    "magnesium": (r"^MAGNESIUM$",),
    "sodium": (r"^SODIUM$",),
    "sulfate": (r"^SULFATE$|^SULPHATE$",),
    "alkalinity": (r"^ALKALINITY, TOTAL$|^TOTAL ALKALINITY$",),
    "silica": (r"^SILICA$|^SILICON$",),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _load_table(html_path: Path) -> pd.DataFrame:
    tables = pd.read_html(html_path)
    candidates: list[pd.DataFrame] = []
    for table in tables:
        if isinstance(table.columns, pd.MultiIndex):
            table.columns = [column[-1] for column in table.columns]
        if "Analyte Name" in table.columns:
            candidates.append(table)
    if not candidates:
        raise ValueError("No SDWIS analyte table found")
    table = max(candidates, key=len).copy()
    table["Analyte Name"] = table["Analyte Name"].fillna("").astype(str).str.strip().str.upper()
    return table[table["Analyte Name"] != ""].reset_index(drop=True)


def inventory_from_table(table: pd.DataFrame) -> dict[str, Any]:
    dates = pd.to_datetime(table["Sampling Date"], format="%m-%d-%Y", errors="coerce")
    coverage: dict[str, Any] = {}
    for name, patterns in REQUIRED_ANALYTES.items():
        mask = pd.Series(False, index=table.index)
        for pattern in patterns:
            mask = mask | table["Analyte Name"].str.contains(pattern, regex=True, na=False)
        rows = table[mask]
        coverage[name] = {
            "row_count": int(len(rows)),
            "sampling_date_count": int(rows["Sampling Date"].nunique()),
            "sampling_dates": sorted(rows["Sampling Date"].dropna().astype(str).unique().tolist()),
            "units": sorted({str(value) for value in rows["Unit"].dropna()}),
            "observed": bool(rows["Detected Level"].notna().any()),
        }
    panel_keys = set(REQUIRED_ANALYTES)
    complete_dates: set[str] | None = None
    for name in panel_keys:
        dates_for_key = set(coverage[name]["sampling_dates"])
        complete_dates = dates_for_key if complete_dates is None else complete_dates & dates_for_key
    return {
        "analyte_row_count": int(len(table)),
        "lab_sample_id_count": int(table["Lab Sample ID"].nunique()),
        "sampling_date_count": int(table["Sampling Date"].nunique()),
        "date_start": dates.min().date().isoformat() if dates.notna().any() else None,
        "date_end": dates.max().date().isoformat() if dates.notna().any() else None,
        "date_parse_failures": int(dates.isna().sum()),
        "complete_required_panel_date_count": len(complete_dates or set()),
        "coverage": coverage,
    }


def build_inventory(html_path: Path, output: Path | None = None) -> dict[str, Any]:
    html_path = html_path.resolve()
    summary = inventory_from_table(_load_table(html_path))
    payload: dict[str, Any] = {
        "artifact": "SDWIS_IEU_RECYCLED_WATER_E2_INVENTORY",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "E2_PUBLIC_RECLAIMED_WATER_INCOMPLETE_PANEL",
        "evidence_class": "E2_public_reclaimed_water",
        "source_context": "Inland Empire Utilities Agency, 001B EFFLUENT - RP1 RECYCLED WATER",
        "source_url": "https://sdwis.waterboards.ca.gov/PDWW/JSP/WSamplingResultsByStoret.jsp?FacilityID=038&SamplingPointID=038&SamplingPointName=001B+EFFLUENT+-+RP1+RECYCLED+WATER&SystemName=INLAND+EMPIRE+UTILITIES+AGENCY&SystemNumber=3690001&WSFNumber=72452",
        "snapshot": {"path": str(html_path), "sha256": _sha256(html_path), "bytes": html_path.stat().st_size},
        "summary": summary,
        "formal_g2_eligible": False,
        "applicable_to": ["direct recycled-water provenance", "major-ion plausibility bounds", "future G2 acquisition planning"],
        "not_valid_for": [
            "formal G2 chemistry cross-validation",
            "cooling-tower makeup chemistry",
            "temperature-dependent PHREEQC validation",
            "facility holdout validation",
        ],
        "limitations": [
            "the public page lacks observed pH, temperature, TDS and silica rows",
            "the page is a live utility portal snapshot rather than a versioned analytical dataset",
            "sample quality flags and measurement uncertainty are not exposed consistently",
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
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_inventory(args.html, args.output)
    print(json.dumps({"status": payload["status"], "lab_sample_id_count": payload["summary"]["lab_sample_id_count"], "complete_required_panel_date_count": payload["summary"]["complete_required_panel_date_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
