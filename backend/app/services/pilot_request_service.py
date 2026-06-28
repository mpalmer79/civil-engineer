"""Service for public pilot / design-partner requests.

Pilot requests are public leads, not tenant-owned project data. This service
creates them (public), and lists, filters, updates operator state for, and
exports them (operator-gated at the route layer). It sends no email and contacts
no external service; persistence is local.
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.schemas.pilot import PilotRequestCreate


def _short() -> str:
    return uuid.uuid4().hex[:12]


def _now() -> datetime:
    return datetime.now(timezone.utc)


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


def list_pilot_requests(
    db: Session,
    *,
    status: str | None = None,
    interest_level: str | None = None,
    has_sample_package: bool | None = None,
) -> list[models.PilotRequest]:
    """Return pilot requests, newest first, with optional operator filters.

    Caller must enforce operator authorization at the route layer.
    """

    stmt = select(models.PilotRequest)
    if status:
        stmt = stmt.where(models.PilotRequest.status == status)
    if interest_level:
        stmt = stmt.where(models.PilotRequest.interest_level == interest_level)
    if has_sample_package is not None:
        stmt = stmt.where(
            models.PilotRequest.has_sample_package == has_sample_package
        )
    stmt = stmt.order_by(models.PilotRequest.created_at.desc())
    return list(db.execute(stmt).scalars().all())


def get_pilot_request(
    db: Session, pilot_request_id: str
) -> models.PilotRequest | None:
    return db.get(models.PilotRequest, pilot_request_id)


def update_status(
    db: Session,
    pilot_request_id: str,
    *,
    status: str,
    mark_contacted: bool = False,
) -> models.PilotRequest | None:
    """Update a request's operator pipeline status. Returns None if not found."""

    record = db.get(models.PilotRequest, pilot_request_id)
    if record is None:
        return None
    record.status = status
    if mark_contacted:
        record.last_contacted_at = _now()
    db.commit()
    db.refresh(record)
    return record


def update_internal_notes(
    db: Session,
    pilot_request_id: str,
    *,
    internal_notes: str | None,
) -> models.PilotRequest | None:
    """Update a request's operator-only internal notes. None clears the notes."""

    record = db.get(models.PilotRequest, pilot_request_id)
    if record is None:
        return None
    cleaned = internal_notes.strip() if internal_notes else None
    record.internal_notes = cleaned or None
    db.commit()
    db.refresh(record)
    return record


# Columns exported to CSV. No file content exists to export, and no secret or
# auth field is ever included.
_EXPORT_COLUMNS: tuple[str, ...] = (
    "created_at",
    "status",
    "full_name",
    "work_email",
    "firm_name",
    "role_title",
    "project_type",
    "interest_level",
    "has_sample_package",
    "last_contacted_at",
    "primary_pain",
    "notes",
    "internal_notes",
)


def export_pilot_requests_csv(db: Session) -> str:
    """Build a CSV of all pilot requests for an operator. No file content."""

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(_EXPORT_COLUMNS)
    for record in list_pilot_requests(db):
        writer.writerow(
            [
                record.created_at.isoformat() if record.created_at else "",
                record.status,
                record.full_name,
                record.work_email,
                record.firm_name,
                record.role_title,
                record.project_type,
                record.interest_level,
                "yes" if record.has_sample_package else "no",
                record.last_contacted_at.isoformat()
                if record.last_contacted_at
                else "",
                record.primary_pain,
                record.notes or "",
                record.internal_notes or "",
            ]
        )
    return buffer.getvalue()
