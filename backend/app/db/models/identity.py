"""Identity and access domain: actors, user accounts, organizations,
memberships, per-project access, password reset, invitations, and pilot
requests."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.shared import _utcnow

class Actor(Base):
    """A lightweight reviewer or actor identity for real-action attribution.

    Sprint 1 has no real authentication. This records a demo reviewer identity
    so real actions (project creation, document registration, reviewer findings)
    carry attribution that real authentication can replace later. It is not an
    authentication or authorization record and grants no access.
    """

    __tablename__ = "actors"

    actor_id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    actor_type: Mapped[str] = mapped_column(String, nullable=False)
    organization_name: Mapped[str | None] = mapped_column(String, nullable=True)
    role_label: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class UserAccount(Base):
    """A real local user account for authentication (Sprint 5).

    Civil Engineer AI adds a local authentication foundation so real actions can
    be attributed to a signed-in user instead of a shared demo reviewer. The
    password is never stored in plaintext; only a PBKDF2 hash is kept and it is
    never returned by the API. This is a local auth foundation, not enterprise
    SSO, and it grants no engineering authority.
    """

    __tablename__ = "user_accounts"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_demo_user: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )


class Organization(Base):
    """An organization account that groups users and projects (Sprint 5)."""

    __tablename__ = "organizations"

    organization_id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_name: Mapped[str] = mapped_column(String, nullable=False)
    organization_type: Mapped[str] = mapped_column(
        String, default="municipality"
    )
    source_mode: Mapped[str] = mapped_column(String, default="user_created")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    memberships: Mapped[list["OrganizationMembership"]] = relationship(
        back_populates="organization"
    )


class OrganizationMembership(Base):
    """A user's role within an organization (Sprint 5)."""

    __tablename__ = "organization_memberships"

    membership_id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.organization_id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("user_accounts.user_id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String, default="reviewer")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    organization: Mapped["Organization"] = relationship(
        back_populates="memberships"
    )


class ProjectAccess(Base):
    """A user or organization grant of access to a project (Sprint 5).

    Access controls who may view or take reviewer actions on a project's review
    records. It never controls whether a project satisfies engineering
    requirements and never implies approval or compliance.
    """

    __tablename__ = "project_access"

    project_access_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    organization_id: Mapped[str | None] = mapped_column(
        ForeignKey("organizations.organization_id"), nullable=True
    )
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("user_accounts.user_id"), nullable=True
    )
    access_level: Mapped[str] = mapped_column(String, default="reviewer")
    granted_by_user_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    # token_hash is a one-way hash of the reset token. The plaintext token is
    # returned to the requester (or surfaced to a dev mailer) and never stored.
    reset_token_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("user_accounts.user_id"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class OrganizationInvitation(Base):
    __tablename__ = "organization_invitations"

    # token_hash is a one-way hash of the invitation token. The plaintext token is
    # delivered through the mailer (or returned in non-production) and never
    # stored. status is one of ALLOWED_INVITATION_STATUSES; expiry is enforced at
    # read time against expires_at.
    invitation_id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.organization_id"), nullable=False
    )
    email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String, nullable=False, default="reviewer")
    token_hash: Mapped[str] = mapped_column(String, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    invited_by_user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    accepted_by_user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )


class PilotRequest(Base):
    """A public design-partner / pilot request captured from the marketing site.

    A pilot request is a public lead, not tenant-owned project data. It is never
    attached to a project, organization, or user account, and it carries no
    review-support state. Anyone can submit one without a login; listing stored
    requests requires an authenticated user. No uploaded file content is stored;
    the sample_package flag only records that the submitter said they have a
    sample package to test.
    """

    __tablename__ = "pilot_requests"

    pilot_request_id: Mapped[str] = mapped_column(String, primary_key=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    work_email: Mapped[str] = mapped_column(String, nullable=False)
    firm_name: Mapped[str] = mapped_column(String, nullable=False)
    role_title: Mapped[str] = mapped_column(String, nullable=False)
    project_type: Mapped[str] = mapped_column(String, nullable=False)
    primary_pain: Mapped[str] = mapped_column(Text, nullable=False)
    interest_level: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_sample_package: Mapped[bool] = mapped_column(default=False)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    # Operator pipeline state. status tracks the design-partner conversation;
    # internal_notes are operator-only and never returned by the public POST.
    # last_contacted_at records the most recent outreach. These support pilot
    # operations only and carry no review-support or engineering meaning.
    status: Mapped[str] = mapped_column(String, nullable=False, default="new")
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_contacted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )


# ---------------------------------------------------------------------------
# Production Phase 4B/4C: auth lifecycle, team invitations, billing and usage
# ---------------------------------------------------------------------------
#
# These tables support the production SaaS account lifecycle. They carry no file
# content, no document text, and no secret value. Reset and invitation tokens are
# stored only as a one-way hash, never in plaintext. Subscription and usage rows
# are billing-posture and metering state; none implies a review outcome,
# approval, certification, or compliance.
