"""Mailer abstraction for account lifecycle and team invitations.

The default "noop" provider records a safe, redacted delivery log and sends
nothing, which keeps local development and tests free of any email service. The
"smtp" provider (Production Phase 4D) delivers real email through a configured
SMTP server using the Python standard library, so no third-party dependency is
required. Provider-specific code is isolated in this module; business logic calls
`send_email` and never imports a vendor client.

Security: this module never logs a reset token, an invitation token, a full
reset/invite URL, an email body, a subject, or any SMTP credential. It logs only
the provider, the message category, a redacted recipient, and whether a message
was sent.
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import log_event


def _redact_email(address: str) -> str:
    """Return a redacted form of an email address for safe logging."""

    address = (address or "").strip()
    if "@" not in address:
        return "[redacted]"
    local, _, domain = address.partition("@")
    head = local[:1] if local else ""
    return f"{head}***@{domain}"


def _send_smtp(settings: Settings, *, to: str, subject: str, body: str) -> None:
    """Deliver one message through the configured SMTP server.

    Raises on any SMTP failure so the caller can record a safe failure result.
    The credential is read here only; it is never logged.
    """

    message = EmailMessage()
    message["From"] = settings.EMAIL_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    host = settings.EMAIL_SMTP_HOST
    port = settings.EMAIL_SMTP_PORT
    with smtplib.SMTP(host, port, timeout=10) as server:
        if settings.EMAIL_SMTP_USE_TLS:
            server.starttls()
        if settings.EMAIL_SMTP_USERNAME:
            server.login(settings.EMAIL_SMTP_USERNAME, settings.EMAIL_SMTP_PASSWORD)
        server.send_message(message)


def send_email(
    *,
    to: str,
    category: str,
    subject: str,
    body: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Deliver an email through the configured provider.

    Returns a delivery result describing the provider and whether a message was
    actually sent. With the default "noop" provider nothing is sent. With the
    "smtp" provider a real message is sent; on failure the result reports
    sent=False with a generic error and the failure is logged without any secret,
    token, URL, subject, or body.
    """

    settings = settings or get_settings()
    provider = (settings.EMAIL_PROVIDER or "noop").strip().lower()

    if provider != "smtp" or not settings.email_configured:
        # noop (or misconfigured smtp): record a redacted log and send nothing.
        log_event(
            "email_dispatch",
            provider="noop" if provider != "smtp" else "smtp_unconfigured",
            category=category,
            to=_redact_email(to),
            sent=False,
        )
        return {"provider": "noop", "sent": False, "category": category}

    try:
        _send_smtp(settings, to=to, subject=subject, body=body)
        log_event(
            "email_dispatch",
            provider="smtp",
            category=category,
            to=_redact_email(to),
            sent=True,
        )
        return {"provider": "smtp", "sent": True, "category": category}
    except Exception:  # noqa: BLE001 - a delivery failure is reported safely
        # Never log the exception detail: it can contain the recipient, subject,
        # or server hints. Record only that a send failed for this category.
        log_event(
            "email_dispatch",
            provider="smtp",
            category=category,
            to=_redact_email(to),
            sent=False,
            error="delivery_failed",
        )
        return {
            "provider": "smtp",
            "sent": False,
            "category": category,
            "error": "delivery_failed",
        }
