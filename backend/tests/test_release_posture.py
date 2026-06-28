"""Production-posture tests for the design-partner pilot deployment.

The recommended public-pilot posture is:

- AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS=true  (real projects require a login)
- AUTH_DEMO_MODE=false                        (no anonymous demo-reviewer fallback
                                                for real projects)
- AUTH_ALLOW_PUBLIC_DEMO=true                 (the Brookside demo stays public)

These tests pin that behavior: with the production flags, the public Brookside
demo stays anonymously readable, but a real project rejects anonymous and
non-member access.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings

BROOKSIDE_ID = "proj_brookside_meadows"


@pytest.fixture
def production_posture():
    settings = get_settings()
    old = (
        settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS,
        settings.AUTH_DEMO_MODE,
        settings.AUTH_ALLOW_PUBLIC_DEMO,
    )
    settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS = True
    settings.AUTH_DEMO_MODE = False
    settings.AUTH_ALLOW_PUBLIC_DEMO = True
    yield
    (
        settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS,
        settings.AUTH_DEMO_MODE,
        settings.AUTH_ALLOW_PUBLIC_DEMO,
    ) = old


def _register(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"user_{uuid.uuid4().hex[:10]}@example.com",
            "password": "password123",
            "display_name": "Posture User",
            "organization_name": f"Firm {uuid.uuid4().hex[:6]}",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _create_project(client: TestClient, token: str) -> str:
    response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_name": "Posture Project",
            "project_type": "Subdivision",
            "jurisdiction": "Town",
            "review_type": "Review",
            "review_domain": "stormwater",
            "location_context": "Parcel",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["project_id"]


def test_public_demo_readable_under_production_posture(
    client: TestClient, production_posture
):
    # The guided demo must keep working: Brookside stays readable without a login.
    for path in ("", "/traceability", "/findings", "/documents"):
        response = client.get(f"/api/v1/projects/{BROOKSIDE_ID}{path}")
        assert response.status_code == 200, f"{path} -> {response.status_code}"


def test_real_project_rejects_anonymous_under_production_posture(
    client: TestClient, production_posture
):
    owner_token = _register(client)
    project_id = _create_project(client, owner_token)

    # No anonymous demo fallback for real projects in the production posture.
    response = client.get(f"/api/v1/projects/{project_id}/findings")
    assert response.status_code == 401, response.text


def test_real_project_rejects_non_member_under_production_posture(
    client: TestClient, production_posture
):
    owner_token = _register(client)
    project_id = _create_project(client, owner_token)
    other_token = _register(client)

    response = client.get(
        f"/api/v1/projects/{project_id}/findings",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403, response.text


def test_owner_reads_real_project_under_production_posture(
    client: TestClient, production_posture
):
    owner_token = _register(client)
    project_id = _create_project(client, owner_token)

    response = client.get(
        f"/api/v1/projects/{project_id}/findings",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 200, response.text


def test_public_pilot_submission_works_under_production_posture(
    client: TestClient, production_posture
):
    response = client.post(
        "/api/v1/pilot-requests",
        json={
            "full_name": "Dana Civil",
            "work_email": f"dana_{uuid.uuid4().hex[:8]}@example.com",
            "firm_name": "Meadow Civil Group",
            "role_title": "Project Engineer",
            "project_type": "Residential subdivision",
            "primary_pain": "Avoidable resubmittal cycles.",
            "interest_level": "evaluating",
            "has_sample_package": False,
        },
    )
    assert response.status_code == 201, response.text


def test_pilot_admin_still_protected_under_production_posture(
    client: TestClient, production_posture
):
    response = client.get("/api/v1/pilot-requests")
    assert response.status_code == 401, response.text
