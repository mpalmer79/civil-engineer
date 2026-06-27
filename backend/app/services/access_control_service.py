"""Authorization and project access control (Sprint 5).

Builds on the local authentication foundation in auth_service. Resolves the
current user from a bearer token, decides who may read or take reviewer actions
on a project, and records access grants. The seeded Brookside Meadows demo
remains publicly readable when AUTH_ALLOW_PUBLIC_DEMO is true, and demo reviewer
actions keep working when AUTH_DEMO_MODE is true so the public demo and the
existing seeded workflow are preserved.

Access control protects review records and improves audit attribution. It never
controls whether a project satisfies engineering requirements and never implies
approval, certification, or compliance.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.safety import (
    ALLOWED_MEMBERSHIP_ROLES,
    ALLOWED_ORGANIZATION_TYPES,
    ALLOWED_PROJECT_ACCESS_LEVELS,
    REVIEWER_ACCESS_LEVELS,
)
from app.db import models
from app.db.database import get_db
from app.services import auth_service
from app.services.auth_service import ActorContext, AuthError

# Seeded demo identities. The demo reviewer reuses the Sprint 1 demo display name
# so existing attribution assertions keep working.
DEMO_ORG_ID = "org_internal_demo"
DEMO_ORG_NAME = "Civil Engineer AI Demo Review Team"
DEMO_REVIEWER_USER_ID = "user_demo_reviewer"
DEMO_REVIEWER_EMAIL = "reviewer@example.com"
DEMO_REVIEWER_NAME = "Demo Reviewer"
DEMO_ADMIN_USER_ID = "user_demo_admin"
DEMO_ADMIN_EMAIL = "admin@example.com"
DEMO_ADMIN_NAME = "Demo Admin"
BROOKSIDE_PROJECT_ID = "proj_brookside_meadows"

# Precedence from strongest to weakest, used to pick the effective access level.
_ACCESS_PRECEDENCE = [
    "project_admin",
    "senior_reviewer",
    "reviewer",
    "read_only",
    "applicant_placeholder",
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


def _demo_reviewer_context(*, is_anonymous: bool = False) -> ActorContext:
    return ActorContext(
        display_name=DEMO_REVIEWER_NAME,
        actor_type="demo_reviewer",
        user_id=None if is_anonymous else DEMO_REVIEWER_USER_ID,
        user_email=None if is_anonymous else DEMO_REVIEWER_EMAIL,
        organization_id=DEMO_ORG_ID,
        access_level="reviewer",
        is_demo=True,
    )


def _user_context(
    user: models.UserAccount,
    *,
    access_level: str | None,
    organization_id: str | None,
    actor_type: str | None = None,
) -> ActorContext:
    return ActorContext(
        display_name=user.display_name,
        actor_type=actor_type or (access_level or "user"),
        user_id=user.user_id,
        user_email=user.email,
        organization_id=organization_id,
        access_level=access_level,
        is_demo=user.is_demo_user,
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

    # Mark the seeded Brookside Meadows demo project as a public demo so it stays
    # readable without a login, and grant the demo reviewer reviewer access.
    project = db.get(models.Project, BROOKSIDE_PROJECT_ID)
    if project is not None:
        project.demo_public = True
        project.visibility_mode = "demo_public"
        if project.organization_id is None:
            project.organization_id = DEMO_ORG_ID
        _ensure_project_access(
            db,
            project_id=BROOKSIDE_PROJECT_ID,
            user_id=DEMO_REVIEWER_USER_ID,
            access_level="reviewer",
        )
        _ensure_project_access(
            db,
            project_id=BROOKSIDE_PROJECT_ID,
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


# ---------------------------------------------------------------------------
# Project access
# ---------------------------------------------------------------------------


def list_project_access(
    db: Session, project_id: str
) -> list[models.ProjectAccess]:
    return list(
        db.scalars(
            select(models.ProjectAccess).where(
                models.ProjectAccess.project_id == project_id
            )
        ).all()
    )


def effective_access_level(
    db: Session, project_id: str, user: models.UserAccount
) -> str | None:
    """Return the strongest active access level a user has on a project, or None."""

    org_ids = user_org_ids(db, user.user_id)
    levels: list[str] = []
    for access in list_project_access(db, project_id):
        if not access.is_active:
            continue
        if access.user_id == user.user_id:
            levels.append(access.access_level)
        elif access.organization_id and access.organization_id in org_ids:
            levels.append(access.access_level)
    # org_admins of the project's organization implicitly hold project_admin.
    project = db.get(models.Project, project_id)
    if project is not None and project.organization_id in org_admin_org_ids(
        db, user.user_id
    ):
        levels.append("project_admin")
    for level in _ACCESS_PRECEDENCE:
        if level in levels:
            return level
    return None


def grant_project_access(
    db: Session,
    project_id: str,
    *,
    access_level: str,
    user_id: str | None = None,
    organization_id: str | None = None,
    granted_by_user_id: str | None = None,
    granted_by_name: str = "Demo Admin",
) -> models.ProjectAccess:
    """Grant a user or organization access to a project and write an audit event."""

    from app.services.real_intake_service import record_audit_event

    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if access_level not in ALLOWED_PROJECT_ACCESS_LEVELS:
        raise HTTPException(
            status_code=422, detail=f"Invalid access_level '{access_level}'."
        )
    if not user_id and not organization_id:
        raise HTTPException(
            status_code=422,
            detail="A user_id or organization_id is required.",
        )
    now = _now()
    access = models.ProjectAccess(
        project_access_id=f"pacc_{_short()}",
        project_id=project_id,
        user_id=user_id,
        organization_id=organization_id,
        access_level=access_level,
        granted_by_user_id=granted_by_user_id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(access)
    record_audit_event(
        db,
        project_id=project_id,
        event_type="project_access_granted",
        related_entity_type="project_access",
        related_entity_id=access.project_access_id,
        description=(
            f"{granted_by_name} granted {access_level} access to "
            f"{'user ' + user_id if user_id else 'organization ' + str(organization_id)}."
        ),
        actor_type="org_admin",
        actor_id=granted_by_user_id,
        actor_display_name=granted_by_name,
        metadata={
            "project_access_id": access.project_access_id,
            "access_level": access_level,
            "target_user_id": user_id,
            "target_organization_id": organization_id,
        },
        user_id=granted_by_user_id,
        organization_id=project.organization_id,
        access_level="project_admin",
    )
    db.commit()
    db.refresh(access)
    return access


def list_user_accessible_projects(
    db: Session, user: models.UserAccount
) -> list[models.Project]:
    """Return projects the user can read: demo_public plus their granted projects."""

    settings = get_settings()
    org_ids = user_org_ids(db, user.user_id)
    accessible: dict[str, models.Project] = {}
    for project in db.scalars(select(models.Project)).all():
        if project.demo_public and settings.AUTH_ALLOW_PUBLIC_DEMO:
            accessible[project.project_id] = project
            continue
        if effective_access_level(db, project.project_id, user) is not None:
            accessible[project.project_id] = project
            continue
        if project.organization_id and project.organization_id in org_ids:
            accessible[project.project_id] = project
    return list(accessible.values())


# ---------------------------------------------------------------------------
# Access requirement helpers (used inside route handlers)
# ---------------------------------------------------------------------------


def _require_project(db: Session, project_id: str) -> models.Project:
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def require_project_read(
    db: Session, project_id: str, user: models.UserAccount | None
) -> ActorContext:
    """Require read access to a project. Returns the resolved actor context."""

    settings = get_settings()
    project = _require_project(db, project_id)
    if project.demo_public and settings.AUTH_ALLOW_PUBLIC_DEMO:
        if user is not None:
            level = effective_access_level(db, project_id, user) or "read_only"
            return _user_context(
                user, access_level=level, organization_id=project.organization_id
            )
        return _demo_reviewer_context(is_anonymous=True)
    if user is None:
        if (
            not settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS
            and settings.AUTH_DEMO_MODE
        ):
            return _demo_reviewer_context()
        raise HTTPException(
            status_code=401,
            detail="Sign in to access this project's review records.",
        )
    level = effective_access_level(db, project_id, user)
    if level is None:
        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have access to this project. Ask a project admin or "
                "organization admin for access."
            ),
        )
    return _user_context(
        user, access_level=level, organization_id=project.organization_id
    )


def require_project_reviewer(
    db: Session, project_id: str, user: models.UserAccount | None
) -> ActorContext:
    """Require reviewer (write) access to a project."""

    settings = get_settings()
    project = _require_project(db, project_id)
    if user is not None:
        level = effective_access_level(db, project_id, user)
        if level in REVIEWER_ACCESS_LEVELS:
            return _user_context(
                user, access_level=level, organization_id=project.organization_id
            )
        if level is None and not (
            project.demo_public and settings.AUTH_DEMO_MODE
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "You do not have access to this project action. Ask a "
                    "project admin or organization admin for access."
                ),
            )
        if level is not None:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Your access level is read-only for this project. Ask a "
                    "project admin for reviewer access."
                ),
            )
        # Authenticated user with no explicit access on a public demo project
        # may act under the demo reviewer fallback.
        return _user_context(
            user,
            access_level="reviewer",
            organization_id=project.organization_id,
            actor_type="demo_reviewer",
        )
    # Unauthenticated.
    if project.demo_public and settings.AUTH_DEMO_MODE:
        return _demo_reviewer_context()
    if (
        not settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS
        and settings.AUTH_DEMO_MODE
    ):
        return _demo_reviewer_context()
    raise HTTPException(
        status_code=401,
        detail="Sign in to take reviewer actions on this project.",
    )


def require_project_admin(
    db: Session, project_id: str, user: models.UserAccount | None
) -> ActorContext:
    """Require project admin or organization admin access to a project."""

    settings = get_settings()
    project = _require_project(db, project_id)
    if user is not None:
        level = effective_access_level(db, project_id, user)
        if level == "project_admin":
            return _user_context(
                user, access_level=level, organization_id=project.organization_id
            )
        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have admin access to this project. Ask an "
                "organization admin for access."
            ),
        )
    if project.demo_public and settings.AUTH_DEMO_MODE:
        return ActorContext(
            display_name=DEMO_ADMIN_NAME,
            actor_type="org_admin",
            user_id=DEMO_ADMIN_USER_ID,
            user_email=DEMO_ADMIN_EMAIL,
            organization_id=DEMO_ORG_ID,
            access_level="project_admin",
            is_demo=True,
        )
    raise HTTPException(
        status_code=401, detail="Sign in to manage project access."
    )


def is_admin_user(db: Session, user: models.UserAccount) -> bool:
    """Return True if the user is an org_admin in at least one organization.

    Used to gate detailed deployment diagnostics (Sprint 10) to admin-level
    operators. It never grants engineering authority; it only controls who may
    read operational configuration status.
    """

    return bool(org_admin_org_ids(db, user.user_id))


def require_admin_user(
    db: Session, user: models.UserAccount | None
) -> ActorContext:
    """Require a signed-in organization admin. Returns the actor context.

    Raises 401 when no user is signed in and 403 when the user is not an
    org_admin in any organization. Detailed diagnostics never expose secrets, so
    this protects only the configuration-status surface.
    """

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Sign in as an organization admin to view diagnostics.",
        )
    if not is_admin_user(db, user):
        raise HTTPException(
            status_code=403,
            detail=(
                "Organization admin access is required to view deployment "
                "diagnostics."
            ),
        )
    org_ids = sorted(org_admin_org_ids(db, user.user_id))
    return _user_context(
        user,
        access_level="org_admin",
        organization_id=org_ids[0] if org_ids else None,
        actor_type="org_admin",
    )


def context_for_create(user: models.UserAccount | None) -> ActorContext:
    """Resolve the actor context for creating a new project (not yet scoped).

    Requires a signed-in user when AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS is true
    and demo mode is off; otherwise falls back to the demo reviewer.
    """

    settings = get_settings()
    if user is not None:
        return _user_context(
            user, access_level="project_admin", organization_id=None
        )
    # Creating a real project record requires a signed-in user when configured.
    # The public Brookside Meadows demo remains readable separately.
    if settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS:
        raise HTTPException(
            status_code=401, detail="Sign in to create a project."
        )
    return _demo_reviewer_context()


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------


def _token_from_header(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return authorization.strip()


def get_optional_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> models.UserAccount | None:
    """Resolve the signed-in user from the Authorization header, or None."""

    token = _token_from_header(authorization)
    if not token:
        return None
    try:
        return auth_service.get_current_user_from_token(db, token)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


def get_current_user(
    user: models.UserAccount | None = Depends(get_optional_user),
) -> models.UserAccount:
    """Require a signed-in user; raise 401 otherwise."""

    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user


# Re-export allowed sets for schema validation reuse.
__all__ = [
    "ActorContext",
    "ALLOWED_MEMBERSHIP_ROLES",
    "ALLOWED_ORGANIZATION_TYPES",
    "ALLOWED_PROJECT_ACCESS_LEVELS",
    "ensure_auth_seed",
    "get_optional_user",
    "get_current_user",
    "require_project_read",
    "require_project_reviewer",
    "require_project_admin",
    "require_admin_user",
    "is_admin_user",
    "context_for_create",
]
