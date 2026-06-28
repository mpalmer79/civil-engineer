"""Tests for Production Phase 4D Stripe checkout and webhooks.

Covers webhook signature verification (valid, invalid, expired, malformed),
idempotent event processing, subscription state mapping, the org-admin checkout
gate, the unavailable state when Stripe is not configured, and a mocked checkout
success path. No test makes a real Stripe network call, and no secret appears in
any response.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.database import SessionLocal
from app.services import billing_service, stripe_service

_SECRET = "whsec_test_secret"


@contextmanager
def _settings_override(**kwargs):
    settings = get_settings()
    saved = {k: getattr(settings, k) for k in kwargs}
    for k, v in kwargs.items():
        setattr(settings, k, v)
    try:
        yield settings
    finally:
        for k, v in saved.items():
            setattr(settings, k, v)


def _email() -> str:
    return f"user_{uuid.uuid4().hex[:10]}@example.com"


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_with_org(client: TestClient) -> tuple[dict, str]:
    body = {
        "email": _email(),
        "password": "password123",
        "display_name": "Billing Admin",
        "organization_name": "Stripe Org",
    }
    admin = client.post("/api/v1/auth/register", json=body).json()
    org_id = client.get(
        "/api/v1/me/organizations", headers=_headers(admin["access_token"])
    ).json()[0]["organization_id"]
    return admin, org_id


def _sign(payload: bytes, secret: str = _SECRET, *, ts: int | None = None) -> str:
    ts = ts if ts is not None else int(time.time())
    sig = hmac.new(
        secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256
    ).hexdigest()
    return f"t={ts},v1={sig}"


# ---------------------------------------------------------------------------
# Signature verification (standard library)
# ---------------------------------------------------------------------------


def test_valid_signature_is_accepted():
    payload = json.dumps({"id": "evt_1", "type": "ping"}).encode()
    event = stripe_service.verify_webhook_signature(
        payload, _sign(payload), _SECRET
    )
    assert event["id"] == "evt_1"


def test_invalid_signature_is_rejected():
    payload = b'{"id":"evt_1"}'
    try:
        stripe_service.verify_webhook_signature(
            payload, "t=1,v1=deadbeef", _SECRET, now=1
        )
        assert False, "expected StripeError"
    except stripe_service.StripeError:
        pass


def test_expired_timestamp_is_rejected():
    payload = b'{"id":"evt_1"}'
    old = int(time.time()) - 10_000
    try:
        stripe_service.verify_webhook_signature(
            payload, _sign(payload, ts=old), _SECRET
        )
        assert False, "expected StripeError"
    except stripe_service.StripeError:
        pass


def test_malformed_header_is_rejected():
    payload = b'{"id":"evt_1"}'
    for header in ("", "garbage", "v1=abc"):
        try:
            stripe_service.verify_webhook_signature(payload, header, _SECRET)
            assert False, "expected StripeError"
        except stripe_service.StripeError:
            pass


def test_missing_secret_is_rejected():
    try:
        stripe_service.verify_webhook_signature(b"{}", "t=1,v1=x", "")
        assert False, "expected StripeError"
    except stripe_service.StripeError:
        pass


def test_subscription_status_mapping():
    assert stripe_service.map_subscription_status("active") == "active"
    assert stripe_service.map_subscription_status("past_due") == "past_due"
    assert stripe_service.map_subscription_status("canceled") == "canceled"
    assert stripe_service.map_subscription_status("incomplete") == "inactive"
    assert stripe_service.map_subscription_status("unknown_x") == "inactive"


# ---------------------------------------------------------------------------
# Idempotent event handling (service level)
# ---------------------------------------------------------------------------


def test_duplicate_event_is_ignored(client: TestClient):
    org_id = f"org_dup_{uuid.uuid4().hex[:8]}"
    event = {
        "id": f"evt_{uuid.uuid4().hex[:10]}",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_x",
                "customer": "cus_x",
                "status": "active",
                "metadata": {"organization_id": org_id},
            }
        },
    }
    db = SessionLocal()
    try:
        first = stripe_service.handle_event(db, event)
        assert first["status"] == "processed"
        second = stripe_service.handle_event(db, event)
        assert second["status"] == "duplicate"
    finally:
        db.close()


def test_unknown_event_is_ignored_safely(client: TestClient):
    db = SessionLocal()
    try:
        result = stripe_service.handle_event(
            db,
            {"id": f"evt_{uuid.uuid4().hex[:10]}", "type": "ping.unknown", "data": {}},
        )
        assert result["status"] == "ignored"
    finally:
        db.close()


def test_subscription_deleted_marks_canceled(client: TestClient):
    org_id = f"org_del_{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    try:
        billing_service.set_subscription_plan(
            db, org_id, plan_code="professional", status="active"
        )
        db.commit()
        stripe_service.handle_event(
            db,
            {
                "id": f"evt_{uuid.uuid4().hex[:10]}",
                "type": "customer.subscription.deleted",
                "data": {"object": {"id": "sub_x", "metadata": {"organization_id": org_id}}},
            },
        )
        sub = billing_service.get_or_create_subscription(db, org_id)
        assert sub.status == "canceled"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Checkout endpoint
# ---------------------------------------------------------------------------


def test_checkout_requires_org_admin(client: TestClient):
    _admin, org_id = _admin_with_org(client)
    # Anonymous.
    assert (
        client.post(f"/api/v1/organizations/{org_id}/billing/checkout").status_code
        == 401
    )
    # Signed-in non-member.
    outsider = client.post(
        "/api/v1/auth/register",
        json={"email": _email(), "password": "password123", "display_name": "X"},
    ).json()
    assert (
        client.post(
            f"/api/v1/organizations/{org_id}/billing/checkout",
            headers=_headers(outsider["access_token"]),
        ).status_code
        == 403
    )


def test_checkout_unavailable_when_stripe_not_configured(client: TestClient):
    admin, org_id = _admin_with_org(client)
    resp = client.post(
        f"/api/v1/organizations/{org_id}/billing/checkout",
        headers=_headers(admin["access_token"]),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is False
    assert body["checkout_url"] is None


def test_checkout_success_path_with_mocked_stripe(client: TestClient, monkeypatch):
    admin, org_id = _admin_with_org(client)

    class FakeCustomers:
        @staticmethod
        def create(**kwargs):
            return {"id": "cus_mock"}

    class FakeSessions:
        @staticmethod
        def create(**kwargs):
            return {"url": "https://checkout.stripe.test/session/abc"}

    class FakeStripe:
        api_key = None
        Customer = FakeCustomers
        checkout = type("C", (), {"Session": FakeSessions})

    monkeypatch.setattr(
        stripe_service, "_stripe_client", lambda settings: FakeStripe
    )
    with _settings_override(
        STRIPE_SECRET_KEY="sk_test_x",
        STRIPE_PRICE_PROFESSIONAL="price_x",
        STRIPE_SUCCESS_URL="https://app/success",
        STRIPE_CANCEL_URL="https://app/cancel",
    ):
        resp = client.post(
            f"/api/v1/organizations/{org_id}/billing/checkout",
            headers=_headers(admin["access_token"]),
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is True
    assert body["checkout_url"].startswith("https://checkout.stripe.test/")
    # No secret leaked.
    assert "sk_test_x" not in str(body)


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------


def test_webhook_rejects_invalid_signature(client: TestClient):
    with _settings_override(STRIPE_SECRET_KEY="sk_test_x", STRIPE_WEBHOOK_SECRET=_SECRET):
        resp = client.post(
            "/api/v1/billing/webhook",
            content=b'{"id":"evt_1","type":"ping"}',
            headers={"Stripe-Signature": "t=1,v1=bad"},
        )
    assert resp.status_code == 400


def test_webhook_processes_checkout_completed(client: TestClient):
    admin, org_id = _admin_with_org(client)
    event = {
        "id": f"evt_{uuid.uuid4().hex[:10]}",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": org_id,
                "customer": "cus_1",
                "subscription": "sub_1",
            }
        },
    }
    payload = json.dumps(event).encode()
    with _settings_override(STRIPE_SECRET_KEY="sk_test_x", STRIPE_WEBHOOK_SECRET=_SECRET):
        resp = client.post(
            "/api/v1/billing/webhook",
            content=payload,
            headers={"Stripe-Signature": _sign(payload)},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "processed"
        billing = client.get(
            f"/api/v1/organizations/{org_id}/billing",
            headers=_headers(admin["access_token"]),
        ).json()
    assert billing["subscription"]["status"] == "active"
    assert billing["subscription"]["plan_code"] == "professional"


def test_webhook_duplicate_is_ignored_at_endpoint(client: TestClient):
    _admin, org_id = _admin_with_org(client)
    event = {
        "id": f"evt_{uuid.uuid4().hex[:10]}",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_2",
                "customer": "cus_2",
                "status": "active",
                "metadata": {"organization_id": org_id},
            }
        },
    }
    payload = json.dumps(event).encode()
    with _settings_override(STRIPE_SECRET_KEY="sk_test_x", STRIPE_WEBHOOK_SECRET=_SECRET):
        first = client.post(
            "/api/v1/billing/webhook",
            content=payload,
            headers={"Stripe-Signature": _sign(payload)},
        )
        second = client.post(
            "/api/v1/billing/webhook",
            content=payload,
            headers={"Stripe-Signature": _sign(payload)},
        )
    assert first.json()["status"] == "processed"
    assert second.json()["status"] == "duplicate"


def test_billing_status_mode_is_inactive_by_default(client: TestClient):
    body = client.get("/api/v1/billing/status").json()
    assert body["enabled"] is False
    assert body["mode"] == "inactive"
