from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.register_external_evidence import register


def test_external_registry_records_hashes_and_keeps_gates_closed(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    with (dataset / "pilot.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["Time", "Stream", "RO_Y"])
        writer.writerow(["10.06.2022 00:01", "RAW W", "0.8"])
        writer.writerow(["10.06.2022 00:03", "RAW W", "0.9"])

    output = tmp_path / "manifest.json"
    payload = register(dataset, output)

    assert output.exists()
    assert payload["files"][0]["rows"] == 2
    assert payload["files"][0]["sha256"].startswith("sha256:")
    assert payload["gate_effect"] == {
        "g2": "unchanged_NOT_READY",
        "g3": "unchanged_NOT_READY",
        "reason": payload["gate_effect"]["reason"],
    }
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["dataset"]["evidence_class"] == "E2_public_pilot"
    assert "data_center_facility_holdout" in persisted["dataset"]["not_valid_for"]
