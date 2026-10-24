from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts import audit_water_balance_closure as closure


def test_closure_cli_returns_zero_after_writing_pass_report(tmp_path: Path, monkeypatch) -> None:
    timeseries = tmp_path / "timeseries" / "co" / "cap_0000"
    timeseries.mkdir(parents=True)
    pd.DataFrame(
        {
            "storage_ml": [0.0, 10.0, 15.0],
            "inflow_ml": [0.0, 10.0, 5.0],
            "outflow_ml": [0.0, 0.0, 0.0],
            "loss_ml": [0.0, 0.0, 0.0],
            "delivered_ml": [1.0, 2.0, 3.0],
            "potable_delivered_ml": [0.5, 1.0, 1.5],
            "reuse_delivered_ml": [0.5, 1.0, 1.5],
        }
    ).to_csv(timeseries / "system_daily.csv", index=False)
    output = tmp_path / "closure.csv"
    monkeypatch.setattr(closure, "TS", tmp_path / "timeseries")
    monkeypatch.setattr(closure, "OUT", output)

    assert closure.main() == 0
    assert output.exists()
    report = pd.read_csv(output)
    assert set(report["是否满足<=5%"].astype(str)) == {"PASS"}
