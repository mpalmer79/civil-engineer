"""Organizations, memberships, and demo seeding.

Seeds the demo organization, demo users, memberships, and demo project access,
and reads organization membership. Access control protects review records and
improves audit attribution. It never controls whether a project satisfies
engineering requirements and never implies approval, certification, or
compliance.
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models
from app.services import auth_service

from app.services.access_control_service._common import (
    DEMO_ADMIN_EMAIL,
    DEMO_ADMIN_NAME,
    DEMO_ADMIN_USER_ID,
    DEMO_ORG_ID,
    DEMO_ORG_NAME,
    DEMO_REVIEWER_EMAIL,
    DEMO_REVIEWER_NAME,
    DEMO_REVIEWER_USER_ID,
    _now,
    _short,
)


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------


def ensure_auth_seed(db: Session) -> None:
    """Seed the demo organization, demo users, memberships, and demo access.

    Idempotent. The seeded passwords are local demo only and are documented as
    such; they must be changed or disabled before any real use.
    """

    settings = get_settings()
    org = db.get(models.Organization, DEMO_ORG_ID)
    if org is None:
        now = _now()
        org = models.Organization(
            organization_id=DEMO_ORG_ID,
            organization_name=DEMO_ORG_NAME,
            organization_type="internal_demo",
            source_mode="seeded_demo",
            created_at=now,
            updated_at=now,
        )
        db.add(org)

    if settings.AUTH_SEED_DEMO_USERS:
        _ensure_demo_user(
            db,
            user_id=DEMO_REVIEWER_USER_ID,
            email=DEMO_REVIEWER_EMAIL,
            display_name=DEMO_REVIEWER_NAME,
            password=settings.AUTH_DEMO_REVIEWER_PASSWORD,
            role="reviewer",
        )
        _ensure_demo_user(
            db,
            user_id=DEMO_ADMIN_USER_ID,
            email=DEMO_ADMIN_EMAIL,
            display_name=DEMO_ADMIN_NAME,
            password=settings.AUTH_DEMO_ADMIN_PASSWORD,
            role="org_admin",
        )

    # Mark the seeded public demo project (Brookside Meadows by default, see
    # PUBLIC_DEMO_PROJECT_ID) as a public demo so it stays readable without a
    # login, and grant the demo reviewer reviewer access.
    demo_project_id = settings.PUBLIC_DEMO_PROJECT_ID
    project = db.get(models.Project, demo_project_id)
    if project is not None:
        project.demo_public = True
        project.visibility_mode = "demo_public"
        if project.organization_id is None:
            project.organization_id = DEMO_ORG_ID
        _ensure_project_access(
            db,
            project_id=demo_project_id,
            user_id=DEMO_REVIEWER_USER_ID,
            access_level="reviewer",
        )
        _ensure_project_access(
            db,
            project_id=demo_project_id,
            user_id=DEMO_ADMIN_USER_ID,
            access_level="project_admin",
        )


def _ensure_demo_user(
    db: Session,
    *,
    user_id: str,
    email: str,
    display_name: str,
    password: str,
    role: str,
) -> models.UserAccount:
    user = db.get(models.UserAccount, user_id)
    if user is None:
        now = _now()
        user = models.UserAccount(
            user_id=user_id,
            email=email,
            display_name=display_name,
            password_hash=auth_service.hash_password(password),
            is_active=True,
            is_demo_user=True,
            created_at=now,
            updated_at=now,
        )
        db.add(user)
    membership = db.scalars(
        select(models.OrganizationMembership).where(
            models.OrganizationMembership.organization_id == DEMO_ORG_ID,
            models.OrganizationMembership.user_id == user_id,
        )
    ).first()
    if membership is None:
        db.add(
            models.OrganizationMembership(
                membership_id=f"mem_{_short()}",
                organization_id=DEMO_ORG_ID,
                user_id=user_id,
                role=role,
                is_active=True,
            )
        )
    return user


def _ensure_project_access(
    db: Session,
    *,
    project_id: str,
    user_id: str,
    access_level: str,
) -> None:
    existing = db.scalars(
        select(models.ProjectAccess).where(
            models.ProjectAccess.project_id == project_id,
            models.ProjectAccess.user_id == user_id,
        )
    ).first()
    if existing is None:
        db.add(
            models.ProjectAccess(
                project_access_id=f"pacc_{_short()}",
                project_id=project_id,
                user_id=user_id,
                access_level=access_level,
                is_active=True,
            )
        )


# ---------------------------------------------------------------------------
# Organizations and memberships
# ---------------------------------------------------------------------------


def list_user_memberships(
    db: Session, user_id: str
) -> list[models.OrganizationMembership]:
    return list(
        db.scalars(
            select(models.OrganizationMembership).where(
                models.OrganizationMembership.user_id == user_id,
                models.OrganizationMembership.is_active.is_(True),
            )
        ).all()
    )


def list_user_organizations(db: Session, user_id: str) -> list[dict]:
    memberships = list_user_memberships(db, user_id)
    result: list[dict] = []
    for membership in memberships:
        org = db.get(models.Organization, membership.organization_id)
        if org is None:
            continue
        result.append(
            {
                "organization_id": org.organization_id,
                "organization_name": org.organization_name,
                "organization_type": org.organization_type,
                "source_mode": org.source_mode,
                "role": membership.role,
                "membership_id": membership.membership_id,
            }
        )
    return result


def get_organization(db: Session, organization_id: str) -> models.Organization:
    org = db.get(models.Organization, organization_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


def list_organization_members(
    db: Session, organization_id: str
) -> list[dict]:
    memberships = db.scalars(
        select(models.OrganizationMembership).where(
            models.OrganizationMembership.organization_id == organization_id
        )
    ).all()
    result: list[dict] = []
    for membership in memberships:
        user = db.get(models.UserAccount, membership.user_id)
        result.append(
            {
                "membership_id": membership.membership_id,
                "organization_id": membership.organization_id,
                "user_id": membership.user_id,
                "user_email": user.email if user else None,
                "display_name": user.display_name if user else None,
                "role": membership.role,
                "is_active": membership.is_active,
            }
        )
    return result


def user_org_ids(db: Session, user_id: str) -> set[str]:
    return {m.organization_id for m in list_user_memberships(db, user_id)}


def org_admin_org_ids(db: Session, user_id: str) -> set[str]:
    return {
        m.organization_id
        for m in list_user_memberships(db, user_id)
        if m.role == "org_admin"
    }


def primary_organization_id(db: Session, user_id: str) -> str | None:
    """Return the user's primary organization id, or None when they have none.

    Prefers an organization where the user is an org_admin (their own workspace),
    then falls back to their first active membership. Used to attach a created
    project to the creating user's organization so usage is organization-scoped.
    """

    memberships = list_user_memberships(db, user_id)
    if not memberships:
        return None
    admin = next((m for m in memberships if m.role == "org_admin"), None)
    return (admin or memberships[0]).organization_id
