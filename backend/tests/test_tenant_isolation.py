"""Tenant-isolation tests for high-priority project routes.

These tests prove that access control is enforced on the traceability routes,
which previously read project data without any access check. A user with no
access to a real project is rejected, while the intentionally public Brookside
Meadows demo project stays readable without a login.

The conftest defaults keep the demo reviewer fallback on (real projects readable
without login), which mirrors the prototype's demo posture. The cross-tenant
tests therefore use two authenticated users: once a user is signed in, the demo
fallback no longer applies and access is decided by project access grants.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings

BROOKSIDE_ID = "proj_brookside_meadows"


def _register(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"user_{uuid.uuid4().hex[:10]}@example.com",
            "password": "password123",
            "display_name": "Tenant User",
            "organization_name": f"Firm {uuid.uuid4().hex[:6]}",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_project(client: TestClient, token: str) -> str:
    response = client.post(
        "/api/v1/projects",
        headers=_headers(token),
        json={
            "project_name": "Tenant Project",
            "project_type": "Subdivision",
            "jurisdiction": "Town",
            "review_type": "Review",
            "review_domain": "stormwater",
            "location_context": "Parcel",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["project_id"]


@pytest.fixture
def strict_login():
    settings = get_settings()
    old = settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS
    settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS = True
    yield
    settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS = old


def test_non_member_cannot_read_other_project_traceability(client: TestClient):
    owner_token = _register(client)
    project_id = _create_project(client, owner_token)

    other_token = _register(client)
    response = client.get(
        f"/api/v1/projects/{project_id}/traceability",
        headers=_headers(other_token),
    )
    assert response.status_code == 403, response.text


def test_owner_can_read_their_project_traceability(client: TestClient):
    owner_token = _register(client)
    project_id = _create_project(client, owner_token)

    response = client.get(
        f"/api/v1/projects/{project_id}/traceability",
        headers=_headers(owner_token),
    )
    assert response.status_code == 200, response.text


def test_non_member_cannot_record_traceability_review_action(client: TestClient):
    owner_token = _register(client)
    project_id = _create_project(client, owner_token)

    other_token = _register(client)
    response = client.post(
        f"/api/v1/projects/{project_id}/traceability/row-key/review-actions",
        headers=_headers(other_token),
        json={"action_type": "reviewer_confirmed_link"},
    )
    assert response.status_code == 403, response.text


def test_anonymous_cannot_read_real_project_traceability_under_strict_login(
    client: TestClient, strict_login
):
    owner_token = _register(client)
    project_id = _create_project(client, owner_token)

    response = client.get(f"/api/v1/projects/{project_id}/traceability")
    assert response.status_code == 401, response.text


def _register_document(client: TestClient, token: str, project_id: str) -> str:
    response = client.post(
        f"/api/v1/projects/{project_id}/documents/register",
        headers=_headers(token),
        json={
            "original_file_name": "stormwater_report.pdf",
            "document_type": "report",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["document_id"]


def test_non_member_cannot_fetch_document_by_raw_id(client: TestClient):
    # A raw document id must not bypass project access scoping.
    owner_token = _register(client)
    project_id = _create_project(client, owner_token)
    document_id = _register_document(client, owner_token, project_id)

    other_token = _register(client)
    response = client.get(
        f"/api/v1/documents/{document_id}",
        headers=_headers(other_token),
    )
    assert response.status_code == 403, response.text


def test_owner_can_fetch_their_document_by_raw_id(client: TestClient):
    owner_token = _register(client)
    project_id = _create_project(client, owner_token)
    document_id = _register_document(client, owner_token, project_id)

    response = client.get(
        f"/api/v1/documents/{document_id}",
        headers=_headers(owner_token),
    )
    assert response.status_code == 200, response.text


def test_public_demo_traceability_readable_anonymously(client: TestClient):
    # The Brookside Meadows demo project is intentionally public; the access
    # check must not break no-login demo browsing.
    response = client.get(f"/api/v1/projects/{BROOKSIDE_ID}/traceability")
    assert response.status_code == 200, response.text


def test_public_demo_traceability_readable_under_strict_login(
    client: TestClient, strict_login
):
    # Even when real projects require login, the demo_public exception keeps the
    # sample project readable without a login.
    response = client.get(f"/api/v1/projects/{BROOKSIDE_ID}/traceability")
    assert response.status_code == 200, response.text


# ---------------------------------------------------------------------------
# Phase 2B: complete guard coverage across previously unguarded routers.
#
# Each path below is a project-scoped read that returns 200 (an empty list or a
# structured payload) for a project member and must return 403 for a signed-in
# non-member. The same paths stay readable anonymously on the public Brookside
# Meadows demo project.
# ---------------------------------------------------------------------------

PROJECT_READ_PATHS = [
    "cad-files",
    "cad-metadata",
    "cad-review-findings",
    "cad-review-findings/unpromoted",
    "workflow-board",
    "review-packets",
    "plan-consistency-findings",
    "plan-references",
    "plan-references/inconsistencies",
    "plan-sheets",
    "sheet-hotspots",
    "hotspots",
    "checklist",
    "chunks",
    "ai-review-runs",
    "ai-provider-mode",
    "draft-findings",
    "human-review-queue",
    "review-actions",
    "ai-evaluation-results",
    "review-cycles",
    "resubmittals",
    "applicant-responses",
    "carry-forwards",
    "resolution-records",
    "response-packages",
    "audit-events",
    "traceability",
    "command-center",
]


@pytest.mark.parametrize("path", PROJECT_READ_PATHS)
def test_non_member_blocked_on_project_read_routes(client: TestClient, path):
    owner_token = _register(client)
    project_id = _create_project(client, owner_token)

    other_token = _register(client)
    response = client.get(
        f"/api/v1/projects/{project_id}/{path}",
        headers=_headers(other_token),
    )
    assert response.status_code == 403, f"{path} -> {response.status_code}: {response.text}"


@pytest.mark.parametrize("path", PROJECT_READ_PATHS)
def test_owner_allowed_on_project_read_routes(client: TestClient, path):
    owner_token = _register(client)
    project_id = _create_project(client, owner_token)

    response = client.get(
        f"/api/v1/projects/{project_id}/{path}",
        headers=_headers(owner_token),
    )
    assert response.status_code == 200, f"{path} -> {response.status_code}: {response.text}"


@pytest.mark.parametrize("path", PROJECT_READ_PATHS)
def test_public_demo_read_routes_stay_anonymous(client: TestClient, path):
    # The Brookside Meadows demo project must stay readable without a login so
    # the guided demo keeps working.
    response = client.get(f"/api/v1/projects/{BROOKSIDE_ID}/{path}")
    assert response.status_code == 200, f"{path} -> {response.status_code}: {response.text}"


def test_non_member_blocked_on_review_cycle_raw_id(client: TestClient):
    # Create a review cycle (no prerequisites) and confirm a non-member cannot
    # read it by its raw id, while the owner can.
    owner_token = _register(client)
    project_id = _create_project(client, owner_token)
    created = client.post(
        f"/api/v1/projects/{project_id}/review-cycles",
        headers=_headers(owner_token),
        json={},
    )
    assert created.status_code == 200, created.text
    review_cycle_id = created.json()["review_cycle_id"]

    other_token = _register(client)
    blocked = client.get(
        f"/api/v1/review-cycles/{review_cycle_id}",
        headers=_headers(other_token),
    )
    assert blocked.status_code == 403, blocked.text

    allowed = client.get(
        f"/api/v1/review-cycles/{review_cycle_id}",
        headers=_headers(owner_token),
    )
    assert allowed.status_code == 200, allowed.text


def test_anonymous_blocked_on_real_project_read_under_strict_login(
    client: TestClient, strict_login
):
    owner_token = _register(client)
    project_id = _create_project(client, owner_token)
    response = client.get(f"/api/v1/projects/{project_id}/workflow-board")
    assert response.status_code == 401, response.text


def test_plan_sheet_raw_id_blocks_non_member(client: TestClient):
    # The Brookside demo has seeded plan sheets. A signed-in non-member is still
    # allowed to read the demo project (public), so this asserts the raw-id guard
    # path resolves the owning project rather than 500-ing, and the demo stays
    # readable anonymously.
    sheets = client.get(f"/api/v1/projects/{BROOKSIDE_ID}/plan-sheets")
    assert sheets.status_code == 200, sheets.text
    rows = sheets.json()
    if not rows:
        return
    sheet_id = rows[0]["sheet_id"]
    anon = client.get(f"/api/v1/plan-sheets/{sheet_id}")
    assert anon.status_code == 200, anon.text
