from __future__ import annotations

import csv
from pathlib import Path

from scripts.build_aquaspice_adaptation_screen import summarize_dataset


def _write(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(header)
        writer.writerows(rows)


def test_aquaspice_screen_records_flow_and_tds_metrics(tmp_path: Path) -> None:
    for name in (
        "BACF_CTMU_Enhanced.csv",
        "UF_CTMU_Enhanced.csv",
    ):
        _write(tmp_path / name, ["Time"], [["10.06.2022 00:01"]])
    header = [
        "Time", "RO_C_Feed_TDS", "RO_C_Perm", "RO_Perm_Flow",
        "RO_Conc_Flow", "RO_Feed_Flow_ultrasonic", "RO_Feed_pH",
        "RO_Feed_T", "RO_Y",
    ]
    rows = [
        ["10.06.2022 00:01", "1000", "10", "80", "20", "100", "7.5", "20", "0.8"],
        ["10.06.2022 00:03", "1200", "12", "75", "25", "100", "7.7", "21", "0.75"],
    ]
    for name in ("RO_CTMU_Enhanced.csv", "RO_CTBD.csv"):
        _write(tmp_path / name, header, rows)

    output = tmp_path / "screen.json"
    payload = summarize_dataset(tmp_path, output)

    assert payload["status"] == "PASS_E2_SCREEN"
    assert payload["gate_effect"]["g2"] == "unchanged_NOT_READY"
    ro = next(item for item in payload["files"] if item["path"].endswith("RO_CTMU_Enhanced.csv"))
    assert ro["derived_screening_metrics"]["flow_recovery_fraction"]["median"] == 0.775
    assert output.is_file()


def test_aquaspice_screen_reports_missing_file(tmp_path: Path) -> None:
    payload = summarize_dataset(tmp_path)
    assert payload["status"] == "INCOMPLETE_E2_SCREEN"
    assert len(payload["missing_files"]) == 4
