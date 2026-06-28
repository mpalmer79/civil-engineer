"""Organization team invitations (Production Phase 4B).

An owner/admin (an org_admin member) can invite a teammate by email with a role,
list pending invitations, and revoke them. A new or existing user accepts an
invitation with the token, which creates an active membership in the
organization. Invitation tokens are stored only as a one-way hash and have an
expiry; expired, accepted, and revoked invitations cannot be reused.

Invitations control team membership and audit attribution only. They never grant
engineering authority and never imply approval, certification, or compliance.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services import auth_service

# Roles an invitation may assign. demo_reviewer and applicant_placeholder are
# internal/seed roles and are not invitable.
INVITABLE_ROLES: set[str] = {
    "org_admin",
    "senior_reviewer",
    "reviewer",
    "read_only",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


def _aware(value: datetime) -> datetime:
    """Return a timezone-aware UTC datetime (SQLite stores naive datetimes)."""

    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def derived_status(invitation: models.OrganizationInvitation) -> str:
    """Return the effective status, deriving 'expired' from the expiry time."""

    if invitation.status == "pending" and _aware(invitation.expires_at) < _now():
        return "expired"
    return invitation.status


def is_acceptable(invitation: models.OrganizationInvitation) -> bool:
    """Return True when an invitation can still be accepted."""

    return derived_status(invitation) == "pending"


def create_invitation(
    db: Session,
    *,
    organization_id: str,
    email: str,
    role: str,
    invited_by_user_id: str | None,
) -> tuple[models.OrganizationInvitation, str]:
    """Create a pending invitation and return (record, plaintext token).

    The plaintext token is returned for delivery and never stored; only its hash
    is persisted. Raises HTTPException(422) on an invalid email or role.
    """

    from app.core.config import get_settings

    normalized = (email or "").strip().lower()
    if "@" not in normalized or "." not in normalized.split("@")[-1]:
        raise HTTPException(status_code=422, detail="A valid email is required.")
    if role not in INVITABLE_ROLES:
        raise HTTPException(
            status_code=422, detail=f"Invalid invitation role '{role}'."
        )
    org = db.get(models.Organization, organization_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    settings = get_settings()
    token = auth_service.generate_opaque_token()
    now = _now()
    record = models.OrganizationInvitation(
        invitation_id=f"inv_{_short()}",
        organization_id=organization_id,
        email=normalized,
        role=role,
        token_hash=auth_service.hash_token(token),
        status="pending",
        invited_by_user_id=invited_by_user_id,
        expires_at=now + timedelta(days=settings.AUTH_INVITATION_EXPIRE_DAYS),
        created_at=now,
        updated_at=now,
    )
    db.add(record)
    db.flush()
    return record, token


def list_invitations(
    db: Session, organization_id: str
) -> list[models.OrganizationInvitation]:
    """Return all invitations for an organization, newest first."""

    return list(
        db.scalars(
            select(models.OrganizationInvitation)
            .where(
                models.OrganizationInvitation.organization_id == organization_id
            )
            .order_by(models.OrganizationInvitation.created_at.desc())
        ).all()
    )


def revoke_invitation(
    db: Session, *, organization_id: str, invitation_id: str
) -> models.OrganizationInvitation:
    """Revoke a pending invitation. Raises 404 if missing, 409 if not pending."""

    record = db.get(models.OrganizationInvitation, invitation_id)
    if record is None or record.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if record.status != "pending":
        raise HTTPException(
            status_code=409,
            detail="Only a pending invitation can be revoked.",
        )
    record.status = "revoked"
    record.revoked_at = _now()
    record.updated_at = _now()
    db.flush()
    return record


def _find_by_token(
    db: Session, token: str
) -> models.OrganizationInvitation | None:
    return db.scalars(
        select(models.OrganizationInvitation).where(
            models.OrganizationInvitation.token_hash
            == auth_service.hash_token(token)
        )
    ).first()


def lookup_invitation(db: Session, token: str) -> dict:
    """Return a safe preview of an invitation for the accept page. No token echo.

    Used by the public accept page to show the organization, email, and role
    before sign-in. Raises 404 when the token does not match any invitation.
    """

    record = _find_by_token(db, token)
    if record is None:
        raise HTTPException(status_code=404, detail="Invitation not found")
    org = db.get(models.Organization, record.organization_id)
    return {
        "organization_id": record.organization_id,
        "organization_name": org.organization_name if org else None,
        "email": record.email,
        "role": record.role,
        "status": derived_status(record),
        "acceptable": is_acceptable(record),
        "expires_at": record.expires_at,
    }


def accept_invitation(
    db: Session, *, token: str, user: models.UserAccount
) -> models.OrganizationMembership:
    """Accept an invitation for a signed-in user and return the membership.

    Creates an active membership in the organization with the invited role (or
    updates an existing membership's role). Marks the invitation accepted so it
    cannot be reused. Raises 400 when the invitation is not acceptable.
    """

    record = _find_by_token(db, token)
    if record is None:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if not is_acceptable(record):
        raise HTTPException(
            status_code=400,
            detail="This invitation is no longer valid.",
        )
    now = _now()
    membership = db.scalars(
        select(models.OrganizationMembership).where(
            models.OrganizationMembership.organization_id
            == record.organization_id,
            models.OrganizationMembership.user_id == user.user_id,
        )
    ).first()
    if membership is None:
        membership = models.OrganizationMembership(
            membership_id=f"mem_{_short()}",
            organization_id=record.organization_id,
            user_id=user.user_id,
            role=record.role,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(membership)
    else:
        membership.role = record.role
        membership.is_active = True
        membership.updated_at = now
    record.status = "accepted"
    record.accepted_at = now
    record.accepted_by_user_id = user.user_id
    record.updated_at = now
    db.flush()
    return membership


def invitation_public_dict(invitation: models.OrganizationInvitation) -> dict:
    """Return a safe dict for an invitation. The token hash is never included."""

    return {
        "invitation_id": invitation.invitation_id,
        "organization_id": invitation.organization_id,
        "email": invitation.email,
        "role": invitation.role,
        "status": derived_status(invitation),
        "invited_by_user_id": invitation.invited_by_user_id,
        "accepted_by_user_id": invitation.accepted_by_user_id,
        "expires_at": invitation.expires_at,
        "accepted_at": invitation.accepted_at,
        "revoked_at": invitation.revoked_at,
        "created_at": invitation.created_at,
    }
