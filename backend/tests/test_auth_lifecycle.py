"""Tests for the Production Phase 4B account lifecycle and team invitations.

Covers password reset request/confirm with expiry and use-once behavior, the
account profile endpoint, and the organization invitation workflow (create, list,
revoke, accept, role enforcement, and reuse protection). Security is asserted
throughout: reset and invitation tokens are stored only as a hash and never
appear in a response outside the documented dev-token field.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db import models
from app.db.database import SessionLocal
from app.services import auth_service, invitation_service


def _email() -> str:
    return f"user_{uuid.uuid4().hex[:10]}@example.com"


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register(client: TestClient, *, organization_name: str | None = None) -> dict:
    body = {
        "email": _email(),
        "password": "password123",
        "display_name": "Lifecycle User",
    }
    if organization_name:
        body["organization_name"] = organization_name
    resp = client.post("/api/v1/auth/register", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    data["email"] = body["email"]
    return data


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


def test_password_reset_request_is_uniform_for_unknown_email(client: TestClient):
    resp = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "nobody-" + _email()},
    )
    assert resp.status_code == 200
    body = resp.json()
    # No account: the same message, and no token is issued.
    assert "account exists" in body["detail"].lower()
    assert body["dev_reset_token"] is None


def test_password_reset_full_flow_and_use_once(client: TestClient):
    account = _register(client)
    req = client.post(
        "/api/v1/auth/password-reset/request", json={"email": account["email"]}
    )
    assert req.status_code == 200
    token = req.json()["dev_reset_token"]
    assert token  # exposed outside production for local/test flows

    confirm = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "brandnewpass1"},
    )
    assert confirm.status_code == 200

    # The new password works.
    login = client.post(
        "/api/v1/auth/login",
        json={"email": account["email"], "password": "brandnewpass1"},
    )
    assert login.status_code == 200

    # The token cannot be reused.
    reuse = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "anotherpass99"},
    )
    assert reuse.status_code == 400


def test_password_reset_rejects_invalid_token(client: TestClient):
    resp = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": "not-a-real-token", "new_password": "whateverpass1"},
    )
    assert resp.status_code == 400


def test_password_reset_rejects_expired_token(client: TestClient):
    account = _register(client)
    req = client.post(
        "/api/v1/auth/password-reset/request", json={"email": account["email"]}
    )
    token = req.json()["dev_reset_token"]
    # Force the stored token to be expired.
    from datetime import datetime, timedelta, timezone

    db = SessionLocal()
    try:
        record = (
            db.query(models.PasswordResetToken)
            .filter(
                models.PasswordResetToken.token_hash
                == auth_service.hash_token(token)
            )
            .first()
        )
        record.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    finally:
        db.close()
    resp = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "freshpass1234"},
    )
    assert resp.status_code == 400


def test_password_reset_token_is_stored_hashed(client: TestClient):
    account = _register(client)
    req = client.post(
        "/api/v1/auth/password-reset/request", json={"email": account["email"]}
    )
    token = req.json()["dev_reset_token"]
    db = SessionLocal()
    try:
        rows = db.query(models.PasswordResetToken).all()
        # The plaintext token is never stored; only its hash is.
        assert all(r.token_hash != token for r in rows)
        assert any(
            r.token_hash == auth_service.hash_token(token) for r in rows
        )
    finally:
        db.close()


def test_password_reset_enforces_minimum_length(client: TestClient):
    account = _register(client)
    token = client.post(
        "/api/v1/auth/password-reset/request", json={"email": account["email"]}
    ).json()["dev_reset_token"]
    resp = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "short"},
    )
    assert resp.status_code == 422


def test_account_profile_returns_identity_and_orgs(client: TestClient):
    account = _register(client, organization_name="Profile Firm")
    resp = client.get(
        "/api/v1/account/profile", headers=_headers(account["access_token"])
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["email"] == account["email"]
    assert any(o["organization_name"] == "Profile Firm" for o in body["organizations"])
    assert "password_hash" not in str(body)


def test_account_profile_requires_auth(client: TestClient):
    assert client.get("/api/v1/account/profile").status_code == 401


# ---------------------------------------------------------------------------
# Organization invitations
# ---------------------------------------------------------------------------


def _admin_with_org(client: TestClient) -> tuple[dict, str]:
    admin = _register(client, organization_name="Invite Org")
    orgs = client.get(
        "/api/v1/me/organizations", headers=_headers(admin["access_token"])
    ).json()
    return admin, orgs[0]["organization_id"]


def test_admin_can_invite_list_and_revoke(client: TestClient):
    admin, org_id = _admin_with_org(client)
    h = _headers(admin["access_token"])
    create = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=h,
        json={"email": "teammate@example.com", "role": "reviewer"},
    )
    assert create.status_code == 201, create.text
    body = create.json()
    assert body["invitation"]["status"] == "pending"
    assert body["dev_invite_token"]
    invitation_id = body["invitation"]["invitation_id"]

    listed = client.get(f"/api/v1/organizations/{org_id}/invitations", headers=h)
    assert listed.status_code == 200
    assert any(i["invitation_id"] == invitation_id for i in listed.json())

    revoke = client.post(
        f"/api/v1/organizations/{org_id}/invitations/{invitation_id}/revoke",
        headers=h,
    )
    assert revoke.status_code == 200
    assert revoke.json()["status"] == "revoked"


def test_invitation_accept_creates_membership(client: TestClient):
    admin, org_id = _admin_with_org(client)
    token = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=_headers(admin["access_token"]),
        json={"email": "newmember@example.com", "role": "reviewer"},
    ).json()["dev_invite_token"]

    member = _register(client)
    accept = client.post(
        "/api/v1/invitations/accept",
        headers=_headers(member["access_token"]),
        json={"token": token},
    )
    assert accept.status_code == 200
    assert accept.json()["role"] == "reviewer"
    # The accepting user is now a member of the organization.
    orgs = client.get(
        "/api/v1/me/organizations", headers=_headers(member["access_token"])
    ).json()
    assert any(o["organization_id"] == org_id for o in orgs)


def test_invitation_cannot_be_accepted_twice(client: TestClient):
    admin, org_id = _admin_with_org(client)
    token = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=_headers(admin["access_token"]),
        json={"email": "once@example.com", "role": "reviewer"},
    ).json()["dev_invite_token"]
    member = _register(client)
    h = _headers(member["access_token"])
    assert client.post(
        "/api/v1/invitations/accept", headers=h, json={"token": token}
    ).status_code == 200
    assert client.post(
        "/api/v1/invitations/accept", headers=h, json={"token": token}
    ).status_code == 400


def test_revoked_invitation_cannot_be_accepted(client: TestClient):
    admin, org_id = _admin_with_org(client)
    h = _headers(admin["access_token"])
    created = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=h,
        json={"email": "revoked@example.com", "role": "reviewer"},
    ).json()
    token = created["dev_invite_token"]
    client.post(
        f"/api/v1/organizations/{org_id}/invitations/"
        f"{created['invitation']['invitation_id']}/revoke",
        headers=h,
    )
    member = _register(client)
    resp = client.post(
        "/api/v1/invitations/accept",
        headers=_headers(member["access_token"]),
        json={"token": token},
    )
    assert resp.status_code == 400


def test_non_admin_cannot_invite_or_revoke(client: TestClient):
    admin, org_id = _admin_with_org(client)
    created = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=_headers(admin["access_token"]),
        json={"email": "x@example.com", "role": "reviewer"},
    ).json()
    invitation_id = created["invitation"]["invitation_id"]

    outsider = _register(client)
    oh = _headers(outsider["access_token"])
    assert client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=oh,
        json={"email": "y@example.com", "role": "reviewer"},
    ).status_code == 403
    assert client.post(
        f"/api/v1/organizations/{org_id}/invitations/{invitation_id}/revoke",
        headers=oh,
    ).status_code == 403
    assert client.get(
        f"/api/v1/organizations/{org_id}/invitations", headers=oh
    ).status_code == 403


def test_anonymous_cannot_invite(client: TestClient):
    admin, org_id = _admin_with_org(client)
    assert client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        json={"email": "z@example.com", "role": "reviewer"},
    ).status_code == 401


def test_invitation_rejects_invalid_role(client: TestClient):
    admin, org_id = _admin_with_org(client)
    resp = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=_headers(admin["access_token"]),
        json={"email": "bad@example.com", "role": "supreme_overlord"},
    )
    assert resp.status_code == 422


def test_invitation_lookup_is_public_and_safe(client: TestClient):
    admin, org_id = _admin_with_org(client)
    token = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=_headers(admin["access_token"]),
        json={"email": "lookup@example.com", "role": "reviewer"},
    ).json()["dev_invite_token"]
    # No auth required for the accept-page preview.
    resp = client.get("/api/v1/invitations/lookup", params={"token": token})
    assert resp.status_code == 200
    body = resp.json()
    assert body["organization_name"] == "Invite Org"
    assert body["acceptable"] is True
    # The token is not echoed back.
    assert token not in str(body)


def test_invitation_token_stored_hashed(client: TestClient):
    admin, org_id = _admin_with_org(client)
    token = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers=_headers(admin["access_token"]),
        json={"email": "hashed@example.com", "role": "reviewer"},
    ).json()["dev_invite_token"]
    db = SessionLocal()
    try:
        rows = db.query(models.OrganizationInvitation).all()
        assert all(r.token_hash != token for r in rows)
        assert any(
            r.token_hash == auth_service.hash_token(token) for r in rows
        )
    finally:
        db.close()


def test_invitation_service_invitable_roles():
    # demo_reviewer and applicant_placeholder are not invitable.
    assert "reviewer" in invitation_service.INVITABLE_ROLES
    assert "org_admin" in invitation_service.INVITABLE_ROLES
    assert "demo_reviewer" not in invitation_service.INVITABLE_ROLES
    assert "applicant_placeholder" not in invitation_service.INVITABLE_ROLES
