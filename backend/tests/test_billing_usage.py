"""Tests for the Production Phase 4B/4C billing and usage foundation.

Covers the plan catalog, honest inactive billing status, per-organization
subscription posture and advisory usage summary with membership gating, the
deferred-checkout response, and the usage service (category validation, demo
exclusion, totals, and limit status). Billing is deferred: no test asserts an
active paid subscription, and no secret or Stripe key appears in any response.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.database import SessionLocal
from app.services import billing_service, usage_service


def _email() -> str:
    return f"user_{uuid.uuid4().hex[:10]}@example.com"


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register(client: TestClient, *, organization_name: str | None = None) -> dict:
    body = {
        "email": _email(),
        "password": "password123",
        "display_name": "Billing User",
    }
    if organization_name:
        body["organization_name"] = organization_name
    resp = client.post("/api/v1/auth/register", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _admin_with_org(client: TestClient) -> tuple[dict, str]:
    admin = _register(client, organization_name="Billing Org")
    orgs = client.get(
        "/api/v1/me/organizations", headers=_headers(admin["access_token"])
    ).json()
    return admin, orgs[0]["organization_id"]


# ---------------------------------------------------------------------------
# Plans and billing status
# ---------------------------------------------------------------------------


def test_plan_catalog_lists_all_tiers(client: TestClient):
    resp = client.get("/api/v1/billing/plans")
    assert resp.status_code == 200
    codes = {p["plan_code"] for p in resp.json()}
    assert {"demo", "design_partner", "professional", "team"} <= codes
    for plan in resp.json():
        assert "limits" in plan
        assert "projects" in plan["limits"]


def test_billing_status_inactive_by_default(client: TestClient):
    resp = client.get("/api/v1/billing/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is False
    assert body["mode"] == "inactive"
    assert "not active" in body["message"].lower()


def test_billing_enabled_follows_stripe_key():
    # Billing is enabled only when a Stripe secret key is configured.
    assert Settings(_env_file=None).billing_enabled is False
    assert (
        Settings(_env_file=None, STRIPE_SECRET_KEY="sk_test_x").billing_enabled
        is True
    )


# ---------------------------------------------------------------------------
# Organization billing and usage gating
# ---------------------------------------------------------------------------


def test_org_billing_requires_membership(client: TestClient):
    _admin, org_id = _admin_with_org(client)
    # Anonymous.
    assert client.get(f"/api/v1/organizations/{org_id}/billing").status_code == 401
    # Signed-in non-member.
    outsider = _register(client)
    assert (
        client.get(
            f"/api/v1/organizations/{org_id}/billing",
            headers=_headers(outsider["access_token"]),
        ).status_code
        == 403
    )


def test_org_billing_default_plan_is_demo_inactive(client: TestClient):
    admin, org_id = _admin_with_org(client)
    resp = client.get(
        f"/api/v1/organizations/{org_id}/billing",
        headers=_headers(admin["access_token"]),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["subscription"]["plan_code"] == "demo"
    assert body["subscription"]["status"] == "inactive"
    assert body["billing"]["enabled"] is False
    # The Stripe customer id is never exposed.
    assert "stripe_customer_id" not in str(body)


def test_org_usage_summary_is_advisory(client: TestClient):
    admin, org_id = _admin_with_org(client)
    resp = client.get(
        f"/api/v1/organizations/{org_id}/usage",
        headers=_headers(admin["access_token"]),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["enforcement"] == "advisory"
    keys = {limit["key"] for limit in body["limits"]}
    assert {"projects", "documents", "pdf_pages", "cad_files", "review_packets"} <= keys


def test_usage_summary_requires_membership(client: TestClient):
    _admin, org_id = _admin_with_org(client)
    assert client.get(f"/api/v1/organizations/{org_id}/usage").status_code == 401


def test_checkout_reports_inactive_when_billing_deferred(client: TestClient):
    admin, org_id = _admin_with_org(client)
    resp = client.post(
        f"/api/v1/organizations/{org_id}/billing/checkout",
        headers=_headers(admin["access_token"]),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is False
    assert body["checkout_url"] is None


# ---------------------------------------------------------------------------
# Usage service
# ---------------------------------------------------------------------------


def test_record_usage_rejects_unknown_category():
    db = SessionLocal()
    try:
        try:
            usage_service.record_usage(db, category="not_a_category")
            assert False, "expected ValueError"
        except ValueError:
            pass
    finally:
        db.rollback()
        db.close()


def test_record_usage_safe_skips_demo_org():
    db = SessionLocal()
    try:
        result = usage_service.record_usage_safe(
            db,
            category="project_created",
            organization_id="org_internal_demo",
        )
        assert result is None
    finally:
        db.rollback()
        db.close()


def test_record_usage_safe_never_raises_on_bad_category():
    db = SessionLocal()
    try:
        result = usage_service.record_usage_safe(
            db, category="bogus", organization_id="org_real_x"
        )
        assert result is None
    finally:
        db.rollback()
        db.close()


def test_usage_summary_reflects_recorded_events():
    org_id = f"org_usage_{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    try:
        for _ in range(2):
            usage_service.record_usage(
                db, category="project_created", organization_id=org_id
            )
        db.commit()
        summary = usage_service.usage_summary(db, org_id)
        projects = next(
            limit for limit in summary["limits"] if limit["key"] == "projects"
        )
        assert projects["used"] == 2
        # The default demo plan limits projects to 1, so two is over.
        assert projects["status"] == "over"
    finally:
        db.close()


def test_limit_status_thresholds():
    assert usage_service._limit_status(0, 10) == "ok"
    assert usage_service._limit_status(8, 10) == "approaching"
    assert usage_service._limit_status(10, 10) == "over"
    # None means no metered limit (advisory unlimited).
    assert usage_service._limit_status(9999, None) == "ok"


def test_set_subscription_plan_validates_inputs():
    org_id = f"org_sub_{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    try:
        sub = billing_service.set_subscription_plan(
            db, org_id, plan_code="professional", status="active"
        )
        assert sub.plan_code == "professional"
        assert sub.status == "active"
        for bad in (
            lambda: billing_service.set_subscription_plan(
                db, org_id, plan_code="enterprise_ultra"
            ),
            lambda: billing_service.set_subscription_plan(
                db, org_id, plan_code="demo", status="paid_forever"
            ),
        ):
            try:
                bad()
                assert False, "expected ValueError"
            except ValueError:
                pass
        db.commit()
    finally:
        db.close()


def test_pilot_request_records_global_usage(client: TestClient):
    before = _global_pilot_usage()
    resp = client.post(
        "/api/v1/pilot-requests",
        json={
            "full_name": "Usage Tester",
            "work_email": "usage@example.com",
            "firm_name": "Usage Firm",
            "role_title": "Engineer",
            "project_type": "stormwater",
            "primary_pain": "Avoidable resubmittals.",
            "interest_level": "ready_to_pilot",
        },
    )
    assert resp.status_code in (200, 201)
    assert _global_pilot_usage() == before + 1


def _global_pilot_usage() -> int:
    from app.db import models

    db = SessionLocal()
    try:
        return (
            db.query(models.UsageEvent)
            .filter(models.UsageEvent.category == "pilot_request_submitted")
            .count()
        )
    finally:
        db.close()
