"""Project access records: reading, resolving, and granting access.

Resolves the strongest active access level a user holds on a project, lists the
projects a user may read, and records access grants with an audit event. This
never controls whether a project satisfies engineering requirements and never
implies approval, certification, or compliance.
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.safety import ALLOWED_PROJECT_ACCESS_LEVELS
from app.db import models

from app.services.access_control_service._common import (
    _ACCESS_PRECEDENCE,
    _now,
    _short,
)
from app.services.access_control_service.organizations import (
    org_admin_org_ids,
    user_org_ids,
)


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
