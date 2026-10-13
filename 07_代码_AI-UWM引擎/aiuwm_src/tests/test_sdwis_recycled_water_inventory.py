from __future__ import annotations

import pandas as pd

from scripts.build_sdwis_recycled_water_inventory import inventory_from_table


def test_inventory_requires_complete_panel_and_preserves_observed_rows() -> None:
    table = pd.DataFrame(
        {
            "Analyte Name": ["CHLORIDE", "SULFATE", "CALCIUM", "MAGNESIUM", "SODIUM", "ALKALINITY, TOTAL"],
            "Sampling Date": ["01-02-2026"] * 6,
            "Detected Level": [90, 40, 45, 9, 80, 150],
            "Unit": ["MG/L"] * 6,
            "Lab Sample ID": ["S1"] * 6,
        }
    )
    result = inventory_from_table(table)
    assert result["lab_sample_id_count"] == 1
    assert result["coverage"]["chloride"]["observed"] is True
    assert result["coverage"]["pH"]["observed"] is False
    assert result["complete_required_panel_date_count"] == 0


def test_inventory_counts_dates_and_missing_values() -> None:
    table = pd.DataFrame(
        {
            "Analyte Name": ["CHLORIDE", "CHLORIDE"],
            "Sampling Date": ["01-02-2026", "bad"],
            "Detected Level": [90, None],
            "Unit": ["MG/L", "MG/L"],
            "Lab Sample ID": ["S1", "S2"],
        }
    )
    result = inventory_from_table(table)
    assert result["sampling_date_count"] == 2
    assert result["date_parse_failures"] == 1
    assert result["coverage"]["chloride"]["row_count"] == 2
