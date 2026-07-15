"""Shared constants and helpers for access control.

Seeded demo identities, access-level precedence, and small context builders used
across the access control submodules. These helpers never control whether a
project satisfies engineering requirements and never imply approval,
certification, or compliance.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.services.auth_service import ActorContext

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


def _require_project(db: Session, project_id: str) -> models.Project:
    project = db.get(models.Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
