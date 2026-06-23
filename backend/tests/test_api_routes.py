"""API route count and shape tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

PROJECT_ID = "proj_brookside_meadows"


def test_documents_endpoint_returns_19(client: TestClient) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}/documents")
    assert response.status_code == 200
    assert len(response.json()) == 19


def test_single_document_lookup(client: TestClient) -> None:
    response = client.get("/api/v1/documents/doc_stormwater_report")
    assert response.status_code == 200
    assert response.json()["document_type"] == "stormwater_management_report"


def test_checklist_endpoint_returns_19(client: TestClient) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}/checklist")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 19
    assert all(item["review_domain"] == "stormwater" for item in items)


def test_single_checklist_item_lookup(client: TestClient) -> None:
    response = client.get("/api/v1/checklist/chk_infiltration_testing")
    assert response.status_code == 200
    assert (
        response.json()["expected_status_for_brookside_meadows"] == "missing"
    )


def test_findings_endpoint_returns_10(client: TestClient) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}/findings")
    assert response.status_code == 200
    assert len(response.json()) == 10


def test_audit_endpoint_returns_events(client: TestClient) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}/audit-events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 10
    assert all(event["project_id"] == PROJECT_ID for event in events)


def test_evaluation_endpoint_returns_8(client: TestClient) -> None:
    response = client.get("/api/v1/evaluation-cases")
    assert response.status_code == 200
    assert len(response.json()) == 8


def test_project_evaluation_endpoint_returns_8(client: TestClient) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}/evaluation-cases")
    assert response.status_code == 200
    assert len(response.json()) == 8


def test_hotspots_endpoint_returns_10(client: TestClient) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}/hotspots")
    assert response.status_code == 200
    assert len(response.json()) == 10


def test_unknown_project_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/projects/proj_does_not_exist")
    assert response.status_code == 404
