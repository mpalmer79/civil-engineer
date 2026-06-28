"""Email subjects and bodies for account-lifecycle messages (Phase 4D).

Builds the password reset and invitation emails, including the public link the
recipient follows. The raw token appears only inside the link sent to the
recipient; it is never logged (the mailer logs no body or URL). The copy is
review-support only and makes no engineering or compliance claim.
"""

from __future__ import annotations

from app.core.config import Settings, get_settings


def _base_url(settings: Settings | None) -> str:
    return (settings or get_settings()).public_base_url


def password_reset_email(token: str, *, settings: Settings | None = None) -> tuple[str, str]:
    """Return (subject, body) for a password reset email."""

    settings = settings or get_settings()
    link = f"{_base_url(settings)}/reset-password/confirm?token={token}"
    minutes = settings.AUTH_PASSWORD_RESET_EXPIRE_MINUTES
    subject = "Reset your Civil Engineer AI password"
    body = (
        "We received a request to reset your Civil Engineer AI password.\n\n"
        f"Reset your password: {link}\n\n"
        f"This link expires in {minutes} minutes and can be used once. If you "
        "did not request a reset, you can safely ignore this message and your "
        "password will stay the same.\n"
    )
    return subject, body


def invitation_email(
    *,
    organization_name: str,
    role: str,
    token: str,
    settings: Settings | None = None,
) -> tuple[str, str]:
    """Return (subject, body) for a team invitation email."""

    settings = settings or get_settings()
    link = f"{_base_url(settings)}/invitations/accept?token={token}"
    days = settings.AUTH_INVITATION_EXPIRE_DAYS
    org = organization_name or "a workspace"
    subject = f"You're invited to {org} on Civil Engineer AI"
    body = (
        f"You have been invited to join {org} on Civil Engineer AI as "
        f"'{role}'.\n\n"
        f"Accept your invitation: {link}\n\n"
        f"This invitation expires in {days} days. Civil Engineer AI is "
        "review-support tooling for pre-submittal QA; a human reviewer remains "
        "responsible for every finding. If you were not expecting this "
        "invitation, you can ignore this message.\n"
    )
    return subject, body
