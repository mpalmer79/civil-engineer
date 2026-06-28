"""Tests for the public pilot / design-partner request flow.

A pilot request is a public lead. Anyone can submit one without a login, but
listing stored requests requires an authenticated user. No file content is
stored. No prohibited final-decision wording appears in the acknowledgement.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.core.safety import PROHIBITED_FINAL_DECISION_WORDS


def _valid_payload(**overrides) -> dict:
    payload = {
        "full_name": "Dana Civil",
        "work_email": f"dana_{uuid.uuid4().hex[:8]}@example.com",
        "firm_name": "Meadow Civil Group",
        "role_title": "Project Engineer",
        "project_type": "Residential subdivision",
        "primary_pain": "Avoidable resubmittal cycles from missed review comments.",
        "interest_level": "evaluating",
        "notes": "Saw the guided demo.",
        "has_sample_package": True,
    }
    payload.update(overrides)
    return payload


def _register(client: TestClient, *, organization_name: str | None = "Pilot Ops") -> str:
    # Registering with an organization name makes the new user an org admin, which
    # is the operator gate for the pilot request list. Pass organization_name=None
    # to register a plain (non-admin) member.
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"user_{uuid.uuid4().hex[:10]}@example.com",
            "password": "password123",
            "display_name": "Pilot Lister",
            "organization_name": (
                f"{organization_name} {uuid.uuid4().hex[:6]}"
                if organization_name
                else None
            ),
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def test_public_can_submit_pilot_request(client: TestClient):
    response = client.post("/api/v1/pilot-requests", json=_valid_payload())
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["pilot_request_id"].startswith("pilot_")
    assert body["received"] is True
    assert "received" in body["message"].lower()


def test_pilot_request_ack_has_no_final_decision_wording(client: TestClient):
    response = client.post("/api/v1/pilot-requests", json=_valid_payload())
    assert response.status_code == 201, response.text
    message = response.json()["message"].lower()
    for word in PROHIBITED_FINAL_DECISION_WORDS:
        assert word.lower() not in message


def test_pilot_request_requires_fields(client: TestClient):
    payload = _valid_payload()
    del payload["firm_name"]
    response = client.post("/api/v1/pilot-requests", json=payload)
    assert response.status_code == 422, response.text


def test_pilot_request_rejects_invalid_email(client: TestClient):
    response = client.post(
        "/api/v1/pilot-requests", json=_valid_payload(work_email="not-an-email")
    )
    assert response.status_code == 422, response.text


def test_pilot_request_rejects_invalid_interest_level(client: TestClient):
    response = client.post(
        "/api/v1/pilot-requests", json=_valid_payload(interest_level="urgent")
    )
    assert response.status_code == 422, response.text


def test_public_cannot_list_pilot_requests(client: TestClient):
    # No Authorization header: the list must not be exposed anonymously.
    response = client.get("/api/v1/pilot-requests")
    assert response.status_code == 401, response.text


def test_non_admin_authenticated_user_cannot_list_pilot_requests(client: TestClient):
    # A signed-in user who is not an organization admin must be rejected (403).
    token = _register(client, organization_name=None)
    response = client.get(
        "/api/v1/pilot-requests",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403, response.text


def test_org_admin_can_list_pilot_requests(client: TestClient):
    submitted = client.post("/api/v1/pilot-requests", json=_valid_payload())
    assert submitted.status_code == 201, submitted.text
    submitted_id = submitted.json()["pilot_request_id"]

    token = _register(client)  # registers with an org, so the user is an admin
    response = client.get(
        "/api/v1/pilot-requests",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    ids = [row["pilot_request_id"] for row in response.json()]
    assert submitted_id in ids


def test_pilot_request_stores_flag_not_file_content(client: TestClient):
    response = client.post(
        "/api/v1/pilot-requests", json=_valid_payload(has_sample_package=True)
    )
    assert response.status_code == 201, response.text

    token = _register(client)
    listed = client.get(
        "/api/v1/pilot-requests",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert listed.status_code == 200, listed.text
    rows = listed.json()
    # The sample-package intent is a boolean flag only. No file content fields
    # are ever accepted or returned for any stored request.
    assert any(row["has_sample_package"] is True for row in rows)
    for row in rows:
        for forbidden in ("file", "file_content", "attachment", "upload"):
            assert forbidden not in row


# ---------------------------------------------------------------------------
# Phase 3A/3B: operator status tracking, internal notes, and CSV export.
# All of these are operator-gated (organization admin). A signed-in non-admin and
# an anonymous caller are both rejected.
# ---------------------------------------------------------------------------


def _submit(client: TestClient) -> str:
    response = client.post("/api/v1/pilot-requests", json=_valid_payload())
    assert response.status_code == 201, response.text
    return response.json()["pilot_request_id"]


def test_new_request_defaults_to_status_new(client: TestClient):
    request_id = _submit(client)
    token = _register(client)
    listed = client.get(
        "/api/v1/pilot-requests", headers={"Authorization": f"Bearer {token}"}
    )
    assert listed.status_code == 200, listed.text
    row = next(r for r in listed.json() if r["pilot_request_id"] == request_id)
    assert row["status"] == "new"


def test_public_ack_does_not_expose_internal_notes(client: TestClient):
    response = client.post("/api/v1/pilot-requests", json=_valid_payload())
    assert response.status_code == 201, response.text
    body = response.json()
    assert "internal_notes" not in body
    assert "status" not in body


def test_org_admin_can_update_status(client: TestClient):
    request_id = _submit(client)
    token = _register(client)
    response = client.patch(
        f"/api/v1/pilot-requests/{request_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "contacted", "mark_contacted": True},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "contacted"
    assert body["last_contacted_at"] is not None


def test_status_update_rejects_invalid_status(client: TestClient):
    request_id = _submit(client)
    token = _register(client)
    response = client.patch(
        f"/api/v1/pilot-requests/{request_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "won"},
    )
    assert response.status_code == 422, response.text


def test_status_update_unknown_request_is_404(client: TestClient):
    token = _register(client)
    response = client.patch(
        "/api/v1/pilot-requests/pilot_missing/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "qualified"},
    )
    assert response.status_code == 404, response.text


def test_anonymous_cannot_update_status(client: TestClient):
    request_id = _submit(client)
    response = client.patch(
        f"/api/v1/pilot-requests/{request_id}/status",
        json={"status": "contacted"},
    )
    assert response.status_code == 401, response.text


def test_non_admin_cannot_update_status(client: TestClient):
    request_id = _submit(client)
    token = _register(client, organization_name=None)
    response = client.patch(
        f"/api/v1/pilot-requests/{request_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "contacted"},
    )
    assert response.status_code == 403, response.text


def test_org_admin_can_save_internal_notes(client: TestClient):
    request_id = _submit(client)
    token = _register(client)
    response = client.patch(
        f"/api/v1/pilot-requests/{request_id}/notes",
        headers={"Authorization": f"Bearer {token}"},
        json={"internal_notes": "Left a voicemail; follow up next week."},
    )
    assert response.status_code == 200, response.text
    assert response.json()["internal_notes"].startswith("Left a voicemail")


def test_anonymous_and_non_admin_cannot_save_notes(client: TestClient):
    request_id = _submit(client)
    anon = client.patch(
        f"/api/v1/pilot-requests/{request_id}/notes",
        json={"internal_notes": "x"},
    )
    assert anon.status_code == 401, anon.text
    token = _register(client, organization_name=None)
    forbidden = client.patch(
        f"/api/v1/pilot-requests/{request_id}/notes",
        headers={"Authorization": f"Bearer {token}"},
        json={"internal_notes": "x"},
    )
    assert forbidden.status_code == 403, forbidden.text


def test_org_admin_can_export_csv(client: TestClient):
    _submit(client)
    token = _register(client)
    response = client.get(
        "/api/v1/pilot-requests/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/csv")
    text = response.text
    header = text.splitlines()[0]
    assert "work_email" in header
    assert "status" in header
    # No file content column exists, and no secret/auth field is exported.
    for forbidden in ("file", "attachment", "upload", "password", "token", "secret"):
        assert forbidden not in header.lower()


def test_anonymous_and_non_admin_cannot_export_csv(client: TestClient):
    anon = client.get("/api/v1/pilot-requests/export")
    assert anon.status_code == 401, anon.text
    token = _register(client, organization_name=None)
    forbidden = client.get(
        "/api/v1/pilot-requests/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert forbidden.status_code == 403, forbidden.text


def test_status_filter_narrows_the_list(client: TestClient):
    request_id = _submit(client)
    token = _register(client)
    client.patch(
        f"/api/v1/pilot-requests/{request_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "qualified"},
    )
    filtered = client.get(
        "/api/v1/pilot-requests?status=qualified",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert filtered.status_code == 200, filtered.text
    assert all(r["status"] == "qualified" for r in filtered.json())
    assert any(r["pilot_request_id"] == request_id for r in filtered.json())
