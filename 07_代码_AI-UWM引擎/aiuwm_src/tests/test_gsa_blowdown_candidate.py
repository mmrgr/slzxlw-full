from __future__ import annotations

import csv

from scripts.build_gsa_blowdown_candidate import build_candidate


def test_gsa_candidate_is_bounded_and_not_formal_g3(tmp_path) -> None:
    csv_path = tmp_path / "periods.csv"
    pdf_path = tmp_path / "source.pdf"
    fields = [
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
        "source_page",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow({name: "1" for name in fields})
    pdf_path.write_bytes(b"pdf")
    result = build_candidate(csv_path, pdf_path)
    assert result["coverage"]["facility_count"] == 1
    assert result["formal_g3_eligible"] is False
    assert result["gate_effect"]["g3"] == "unchanged_NOT_READY"


def test_gsa_candidate_rejects_missing_operational_field(tmp_path) -> None:
    csv_path = tmp_path / "periods.csv"
    pdf_path = tmp_path / "source.pdf"
    csv_path.write_text("facility_id,period_days\nsite,30\n", encoding="utf-8")
    pdf_path.write_bytes(b"pdf")
    result = build_candidate(csv_path, pdf_path)
    assert result["status"] == "INVALID_CANDIDATE"
    assert "makeup_gal" in result["missing_columns"]
