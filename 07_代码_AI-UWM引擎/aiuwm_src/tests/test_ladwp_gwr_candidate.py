from __future__ import annotations

import pandas as pd

from scripts.build_ladwp_gwr_candidate import build_candidate


def test_ladwp_candidate_requires_reported_value_for_each_metric(tmp_path) -> None:
    csv_path = tmp_path / "normalized.csv"
    pdf_path = tmp_path / "source.pdf"
    names = [
        "pH",
        "temperature_c",
        "tds_mg_l",
        "chloride_mg_l",
        "calcium_mg_l",
        "magnesium_mg_l",
        "sodium_mg_l",
        "sulfate_mg_l",
        "alkalinity_mg_l_as_caco3",
        "silica_mg_l",
    ]
    pd.DataFrame(
        {
            "metric": names,
            "units": ["mg/L"] * len(names),
            "reported_value": [1] * len(names),
            "detection_limit": [0.1] * len(names),
            "qualifier": [""] * len(names),
        }
    ).to_csv(csv_path, index=False)
    pdf_path.write_bytes(b"pdf")
    result = build_candidate(csv_path, pdf_path)
    assert result["required_panel_complete"] is True
    assert result["formal_g2_eligible"] is False


def test_ladwp_candidate_keeps_non_detect_as_missing_value(tmp_path) -> None:
    csv_path = tmp_path / "normalized.csv"
    pdf_path = tmp_path / "source.pdf"
    pd.DataFrame(
        {
            "metric": ["magnesium_mg_l"],
            "units": ["mg/L"],
            "reported_value": [""],
            "detection_limit": [0.1],
            "qualifier": ["ND"],
        }
    ).to_csv(csv_path, index=False)
    pdf_path.write_bytes(b"pdf")
    result = build_candidate(csv_path, pdf_path)
    assert result["coverage"]["magnesium_mg_l"]["observed"] is True
    assert result["coverage"]["magnesium_mg_l"]["reported_value_present"] is False
    assert result["required_panel_complete"] is False
