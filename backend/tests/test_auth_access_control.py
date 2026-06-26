"""Tests for Production Foundations Sprint 5 authentication and access control.

These tests exercise local registration and login, the current-user endpoint,
project access control (read, reviewer, and admin), demo-mode preservation, and
authenticated audit attribution. They confirm the security boundary: password
hashes are never returned, tokens and secrets never appear in audit metadata,
401 and 403 responses are clear, and no final-decision wording is used.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.safety import PROHIBITED_FINAL_DECISION_WORDS

BROOKSIDE_ID = "proj_brookside_meadows"


def _email() -> str:
    return f"user_{uuid.uuid4().hex[:10]}@example.com"


def _register(
    client: TestClient,
    *,
    email: str | None = None,
    password: str = "password123",
    display_name: str = "Test User",
    organization_name: str | None = None,
) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email or _email(),
            "password": password,
            "display_name": display_name,
            "organization_name": organization_name,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_project(client: TestClient, token: str, name: str = "Auth Project") -> str:
    response = client.post(
        "/api/v1/projects",
        headers=_headers(token),
        json={
            "project_name": name,
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
    """Require login for real projects for the duration of a test."""

    settings = get_settings()
    old = settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS
    settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS = True
    yield
    settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS = old


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


def test_register_user_returns_token_and_user(client: TestClient):
    data = _register(client)
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert "password_hash" not in data["user"]
    assert data["user"]["email"]


def test_register_rejects_duplicate_email(client: TestClient):
    email = _email()
    _register(client, email=email)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "X"},
    )
    assert response.status_code == 409


def test_register_rejects_weak_password(client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": _email(), "password": "short", "display_name": "X"},
    )
    assert response.status_code == 422


def test_login_success_and_failure(client: TestClient):
    email = _email()
    _register(client, email=email, password="password123")
    ok = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert ok.status_code == 200
    assert ok.json()["access_token"]
    bad = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrong-password"},
    )
    assert bad.status_code == 401


def test_current_user_requires_token(client: TestClient):
    data = _register(client)
    me = client.get("/api/v1/auth/me", headers=_headers(data["access_token"]))
    assert me.status_code == 200
    assert me.json()["user_id"] == data["user"]["user_id"]
    assert "password_hash" not in me.json()
    anon = client.get("/api/v1/auth/me")
    assert anon.status_code == 401


def test_password_is_hashed_not_plaintext():
    from app.services import auth_service

    hashed = auth_service.hash_password("password123")
    assert hashed != "password123"
    assert hashed.startswith("pbkdf2_")
    assert auth_service.verify_password("password123", hashed)
    assert not auth_service.verify_password("wrong", hashed)


def test_invalid_token_rejected(client: TestClient):
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not.a.token"}
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Project access
# ---------------------------------------------------------------------------


def test_creator_can_read_their_project(client: TestClient):
    token = _register(client)["access_token"]
    project_id = _create_project(client, token)
    response = client.get(
        f"/api/v1/projects/{project_id}", headers=_headers(token)
    )
    assert response.status_code == 200


def test_user_without_access_gets_403(client: TestClient):
    owner_token = _register(client)["access_token"]
    project_id = _create_project(client, owner_token)
    other_token = _register(client)["access_token"]
    response = client.get(
        f"/api/v1/projects/{project_id}", headers=_headers(other_token)
    )
    assert response.status_code == 403


def test_unauthenticated_real_project_gets_401_under_strict(
    client: TestClient, strict_login
):
    owner_token = _register(client)["access_token"]
    project_id = _create_project(client, owner_token)
    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 401


def test_public_demo_readable_without_login(client: TestClient, strict_login):
    # Brookside Meadows is a public demo and stays readable without a login even
    # when real projects require one.
    response = client.get(f"/api/v1/projects/{BROOKSIDE_ID}")
    assert response.status_code == 200


def test_reviewer_can_create_finding(client: TestClient):
    token = _register(client)["access_token"]
    project_id = _create_project(client, token)
    response = client.post(
        f"/api/v1/projects/{project_id}/findings",
        headers=_headers(token),
        json={
            "title": "Detention basin outlet needs reviewer confirmation",
            "category": "stormwater",
            "risk_level": "medium",
            "evidence_status": "needs_reviewer_confirmation",
            "evidence_to_find": "Outlet sizing",
            "reason_it_matters": "Downstream capacity",
            "recommended_human_action": "Reviewer confirms sizing",
        },
    )
    assert response.status_code == 201, response.text


def test_read_only_user_cannot_create_finding(client: TestClient):
    owner = _register(client)
    project_id = _create_project(client, owner["access_token"])
    viewer = _register(client)
    # Grant the viewer read_only access.
    grant = client.post(
        f"/api/v1/projects/{project_id}/access/grant",
        headers=_headers(owner["access_token"]),
        json={"access_level": "read_only", "user_id": viewer["user"]["user_id"]},
    )
    assert grant.status_code == 201, grant.text
    # The viewer can read but not create a finding.
    read = client.get(
        f"/api/v1/projects/{project_id}", headers=_headers(viewer["access_token"])
    )
    assert read.status_code == 200
    create = client.post(
        f"/api/v1/projects/{project_id}/findings",
        headers=_headers(viewer["access_token"]),
        json={
            "title": "Should be blocked",
            "category": "stormwater",
            "risk_level": "low",
            "evidence_status": "needs_reviewer_confirmation",
            "evidence_to_find": "x",
            "reason_it_matters": "y",
            "recommended_human_action": "z",
        },
    )
    assert create.status_code == 403


def test_org_admin_can_grant_access_and_audit_written(client: TestClient):
    owner = _register(client)
    project_id = _create_project(client, owner["access_token"])
    other = _register(client)
    grant = client.post(
        f"/api/v1/projects/{project_id}/access/grant",
        headers=_headers(owner["access_token"]),
        json={"access_level": "reviewer", "user_id": other["user"]["user_id"]},
    )
    assert grant.status_code == 201, grant.text
    assert grant.json()["access_level"] == "reviewer"
    audit = client.get(
        f"/api/v1/projects/{project_id}/audit-events",
        headers=_headers(owner["access_token"]),
    )
    types = [e["event_type"] for e in audit.json()]
    assert "project_access_granted" in types


def test_reviewer_cannot_grant_access(client: TestClient):
    owner = _register(client)
    project_id = _create_project(client, owner["access_token"])
    reviewer = _register(client)
    client.post(
        f"/api/v1/projects/{project_id}/access/grant",
        headers=_headers(owner["access_token"]),
        json={"access_level": "reviewer", "user_id": reviewer["user"]["user_id"]},
    )
    # The reviewer (not a project admin) cannot grant access.
    response = client.post(
        f"/api/v1/projects/{project_id}/access/grant",
        headers=_headers(reviewer["access_token"]),
        json={"access_level": "reviewer", "user_id": owner["user"]["user_id"]},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Route protection
# ---------------------------------------------------------------------------


def test_project_creation_requires_login_under_strict(
    client: TestClient, strict_login
):
    response = client.post(
        "/api/v1/projects",
        json={
            "project_name": "No Auth Project",
            "project_type": "Subdivision",
            "jurisdiction": "Town",
            "review_type": "Review",
            "review_domain": "stormwater",
            "location_context": "Parcel",
        },
    )
    assert response.status_code == 401


def test_candidate_save_and_checklist_update_require_reviewer(client: TestClient):
    owner = _register(client)
    project_id = _create_project(client, owner["access_token"])
    viewer = _register(client)
    client.post(
        f"/api/v1/projects/{project_id}/access/grant",
        headers=_headers(owner["access_token"]),
        json={"access_level": "read_only", "user_id": viewer["user"]["user_id"]},
    )
    # A read_only viewer cannot save a candidate.
    save = client.post(
        f"/api/v1/projects/{project_id}/evidence-candidates",
        headers=_headers(viewer["access_token"]),
        json={"document_id": "doc_x", "candidate_title": "x"},
    )
    assert save.status_code == 403
    # A read_only viewer cannot create a checklist from a rule pack.
    create = client.post(
        f"/api/v1/projects/{project_id}/checklists/from-rule-pack",
        headers=_headers(viewer["access_token"]),
        json={"rule_pack_id": "rulepack_brookside_stormwater_starter"},
    )
    assert create.status_code == 403


# ---------------------------------------------------------------------------
# Audit attribution and security
# ---------------------------------------------------------------------------


def test_audit_includes_user_identity_and_no_secrets(client: TestClient):
    user = _register(client, display_name="Attributed Reviewer")
    token = user["access_token"]
    project_id = _create_project(client, token)
    # Create a finding so there are user-attributed events.
    client.post(
        f"/api/v1/projects/{project_id}/findings",
        headers=_headers(token),
        json={
            "title": "Attributed finding needs reviewer confirmation",
            "category": "stormwater",
            "risk_level": "low",
            "evidence_status": "needs_reviewer_confirmation",
            "evidence_to_find": "x",
            "reason_it_matters": "y",
            "recommended_human_action": "z",
        },
    )
    # Create a checklist so there is a checklist action event.
    client.post(
        f"/api/v1/projects/{project_id}/checklists/from-rule-pack",
        headers=_headers(token),
        json={"rule_pack_id": "rulepack_brookside_stormwater_starter"},
    )
    audit = client.get(
        f"/api/v1/projects/{project_id}/audit-events", headers=_headers(token)
    ).json()
    by_type = {e["event_type"]: e for e in audit}
    user_id = user["user"]["user_id"]
    assert by_type["project_created"]["user_id"] == user_id
    assert by_type["finding_created"]["user_id"] == user_id
    assert by_type["project_checklist_created"]["user_id"] == user_id
    # No event leaks a token, password, or password hash.
    blob = str(audit).lower()
    assert token.lower() not in blob
    assert "password" not in blob
    assert "pbkdf2" not in blob
    assert "secret" not in blob


def test_password_hash_never_in_responses(client: TestClient):
    data = _register(client)
    token = data["access_token"]
    for text in (
        client.post(
            "/api/v1/auth/login",
            json={"email": data["user"]["email"], "password": "password123"},
        ).text,
        client.get("/api/v1/auth/me", headers=_headers(token)).text,
        client.get("/api/v1/me/projects", headers=_headers(token)).text,
    ):
        assert "password_hash" not in text
        assert "pbkdf2" not in text


def test_permission_messages_have_no_prohibited_wording(client: TestClient):
    owner_token = _register(client)["access_token"]
    project_id = _create_project(client, owner_token)
    other_token = _register(client)["access_token"]
    response = client.get(
        f"/api/v1/projects/{project_id}", headers=_headers(other_token)
    )
    assert response.status_code == 403
    detail = response.json()["detail"].lower()
    for word in PROHIBITED_FINAL_DECISION_WORDS:
        assert word not in detail


def test_me_projects_and_organizations(client: TestClient):
    data = _register(client, organization_name="Riverton Public Works")
    token = data["access_token"]
    project_id = _create_project(client, token)
    projects = client.get("/api/v1/me/projects", headers=_headers(token))
    assert projects.status_code == 200
    ids = {p["project_id"] for p in projects.json()}
    assert project_id in ids
    orgs = client.get("/api/v1/me/organizations", headers=_headers(token))
    assert orgs.status_code == 200
    assert any(o["organization_name"] == "Riverton Public Works" for o in orgs.json())


# ---------------------------------------------------------------------------
# Regression
# ---------------------------------------------------------------------------


def test_organization_routes(client: TestClient):
    data = _register(client, organization_name="Hartwell County Agency")
    token = data["access_token"]
    orgs = client.get("/api/v1/organizations", headers=_headers(token)).json()
    assert len(orgs) >= 1
    org_id = orgs[0]["organization_id"]
    detail = client.get(
        f"/api/v1/organizations/{org_id}", headers=_headers(token)
    )
    assert detail.status_code == 200
    assert detail.json()["role"] == "org_admin"
    members = client.get(
        f"/api/v1/organizations/{org_id}/members", headers=_headers(token)
    )
    assert members.status_code == 200
    assert any(m["role"] == "org_admin" for m in members.json())


def test_non_member_cannot_read_organization(client: TestClient):
    owner = _register(client, organization_name="Private Org")
    org_id = client.get(
        "/api/v1/organizations", headers=_headers(owner["access_token"])
    ).json()[0]["organization_id"]
    outsider = _register(client)
    response = client.get(
        f"/api/v1/organizations/{org_id}",
        headers=_headers(outsider["access_token"]),
    )
    assert response.status_code == 403


def test_list_project_access_and_logout(client: TestClient):
    owner = _register(client)
    project_id = _create_project(client, owner["access_token"])
    access = client.get(
        f"/api/v1/projects/{project_id}/access",
        headers=_headers(owner["access_token"]),
    )
    assert access.status_code == 200
    assert any(a["access_level"] == "project_admin" for a in access.json())
    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 200
    assert logout.json()["ok"] is True


def test_health_and_demo_still_work(client: TestClient):
    assert client.get("/health").status_code == 200
    assert client.get(f"/api/v1/projects/{BROOKSIDE_ID}").status_code == 200
    assert (
        client.get(f"/api/v1/projects/{BROOKSIDE_ID}/findings").status_code == 200
    )
