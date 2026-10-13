from __future__ import annotations

import pandas as pd

from scripts.build_ieua_recycled_water_candidate import build_candidate


def test_candidate_keeps_temperature_missing(tmp_path) -> None:
    csv_path = tmp_path / "normalized.csv"
    pdf_path = tmp_path / "source.pdf"
    pd.DataFrame(
        {
            "metric": ["pH", "tds_mg_l", "chloride_mg_l"],
            "units": ["units", "mg/L", "mg/L"],
            "average": [7.0, 450, 100],
            "minimum": [6.8, 430, 95],
            "maximum": [7.2, 470, 105],
        }
    ).to_csv(csv_path, index=False)
    pdf_path.write_bytes(b"pdf")
    result = build_candidate(csv_path, pdf_path)
    assert result["coverage"]["pH"]["observed"] is True
    assert result["coverage"]["temperature_c"]["observed"] is False
    assert result["required_panel_complete"] is False
    assert result["formal_g2_eligible"] is False


def test_candidate_detects_complete_panel_in_test_fixture(tmp_path) -> None:
    csv_path = tmp_path / "normalized.csv"
    pdf_path = tmp_path / "source.pdf"
    names = ["pH", "temperature_c", "tds_mg_l", "chloride_mg_l", "calcium_mg_l", "magnesium_mg_l", "sodium_mg_l", "sulfate_mg_l", "alkalinity_mg_l_as_caco3", "silica_mg_l"]
    pd.DataFrame({"metric": names, "units": ["mg/L"] * len(names), "average": [1] * len(names), "minimum": [1] * len(names), "maximum": [1] * len(names)}).to_csv(csv_path, index=False)
    pdf_path.write_bytes(b"pdf")
    result = build_candidate(csv_path, pdf_path)
    assert result["required_panel_complete"] is True
    assert result["formal_g2_eligible"] is False
