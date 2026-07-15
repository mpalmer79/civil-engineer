"""Access requirement helpers used inside route handlers.

These functions decide who may read or take reviewer actions on a project and
who may manage access. They enforce authorization only. They never control
whether a project satisfies engineering requirements and never imply approval,
certification, or compliance.
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.safety import REVIEWER_ACCESS_LEVELS
from app.db import models
from app.services.auth_service import ActorContext

from app.services.access_control_service._common import (
    DEMO_ADMIN_EMAIL,
    DEMO_ADMIN_NAME,
    DEMO_ADMIN_USER_ID,
    DEMO_ORG_ID,
    _demo_reviewer_context,
    _require_project,
    _user_context,
)
from app.services.access_control_service.organizations import (
    org_admin_org_ids,
    user_org_ids,
)
from app.services.access_control_service.projects import effective_access_level


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


def require_org_member(
    db: Session, organization_id: str, user: models.UserAccount | None
) -> models.UserAccount:
    """Require the user to be a member of the organization. Returns the user.

    Raises 401 when anonymous and 403 when the user is not a member. Used to gate
    organization-scoped reads (members, invitations list, billing, usage).
    """

    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if organization_id not in user_org_ids(db, user.user_id):
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this organization.",
        )
    return user


def require_org_admin(
    db: Session, organization_id: str, user: models.UserAccount | None
) -> models.UserAccount:
    """Require the user to be an org_admin of the organization. Returns the user.

    Raises 401 when anonymous and 403 when the user is not an org_admin of the
    organization. Used to gate team management (invite, revoke) and other
    owner/admin organization actions.
    """

    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if organization_id not in org_admin_org_ids(db, user.user_id):
        raise HTTPException(
            status_code=403,
            detail="Organization admin access is required for this action.",
        )
    return user


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
