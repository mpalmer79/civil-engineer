"""Tests for Production Foundations Sprint 7 response matrix and resubmittals.

These tests exercise the applicant response matrix, matrix items from findings
and checklist items, recorded applicant responses, document links, carry-forward,
resubmittal rounds, access control, and the review-support boundary. They confirm
that nothing is resolved or closed, no final-decision wording appears, and audit
metadata never carries full response text or secrets.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.safety import PROHIBITED_FINAL_DECISION_WORDS
from app.services.checklist_review_service import STARTER_RULE_PACK_ID
from tests.test_pdf_indexing import _make_pdf

BROOKSIDE_ID = "proj_brookside_meadows"


def _register(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"u_{uuid.uuid4().hex[:8]}@example.com",
            "display_name": "Reviewer",
            "password": "password123",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_project(client: TestClient, token: str) -> str:
    response = client.post(
        "/api/v1/projects",
        headers=_headers(token),
        json={
            "project_name": "Response Project",
            "project_type": "Subdivision",
            "jurisdiction": "Town",
            "review_type": "Review",
            "review_domain": "stormwater",
            "location_context": "Parcel",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["project_id"]


def _create_finding(client: TestClient, token: str, project_id: str) -> str:
    response = client.post(
        f"/api/v1/projects/{project_id}/findings",
        headers=_headers(token),
        json={
            "title": "Detention basin outlet needs reviewer confirmation",
            "category": "stormwater",
            "risk_level": "medium",
            "evidence_status": "needs_reviewer_confirmation",
            "evidence_to_find": "Outlet sizing detail",
            "reason_it_matters": "Downstream capacity",
            "recommended_human_action": "Reviewer confirms sizing",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["finding_id"]


def _create_matrix(client: TestClient, token: str, project_id: str) -> str:
    response = client.post(
        f"/api/v1/projects/{project_id}/response-matrices",
        headers=_headers(token),
        json={},
    )
    assert response.status_code == 201, response.text
    return response.json()["response_matrix_id"]


def _add_finding_item(
    client: TestClient, token: str, project_id: str, matrix_id: str, finding_id: str
) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/response-matrices/{matrix_id}/items/from-finding/{finding_id}",
        headers=_headers(token),
        json={},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _setup_matrix_with_item(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token)
    finding_id = _create_finding(client, token, project_id)
    matrix_id = _create_matrix(client, token, project_id)
    item = _add_finding_item(client, token, project_id, matrix_id, finding_id)
    return token, project_id, matrix_id, item


# ---------------------------------------------------------------------------
# Response matrix
# ---------------------------------------------------------------------------


def test_create_and_list_response_matrix(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token)
    matrix_id = _create_matrix(client, token, project_id)
    listed = client.get(
        f"/api/v1/projects/{project_id}/response-matrices", headers=_headers(token)
    )
    assert listed.status_code == 200
    assert any(m["response_matrix_id"] == matrix_id for m in listed.json())
    assert listed.json()[0]["status"] == "matrix_started"


def test_create_matrix_writes_audit(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token)
    _create_matrix(client, token, project_id)
    audit = client.get(
        f"/api/v1/projects/{project_id}/audit-events", headers=_headers(token)
    ).json()
    assert "response_matrix_created" in [e["event_type"] for e in audit]


def test_create_matrix_rejects_prohibited_language(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token)
    response = client.post(
        f"/api/v1/projects/{project_id}/response-matrices",
        headers=_headers(token),
        json={"name": "Plan approved matrix"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Matrix items
# ---------------------------------------------------------------------------


def test_add_finding_to_matrix(client: TestClient):
    token, project_id, matrix_id, item = _setup_matrix_with_item(client)
    assert item["source_finding_id"]
    assert item["applicant_response_status"] == "awaiting_applicant_response"
    assert item["reviewer_follow_up_status"] == "not_reviewed"


def test_add_checklist_item_to_matrix(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token)
    checklist = client.post(
        f"/api/v1/projects/{project_id}/checklists/from-rule-pack",
        headers=_headers(token),
        json={"rule_pack_id": STARTER_RULE_PACK_ID},
    ).json()
    item = client.get(
        f"/api/v1/projects/{project_id}/checklists/{checklist['project_checklist_id']}/items",
        headers=_headers(token),
    ).json()[0]
    matrix_id = _create_matrix(client, token, project_id)
    response = client.post(
        f"/api/v1/projects/{project_id}/response-matrices/{matrix_id}/items/from-checklist-item/{item['project_checklist_item_id']}",
        headers=_headers(token),
        json={},
    )
    assert response.status_code == 201, response.text
    assert response.json()["source_checklist_item_id"] == item[
        "project_checklist_item_id"
    ]


def test_add_finding_from_other_project_404(client: TestClient):
    token, project_id, matrix_id, _ = _setup_matrix_with_item(client)
    response = client.post(
        f"/api/v1/projects/{project_id}/response-matrices/{matrix_id}/items/from-finding/find_missing",
        headers=_headers(token),
        json={},
    )
    assert response.status_code == 404


def test_update_item_rejects_invalid_status(client: TestClient):
    token, project_id, _, item = _setup_matrix_with_item(client)
    response = client.patch(
        f"/api/v1/projects/{project_id}/response-matrix-items/{item['response_matrix_item_id']}",
        headers=_headers(token),
        json={"applicant_response_status": "resolved"},
    )
    assert response.status_code == 422


def test_update_item_rejects_prohibited_language(client: TestClient):
    token, project_id, _, item = _setup_matrix_with_item(client)
    response = client.patch(
        f"/api/v1/projects/{project_id}/response-matrix-items/{item['response_matrix_item_id']}",
        headers=_headers(token),
        json={"reviewer_note": "This item is approved and compliant"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Applicant response
# ---------------------------------------------------------------------------


def test_record_applicant_response(client: TestClient):
    token, project_id, _, item = _setup_matrix_with_item(client)
    response = client.post(
        f"/api/v1/projects/{project_id}/response-matrix-items/{item['response_matrix_item_id']}/applicant-response",
        headers=_headers(token),
        json={
            "applicant_response_text": "Revised outlet detail provided on sheet C-3.",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["applicant_response_status"] == "applicant_response_received"
    assert body["reviewer_follow_up_status"] == "needs_reviewer_confirmation"
    assert "Revised outlet detail" in body["applicant_response_text"]


def test_applicant_response_audit_excludes_full_text(client: TestClient):
    token, project_id, _, item = _setup_matrix_with_item(client)
    secret_text = "UNIQUE_RESPONSE_BODY_marker_12345 with extra detail"
    client.post(
        f"/api/v1/projects/{project_id}/response-matrix-items/{item['response_matrix_item_id']}/applicant-response",
        headers=_headers(token),
        json={"applicant_response_text": secret_text},
    )
    audit = client.get(
        f"/api/v1/projects/{project_id}/audit-events", headers=_headers(token)
    ).json()
    types = [e["event_type"] for e in audit]
    assert "applicant_response_recorded" in types
    blob = str(audit)
    assert "UNIQUE_RESPONSE_BODY_marker_12345" not in blob


def test_record_response_requires_text(client: TestClient):
    token, project_id, _, item = _setup_matrix_with_item(client)
    response = client.post(
        f"/api/v1/projects/{project_id}/response-matrix-items/{item['response_matrix_item_id']}/applicant-response",
        headers=_headers(token),
        json={"applicant_response_text": ""},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Document linking
# ---------------------------------------------------------------------------


def _upload(client: TestClient, token: str, project_id: str) -> str:
    response = client.post(
        f"/api/v1/projects/{project_id}/documents/upload",
        headers=_headers(token),
        files={"file": ("response.pdf", _make_pdf(["Revised"]), "application/pdf")},
        data={"document_type": "stormwater_report"},
    )
    assert response.status_code == 201, response.text
    return response.json()["document_id"]


def test_link_document_to_matrix_item(client: TestClient):
    token, project_id, _, item = _setup_matrix_with_item(client)
    document_id = _upload(client, token, project_id)
    response = client.post(
        f"/api/v1/projects/{project_id}/response-matrix-items/{item['response_matrix_item_id']}/documents/{document_id}",
        headers=_headers(token),
        json={"link_type": "applicant_response_document"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["document_id"] == document_id
    assert body["link_type"] == "applicant_response_document"
    # No storage key or raw path in the response.
    assert "storage_key" not in response.text
    assert "storage_path" not in response.text


def test_link_document_unknown_404(client: TestClient):
    token, project_id, _, item = _setup_matrix_with_item(client)
    response = client.post(
        f"/api/v1/projects/{project_id}/response-matrix-items/{item['response_matrix_item_id']}/documents/doc_missing",
        headers=_headers(token),
        json={},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Carry-forward
# ---------------------------------------------------------------------------


def test_carry_forward_matrix_item(client: TestClient):
    token, project_id, _, item = _setup_matrix_with_item(client)
    response = client.post(
        f"/api/v1/projects/{project_id}/response-matrix-items/{item['response_matrix_item_id']}/carry-forward",
        headers=_headers(token),
        json={},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["carry_forward_status"] == "carried_forward_for_review"
    assert body["carried_to_round_number"] == 2
    assert body["current_round_number"] == 2


def test_carry_forward_rejects_invalid_status(client: TestClient):
    token, project_id, _, item = _setup_matrix_with_item(client)
    response = client.post(
        f"/api/v1/projects/{project_id}/response-matrix-items/{item['response_matrix_item_id']}/carry-forward",
        headers=_headers(token),
        json={"carry_forward_status": "resolved"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Resubmittal rounds
# ---------------------------------------------------------------------------


def test_register_and_list_resubmittal_round(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token)
    response = client.post(
        f"/api/v1/projects/{project_id}/resubmittal-rounds",
        headers=_headers(token),
        json={"round_label": "First resubmittal", "submitted_by_name": "Design Firm"},
    )
    assert response.status_code == 201, response.text
    round_id = response.json()["resubmittal_round_id"]
    assert response.json()["status"] == "round_registered"
    rounds = client.get(
        f"/api/v1/projects/{project_id}/resubmittal-rounds", headers=_headers(token)
    )
    assert any(r["resubmittal_round_id"] == round_id for r in rounds.json())
    audit = client.get(
        f"/api/v1/projects/{project_id}/audit-events", headers=_headers(token)
    ).json()
    assert "resubmittal_round_registered" in [e["event_type"] for e in audit]


def test_link_document_to_round_and_summary(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token)
    document_id = _upload(client, token, project_id)
    round_id = client.post(
        f"/api/v1/projects/{project_id}/resubmittal-rounds",
        headers=_headers(token),
        json={"round_label": "First resubmittal"},
    ).json()["resubmittal_round_id"]
    link = client.post(
        f"/api/v1/projects/{project_id}/resubmittal-rounds/{round_id}/documents/{document_id}",
        headers=_headers(token),
        json={},
    )
    assert link.status_code == 201, link.text
    assert link.json()["document_count"] == 1
    assert link.json()["status"] == "documents_received"
    summary = client.get(
        f"/api/v1/projects/{project_id}/resubmittal-rounds/{round_id}/summary",
        headers=_headers(token),
    )
    assert summary.status_code == 200
    assert summary.json()["document_count"] == 1


def test_carry_forward_items_to_round(client: TestClient):
    token, project_id, matrix_id, item = _setup_matrix_with_item(client)
    round_id = client.post(
        f"/api/v1/projects/{project_id}/resubmittal-rounds",
        headers=_headers(token),
        json={"round_label": "Second round", "response_matrix_id": matrix_id},
    ).json()["resubmittal_round_id"]
    response = client.post(
        f"/api/v1/projects/{project_id}/resubmittal-rounds/{round_id}/carry-forward-items",
        headers=_headers(token),
        json={"matrix_item_ids": [item["response_matrix_item_id"]]},
    )
    assert response.status_code == 201, response.text
    assert response.json()["carried_forward_item_count"] == 1
    audit = client.get(
        f"/api/v1/projects/{project_id}/audit-events", headers=_headers(token)
    ).json()
    assert "resubmittal_items_carried_forward" in [e["event_type"] for e in audit]


def test_register_round_rejects_invalid_status(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token)
    response = client.post(
        f"/api/v1/projects/{project_id}/resubmittal-rounds",
        headers=_headers(token),
        json={"status": "approved"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------


def test_read_only_user_cannot_mutate(client: TestClient):
    owner = _register(client)
    token = owner["access_token"]
    project_id = _create_project(client, token)
    matrix_id = _create_matrix(client, token, project_id)
    viewer = _register(client)
    client.post(
        f"/api/v1/projects/{project_id}/access/grant",
        headers=_headers(token),
        json={"access_level": "read_only", "user_id": viewer["user"]["user_id"]},
    )
    viewer_headers = _headers(viewer["access_token"])
    # The read_only viewer can read.
    read = client.get(
        f"/api/v1/projects/{project_id}/response-matrices", headers=viewer_headers
    )
    assert read.status_code == 200
    # The read_only viewer cannot create a matrix or register a round.
    create = client.post(
        f"/api/v1/projects/{project_id}/response-matrices",
        headers=viewer_headers,
        json={},
    )
    assert create.status_code == 403
    register = client.post(
        f"/api/v1/projects/{project_id}/resubmittal-rounds",
        headers=viewer_headers,
        json={},
    )
    assert register.status_code == 403


def test_unauthorized_user_cannot_view_matrix(client: TestClient):
    owner = _register(client)
    token = owner["access_token"]
    project_id = _create_project(client, token)
    _create_matrix(client, token, project_id)
    other = _register(client)
    response = client.get(
        f"/api/v1/projects/{project_id}/response-matrices",
        headers=_headers(other["access_token"]),
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Security and regression
# ---------------------------------------------------------------------------


def test_no_prohibited_wording_in_responses(client: TestClient):
    token, project_id, matrix_id, item = _setup_matrix_with_item(client)
    detail = client.get(
        f"/api/v1/projects/{project_id}/response-matrices/{matrix_id}",
        headers=_headers(token),
    )
    blob = detail.text.lower()
    for word in PROHIBITED_FINAL_DECISION_WORDS:
        assert word not in blob
    for word in ("resolved", "closed", "noncompliant", "passed review"):
        assert word not in blob


def test_update_item_get_item_and_list_items(client: TestClient):
    token, project_id, matrix_id, item = _setup_matrix_with_item(client)
    item_id = item["response_matrix_item_id"]
    update = client.patch(
        f"/api/v1/projects/{project_id}/response-matrix-items/{item_id}",
        headers=_headers(token),
        json={
            "reviewer_comment_draft": "Reviewer requests the revised outlet detail",
            "reviewer_follow_up_status": "needs_applicant_follow_up",
        },
    )
    assert update.status_code == 200, update.text
    assert update.json()["reviewer_follow_up_status"] == "needs_applicant_follow_up"
    single = client.get(
        f"/api/v1/projects/{project_id}/response-matrix-items/{item_id}",
        headers=_headers(token),
    )
    assert single.status_code == 200
    items = client.get(
        f"/api/v1/projects/{project_id}/response-matrices/{matrix_id}/items",
        headers=_headers(token),
    )
    assert items.status_code == 200
    assert len(items.json()) == 1
    detail = client.get(
        f"/api/v1/projects/{project_id}/response-matrices/{matrix_id}",
        headers=_headers(token),
    )
    assert detail.status_code == 200
    assert len(detail.json()["items"]) == 1


def test_get_round_and_filter_items_by_status(client: TestClient):
    token, project_id, matrix_id, item = _setup_matrix_with_item(client)
    round_id = client.post(
        f"/api/v1/projects/{project_id}/resubmittal-rounds",
        headers=_headers(token),
        json={"round_label": "Round detail check"},
    ).json()["resubmittal_round_id"]
    got = client.get(
        f"/api/v1/projects/{project_id}/resubmittal-rounds/{round_id}",
        headers=_headers(token),
    )
    assert got.status_code == 200
    filtered = client.get(
        f"/api/v1/projects/{project_id}/response-matrices/{matrix_id}/items",
        headers=_headers(token),
        params={"applicant_response_status": "awaiting_applicant_response"},
    )
    assert filtered.status_code == 200
    assert all(
        i["applicant_response_status"] == "awaiting_applicant_response"
        for i in filtered.json()
    )


def test_unauthenticated_matrix_requires_login_under_strict(client: TestClient):
    from app.core.config import get_settings

    owner = _register(client)
    token = owner["access_token"]
    project_id = _create_project(client, token)
    settings = get_settings()
    old = settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS
    settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS = True
    try:
        response = client.get(
            f"/api/v1/projects/{project_id}/response-matrices"
        )
        assert response.status_code == 401
    finally:
        settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS = old


def test_health_and_demo_still_work(client: TestClient):
    assert client.get("/health").status_code == 200
    assert client.get(f"/api/v1/projects/{BROOKSIDE_ID}").status_code == 200
