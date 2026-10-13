from __future__ import annotations

import pandas as pd

from scripts.build_figshare_reclaimed_water_candidate import CANONICAL_COLUMNS, normalize_frame


def test_normalize_frame_computes_charge_balance_and_nd_values() -> None:
    row = ["RW", 2120, 8.17, 13.5, 0.36, 4.56, 8.85, 2.28, 3.10, 5.28, 5.81, 0.52, 0.05, "ND", "ND", "ND", "ND"]
    payload = normalize_frame(pd.DataFrame([row], columns=CANONICAL_COLUMNS))
    assert payload[0]["sample_id"] == "FIGSHARE-28948753-RW"
    assert payload[0]["pb_mg_l"] is None
    assert payload[0]["charge_balance"]["status"] == "PASS_SCREEN"
    assert payload[0]["charge_balance"]["cation_meq_l"] > payload[0]["charge_balance"]["anion_meq_l"]


def test_normalize_frame_rejects_wrong_column_count() -> None:
    frame = pd.DataFrame([["RW"]], columns=["resource"])
    try:
        normalize_frame(frame)
    except ValueError as error:
        assert "Expected 17 columns" in str(error)
    else:
        raise AssertionError("wrong column count should be rejected")


def test_sample_id_strips_source_markup() -> None:
    row = ["BW (5 g·L<sup>-1</sup>)", 9432, 8.44, 87, 0.07, 2.28, 90.9, 0.92, 0.77, 1.14, 66.86, 1.18, 0.02, "ND", "ND", "ND", "ND"]
    payload = normalize_frame(pd.DataFrame([row], columns=CANONICAL_COLUMNS))
    assert payload[0]["sample_id"] == "FIGSHARE-28948753-BW_5_g_L_1"
