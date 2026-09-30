from scripts.acquire_wqp_chemistry import PARAMETERS, normalize_tables


def test_normalize_tables_joins_complete_activity_and_ignores_non_numeric_duplicate() -> None:
    rows = {
        parameter: [
            {
                "ActivityIdentifier": "A1",
                "MonitoringLocationIdentifier": "USGS-TEST",
                "ActivityStartDate": "2020-01-02",
                "ResultMeasureValue": str(index + 1),
            }
        ]
        for index, parameter in enumerate(PARAMETERS)
    }
    rows["Ca_mg_l"].insert(0, {"ActivityIdentifier": "A1", "ResultMeasureValue": "<0.1"})
    rows["pH"].append({"ActivityIdentifier": "A2", "ResultMeasureValue": "7.1"})

    output = normalize_tables(rows)

    assert len(output) == 1
    assert output[0]["sample_id"] == "A1"
    assert output[0]["site_id"] == "USGS-TEST"
    assert output[0]["Ca_mg_l"] == str(list(PARAMETERS).index("Ca_mg_l") + 1)


def test_normalize_tables_requires_all_parameters() -> None:
    rows = {parameter: [] for parameter in PARAMETERS}
    rows["pH"] = [{"ActivityIdentifier": "A1", "ResultMeasureValue": "7"}]
    try:
        normalize_tables(rows)
    except ValueError as exc:
        assert "no complete samples" in str(exc)
    else:
        raise AssertionError("expected incomplete WQP tables to be rejected")
