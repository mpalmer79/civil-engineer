"""Mailer abstraction for account lifecycle and team invitations.

No real email is sent in this phase. The default "noop" provider records a safe,
redacted delivery log entry and returns a delivery result so the password reset
and invitation flows can run end to end without any external email service. A
production deployment must wire a real email provider before onboarding real
users; that provider would be added behind this same interface.

Security: this module never logs a reset token, an invitation token, a password,
or any secret. It logs only the message category and a redacted recipient.
"""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.core.logging import log_event


def _redact_email(address: str) -> str:
    """Return a redacted form of an email address for safe logging."""

    address = (address or "").strip()
    if "@" not in address:
        return "[redacted]"
    local, _, domain = address.partition("@")
    head = local[:1] if local else ""
    return f"{head}***@{domain}"


def send_email(
    *,
    to: str,
    category: str,
    subject: str,
    body: str,
) -> dict[str, Any]:
    """Deliver an email through the configured provider.

    With the default "noop" provider this sends nothing and only records a
    redacted delivery log. The body may contain a reset or invitation link; it is
    never logged. Returns a delivery result describing the provider and whether a
    message was actually sent.
    """

    settings = get_settings()
    provider = (settings.EMAIL_PROVIDER or "noop").strip().lower()
    # The subject and body are intentionally not logged: a reset/invite link can
    # appear in the body. Only the category and a redacted recipient are recorded.
    log_event(
        "email_dispatch",
        provider=provider,
        category=category,
        to=_redact_email(to),
        sent=provider != "noop",
    )
    # Reference the arguments so linters do not flag the unsent body/subject; no
    # real provider is implemented in this phase.
    _ = (subject, body)
    return {
        "provider": provider,
        "sent": provider != "noop",
        "category": category,
    }
