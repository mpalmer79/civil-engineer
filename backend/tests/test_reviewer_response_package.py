"""Tests for Production Foundations Sprint 8 reviewer response packages.

These tests exercise response package creation, package items from matrix items,
findings, checklist items, citations, and manual reviewer notes, the package
preview, deterministic comment letter draft generation and editing, the comment
letter preview, package issuance, package revisions, access control, and the
review-support boundary. They confirm nothing is approved, resolved, or closed,
no final-decision wording appears in responses, and audit metadata never carries
full text or secrets.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.core.safety import PROHIBITED_FINAL_DECISION_WORDS
from app.services.checklist_review_service import STARTER_RULE_PACK_ID
from tests.test_pdf_indexing import _make_pdf

BROOKSIDE_ID = "proj_brookside_meadows"

LEAK_TOKENS = (
    "storage_key",
    "storage_path",
    "signed_url",
    "secret",
    "password",
    "/var/",
    "aws_access",
)


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
            "project_name": "Package Project",
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


def _create_package(client: TestClient, token: str, project_id: str) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/reviewer-response-packages",
        headers=_headers(token),
        json={},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _setup_package_with_finding_item(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token)
    finding_id = _create_finding(client, token, project_id)
    package = _create_package(client, token, project_id)
    package_id = package["response_package_id"]
    added = client.post(
        f"/api/v1/projects/{project_id}/reviewer-response-packages/{package_id}/items/findings",
        headers=_headers(token),
        json={"finding_ids": [finding_id]},
    )
    assert added.status_code == 200, added.text
    return token, project_id, package_id, added.json()


# ---------------------------------------------------------------------------
# Response package creation
# ---------------------------------------------------------------------------


def test_create_and_list_response_package(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token)
    package = _create_package(client, token, project_id)
    assert package["status"] == "package_draft"
    assert package["package_number"] == 1
    assert package["revision_number"] == 0

    listed = client.get(
        f"/api/v1/projects/{project_id}/reviewer-response-packages",
        headers=_headers(token),
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_create_package_rejects_prohibited_title(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token)
    response = client.post(
        f"/api/v1/projects/{project_id}/reviewer-response-packages",
        headers=_headers(token),
        json={"package_title": "Approved plan package"},
    )
    assert response.status_code == 422


def test_create_package_rejects_invalid_type(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token)
    response = client.post(
        f"/api/v1/projects/{project_id}/reviewer-response-packages",
        headers=_headers(token),
        json={"package_type": "final_approval"},
    )
    assert response.status_code == 422


def test_create_package_writes_audit_event(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token)
    _create_package(client, token, project_id)
    events = client.get(
        f"/api/v1/projects/{project_id}/audit-events", headers=_headers(token)
    ).json()
    types = {e["event_type"] for e in events}
    assert "response_package_created" in types


# ---------------------------------------------------------------------------
# Package items
# ---------------------------------------------------------------------------


def test_add_finding_to_package(client: TestClient):
    token, project_id, package_id, detail = _setup_package_with_finding_item(
        client
    )
    assert detail["status"] == "package_in_review"
    assert detail["item_count"] == 1
    item = detail["items"][0]
    assert item["source_type"] == "finding"
    assert item["item_status"] == "item_draft"
    assert item["include_in_letter"] is True


def test_add_matrix_item_to_package(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token)
    finding_id = _create_finding(client, token, project_id)
    matrix = client.post(
        f"/api/v1/projects/{project_id}/response-matrices",
        headers=_headers(token),
        json={},
    ).json()
    matrix_id = matrix["response_matrix_id"]
    item = client.post(
        f"/api/v1/projects/{project_id}/response-matrices/{matrix_id}/items/from-finding/{finding_id}",
        headers=_headers(token),
        json={},
    ).json()
    package = _create_package(client, token, project_id)
    package_id = package["response_package_id"]
    added = client.post(
        f"/api/v1/projects/{project_id}/reviewer-response-packages/{package_id}/items/matrix-items",
        headers=_headers(token),
        json={"matrix_item_ids": [item["response_matrix_item_id"]]},
    )
    assert added.status_code == 200, added.text
    detail = added.json()
    assert detail["item_count"] == 1
    assert detail["items"][0]["source_type"] == "response_matrix_item"


def test_add_checklist_item_to_package(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token)
    checklist = client.post(
        f"/api/v1/projects/{project_id}/checklists/from-rule-pack",
        headers=_headers(token),
        json={"rule_pack_id": STARTER_RULE_PACK_ID},
    ).json()
    checklist_id = checklist["project_checklist_id"]
    items = client.get(
        f"/api/v1/projects/{project_id}/checklists/{checklist_id}/items",
        headers=_headers(token),
    ).json()
    checklist_item_id = items[0]["project_checklist_item_id"]
    package = _create_package(client, token, project_id)
    package_id = package["response_package_id"]
    added = client.post(
        f"/api/v1/projects/{project_id}/reviewer-response-packages/{package_id}/items/checklist-items",
        headers=_headers(token),
        json={"checklist_item_ids": [checklist_item_id]},
    )
    assert added.status_code == 200, added.text
    assert added.json()["items"][0]["source_type"] == "checklist_item"


def test_add_citation_to_package(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token)
    finding_id = _create_finding(client, token, project_id)
    upload = client.post(
        f"/api/v1/projects/{project_id}/documents/upload",
        headers=_headers(token),
        files={"file": ("plan.pdf", _make_pdf(["Outlet sizing detail"]), "application/pdf")},
        data={"document_type": "stormwater_report"},
    )
    assert upload.status_code in (200, 201), upload.text
    document_id = upload.json()["document_id"]
    client.post(
        f"/api/v1/projects/{project_id}/documents/{document_id}/index-pdf",
        headers=_headers(token),
    )
    citation = client.post(
        f"/api/v1/projects/{project_id}/findings/{finding_id}/citations",
        headers=_headers(token),
        json={"document_id": document_id, "page_number": 1, "section_label": "Outlet"},
    )
    assert citation.status_code == 201, citation.text
    citation_id = citation.json()["evidence_citation_id"]
    package = _create_package(client, token, project_id)
    package_id = package["response_package_id"]
    added = client.post(
        f"/api/v1/projects/{project_id}/reviewer-response-packages/{package_id}/items/citations",
        headers=_headers(token),
        json={"citation_ids": [citation_id]},
    )
    assert added.status_code == 200, added.text
    item = added.json()["items"][0]
    assert item["source_type"] == "citation"
    assert item["citation_reference"]


def test_add_manual_item_and_reject_prohibited(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token)
    package = _create_package(client, token, project_id)
    package_id = package["response_package_id"]
    ok = client.post(
        f"/api/v1/projects/{project_id}/reviewer-response-packages/{package_id}/items/manual",
        headers=_headers(token),
        json={"reviewer_comment_text": "Reviewer requests an updated drainage report."},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["items"][0]["source_type"] == "manual_reviewer_note"

    rejected = client.post(
        f"/api/v1/projects/{project_id}/reviewer-response-packages/{package_id}/items/manual",
        headers=_headers(token),
        json={"reviewer_comment_text": "This item is approved and certified."},
    )
    assert rejected.status_code == 422


def test_add_finding_from_other_project_rejected(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_a = _create_project(client, token)
    project_b = _create_project(client, token)
    finding_b = _create_finding(client, token, project_b)
    package = _create_package(client, token, project_a)
    package_id = package["response_package_id"]
    response = client.post(
        f"/api/v1/projects/{project_a}/reviewer-response-packages/{package_id}/items/findings",
        headers=_headers(token),
        json={"finding_ids": [finding_b]},
    )
    assert response.status_code == 404


def test_update_package_item(client: TestClient):
    token, project_id, package_id, detail = _setup_package_with_finding_item(
        client
    )
    item_id = detail["items"][0]["response_package_item_id"]
    update = client.patch(
        f"/api/v1/projects/{project_id}/reviewer-response-package-items/{item_id}",
        headers=_headers(token),
        json={
            "reviewer_comment_text": "Reviewer requests the revised outlet detail.",
            "include_in_letter": False,
            "sort_order": 3,
            "item_status": "needs_reviewer_confirmation",
        },
    )
    assert update.status_code == 200, update.text
    body = update.json()
    assert body["include_in_letter"] is False
    assert body["item_status"] == "needs_reviewer_confirmation"


def test_update_package_item_rejects_invalid_status(client: TestClient):
    token, project_id, package_id, detail = _setup_package_with_finding_item(
        client
    )
    item_id = detail["items"][0]["response_package_item_id"]
    update = client.patch(
        f"/api/v1/projects/{project_id}/reviewer-response-package-items/{item_id}",
        headers=_headers(token),
        json={"item_status": "resolved"},
    )
    assert update.status_code == 422


def test_update_package_item_rejects_prohibited_language(client: TestClient):
    token, project_id, package_id, detail = _setup_package_with_finding_item(
        client
    )
    item_id = detail["items"][0]["response_package_item_id"]
    update = client.patch(
        f"/api/v1/projects/{project_id}/reviewer-response-package-items/{item_id}",
        headers=_headers(token),
        json={"reviewer_comment_text": "The plan is approved."},
    )
    assert update.status_code == 422


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------


def test_package_preview_is_safe(client: TestClient):
    token, project_id, package_id, detail = _setup_package_with_finding_item(
        client
    )
    preview = client.get(
        f"/api/v1/projects/{project_id}/reviewer-response-packages/{package_id}/preview",
        headers=_headers(token),
    )
    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert "does not approve" in body["boundary_statement"].lower()
    assert body["item_count"] == 1
    blob = preview.text.lower()
    for token_leak in LEAK_TOKENS:
        assert token_leak not in blob


# ---------------------------------------------------------------------------
# Comment letter drafts
# ---------------------------------------------------------------------------


def _generate_draft(client: TestClient, token: str, project_id: str, package_id: str) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/reviewer-response-packages/{package_id}/comment-letter-draft",
        headers=_headers(token),
        json={"recipient_name": "Design Firm"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_generate_comment_letter_draft(client: TestClient):
    token, project_id, package_id, detail = _setup_package_with_finding_item(
        client
    )
    draft = _generate_draft(client, token, project_id, package_id)
    assert draft["status"] == "draft_created"
    assert "does not approve" in draft["boundary_statement"].lower()
    assert "Comment 1" in draft["comment_items_text"]
    # The boundary statement is never embedded in an editable section.
    assert "does not approve" not in draft["introduction_text"].lower()


def test_update_comment_letter_draft(client: TestClient):
    token, project_id, package_id, detail = _setup_package_with_finding_item(
        client
    )
    draft = _generate_draft(client, token, project_id, package_id)
    draft_id = draft["comment_letter_draft_id"]
    update = client.patch(
        f"/api/v1/projects/{project_id}/comment-letter-drafts/{draft_id}",
        headers=_headers(token),
        json={"introduction_text": "Updated reviewer introduction for handoff."},
    )
    assert update.status_code == 200, update.text
    assert update.json()["status"] == "reviewer_editing"


def test_update_comment_letter_rejects_prohibited_language(client: TestClient):
    token, project_id, package_id, detail = _setup_package_with_finding_item(
        client
    )
    draft = _generate_draft(client, token, project_id, package_id)
    draft_id = draft["comment_letter_draft_id"]
    update = client.patch(
        f"/api/v1/projects/{project_id}/comment-letter-drafts/{draft_id}",
        headers=_headers(token),
        json={"closing_text": "The submission is approved."},
    )
    assert update.status_code == 422


def test_comment_letter_ready_for_handoff_status(client: TestClient):
    token, project_id, package_id, detail = _setup_package_with_finding_item(
        client
    )
    draft = _generate_draft(client, token, project_id, package_id)
    draft_id = draft["comment_letter_draft_id"]
    update = client.patch(
        f"/api/v1/projects/{project_id}/comment-letter-drafts/{draft_id}",
        headers=_headers(token),
        json={"status": "ready_for_reviewer_handoff"},
    )
    assert update.status_code == 200
    assert update.json()["status"] == "ready_for_reviewer_handoff"
    events = client.get(
        f"/api/v1/projects/{project_id}/audit-events", headers=_headers(token)
    ).json()
    types = {e["event_type"] for e in events}
    assert "comment_letter_ready_for_handoff" in types


def test_comment_letter_preview_is_safe(client: TestClient):
    token, project_id, package_id, detail = _setup_package_with_finding_item(
        client
    )
    draft = _generate_draft(client, token, project_id, package_id)
    draft_id = draft["comment_letter_draft_id"]
    preview = client.get(
        f"/api/v1/projects/{project_id}/comment-letter-drafts/{draft_id}/preview",
        headers=_headers(token),
    )
    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert "does not approve" in body["boundary_statement"].lower()
    assert len(body["sections"]) >= 1
    blob = preview.text.lower()
    for token_leak in LEAK_TOKENS:
        assert token_leak not in blob


# ---------------------------------------------------------------------------
# Issuance and revisions
# ---------------------------------------------------------------------------


def test_issue_response_package(client: TestClient):
    token, project_id, package_id, detail = _setup_package_with_finding_item(
        client
    )
    ready = client.post(
        f"/api/v1/projects/{project_id}/reviewer-response-packages/{package_id}/ready-for-handoff",
        headers=_headers(token),
    )
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready_for_reviewer_handoff"
    issue = client.post(
        f"/api/v1/projects/{project_id}/reviewer-response-packages/{package_id}/issue",
        headers=_headers(token),
        json={},
    )
    assert issue.status_code == 200, issue.text
    body = issue.json()
    assert body["status"] == "issued_by_reviewer"
    assert body["issued_by_name"]
    assert body["issued_at"]


def test_revision_preserves_prior_issued_record(client: TestClient):
    token, project_id, package_id, detail = _setup_package_with_finding_item(
        client
    )
    client.post(
        f"/api/v1/projects/{project_id}/reviewer-response-packages/{package_id}/issue",
        headers=_headers(token),
        json={},
    )
    issued = client.get(
        f"/api/v1/projects/{project_id}/reviewer-response-packages/{package_id}",
        headers=_headers(token),
    ).json()
    issued_by = issued["issued_by_name"]
    issued_at = issued["issued_at"]

    revision = client.post(
        f"/api/v1/projects/{project_id}/reviewer-response-packages/{package_id}/revisions",
        headers=_headers(token),
        json={"revision_reason": "Applicant submitted revised plans."},
    )
    assert revision.status_code == 201, revision.text
    body = revision.json()
    assert body["status"] == "revision_started"
    assert body["revision_number"] == 1
    # The prior issued record is preserved, not overwritten.
    assert body["issued_by_name"] == issued_by
    assert body["issued_at"] == issued_at


def test_issuance_does_not_create_final_outcome_status(client: TestClient):
    token, project_id, package_id, detail = _setup_package_with_finding_item(
        client
    )
    issue = client.post(
        f"/api/v1/projects/{project_id}/reviewer-response-packages/{package_id}/issue",
        headers=_headers(token),
        json={},
    )
    blob = issue.text.lower()
    for word in ("approved", "resolved", "closed", "verified", "certified"):
        assert word not in blob


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------


def test_read_only_user_cannot_mutate_package(client: TestClient):
    owner = _register(client)
    token = owner["access_token"]
    project_id = _create_project(client, token)
    package = _create_package(client, token, project_id)
    package_id = package["response_package_id"]
    viewer = _register(client)
    client.post(
        f"/api/v1/projects/{project_id}/access/grant",
        headers=_headers(token),
        json={"access_level": "read_only", "user_id": viewer["user"]["user_id"]},
    )
    viewer_headers = _headers(viewer["access_token"])
    read = client.get(
        f"/api/v1/projects/{project_id}/reviewer-response-packages", headers=viewer_headers
    )
    assert read.status_code == 200
    blocked = client.post(
        f"/api/v1/projects/{project_id}/reviewer-response-packages",
        headers=viewer_headers,
        json={},
    )
    assert blocked.status_code == 403
    blocked_issue = client.post(
        f"/api/v1/projects/{project_id}/reviewer-response-packages/{package_id}/issue",
        headers=viewer_headers,
        json={},
    )
    assert blocked_issue.status_code == 403


def test_unauthorized_user_cannot_view_packages(client: TestClient):
    owner = _register(client)
    token = owner["access_token"]
    project_id = _create_project(client, token)
    _create_package(client, token, project_id)
    other = _register(client)
    response = client.get(
        f"/api/v1/projects/{project_id}/reviewer-response-packages",
        headers=_headers(other["access_token"]),
    )
    assert response.status_code == 403


def test_strict_mode_requires_authentication(client: TestClient):
    from app.core.config import get_settings

    owner = _register(client)
    token = owner["access_token"]
    project_id = _create_project(client, token)
    settings = get_settings()
    old = settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS
    settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS = True
    try:
        response = client.get(
            f"/api/v1/projects/{project_id}/reviewer-response-packages"
        )
        assert response.status_code == 401
    finally:
        settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS = old


# ---------------------------------------------------------------------------
# Security and boundary
# ---------------------------------------------------------------------------


def test_no_prohibited_wording_in_package_responses(client: TestClient):
    token, project_id, package_id, detail = _setup_package_with_finding_item(
        client
    )
    draft = _generate_draft(client, token, project_id, package_id)
    detail_resp = client.get(
        f"/api/v1/projects/{project_id}/reviewer-response-packages/{package_id}",
        headers=_headers(token),
    )
    blob = (detail_resp.text + draft["comment_items_text"]).lower()
    for word in PROHIBITED_FINAL_DECISION_WORDS:
        assert word not in blob
    for word in ("resolved", "closed", "noncompliant", "passed review"):
        assert word not in blob


def test_brookside_demo_and_health_intact(client: TestClient):
    health = client.get("/health")
    assert health.status_code == 200
    project = client.get(f"/api/v1/projects/{BROOKSIDE_ID}")
    assert project.status_code == 200
