"""Tests for chunk auto-link suggestions to checklist items and findings."""

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
from tests.test_chunk_scoped_retrieval import _embed, _insert_checklist_item


def _suggest(client: TestClient, project_id: str) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-retrieval/suggest-links"
    )
    assert response.status_code == 200, response.text
    return response.json()


def _chunked_project(client: TestClient, pages: list[str]) -> tuple[str, str]:
    pid = _create_project(client, "Autolink Project")
    did = _upload_pdf(client, pid, _make_pdf(pages))
    _index(client, pid, did)
    _chunk(client, pid, did)
    _embed(client, pid)
    return pid, did


def _create_finding(client: TestClient, pid: str, title: str, evidence: str) -> str:
    response = client.post(
        f"/api/v1/projects/{pid}/findings",
        json={
            "title": title,
            "category": "stormwater",
            "risk_level": "medium",
            "evidence_status": "needs_reviewer_confirmation",
            "evidence_to_find": evidence,
            "reason_it_matters": "Matters for review",
            "recommended_human_action": "Reviewer should confirm",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["finding_id"]


def test_relevant_chunk_receives_checklist_and_finding_suggestions(
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
    finding_id = _create_finding(
        client,
        pid,
        "Detention basin outlet structure",
        "Detention basin outlet structure sizing",
    )

    summary = _suggest(client, pid)
    assert summary["chunks_with_suggestions"] >= 1
    assert summary["checklist_links_added"] >= 1
    assert summary["finding_links_added"] >= 1

    # All suggestions are for real-derived chunks only.
    for suggestion in summary["suggestions"]:
        assert suggestion["chunk_id"].startswith(REAL_DERIVED_CHUNK_PREFIX)

    # The links are persisted on the chunk's related arrays as suggestions.
    chunks = client.get(f"/api/v1/documents/{did}/chunks").json()
    linked = [c for c in chunks if item_id in c["related_checklist_items"]]
    assert linked
    finding_linked = [c for c in chunks if finding_id in c["related_findings"]]
    assert finding_linked


def test_noisy_match_is_excluded(client: TestClient) -> None:
    pid, did = _chunked_project(
        client, ["Detention basin outlet structure and stormwater drainage."]
    )
    # An unrelated checklist item about a different topic should not be linked.
    unrelated = _insert_checklist_item(
        pid,
        requirement="Landscaping plant species list and irrigation schedule",
        expected_evidence="Planting plan",
    )
    _suggest(client, pid)
    chunks = client.get(f"/api/v1/documents/{did}/chunks").json()
    for chunk in chunks:
        assert unrelated not in chunk["related_checklist_items"]


def test_suggestions_do_not_change_finding_review_status(
    client: TestClient,
) -> None:
    pid, did = _chunked_project(
        client, ["Detention basin outlet structure and stormwater drainage."]
    )
    finding_id = _create_finding(
        client,
        pid,
        "Detention basin outlet structure",
        "Detention basin outlet structure sizing",
    )
    before = client.get(f"/api/v1/findings/{finding_id}").json()
    _suggest(client, pid)
    after = client.get(f"/api/v1/findings/{finding_id}").json()
    assert after["human_review_status"] == before["human_review_status"]


def test_seeded_chunks_are_not_modified(client: TestClient) -> None:
    # Running suggestions for a user project never touches seeded demo chunks in
    # the Brookside project.
    pid, did = _chunked_project(
        client, ["Detention basin outlet structure and stormwater drainage."]
    )
    _insert_checklist_item(
        pid,
        requirement="Detention basin outlet structure sizing",
        expected_evidence="Outlet sizing detail",
    )
    before = client.get(
        "/api/v1/projects/proj_brookside_meadows/chunks"
    ).json()
    _suggest(client, pid)
    after = client.get(
        "/api/v1/projects/proj_brookside_meadows/chunks"
    ).json()
    assert before == after
