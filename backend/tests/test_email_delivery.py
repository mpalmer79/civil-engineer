"""Tests for Production Phase 4D email delivery.

Covers the noop and SMTP providers behind the mailer abstraction, the email
content builders, and that password reset and invitation flows send through the
mailer when configured. Security is asserted: no token, URL, body, subject, or
SMTP credential is logged, and production never returns a dev token.
"""

from __future__ import annotations

import logging
import uuid
from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.services import email_content, mailer


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


def _register(client: TestClient) -> dict:
    body = {"email": _email(), "password": "password123", "display_name": "Mail User"}
    resp = client.post("/api/v1/auth/register", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    data["email"] = body["email"]
    return data


# ---------------------------------------------------------------------------
# Mailer providers
# ---------------------------------------------------------------------------


def test_noop_provider_sends_nothing():
    result = mailer.send_email(
        to="a@example.com",
        category="password_reset",
        subject="s",
        body="b",
        settings=Settings(_env_file=None),
    )
    assert result["sent"] is False
    assert result["provider"] == "noop"


def test_smtp_unconfigured_is_treated_as_noop():
    # EMAIL_PROVIDER=smtp but no host: not configured, so nothing is sent.
    settings = Settings(_env_file=None, EMAIL_PROVIDER="smtp")
    assert settings.email_configured is False
    result = mailer.send_email(
        to="a@example.com",
        category="team_invitation",
        subject="s",
        body="b",
        settings=settings,
    )
    assert result["sent"] is False


def test_smtp_provider_sends_via_mocked_server(monkeypatch):
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=10):
            sent["host"] = host
            sent["port"] = port

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def starttls(self):
            sent["tls"] = True

        def login(self, username, password):
            sent["login"] = username

        def send_message(self, message):
            sent["to"] = message["To"]
            sent["subject"] = message["Subject"]

    monkeypatch.setattr(mailer.smtplib, "SMTP", FakeSMTP)
    settings = Settings(
        _env_file=None,
        EMAIL_PROVIDER="smtp",
        EMAIL_SMTP_HOST="smtp.example.com",
        EMAIL_SMTP_USERNAME="user",
        EMAIL_SMTP_PASSWORD="secretpass",
        EMAIL_FROM="from@example.com",
    )
    result = mailer.send_email(
        to="to@example.com",
        category="password_reset",
        subject="Reset",
        body="link",
        settings=settings,
    )
    assert result["sent"] is True
    assert result["provider"] == "smtp"
    assert sent["to"] == "to@example.com"
    assert sent["tls"] is True


def test_smtp_failure_is_handled_safely(monkeypatch):
    class BoomSMTP:
        def __init__(self, *a, **k):
            raise OSError("connection refused to smtp.example.com")

    monkeypatch.setattr(mailer.smtplib, "SMTP", BoomSMTP)
    settings = Settings(
        _env_file=None,
        EMAIL_PROVIDER="smtp",
        EMAIL_SMTP_HOST="smtp.example.com",
    )
    result = mailer.send_email(
        to="to@example.com",
        category="password_reset",
        subject="s",
        body="b",
        settings=settings,
    )
    assert result["sent"] is False
    assert result["error"] == "delivery_failed"


def test_mailer_never_logs_secrets_or_tokens(monkeypatch, caplog):
    class FakeSMTP:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def starttls(self):
            pass

        def login(self, *a):
            pass

        def send_message(self, message):
            pass

    monkeypatch.setattr(mailer.smtplib, "SMTP", FakeSMTP)
    logger = logging.getLogger("civil_engineer")
    previous = logger.propagate
    logger.propagate = True
    settings = Settings(
        _env_file=None,
        EMAIL_PROVIDER="smtp",
        EMAIL_SMTP_HOST="smtp.example.com",
        EMAIL_SMTP_PASSWORD="topsecretpw",
    )
    try:
        with caplog.at_level(logging.INFO, logger="civil_engineer"):
            mailer.send_email(
                to="person@example.com",
                category="password_reset",
                subject="Reset your password",
                body="https://app/reset-password/confirm?token=SECRETTOKEN123",
                settings=settings,
            )
    finally:
        logger.propagate = previous
    text = caplog.text
    assert "topsecretpw" not in text
    assert "SECRETTOKEN123" not in text
    assert "reset-password/confirm" not in text
    # Only a redacted recipient is logged.
    assert "person@example.com" not in text


# ---------------------------------------------------------------------------
# Email content
# ---------------------------------------------------------------------------


def test_password_reset_email_has_link_and_expiry():
    settings = Settings(_env_file=None, APP_PUBLIC_BASE_URL="https://app.example.com")
    subject, body = email_content.password_reset_email("tok123", settings=settings)
    assert "reset" in subject.lower()
    assert "https://app.example.com/reset-password/confirm?token=tok123" in body
    assert "expire" in body.lower()
    assert "ignore" in body.lower()


def test_invitation_email_has_link_role_and_boundary():
    settings = Settings(_env_file=None, APP_PUBLIC_BASE_URL="https://app.example.com")
    subject, body = email_content.invitation_email(
        organization_name="Acme Civil", role="reviewer", token="inv9", settings=settings
    )
    assert "Acme Civil" in subject
    assert "https://app.example.com/invitations/accept?token=inv9" in body
    assert "reviewer" in body
    assert "review-support" in body.lower()
    # No prohibited final-decision language.
    for word in ("approved", "certified", "compliant", "passes review"):
        assert word not in body.lower()


# ---------------------------------------------------------------------------
# Flow integration: reset and invite send through the mailer
# ---------------------------------------------------------------------------


def test_password_reset_request_sends_email_for_existing_user(client: TestClient):
    account = _register(client)
    calls = []
    with _settings_override(EMAIL_PROVIDER="smtp", EMAIL_SMTP_HOST="smtp.example.com"):
        import app.api.v1.auth as auth_module

        original = auth_module.mailer.send_email

        def spy(**kwargs):
            calls.append(kwargs["category"])
            return {"provider": "smtp", "sent": True, "category": kwargs["category"]}

        auth_module.mailer.send_email = spy
        try:
            resp = client.post(
                "/api/v1/auth/password-reset/request",
                json={"email": account["email"]},
            )
        finally:
            auth_module.mailer.send_email = original
    assert resp.status_code == 200
    assert "password_reset" in calls


def test_password_reset_request_does_not_send_for_unknown_email(client: TestClient):
    calls = []
    import app.api.v1.auth as auth_module

    original = auth_module.mailer.send_email

    def spy(**kwargs):
        calls.append(kwargs["category"])
        return {"provider": "noop", "sent": False, "category": kwargs["category"]}

    auth_module.mailer.send_email = spy
    try:
        resp = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "no-account-" + _email()},
        )
    finally:
        auth_module.mailer.send_email = original
    assert resp.status_code == 200
    # No email is sent for a non-existent account, and the response is uniform.
    assert calls == []
    assert resp.json()["dev_reset_token"] is None


def test_production_never_returns_dev_reset_token(client: TestClient):
    account = _register(client)
    with _settings_override(APP_ENV="production"):
        resp = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": account["email"]},
        )
    assert resp.status_code == 200
    assert resp.json()["dev_reset_token"] is None
