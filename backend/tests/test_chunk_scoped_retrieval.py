"""Tests for checklist- and finding-scoped retrieval over real-derived chunks."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.db import models
from app.db.database import SessionLocal
from app.services.page_chunking_service import REAL_DERIVED_CHUNK_PREFIX

from tests.test_chunk_evidence_retrieval import (
    _create_project,
    _index,
    _chunk,
    _make_pdf,
    _upload_pdf,
)


def _embed(client: TestClient, project_id: str) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-retrieval/embed-chunks"
    )
    assert response.status_code == 200, response.text
    return response.json()


def _insert_checklist_item(
    project_id: str, requirement: str, expected_evidence: str
) -> str:
    db = SessionLocal()
    try:
        item = models.ChecklistItem(
            checklist_item_id=f"chk_test_{project_id[-6:]}",
            project_id=project_id,
            review_domain="stormwater",
            category="stormwater",
            requirement=requirement,
            expected_evidence=expected_evidence,
            supporting_documents=[],
            risk_level="medium",
            applies_when="always",
            expected_status_for_brookside_meadows="needs_review",
        )
        db.add(item)
        db.commit()
        return item.checklist_item_id
    finally:
        db.close()


def _chunked_project(client: TestClient, pages: list[str]) -> tuple[str, str]:
    pid = _create_project(client, "Scoped Retrieval Project")
    did = _upload_pdf(client, pid, _make_pdf(pages))
    _index(client, pid, did)
    _chunk(client, pid, did)
    _embed(client, pid)
    return pid, did


def test_checklist_scoped_search_returns_real_derived_chunks(
    client: TestClient,
) -> None:
    pid, did = _chunked_project(
        client, ["Detention basin outlet structure and stormwater drainage."]
    )
    item_id = _insert_checklist_item(
        pid,
        requirement="Detention basin outlet structure sizing",
        expected_evidence="Outlet sizing detail",
    )
    response = client.post(
        f"/api/v1/projects/{pid}/evidence-retrieval/checklist/{item_id}"
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["query_type"] == "checklist_item"
    assert data["result_count"] >= 1
    assert data["results"][0]["chunk_id"].startswith(REAL_DERIVED_CHUNK_PREFIX)


def test_finding_scoped_search_returns_real_derived_chunks(
    client: TestClient,
) -> None:
    pid, did = _chunked_project(
        client, ["Detention basin outlet structure and stormwater drainage."]
    )
    finding = client.post(
        f"/api/v1/projects/{pid}/findings",
        json={
            "title": "Detention basin outlet structure needs reviewer confirmation",
            "category": "stormwater",
            "risk_level": "medium",
            "evidence_status": "needs_reviewer_confirmation",
            "evidence_to_find": "Detention basin outlet structure sizing",
            "reason_it_matters": "Outlet sizing affects discharge",
            "recommended_human_action": "Reviewer should confirm outlet sizing",
        },
    )
    assert finding.status_code == 201, finding.text
    finding_id = finding.json()["finding_id"]
    response = client.post(
        f"/api/v1/projects/{pid}/evidence-retrieval/findings/{finding_id}"
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["query_type"] == "finding_context"
    assert data["result_count"] >= 1
    assert data["results"][0]["chunk_id"].startswith(REAL_DERIVED_CHUNK_PREFIX)


def test_checklist_scoped_search_honest_when_no_chunks(client: TestClient) -> None:
    # A project with a checklist item but no real-derived chunks reports that
    # indexed chunk evidence is not available yet, never a false absence.
    pid = _create_project(client, "No Chunks Project")
    item_id = _insert_checklist_item(
        pid,
        requirement="Detention basin outlet structure sizing",
        expected_evidence="Outlet sizing detail",
    )
    response = client.post(
        f"/api/v1/projects/{pid}/evidence-retrieval/checklist/{item_id}"
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["result_count"] == 0
    assert "not available yet" in data["message"].lower()
    assert "not a finding about the document content" in data["message"].lower()
