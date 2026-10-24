from __future__ import annotations

import pandas as pd

from scripts.build_sipibel_data_inventory import inventory_from_frames


def test_inventory_marks_missing_treated_ion_panel() -> None:
    samples = pd.DataFrame(
        {
            "ID Sample": ["E1", "E2"],
            "ID Sampling point": ["SP1", "SP2"],
            "Start date & time": ["01/02/2012 08:00", "02/02/2012 08:00"],
            "Sample quality": ["CORRECT", "UNCERTAIN"],
        }
    )
    methods = pd.DataFrame(
        [
            ["MP_PH", "pH", "Wastewater - treated", ""],
            ["MP_EC", "Conductivity (25°C)", "Wastewater - treated", "µS/cm"],
            ["MP_CL", "Chloride", "Wastewater - raw", "mg/L"],
        ],
        columns=["ID Physico-chemical method", "Physico-chemical indicator", "Sample matrix", "Unit"],
    )
    physico = pd.DataFrame({"ID PC method": ["MP_PH", "MP_EC"]})
    result = inventory_from_frames(samples, methods, physico)
    assert result["sample_count"] == 2
    assert result["coverage"]["pH"]["treated_observed_method"] is True
    assert result["coverage"]["chloride"]["treated_observed_method"] is False
    assert result["treated_required_panel_complete"] is False


def test_inventory_counts_quality_and_date_failures() -> None:
    samples = pd.DataFrame(
        {
            "ID Sample": ["E1", "E2"],
            "ID Sampling point": ["SP1", "SP1"],
            "Start date & time": ["01/02/2012 08:00", "bad"],
            "Sample quality": ["CORRECT", None],
        }
    )
    methods = pd.DataFrame(columns=["ID Physico-chemical method", "Physico-chemical indicator", "Sample matrix", "Unit"])
    physico = pd.DataFrame(columns=["ID PC method"])
    result = inventory_from_frames(samples, methods, physico)
    assert result["date_parse_failures"] == 1
    assert result["sample_quality_counts"]["CORRECT"] == 1
    assert result["sample_quality_counts"]["MISSING"] == 1
