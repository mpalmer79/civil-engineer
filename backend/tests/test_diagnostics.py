"""Tests for Production Foundations Sprint 10 deployment diagnostics.

Covers environment validation, health and readiness, admin-gated diagnostics,
storage diagnostics, and safe logging. The security boundary is asserted
throughout: no secret value, database URL, auth secret, object storage
credential, token, signed URL, or raw file system path appears in any response,
and only safe operational status labels are used.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core import logging as safelog
from app.core.config import get_settings
from app.core.safety import (
    ALLOWED_DIAGNOSTIC_CATEGORIES,
    ALLOWED_DIAGNOSTIC_SEVERITIES,
    ALLOWED_DIAGNOSTIC_STATUSES,
    PROHIBITED_FINAL_DECISION_WORDS,
)
from app.services import environment_validation_service as envval

# Secret-like substrings that must never appear in any diagnostics response.
_FORBIDDEN_SUBSTRINGS = [
    "dev-only-insecure-change-me",
    "demo-reviewer-pass",
    "demo-admin-pass",
    "project_uploads",
    "/home/",
    "sqlite:///",
    "secret_access_key=",
]


def _email() -> str:
    return f"user_{uuid.uuid4().hex[:10]}@example.com"


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_admin(client: TestClient) -> str:
    """Register a user who is an org_admin (created with an organization)."""

    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": _email(),
            "password": "password123",
            "display_name": "Ops Admin",
            "organization_name": "Ops Org",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


def _register_plain(client: TestClient) -> str:
    """Register a user with no organization (not an org_admin)."""

    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": _email(),
            "password": "password123",
            "display_name": "Plain User",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


def _assert_no_secrets(payload) -> None:
    blob = str(payload).lower()
    for bad in _FORBIDDEN_SUBSTRINGS:
        assert bad.lower() not in blob, f"secret-like substring leaked: {bad}"


# ---------------------------------------------------------------------------
# Environment validation service
# ---------------------------------------------------------------------------


def test_environment_validation_uses_only_allowed_labels():
    summary = envval.validate_environment()
    assert summary["overall_status"] in ALLOWED_DIAGNOSTIC_STATUSES
    for item in summary["items"]:
        assert item["category"] in ALLOWED_DIAGNOSTIC_CATEGORIES
        assert item["status"] in ALLOWED_DIAGNOSTIC_STATUSES
        assert item["severity"] in ALLOWED_DIAGNOSTIC_SEVERITIES


def test_environment_validation_never_returns_secret_values():
    summary = envval.validate_environment()
    _assert_no_secrets(summary)


def test_required_config_present_reports_configured_status():
    summary = envval.validate_environment()
    app_items = [i for i in summary["items"] if i["category"] == "application"]
    assert app_items
    assert all(i["configured"] for i in app_items)
    assert all(
        i["status"] in {"ready", "configured"} for i in app_items
    )


def test_default_auth_secret_flagged_for_operator_review():
    settings = get_settings()
    old = settings.AUTH_SECRET_KEY
    settings.AUTH_SECRET_KEY = "dev-only-insecure-change-me"
    try:
        summary = envval.validate_environment(settings)
        secret_items = [
            i for i in summary["items"] if i["key"] == "AUTH_SECRET_KEY"
        ]
        assert secret_items
        assert secret_items[0]["status"] == "needs_operator_review"
        # The value itself is never echoed.
        assert "dev-only-insecure-change-me" not in str(summary)
    finally:
        settings.AUTH_SECRET_KEY = old


def test_missing_required_auth_secret_reports_missing_required():
    settings = get_settings()
    old = settings.AUTH_SECRET_KEY
    settings.AUTH_SECRET_KEY = ""
    try:
        summary = envval.validate_environment(settings)
        secret_items = [
            i for i in summary["items"] if i["key"] == "AUTH_SECRET_KEY"
        ]
        assert secret_items[0]["status"] == "missing_required"
        assert summary["overall_status"] == "needs_operator_review"
    finally:
        settings.AUTH_SECRET_KEY = old


def test_local_storage_path_not_exposed_in_diagnostics():
    settings = get_settings()
    summary = envval.validate_environment(settings)
    local_items = [
        i for i in summary["items"] if i["key"] == "LOCAL_STORAGE_DIR"
    ]
    assert local_items
    # The raw path is never used as a public hint.
    assert local_items[0]["public_hint"] is None
    assert settings.local_storage_dir not in str(summary)


def test_s3_provider_missing_settings_reports_safe_warning():
    settings = get_settings()
    old_provider = settings.STORAGE_PROVIDER
    settings.STORAGE_PROVIDER = "s3"
    try:
        summary = envval.validate_environment(settings)
        obj_items = [
            i for i in summary["items"] if i["category"] == "object_storage"
        ]
        statuses = {i["status"] for i in obj_items}
        assert "missing_required" in statuses or "needs_operator_review" in statuses
        _assert_no_secrets(summary)
    finally:
        settings.STORAGE_PROVIDER = old_provider


def test_s3_provider_configured_reports_without_credentials():
    settings = get_settings()
    saved = (
        settings.STORAGE_PROVIDER,
        settings.OBJECT_STORAGE_BUCKET,
        settings.OBJECT_STORAGE_ACCESS_KEY_ID,
        settings.OBJECT_STORAGE_SECRET_ACCESS_KEY,
    )
    settings.STORAGE_PROVIDER = "s3"
    settings.OBJECT_STORAGE_BUCKET = "demo-bucket"
    settings.OBJECT_STORAGE_ACCESS_KEY_ID = "AKIAEXAMPLEKEY"
    settings.OBJECT_STORAGE_SECRET_ACCESS_KEY = "topsecretvalue"
    try:
        summary = envval.validate_environment(settings)
        # Credential values are never echoed, only their configured state.
        assert "AKIAEXAMPLEKEY" not in str(summary)
        assert "topsecretvalue" not in str(summary)
        key_items = {
            i["key"]: i
            for i in summary["items"]
            if i["category"] == "object_storage"
        }
        assert key_items["OBJECT_STORAGE_ACCESS_KEY_ID"]["configured"] is True
        assert key_items["OBJECT_STORAGE_SECRET_ACCESS_KEY"]["configured"] is True
    finally:
        (
            settings.STORAGE_PROVIDER,
            settings.OBJECT_STORAGE_BUCKET,
            settings.OBJECT_STORAGE_ACCESS_KEY_ID,
            settings.OBJECT_STORAGE_SECRET_ACCESS_KEY,
        ) = saved


def test_no_prohibited_final_decision_language_in_environment_validation():
    summary = envval.validate_environment()
    blob = str(summary).lower()
    for word in PROHIBITED_FINAL_DECISION_WORDS:
        assert word not in blob


# ---------------------------------------------------------------------------
# Health and readiness
# ---------------------------------------------------------------------------


def test_health_still_works(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"]


def test_readiness_returns_safe_status_payload(client: TestClient):
    resp = client.get("/api/v1/readiness")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ALLOWED_DIAGNOSTIC_STATUSES
    assert isinstance(body["checks"], list)
    categories = {c["category"] for c in body["checks"]}
    assert {"database", "authentication", "storage"} <= categories
    for check in body["checks"]:
        assert check["status"] in ALLOWED_DIAGNOSTIC_STATUSES


def test_readiness_checks_database_connectivity(client: TestClient):
    resp = client.get("/api/v1/readiness")
    db_checks = [c for c in resp.json()["checks"] if c["category"] == "database"]
    assert db_checks
    assert db_checks[0]["status"] == "ready"


def test_readiness_does_not_expose_secrets(client: TestClient):
    resp = client.get("/api/v1/readiness")
    _assert_no_secrets(resp.json())


# ---------------------------------------------------------------------------
# Diagnostics access control
# ---------------------------------------------------------------------------


def test_environment_diagnostics_requires_authentication(client: TestClient):
    resp = client.get("/api/v1/diagnostics/environment")
    assert resp.status_code == 401


def test_environment_diagnostics_rejects_non_admin(client: TestClient):
    token = _register_plain(client)
    resp = client.get(
        "/api/v1/diagnostics/environment", headers=_headers(token)
    )
    assert resp.status_code == 403


def test_environment_diagnostics_allows_admin(client: TestClient):
    token = _register_admin(client)
    resp = client.get(
        "/api/v1/diagnostics/environment", headers=_headers(token)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["overall_status"] in ALLOWED_DIAGNOSTIC_STATUSES
    assert body["item_count"] == len(body["items"])
    _assert_no_secrets(body)


def test_storage_diagnostics_requires_authentication(client: TestClient):
    resp = client.get("/api/v1/diagnostics/storage")
    assert resp.status_code == 401


def test_storage_diagnostics_local_provider_has_no_raw_path(client: TestClient):
    token = _register_plain(client)
    resp = client.get("/api/v1/diagnostics/storage", headers=_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "local"
    assert body["status"] in ALLOWED_DIAGNOSTIC_STATUSES
    _assert_no_secrets(body)


def test_frontend_config_diagnostics_public_and_safe(client: TestClient):
    resp = client.get("/api/v1/diagnostics/frontend-config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["api_prefix"] == "/api/v1"
    assert any("origin only" in g.lower() for g in body["guidance"])
    assert any("/api/v1" in g for g in body["guidance"])


def test_security_boundary_diagnostics_lists_prohibited_terms(client: TestClient):
    resp = client.get("/api/v1/diagnostics/security-boundary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["diagnostics_are_operational_only"] is True
    assert "approved" in body["prohibited_outcome_terms"]


# ---------------------------------------------------------------------------
# Safe logging
# ---------------------------------------------------------------------------


def test_redact_masks_secret_like_fields():
    out = safelog.redact(
        {
            "AUTH_SECRET_KEY": "supersecret",
            "password_hash": "abcd",
            "access_token": "tok",
            "OBJECT_STORAGE_SECRET_ACCESS_KEY": "key",
            "region": "us-east-1",
            "count": 5,
        }
    )
    assert out["AUTH_SECRET_KEY"] == "[redacted]"
    assert out["password_hash"] == "[redacted]"
    assert out["access_token"] == "[redacted]"
    assert out["OBJECT_STORAGE_SECRET_ACCESS_KEY"] == "[redacted]"
    # Non-sensitive values are preserved.
    assert out["region"] == "us-east-1"
    assert out["count"] == 5


def test_redact_masks_path_like_fields():
    out = safelog.redact(
        {
            "LOCAL_STORAGE_DIR": "/var/data/uploads",
            "DATABASE_URL": "postgres://user:pw@host/db",
            "storage_key": "proj/doc/file.pdf",
        }
    )
    assert out["LOCAL_STORAGE_DIR"] == "[set]"
    assert out["DATABASE_URL"] == "[set]"
    assert out["storage_key"] == "[set]"


def test_log_event_redacts_before_writing(caplog):
    import logging as _logging

    logger = safelog.get_logger()
    # The application logger does not propagate to root, so temporarily enable
    # propagation for this test so caplog (a root handler) records the event.
    previous = logger.propagate
    logger.propagate = True
    try:
        with caplog.at_level(_logging.INFO, logger="civil_engineer"):
            safelog.log_event(
                "startup_configuration",
                storage_provider="local",
                AUTH_SECRET_KEY="supersecret",
                database_url="sqlite:///./x.db",
            )
    finally:
        logger.propagate = previous
    text = caplog.text
    assert "supersecret" not in text
    assert "sqlite:///./x.db" not in text
    assert "storage_provider=local" in text


@pytest.mark.parametrize(
    "fn",
    [
        lambda: envval.get_frontend_config_diagnostics(),
        lambda: envval.get_security_boundary_diagnostics(),
        lambda: envval.get_storage_diagnostics(),
    ],
)
def test_diagnostic_service_helpers_never_leak_secrets(fn):
    _assert_no_secrets(fn())
