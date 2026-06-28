"""Tests for the read-only project-wide traceability endpoint (Phase 4A)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.safety import PROHIBITED_FINAL_DECISION_WORDS
from app.services.checklist_review_service import STARTER_RULE_PACK_ID
from tests.test_pdf_indexing import _make_pdf

PAGE_TEXT = (
    "Stormwater detention basin outlet structure design for the proposed "
    "subdivision. The outlet structure limits discharge to the downstream "
    "culvert during the design storm event for the contributing watershed."
)


def _create_project(client: TestClient, name: str = "Traceability Project") -> str:
    response = client.post(
        "/api/v1/projects",
        json={
            "project_name": name,
            "project_type": "Subdivision stormwater review",
            "jurisdiction": "Town of Riverton",
            "review_type": "Site plan stormwater review",
            "review_domain": "stormwater",
            "location_context": "Greenfield parcel",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["project_id"]


def _create_checklist(client: TestClient, project_id: str) -> str:
    response = client.post(
        f"/api/v1/projects/{project_id}/checklists/from-rule-pack",
        json={"rule_pack_id": STARTER_RULE_PACK_ID},
    )
    assert response.status_code == 201, response.text
    return response.json()["project_checklist_id"]


def _items(client: TestClient, project_id: str, checklist_id: str) -> list[dict]:
    response = client.get(
        f"/api/v1/projects/{project_id}/checklists/{checklist_id}/items"
    )
    assert response.status_code == 200, response.text
    return response.json()


def _upload_and_index(client: TestClient, project_id: str) -> tuple[str, int]:
    upload = client.post(
        f"/api/v1/projects/{project_id}/documents/upload",
        files={"file": ("plan.pdf", _make_pdf([PAGE_TEXT]), "application/pdf")},
        data={"document_type": "stormwater_report"},
    )
    assert upload.status_code == 201, upload.text
    document_id = upload.json()["document_id"]
    index = client.post(
        f"/api/v1/projects/{project_id}/documents/{document_id}/index-pdf"
    )
    assert index.status_code == 200, index.text
    return document_id, 1


def _link_evidence(
    client: TestClient, project_id: str, item_id: str, document_id: str, page: int
) -> None:
    response = client.post(
        f"/api/v1/projects/{project_id}/checklist-items/{item_id}/evidence-links",
        json={"document_id": document_id, "page_number": page},
    )
    assert response.status_code in (200, 201), response.text


def _traceability(client: TestClient, project_id: str) -> dict:
    response = client.get(f"/api/v1/projects/{project_id}/traceability")
    assert response.status_code == 200, response.text
    return response.json()


def _linked_project(client: TestClient) -> tuple[str, list[dict], str]:
    pid = _create_project(client)
    checklist_id = _create_checklist(client, pid)
    items = _items(client, pid, checklist_id)
    assert len(items) >= 2
    document_id, page = _upload_and_index(client, pid)
    _link_evidence(client, pid, items[0]["project_checklist_item_id"], document_id, page)
    return pid, items, items[0]["project_checklist_item_id"]


def test_traceability_returns_linked_and_unlinked_rows(client: TestClient) -> None:
    pid, items, linked_item_id = _linked_project(client)
    data = _traceability(client, pid)

    assert data["summary"]["total_checklist_items"] == len(items)
    assert data["summary"]["checklist_items_with_linked_evidence"] >= 1
    assert data["summary"]["checklist_items_without_linked_evidence"] >= 1
    assert data["summary"]["total_traceability_rows"] >= len(items)

    linked_rows = [
        r
        for r in data["rows"]
        if r["checklist_item_id"] == linked_item_id
        and r["relationship_type"] == "linked_evidence"
    ]
    assert linked_rows
    # Document/page citation context is present on the linked row.
    assert linked_rows[0]["document_id"] is not None
    assert linked_rows[0]["page_number"] is not None

    unlinked_rows = [
        r for r in data["rows"] if r["relationship_type"] == "no_linked_evidence_yet"
    ]
    assert unlinked_rows


def test_traceability_distinguishes_no_evidence_from_not_reviewed(
    client: TestClient,
) -> None:
    pid, items, linked_item_id = _linked_project(client)
    data = _traceability(client, pid)
    notes = {r["traceability_row_id"]: r["notes"] for r in data["rows"]}
    # Linked but not yet handed off -> not_reviewed.
    linked = [
        r
        for r in data["rows"]
        if r["checklist_item_id"] == linked_item_id
        and r["relationship_type"] == "linked_evidence"
    ]
    assert linked[0]["notes"] == "not_reviewed"
    # Unlinked items -> no_linked_evidence_yet (the project has indexed text).
    unlinked = [
        r for r in data["rows"] if r["relationship_type"] == "no_linked_evidence_yet"
    ]
    assert unlinked
    assert unlinked[0]["notes"] == "no_linked_evidence_yet"
    assert "not_reviewed" in notes.values()


def test_traceability_marks_not_enough_indexed_information(
    client: TestClient,
) -> None:
    # A project with checklist items but no indexed documents reports
    # not_enough_indexed_information rather than implying anything is unsupported.
    pid = _create_project(client, "No Index Project")
    checklist_id = _create_checklist(client, pid)
    _items(client, pid, checklist_id)
    data = _traceability(client, pid)
    assert data["has_indexed_information"] is False
    assert all(
        r["relationship_type"] == "no_linked_evidence_yet" for r in data["rows"]
    )
    assert any(
        r["notes"] == "not_enough_indexed_information" for r in data["rows"]
    )


def test_traceability_is_read_only(client: TestClient) -> None:
    pid, items, _ = _linked_project(client)
    findings_before = client.get(f"/api/v1/projects/{pid}/findings").json()
    first = _traceability(client, pid)
    second = _traceability(client, pid)
    findings_after = client.get(f"/api/v1/projects/{pid}/findings").json()
    # No new findings or row drift from calling the endpoint.
    assert len(findings_before) == len(findings_after)
    assert (
        first["summary"]["total_traceability_rows"]
        == second["summary"]["total_traceability_rows"]
    )


def test_traceability_has_limitations_and_no_banned_language(
    client: TestClient,
) -> None:
    pid, _, _ = _linked_project(client)
    response = client.get(f"/api/v1/projects/{pid}/traceability")
    data = response.json()
    assert data["limitations_note"]
    assert "does not determine whether a requirement is satisfied" in (
        data["limitations_note"]
    )
    blob = response.text.lower()
    for word in PROHIBITED_FINAL_DECISION_WORDS:
        assert word.lower() not in blob


def test_traceability_404_for_unknown_project(client: TestClient) -> None:
    assert (
        client.get("/api/v1/projects/proj_missing/traceability").status_code == 404
    )
