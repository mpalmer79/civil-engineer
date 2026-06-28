"""Service for public pilot / design-partner requests.

Pilot requests are public leads, not tenant-owned project data. This service
only creates and lists them. It sends no email and contacts no external service;
persistence is local. Listing is intended for an authenticated caller, enforced
at the route layer.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.schemas.pilot import PilotRequestCreate


def _short() -> str:
    return uuid.uuid4().hex[:12]


def create_pilot_request(
    db: Session,
    payload: PilotRequestCreate,
    *,
    source: str | None = None,
) -> models.PilotRequest:
    """Persist a public pilot request and return the stored record.

    No file content is stored. has_sample_package only records the submitter's
    self-reported intent to share a sample package later.
    """

    record = models.PilotRequest(
        pilot_request_id=f"pilot_{_short()}",
        full_name=payload.full_name.strip(),
        work_email=payload.work_email.strip(),
        firm_name=payload.firm_name.strip(),
        role_title=payload.role_title.strip(),
        project_type=payload.project_type.strip(),
        primary_pain=payload.primary_pain.strip(),
        interest_level=payload.interest_level.strip(),
        notes=(payload.notes.strip() if payload.notes else None),
        has_sample_package=bool(payload.has_sample_package),
        source=source,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_pilot_requests(db: Session) -> list[models.PilotRequest]:
    """Return all pilot requests, newest first. Caller must enforce auth."""

    stmt = select(models.PilotRequest).order_by(
        models.PilotRequest.created_at.desc()
    )
    return list(db.execute(stmt).scalars().all())
