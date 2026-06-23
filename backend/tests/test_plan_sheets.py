"""Phase 6 plan sheet and CAD-aware review tests.

These tests prove sheet indexing, missing sheet detection, CAD metadata
filtering, reference consistency, the plan consistency check and findings,
audit events, and the safety language boundary for the new plan endpoints.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.safety import (
    ALLOWED_PLAN_FINDING_STATUSES,
    ALLOWED_PLAN_FINDING_TYPES,
    ALLOWED_PLAN_REFERENCE_STATUSES,
    ALLOWED_PLAN_SHEET_STATUSES,
    HUMAN_REVIEW_STATUSES,
    contains_prohibited_language,
)

PROJECT_ID = "proj_brookside_meadows"
PREFIX = f"/api/v1/projects/{PROJECT_ID}"


def test_plan_sheets_are_seeded(client: TestClient) -> None:
    sheets = client.get(f"{PREFIX}/plan-sheets").json()
    assert len(sheets) == 12
    numbers = {s["sheet_number"] for s in sheets}
    assert {"C-0.0", "C-3.0", "C-3.1", "C-5.1", "D-1.0"} <= numbers
    for sheet in sheets:
        assert sheet["status"] in ALLOWED_PLAN_SHEET_STATUSES


def test_plan_sheet_summary_counts(client: TestClient) -> None:
    summary = client.get(f"{PREFIX}/plan-sheets/summary").json()
    assert summary["total_sheets"] == 12
    assert summary["cad_metadata_records"] == 16
    # C-3.1 is referenced but not included.
    assert summary["missing_or_referenced_not_included"] >= 1
    assert "sheet_c31" in summary["missing_sheet_ids"]


def test_c31_is_referenced_not_included(client: TestClient) -> None:
    sheet = client.get("/api/v1/plan-sheets/sheet_c31").json()
    assert sheet["sheet_number"] == "C-3.1"
    assert sheet["status"] == "referenced_not_included"


def test_cad_metadata_is_seeded(client: TestClient) -> None:
    records = client.get(f"{PREFIX}/cad-metadata").json()
    assert len(records) == 16
    labels = {r["entity_label"] for r in records}
    assert {"Basin A", "Basin 1", "Pipe P-12", "Outfall 1", "Lot 17"} <= labels


def test_cad_metadata_filter_by_entity_type(client: TestClient) -> None:
    basins = client.get(f"{PREFIX}/cad-metadata?entity_type=basin").json()
    assert len(basins) >= 1
    assert all(r["entity_type"] == "basin" for r in basins)
    roads = client.get(f"{PREFIX}/cad-metadata?entity_type=road").json()
    assert all(r["entity_type"] == "road" for r in roads)


def test_cad_metadata_by_sheet(client: TestClient) -> None:
    records = client.get("/api/v1/plan-sheets/sheet_c40/cad-metadata").json()
    assert len(records) >= 1
    assert all(r["sheet_id"] == "sheet_c40" for r in records)
    labels = {r["entity_label"] for r in records}
    assert "Pipe P-12" in labels


def test_plan_references_are_seeded(client: TestClient) -> None:
    refs = client.get(f"{PREFIX}/plan-references").json()
    assert len(refs) == 11
    for ref in refs:
        assert ref["consistency_status"] in ALLOWED_PLAN_REFERENCE_STATUSES


def test_plan_inconsistencies_endpoint(client: TestClient) -> None:
    refs = client.get(f"{PREFIX}/plan-references/inconsistencies").json()
    # Six seeded references are missing, conflicting, or unclear.
    assert len(refs) == 6
    statuses = {r["consistency_status"] for r in refs}
    assert "missing_target" in statuses
    assert "conflicting_label" in statuses


def test_plan_consistency_check_creates_findings(client: TestClient) -> None:
    result = client.post(f"{PREFIX}/plan-consistency-check")
    assert result.status_code == 200
    summary = result.json()
    assert summary["plan_consistency_findings"] == 6
    assert summary["conflicting_label_count"] >= 1
    assert summary["missing_referenced_sheet_count"] >= 1

    findings = client.get(f"{PREFIX}/plan-consistency-findings").json()
    assert len(findings) == 6
    for finding in findings:
        assert finding["finding_type"] in ALLOWED_PLAN_FINDING_TYPES
        assert finding["status"] in ALLOWED_PLAN_FINDING_STATUSES


def test_plan_findings_require_human_review(client: TestClient) -> None:
    findings = client.get(f"{PREFIX}/plan-consistency-findings").json()
    assert len(findings) == 6
    for finding in findings:
        assert finding["status"] in HUMAN_REVIEW_STATUSES
        assert finding["status"] == "requires_human_review"


def test_plan_consistency_check_writes_audit_events(client: TestClient) -> None:
    client.post(f"{PREFIX}/plan-consistency-check")
    events = client.get(f"{PREFIX}/audit-events").json()
    event_types = {e["event_type"] for e in events}
    assert "plan_consistency_check_started" in event_types
    assert "plan_sheet_index_loaded" in event_types
    assert "cad_metadata_loaded" in event_types
    assert "plan_reference_evaluated" in event_types
    assert "plan_consistency_finding_created" in event_types
    assert "plan_consistency_check_completed" in event_types


def test_single_plan_finding_endpoint(client: TestClient) -> None:
    findings = client.get(f"{PREFIX}/plan-consistency-findings").json()
    first = findings[0]["plan_finding_id"]
    detail = client.get(f"/api/v1/plan-consistency-findings/{first}").json()
    assert detail["plan_finding_id"] == first


def test_no_plan_endpoint_returns_prohibited_language(client: TestClient) -> None:
    payloads = [
        client.get(f"{PREFIX}/plan-sheets").json(),
        client.get(f"{PREFIX}/cad-metadata").json(),
        client.get(f"{PREFIX}/plan-references").json(),
        client.get(f"{PREFIX}/plan-consistency-findings").json(),
    ]
    for records in payloads:
        for record in records:
            for key in ("status", "consistency_status", "title", "finding_type"):
                value = record.get(key)
                assert not contains_prohibited_language(value), (key, value)
