from __future__ import annotations

import json
from pathlib import Path

import scripts.run_e3_mechanism_pilot as e3
from scripts.run_e3_mechanism_pilot import STATES, run


def _rows(*, ai_potable: float = 10.0, source: float = 20.0, seed: str = "seed-1", provenance: str = "prov-1") -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for day in ("2026-01-01", "2026-01-02"):
        for dc in ("dc-a", "dc-b"):
            rows.append({
                "date": day,
                "dc_id": dc,
                "seed": seed,
                "provenance_id": provenance,
                "ai_potable_ml": ai_potable,
                "ai_reclaimed_ml": 5,
                "source_withdrawal_ml": source,
                "incumbent_potable_ml": 30,
                "energy_kwh": 100,
                "ghg_kgco2e": 40,
                "cost": 2,
                "unmet_ml": 0,
                "sla": 1,
                "coc": 4,
                "wwtw_inflow_ml": 8,
                "wwtw_treated_ml": 7,
                "wwtw_peak_utilization": 0.5,
                "b2_ai_potable_ml": 15,
                "b2_source_withdrawal_ml": 25,
                "b2_incumbent_potable_ml": 35,
            })
    return rows


def _manifest(tmp_path: Path, *, rows_by_state: dict[str, list[dict[str, object]]] | None = None) -> Path:
    rows_by_state = rows_by_state or {state: _rows() for state in STATES}
    path = tmp_path / "e3_input.json"
    path.write_text(json.dumps({"runs": rows_by_state}, ensure_ascii=False), encoding="utf-8")
    return path


def test_paired_diagnostic_computes_deltas_estimands_and_hashes(tmp_path: Path) -> None:
    rows = {
        "Q0/Ls": _rows(ai_potable=10, source=20),
        "Q1/Ls": _rows(ai_potable=11, source=21),
        "Q0/Ld": _rows(ai_potable=8, source=18),
        "Q1/Ld": _rows(ai_potable=9, source=19),
    }
    payload = run(_manifest(tmp_path, rows_by_state=rows), tmp_path / "out")

    assert payload["status"] == "PILOT_ONLY"
    assert payload["diagnostic_status"] == "COMPLETED"
    assert payload["pilot_only"] is True
    assert payload["deltas"]["Delta_Q"]["Ls"]["ai_potable_ml"] == 4.0
    assert payload["deltas"]["Delta_L"]["Q0"]["source_withdrawal_ml"] == -8.0
    assert payload["deltas"]["Delta_QL"]["ai_potable_ml"] == 0.0
    assert payload["estimands"]["Q0/Ls"]["S_AI"] == 20.0
    assert payload["estimands"]["Q0/Ls"]["S_city"] == 20.0
    assert payload["estimands"]["Q0/Ls"]["eta_transfer"] == 1.0
    assert payload["estimands"]["Q0/Ls"]["incumbent_potable_delta"] == 20.0
    assert payload["output_hashes"]["state_metrics"].startswith("sha256:")
    assert payload["paired_row_count"] == 4
    assert payload["output_hashes"]["paired_rows"].startswith("sha256:")
    assert (tmp_path / "out" / "manifest.json").is_file()


def test_pair_key_mismatch_fails_closed(tmp_path: Path) -> None:
    rows = {state: _rows() for state in STATES}
    rows["Q1/Ld"] = _rows()[:-1]
    payload = run(_manifest(tmp_path, rows_by_state=rows), tmp_path / "out")

    assert payload["status"] == "NOT_READY"
    assert payload["diagnostic_status"] == "BLOCKED"
    assert any("paired date/dc keys" in reason for reason in payload["reasons"])
    assert payload["execution_performed"] is False


def test_eta_is_na_when_ai_saving_is_nonpositive(tmp_path: Path) -> None:
    rows = {state: _rows(ai_potable=20) for state in STATES}
    payload = run(_manifest(tmp_path, rows_by_state=rows), tmp_path / "out")

    assert payload["status"] == "PILOT_ONLY"
    assert payload["estimands"]["Q0/Ls"]["S_AI"] == -20.0
    assert payload["estimands"]["Q0/Ls"]["eta_transfer"] == "NA"


def test_formal_request_refuses_without_gates_and_reviews(tmp_path: Path) -> None:
    payload = run(_manifest(tmp_path), tmp_path / "formal", formal=True, repo_root=tmp_path)

    assert payload["status"] == "NOT_READY"
    assert payload["diagnostic_status"] == "BLOCKED"
    assert payload["formal_run_performed"] is False
    assert payload["execution_performed"] is False
    assert any("formal E3 run refused" in reason for reason in payload["reasons"])
    assert payload["state_metrics"] == {}


def test_formal_gate_refusal_happens_before_aggregation(tmp_path: Path, monkeypatch) -> None:
    def should_not_run(rows):
        raise AssertionError("formal preflight must refuse before aggregation")

    monkeypatch.setattr(e3, "_aggregate", should_not_run)
    payload = run(_manifest(tmp_path), tmp_path / "formal", formal=True, repo_root=tmp_path)

    assert payload["status"] == "NOT_READY"
    assert payload["execution_performed"] is False


def test_missing_common_seed_or_provenance_is_not_ready(tmp_path: Path) -> None:
    rows = {state: _rows() for state in STATES}
    for row in rows["Q1/Ls"]:
        row["seed"] = "different"
    payload = run(_manifest(tmp_path, rows_by_state=rows), tmp_path / "out")

    assert payload["status"] == "NOT_READY"
    assert any("seed" in reason for reason in payload["reasons"])
