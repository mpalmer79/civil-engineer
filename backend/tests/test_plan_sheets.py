"""Phase 6 plan sheet, CAD-aware metadata, and plan consistency tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.safety import contains_prohibited_language

PROJECT_ID = "proj_brookside_meadows"


def test_plan_sheets_are_seeded(client: TestClient) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}/plan-sheets")
    assert response.status_code == 200
    sheets = response.json()
    assert len(sheets) == 12
    numbers = {s["sheet_number"] for s in sheets}
    assert "C-3.0" in numbers
    assert "C-3.1" in numbers


def test_plan_sheet_summary_counts(client: TestClient) -> None:
    summary = client.get(
        f"/api/v1/projects/{PROJECT_ID}/plan-sheets/summary"
    ).json()
    assert summary["total_sheets"] == 12
    assert summary["missing_or_referenced_not_included_sheets"] >= 1
    assert "C-3.1" in summary["missing_sheet_numbers"]
    assert summary["cad_metadata_records"] == 16


def test_c31_is_referenced_not_included(client: TestClient) -> None:
    response = client.get("/api/v1/plan-sheets/sheet_c31")
    assert response.status_code == 200
    assert response.json()["status"] == "referenced_not_included"


def test_cad_metadata_is_seeded(client: TestClient) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}/cad-metadata")
    assert response.status_code == 200
    assert len(response.json()) == 16


def test_cad_metadata_filter_by_entity_type(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/projects/{PROJECT_ID}/cad-metadata?entity_type=basin"
    )
    assert response.status_code == 200
    basins = response.json()
    assert len(basins) == 4
    assert all(b["entity_type"] == "basin" for b in basins)
    labels = {b["entity_label"] for b in basins}
    assert {"Basin A", "Basin 1"} <= labels


def test_cad_metadata_listed_by_sheet(client: TestClient) -> None:
    response = client.get("/api/v1/plan-sheets/sheet_c30/cad-metadata")
    assert response.status_code == 200
    records = response.json()
    assert len(records) >= 1
    assert all(r["sheet_id"] == "sheet_c30" for r in records)


def test_plan_references_are_seeded(client: TestClient) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}/plan-references")
    assert response.status_code == 200
    assert len(response.json()) == 11


def test_plan_reference_inconsistencies(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/projects/{PROJECT_ID}/plan-references/inconsistencies"
    )
    assert response.status_code == 200
    inconsistent = response.json()
    assert len(inconsistent) >= 1
    statuses = {r["consistency_status"] for r in inconsistent}
    assert "missing_target" in statuses
    assert "conflicting_label" in statuses


def test_plan_consistency_check_creates_findings(client: TestClient) -> None:
    response = client.post(
        f"/api/v1/projects/{PROJECT_ID}/plan-consistency-check"
    )
    assert response.status_code == 200
    findings = response.json()
    assert len(findings) == 6
    types = {f["finding_type"] for f in findings}
    assert "missing_referenced_sheet" in types
    assert "conflicting_label" in types


def test_plan_consistency_findings_require_human_review(
    client: TestClient,
) -> None:
    client.post(f"/api/v1/projects/{PROJECT_ID}/plan-consistency-check")
    findings = client.get(
        f"/api/v1/projects/{PROJECT_ID}/plan-consistency-findings"
    ).json()
    assert findings
    for f in findings:
        assert f["status"] == "requires_human_review"


def test_plan_consistency_check_is_idempotent(client: TestClient) -> None:
    first = client.post(
        f"/api/v1/projects/{PROJECT_ID}/plan-consistency-check"
    ).json()
    second = client.post(
        f"/api/v1/projects/{PROJECT_ID}/plan-consistency-check"
    ).json()
    assert len(first) == len(second) == 6


def test_single_plan_finding_endpoint(client: TestClient) -> None:
    findings = client.get(
        f"/api/v1/projects/{PROJECT_ID}/plan-consistency-findings"
    ).json()
    fid = findings[0]["plan_finding_id"]
    response = client.get(f"/api/v1/plan-consistency-findings/{fid}")
    assert response.status_code == 200
    assert response.json()["plan_finding_id"] == fid


def test_plan_consistency_check_writes_audit_events(client: TestClient) -> None:
    client.post(f"/api/v1/projects/{PROJECT_ID}/plan-consistency-check")
    events = client.get(
        f"/api/v1/projects/{PROJECT_ID}/audit-events"
    ).json()
    types = {e["event_type"] for e in events}
    assert "plan_consistency_check_started" in types
    assert "plan_sheet_index_loaded" in types
    assert "cad_metadata_loaded" in types
    assert "plan_reference_evaluated" in types
    assert "plan_consistency_finding_created" in types
    assert "plan_consistency_check_completed" in types


def test_no_prohibited_language_in_plan_findings(client: TestClient) -> None:
    findings = client.get(
        f"/api/v1/projects/{PROJECT_ID}/plan-consistency-findings"
    ).json()
    for f in findings:
        assert not contains_prohibited_language(f["title"])
        assert not contains_prohibited_language(f["summary"])
        assert not contains_prohibited_language(f["recommended_human_action"])
        assert not contains_prohibited_language(f["status"])
        assert f["finding_type"] != "approved"


def test_plan_consistency_summary_endpoint(client: TestClient) -> None:
    summary = client.get(
        f"/api/v1/projects/{PROJECT_ID}/plan-consistency-summary"
    ).json()
    assert summary["total_findings"] == 6
    assert summary["missing_sheet_count"] >= 1
    assert summary["conflicting_label_count"] >= 1


def test_unknown_project_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/projects/proj_missing/plan-sheets")
    assert response.status_code == 404
