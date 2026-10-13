from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_r10a_quality_invariants import run_audit


def test_r10a_quality_audit_records_internal_closure_and_response(tmp_path: Path) -> None:
    output = tmp_path / "r10a.json"
    payload = run_audit(Path(__file__).resolve().parents[1], output)

    assert payload["status"] == "PASS_INTERNAL_DIAGNOSTIC"
    assert payload["gate_classification"] == "diagnostic_only"
    assert payload["formal_g2_or_g3_evidence"] is False
    assert all(payload["checks"].values())
    assert output.is_file()
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["status"] == payload["status"]
