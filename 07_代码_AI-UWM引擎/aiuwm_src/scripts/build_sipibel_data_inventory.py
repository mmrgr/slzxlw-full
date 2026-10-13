"""Inventory SIPIBEL wastewater chemistry coverage without opening G2.

The archive contains many wastewater observations and analytical metadata, but
the inventory must distinguish broad wastewater monitoring from a complete,
cooling-relevant reclaimed-water ion panel.  It reports the available treatment
matrix, date/quality coverage and whether required chemistry indicators are
actually defined for treated wastewater.  It never imputes missing ions or
converts conductivity into TDS.
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


REQUIRED_CHEMISTRY = {
    "pH": (r"^pH$",),
    "temperature_c": (r"temperature",),
    "tds_mg_l": (r"total dissolved|dissolved solids|TDS",),
    "chloride": (r"^chloride$|chlorures?",),
    "calcium": (r"^calcium$",),
    "magnesium": (r"^magnesium$",),
    "sodium": (r"^sodium$",),
    "sulfate": (r"^(?:sulfates?|sulphates?)$",),
    "alkalinity": (r"alkal",),
    "silica": (r"silic",),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", encoding="latin1", low_memory=False)


def inventory_from_frames(samples: pd.DataFrame, methods: pd.DataFrame, physico: pd.DataFrame) -> dict[str, Any]:
    matrix_methods = methods[methods["Sample matrix"].isin(["Wastewater - raw", "Wastewater - treated"])].copy()
    observed_method_ids = set(physico["ID PC method"].dropna().astype(str))
    matrix_methods["observed_rows"] = matrix_methods["ID Physico-chemical method"].astype(str).isin(observed_method_ids)
    coverage: dict[str, Any] = {}
    for name, patterns in REQUIRED_CHEMISTRY.items():
        mask = pd.Series(False, index=matrix_methods.index)
        for pattern in patterns:
            mask = mask | matrix_methods["Physico-chemical indicator"].astype(str).str.contains(pattern, case=False, regex=True, na=False)
        matches = matrix_methods[mask]
        treated = matches[matches["Sample matrix"] == "Wastewater - treated"]
        raw = matches[matches["Sample matrix"] == "Wastewater - raw"]
        coverage[name] = {
            "treated_methods": treated["ID Physico-chemical method"].astype(str).tolist(),
            "treated_indicators": treated["Physico-chemical indicator"].astype(str).tolist(),
            "treated_units": sorted({str(value) for value in treated["Unit"].dropna()}),
            "treated_observed_method": bool(treated["observed_rows"].any()),
            "raw_methods": raw["ID Physico-chemical method"].astype(str).tolist(),
            "raw_indicators": raw["Physico-chemical indicator"].astype(str).tolist(),
        }

    dates = pd.to_datetime(samples["Start date & time"], dayfirst=True, errors="coerce")
    quality = samples["Sample quality"].fillna("MISSING").astype(str).value_counts().to_dict()
    treated_complete = all(coverage[name]["treated_observed_method"] for name in REQUIRED_CHEMISTRY)
    return {
        "sample_count": int(len(samples)),
        "sample_id_count": int(samples["ID Sample"].nunique()),
        "sampling_point_count": int(samples["ID Sampling point"].nunique()),
        "date_start": dates.min().isoformat() if dates.notna().any() else None,
        "date_end": dates.max().isoformat() if dates.notna().any() else None,
        "date_parse_failures": int(dates.isna().sum()),
        "sample_quality_counts": {str(key): int(value) for key, value in quality.items()},
        "physico_chemistry_value_count": int(len(physico)),
        "physico_chemistry_method_count": int(physico["ID PC method"].nunique()),
        "treated_required_panel_complete": treated_complete,
        "coverage": coverage,
    }


def build_inventory(data_root: Path, archive_path: Path | None = None, output: Path | None = None) -> dict[str, Any]:
    data_root = data_root.resolve()
    samples = _read_csv(data_root / "08_SIPIBEL_dataset_samples.csv")
    methods = _read_csv(data_root / "04_SIPIBEL_metadata_physico_chemistry_methods.csv")
    physico = _read_csv(data_root / "09_SIPIBEL_dataset_physico_chemistry.csv")
    summary = inventory_from_frames(samples, methods, physico)
    payload: dict[str, Any] = {
        "artifact": "SIPIBEL_E2_WASTEWATER_DATA_INVENTORY",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "E2_INVENTORY_INCOMPLETE_CHEMISTRY",
        "evidence_class": "E2_public_wastewater_observatory",
        "data_root": str(data_root),
        "archive": {
            "path": str(archive_path.resolve()) if archive_path else None,
            "sha256": _sha256(archive_path.resolve()) if archive_path else None,
            "bytes": archive_path.stat().st_size if archive_path else None,
        },
        "summary": summary,
        "formal_g2_eligible": False,
        "applicable_to": ["wastewater monitoring provenance", "treatment-matrix coverage audit", "future chemistry acquisition planning"],
        "not_valid_for": [
            "formal G2 chemistry cross-validation",
            "cooling-tower makeup chemistry",
            "facility holdout validation",
            "imputation of missing TDS, chloride, sodium, alkalinity or silica",
        ],
        "limitations": [
            "treated-wastewater monitoring is not a reclaimed cooling-water dataset",
            "the required major-ion panel is incomplete for the treated matrix",
            "sample quality includes uncertain rows and analytical methods are heterogeneous",
            "no cooling-tower operating conditions or independent PHREEQC outputs are supplied",
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
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_inventory(args.data_root, args.archive, args.output)
    print(json.dumps({"status": payload["status"], "sample_count": payload["summary"]["sample_count"], "treated_required_panel_complete": payload["summary"]["treated_required_panel_complete"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
