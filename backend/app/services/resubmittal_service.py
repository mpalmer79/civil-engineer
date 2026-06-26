"""Resubmittal round collaboration service (Sprint 7).

Registers resubmittal rounds, associates uploaded documents with a round,
summarizes a round, and carries open response matrix items forward into a round.

Everything here is review-support only. Registering a resubmittal round records
an applicant submission for reviewer review; it never decides whether the
resubmittal satisfies engineering requirements and never resolves or closes
anything. Audit metadata records ids, statuses, and counts only; it never records
storage keys, raw server file paths, secrets, or full document content.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_CARRY_FORWARD_STATUSES_V2,
    ALLOWED_RESUBMITTAL_ROUND_STATUSES,
    reject_prohibited_language,
)
from app.db import models
from app.services.auth_service import ActorContext, audit_kwargs
from app.services.real_intake_service import record_audit_event


class ResubmittalError(Exception):
    """Raised when a resubmittal operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


def _actor_name(actor: ActorContext | None) -> str:
    return actor.display_name if actor else "Demo Reviewer"


def _require_project(db: Session, project_id: str) -> models.Project:
    project = db.get(models.Project, project_id)
    if project is None:
        raise ResubmittalError("Project not found.", status_code=404)
    return project


def register_resubmittal_round(
    db: Session,
    project_id: str,
    payload: dict | None = None,
    *,
    actor: ActorContext | None = None,
) -> dict:
    """Register a resubmittal round for a project."""

    project = _require_project(db, project_id)
    payload = payload or {}
    for field in ("round_label", "summary", "submitted_by_name"):
        reject_prohibited_language(payload.get(field), field=field)

    status = payload.get("status") or "round_registered"
    if status not in ALLOWED_RESUBMITTAL_ROUND_STATUSES:
        raise ResubmittalError(
            f"Invalid resubmittal status '{status}'.", status_code=422
        )

    existing = db.scalars(
        select(models.ResubmittalRound).where(
            models.ResubmittalRound.project_id == project_id
        )
    ).all()
    round_number = payload.get("round_number") or (len(existing) + 2)
    now = _now()
    rnd = models.ResubmittalRound(
        resubmittal_round_id=f"rsr_{_short()}",
        project_id=project_id,
        response_matrix_id=payload.get("response_matrix_id"),
        round_number=int(round_number),
        round_label=(payload.get("round_label") or f"Resubmittal round {round_number}"),
        received_at=now,
        submitted_by_name=payload.get("submitted_by_name"),
        submitted_by_organization=payload.get("submitted_by_organization"),
        status=status,
        summary=payload.get("summary"),
        document_ids=[],
        carried_forward_item_ids=[],
        source_mode="user_created",
        organization_id=actor.organization_id if actor else None,
        created_by_user_id=actor.user_id if actor else None,
        created_by_name=_actor_name(actor),
        created_at=now,
        updated_at=now,
    )
    db.add(rnd)
    # Advance the project's current review round so later items carry the round.
    if int(round_number) > (project.review_round_current or 1):
        project.review_round_current = int(round_number)
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="resubmittal_round_registered",
        related_entity_type="resubmittal_round",
        related_entity_id=rnd.resubmittal_round_id,
        description=f"Reviewer registered {rnd.round_label}.",
        actor_type="reviewer",
        actor_id=actor.user_id if actor else None,
        actor_display_name=_actor_name(actor),
        metadata={
            "resubmittal_round_id": rnd.resubmittal_round_id,
            "round_number": rnd.round_number,
            "status": status,
        },
    )
    db.commit()
    db.refresh(rnd)
    return _round_dict(rnd)


def list_resubmittal_rounds(db: Session, project_id: str) -> list[dict]:
    _require_project(db, project_id)
    rounds = db.scalars(
        select(models.ResubmittalRound)
        .where(models.ResubmittalRound.project_id == project_id)
        .order_by(models.ResubmittalRound.round_number)
    ).all()
    return [_round_dict(r) for r in rounds]


def _require_round(
    db: Session, project_id: str, round_id: str
) -> models.ResubmittalRound:
    rnd = db.get(models.ResubmittalRound, round_id)
    if rnd is None or rnd.project_id != project_id:
        raise ResubmittalError("Resubmittal round not found.", status_code=404)
    return rnd


def get_resubmittal_round(db: Session, project_id: str, round_id: str) -> dict:
    return _round_dict(_require_round(db, project_id, round_id))


def _round_dict(rnd: models.ResubmittalRound) -> dict:
    return {
        "resubmittal_round_id": rnd.resubmittal_round_id,
        "project_id": rnd.project_id,
        "response_matrix_id": rnd.response_matrix_id,
        "round_number": rnd.round_number,
        "round_label": rnd.round_label,
        "received_at": rnd.received_at,
        "submitted_by_name": rnd.submitted_by_name,
        "submitted_by_organization": rnd.submitted_by_organization,
        "status": rnd.status,
        "summary": rnd.summary,
        "document_ids": rnd.document_ids or [],
        "carried_forward_item_ids": rnd.carried_forward_item_ids or [],
        "document_count": len(rnd.document_ids or []),
        "carried_forward_item_count": len(rnd.carried_forward_item_ids or []),
        "created_by_name": rnd.created_by_name,
        "created_at": rnd.created_at,
        "updated_at": rnd.updated_at,
    }


def link_document_to_resubmittal_round(
    db: Session,
    project_id: str,
    round_id: str,
    document_id: str,
    payload: dict | None = None,
    *,
    actor: ActorContext | None = None,
) -> dict:
    """Associate an uploaded document with a resubmittal round."""

    rnd = _require_round(db, project_id, round_id)
    document = db.get(models.Document, document_id)
    if document is None or document.project_id != project_id:
        raise ResubmittalError(
            "Document not found for this project.", status_code=404
        )
    document_ids = list(rnd.document_ids or [])
    if document_id not in document_ids:
        document_ids.append(document_id)
        rnd.document_ids = document_ids
    if rnd.status == "round_registered":
        rnd.status = "documents_received"
    rnd.updated_at = _now()
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="resubmittal_document_linked",
        related_entity_type="resubmittal_round",
        related_entity_id=round_id,
        description="Reviewer linked a document to a resubmittal round.",
        actor_type="reviewer",
        actor_id=actor.user_id if actor else None,
        actor_display_name=_actor_name(actor),
        metadata={
            "resubmittal_round_id": round_id,
            "document_id": document_id,
            "document_count": len(document_ids),
        },
    )
    db.commit()
    db.refresh(rnd)
    return _round_dict(rnd)


def summarize_resubmittal_round(
    db: Session, project_id: str, round_id: str
) -> dict:
    """Return safe summary counts for a resubmittal round."""

    rnd = _require_round(db, project_id, round_id)
    items = []
    if rnd.response_matrix_id:
        items = list(
            db.scalars(
                select(models.ResponseMatrixItem).where(
                    models.ResponseMatrixItem.response_matrix_id
                    == rnd.response_matrix_id
                )
            ).all()
        )
    applicant_summary: dict[str, int] = {}
    carry_summary: dict[str, int] = {}
    for item in items:
        applicant_summary[item.applicant_response_status] = (
            applicant_summary.get(item.applicant_response_status, 0) + 1
        )
        carry_summary[item.carry_forward_status] = (
            carry_summary.get(item.carry_forward_status, 0) + 1
        )
    return {
        "resubmittal_round_id": rnd.resubmittal_round_id,
        "project_id": project_id,
        "round_number": rnd.round_number,
        "status": rnd.status,
        "document_count": len(rnd.document_ids or []),
        "carried_forward_item_count": len(rnd.carried_forward_item_ids or []),
        "matrix_item_count": len(items),
        "applicant_response_summary": applicant_summary,
        "carry_forward_summary": carry_summary,
    }


def carry_forward_items_to_round(
    db: Session,
    project_id: str,
    round_id: str,
    payload: dict | None = None,
    *,
    actor: ActorContext | None = None,
) -> dict:
    """Carry forward a set of matrix items into a resubmittal round for review."""

    rnd = _require_round(db, project_id, round_id)
    payload = payload or {}
    item_ids = payload.get("matrix_item_ids") or []
    status = payload.get("carry_forward_status") or "carried_forward_for_review"
    if status not in ALLOWED_CARRY_FORWARD_STATUSES_V2:
        raise ResubmittalError(
            f"Invalid carry_forward_status '{status}'.", status_code=422
        )

    carried: list[str] = list(rnd.carried_forward_item_ids or [])
    for item_id in item_ids:
        item = db.get(models.ResponseMatrixItem, item_id)
        if item is None or item.project_id != project_id:
            continue
        item.carry_forward_status = status
        item.carried_from_round_number = item.current_round_number
        item.carried_to_round_number = rnd.round_number
        item.current_round_number = rnd.round_number
        item.updated_at = _now()
        if item_id not in carried:
            carried.append(item_id)
    rnd.carried_forward_item_ids = carried
    rnd.updated_at = _now()
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="resubmittal_items_carried_forward",
        related_entity_type="resubmittal_round",
        related_entity_id=round_id,
        description=(
            f"Reviewer carried {len(item_ids)} item(s) forward into "
            f"{rnd.round_label} for review."
        ),
        actor_type="reviewer",
        actor_id=actor.user_id if actor else None,
        actor_display_name=_actor_name(actor),
        metadata={
            "resubmittal_round_id": round_id,
            "carried_forward_item_count": len(carried),
            "carry_forward_status": status,
        },
    )
    db.commit()
    db.refresh(rnd)
    return _round_dict(rnd)
