"""Applicant response matrix service (Sprint 7).

Production Foundations Sprint 7 adds the first applicant response and resubmittal
collaboration foundation. A reviewer can organize review-support findings and
checklist items into a response matrix, record applicant responses, link response
documents, and carry items forward across resubmittal rounds.

Everything here is review-support only. An applicant response is recorded as
submitted content for reviewer review; it is never treated as proof and never
marks an item satisfied. Carry-forward means the item remains under review, not a
final resolution. Nothing here approves plans, certifies compliance, verifies
CAD, validates design, declares a project safe, resolves or closes an issue, or
makes any final engineering decision.

Audit metadata records ids, statuses, and counts only. It never records full
extracted page text, storage keys, raw server file paths, secrets, or tokens.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_APPLICANT_RESPONSE_STATUSES_V2,
    ALLOWED_CARRY_FORWARD_STATUSES_V2,
    ALLOWED_MATRIX_LINK_TYPES,
    ALLOWED_RESPONSE_MATRIX_STATUSES,
    ALLOWED_REVIEWER_FOLLOW_UP_STATUSES,
    reject_prohibited_language,
)
from app.db import models
from app.services.auth_service import ActorContext, audit_kwargs
from app.services.real_intake_service import record_audit_event


class ResponseMatrixError(Exception):
    """Raised when a response matrix operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


def _require_project(db: Session, project_id: str) -> models.Project:
    project = db.get(models.Project, project_id)
    if project is None:
        raise ResponseMatrixError("Project not found.", status_code=404)
    return project


def _actor_name(actor: ActorContext | None) -> str:
    return actor.display_name if actor else "Demo Reviewer"


# ---------------------------------------------------------------------------
# Matrices
# ---------------------------------------------------------------------------


def create_response_matrix(
    db: Session,
    project_id: str,
    payload: dict | None = None,
    *,
    actor: ActorContext | None = None,
) -> dict:
    """Create a response matrix for a project."""

    project = _require_project(db, project_id)
    payload = payload or {}
    name = (payload.get("name") or "Applicant response matrix").strip()
    reject_prohibited_language(name, field="name")

    now = _now()
    matrix = models.ResponseMatrix(
        response_matrix_id=f"rmtx_{_short()}",
        project_id=project_id,
        name=name,
        current_round_number=project.review_round_current or 1,
        status="matrix_started",
        source_mode="user_created",
        organization_id=actor.organization_id if actor else None,
        created_by_user_id=actor.user_id if actor else None,
        created_by_name=_actor_name(actor),
        created_at=now,
        updated_at=now,
    )
    db.add(matrix)
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="response_matrix_created",
        related_entity_type="response_matrix",
        related_entity_id=matrix.response_matrix_id,
        description=f"Reviewer created response matrix '{name}'.",
        actor_type="reviewer",
        actor_id=actor.user_id if actor else None,
        actor_display_name=_actor_name(actor),
        metadata={"response_matrix_id": matrix.response_matrix_id},
    )
    db.commit()
    db.refresh(matrix)
    return _matrix_dict(db, matrix)


def ensure_response_matrix(
    db: Session, project_id: str, *, actor: ActorContext | None = None
) -> dict:
    """Return the project's first response matrix, creating one if needed."""

    existing = db.scalars(
        select(models.ResponseMatrix)
        .where(models.ResponseMatrix.project_id == project_id)
        .order_by(models.ResponseMatrix.created_at)
    ).first()
    if existing is not None:
        return _matrix_dict(db, existing)
    return create_response_matrix(db, project_id, actor=actor)


def list_response_matrices(db: Session, project_id: str) -> list[dict]:
    _require_project(db, project_id)
    matrices = db.scalars(
        select(models.ResponseMatrix)
        .where(models.ResponseMatrix.project_id == project_id)
        .order_by(models.ResponseMatrix.created_at)
    ).all()
    return [_matrix_dict(db, m) for m in matrices]


def get_response_matrix(
    db: Session, project_id: str, response_matrix_id: str
) -> dict:
    matrix = _require_matrix(db, project_id, response_matrix_id)
    detail = _matrix_dict(db, matrix)
    detail["items"] = [
        _item_dict(item) for item in _matrix_items(db, response_matrix_id)
    ]
    return detail


def _require_matrix(
    db: Session, project_id: str, response_matrix_id: str
) -> models.ResponseMatrix:
    matrix = db.get(models.ResponseMatrix, response_matrix_id)
    if matrix is None or matrix.project_id != project_id:
        raise ResponseMatrixError("Response matrix not found.", status_code=404)
    return matrix


def _matrix_items(
    db: Session, response_matrix_id: str
) -> list[models.ResponseMatrixItem]:
    return list(
        db.scalars(
            select(models.ResponseMatrixItem)
            .where(
                models.ResponseMatrixItem.response_matrix_id
                == response_matrix_id
            )
            .order_by(models.ResponseMatrixItem.sort_order)
        ).all()
    )


def _matrix_dict(db: Session, matrix: models.ResponseMatrix) -> dict:
    items = _matrix_items(db, matrix.response_matrix_id)
    applicant_summary: dict[str, int] = {}
    follow_up_summary: dict[str, int] = {}
    carry_summary: dict[str, int] = {}
    for item in items:
        applicant_summary[item.applicant_response_status] = (
            applicant_summary.get(item.applicant_response_status, 0) + 1
        )
        follow_up_summary[item.reviewer_follow_up_status] = (
            follow_up_summary.get(item.reviewer_follow_up_status, 0) + 1
        )
        carry_summary[item.carry_forward_status] = (
            carry_summary.get(item.carry_forward_status, 0) + 1
        )
    return {
        "response_matrix_id": matrix.response_matrix_id,
        "project_id": matrix.project_id,
        "name": matrix.name,
        "current_round_number": matrix.current_round_number,
        "status": matrix.status,
        "source_mode": matrix.source_mode,
        "organization_id": matrix.organization_id,
        "created_by_name": matrix.created_by_name,
        "created_at": matrix.created_at,
        "updated_at": matrix.updated_at,
        "item_count": len(items),
        "applicant_response_summary": applicant_summary,
        "reviewer_follow_up_summary": follow_up_summary,
        "carry_forward_summary": carry_summary,
    }


def _item_dict(item: models.ResponseMatrixItem) -> dict:
    return {
        "response_matrix_item_id": item.response_matrix_item_id,
        "response_matrix_id": item.response_matrix_id,
        "project_id": item.project_id,
        "source_finding_id": item.source_finding_id,
        "source_checklist_item_id": item.source_checklist_item_id,
        "source_citation_id": item.source_citation_id,
        "item_number": item.item_number,
        "category": item.category,
        "reviewer_comment_draft": item.reviewer_comment_draft,
        "requested_evidence": item.requested_evidence,
        "applicant_response_text": item.applicant_response_text,
        "applicant_response_status": item.applicant_response_status,
        "reviewer_follow_up_status": item.reviewer_follow_up_status,
        "carry_forward_status": item.carry_forward_status,
        "current_round_number": item.current_round_number,
        "carried_from_round_number": item.carried_from_round_number,
        "carried_to_round_number": item.carried_to_round_number,
        "related_document_ids": item.related_document_ids or [],
        "related_citation_ids": item.related_citation_ids or [],
        "reviewer_note": item.reviewer_note,
        "created_by_name": item.created_by_name,
        "updated_by_name": item.updated_by_name,
        "sort_order": item.sort_order,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------


def _next_sort_order(db: Session, response_matrix_id: str) -> int:
    count = db.scalar(
        select(func.count())
        .select_from(models.ResponseMatrixItem)
        .where(
            models.ResponseMatrixItem.response_matrix_id == response_matrix_id
        )
    )
    return int(count or 0)


def add_finding_to_matrix(
    db: Session,
    project_id: str,
    response_matrix_id: str,
    finding_id: str,
    payload: dict | None = None,
    *,
    actor: ActorContext | None = None,
) -> dict:
    """Add a review-support finding to a response matrix as an item."""

    matrix = _require_matrix(db, project_id, response_matrix_id)
    finding = db.get(models.Finding, finding_id)
    if finding is None or finding.project_id != project_id:
        raise ResponseMatrixError(
            "Finding not found for this project.", status_code=404
        )
    payload = payload or {}
    reviewer_comment = (
        payload.get("reviewer_comment_draft") or finding.title or ""
    ).strip()
    reject_prohibited_language(reviewer_comment, field="reviewer_comment_draft")
    item = _create_item(
        db,
        matrix=matrix,
        source_finding_id=finding_id,
        category=(payload.get("category") or finding.category or "general"),
        reviewer_comment_draft=reviewer_comment,
        requested_evidence=payload.get("requested_evidence")
        or finding.evidence_to_find,
        actor=actor,
    )
    return _item_dict(item)


def add_checklist_item_to_matrix(
    db: Session,
    project_id: str,
    response_matrix_id: str,
    checklist_item_id: str,
    payload: dict | None = None,
    *,
    actor: ActorContext | None = None,
) -> dict:
    """Add a project checklist item to a response matrix as an item."""

    matrix = _require_matrix(db, project_id, response_matrix_id)
    checklist_item = db.get(models.ProjectChecklistItem, checklist_item_id)
    if checklist_item is None or checklist_item.project_id != project_id:
        raise ResponseMatrixError(
            "Checklist item not found for this project.", status_code=404
        )
    payload = payload or {}
    reviewer_comment = (
        payload.get("reviewer_comment_draft")
        or f"{checklist_item.item_code}: {checklist_item.requirement_text}"
    ).strip()
    reject_prohibited_language(reviewer_comment, field="reviewer_comment_draft")
    item = _create_item(
        db,
        matrix=matrix,
        source_checklist_item_id=checklist_item_id,
        category=(payload.get("category") or checklist_item.category or "general"),
        reviewer_comment_draft=reviewer_comment,
        requested_evidence=payload.get("requested_evidence")
        or checklist_item.expected_evidence,
        actor=actor,
    )
    return _item_dict(item)


def _create_item(
    db: Session,
    *,
    matrix: models.ResponseMatrix,
    reviewer_comment_draft: str,
    category: str,
    source_finding_id: str | None = None,
    source_checklist_item_id: str | None = None,
    requested_evidence: str | None = None,
    actor: ActorContext | None = None,
) -> models.ResponseMatrixItem:
    now = _now()
    sort_order = _next_sort_order(db, matrix.response_matrix_id)
    item = models.ResponseMatrixItem(
        response_matrix_item_id=f"rmi_{_short()}",
        response_matrix_id=matrix.response_matrix_id,
        project_id=matrix.project_id,
        source_finding_id=source_finding_id,
        source_checklist_item_id=source_checklist_item_id,
        item_number=str(sort_order + 1),
        category=category or "general",
        reviewer_comment_draft=reviewer_comment_draft,
        requested_evidence=requested_evidence,
        applicant_response_status="awaiting_applicant_response",
        reviewer_follow_up_status="not_reviewed",
        carry_forward_status="not_carried_forward",
        current_round_number=matrix.current_round_number,
        sort_order=sort_order,
        created_by_user_id=actor.user_id if actor else None,
        created_by_name=_actor_name(actor),
        created_at=now,
        updated_at=now,
    )
    db.add(item)
    if matrix.status == "matrix_started":
        matrix.status = "matrix_in_progress"
    matrix.updated_at = now
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=matrix.project_id,
        event_type="response_matrix_item_added",
        related_entity_type="response_matrix_item",
        related_entity_id=item.response_matrix_item_id,
        description="Reviewer added an item to the response matrix.",
        actor_type="reviewer",
        actor_id=actor.user_id if actor else None,
        actor_display_name=_actor_name(actor),
        metadata={
            "response_matrix_id": matrix.response_matrix_id,
            "matrix_item_id": item.response_matrix_item_id,
            "finding_id": source_finding_id,
            "checklist_item_id": source_checklist_item_id,
        },
    )
    db.commit()
    db.refresh(item)
    return item


def list_matrix_items(
    db: Session,
    project_id: str,
    response_matrix_id: str,
    *,
    applicant_response_status: str | None = None,
) -> list[models.ResponseMatrixItem]:
    _require_matrix(db, project_id, response_matrix_id)
    stmt = select(models.ResponseMatrixItem).where(
        models.ResponseMatrixItem.response_matrix_id == response_matrix_id
    )
    if applicant_response_status:
        stmt = stmt.where(
            models.ResponseMatrixItem.applicant_response_status
            == applicant_response_status
        )
    stmt = stmt.order_by(models.ResponseMatrixItem.sort_order)
    return list(db.scalars(stmt).all())


def get_matrix_item(
    db: Session, project_id: str, matrix_item_id: str
) -> models.ResponseMatrixItem:
    item = db.get(models.ResponseMatrixItem, matrix_item_id)
    if item is None or item.project_id != project_id:
        raise ResponseMatrixError(
            "Response matrix item not found.", status_code=404
        )
    return item


def update_matrix_item(
    db: Session,
    project_id: str,
    matrix_item_id: str,
    payload: dict,
    *,
    actor: ActorContext | None = None,
) -> models.ResponseMatrixItem:
    """Update an item's reviewer comment draft, statuses, or reviewer note."""

    item = get_matrix_item(db, project_id, matrix_item_id)
    for field in ("reviewer_comment_draft", "requested_evidence", "reviewer_note"):
        reject_prohibited_language(payload.get(field), field=field)

    if payload.get("reviewer_comment_draft") is not None:
        item.reviewer_comment_draft = payload["reviewer_comment_draft"]
    if payload.get("requested_evidence") is not None:
        item.requested_evidence = payload["requested_evidence"]
    if payload.get("reviewer_note") is not None:
        item.reviewer_note = payload["reviewer_note"]

    applicant_status = payload.get("applicant_response_status")
    if applicant_status is not None:
        if applicant_status not in ALLOWED_APPLICANT_RESPONSE_STATUSES_V2:
            raise ResponseMatrixError(
                f"Invalid applicant_response_status '{applicant_status}'.",
                status_code=422,
            )
        item.applicant_response_status = applicant_status
    follow_up = payload.get("reviewer_follow_up_status")
    if follow_up is not None:
        if follow_up not in ALLOWED_REVIEWER_FOLLOW_UP_STATUSES:
            raise ResponseMatrixError(
                f"Invalid reviewer_follow_up_status '{follow_up}'.",
                status_code=422,
            )
        item.reviewer_follow_up_status = follow_up

    item.updated_by_user_id = actor.user_id if actor else None
    item.updated_by_name = _actor_name(actor)
    item.updated_at = _now()
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="response_matrix_item_updated",
        related_entity_type="response_matrix_item",
        related_entity_id=matrix_item_id,
        description="Reviewer updated a response matrix item.",
        actor_type="reviewer",
        actor_id=actor.user_id if actor else None,
        actor_display_name=_actor_name(actor),
        metadata={
            "matrix_item_id": matrix_item_id,
            "applicant_response_status": item.applicant_response_status,
            "reviewer_follow_up_status": item.reviewer_follow_up_status,
        },
    )
    db.commit()
    db.refresh(item)
    return item


def record_applicant_response(
    db: Session,
    project_id: str,
    matrix_item_id: str,
    payload: dict,
    *,
    actor: ActorContext | None = None,
) -> models.ResponseMatrixItem:
    """Record an applicant response for reviewer review.

    The response text is recorded as submitted content; it is never treated as
    proof and never marks the item satisfied. The status moves to a
    review-support value only. The full response text is not written to audit
    metadata.
    """

    item = get_matrix_item(db, project_id, matrix_item_id)
    response_text = (payload.get("applicant_response_text") or "").strip()
    if not response_text:
        raise ResponseMatrixError(
            "applicant_response_text is required.", status_code=422
        )
    reject_prohibited_language(response_text, field="applicant_response_text")

    status = payload.get("applicant_response_status") or "applicant_response_received"
    if status not in ALLOWED_APPLICANT_RESPONSE_STATUSES_V2:
        raise ResponseMatrixError(
            f"Invalid applicant_response_status '{status}'.", status_code=422
        )

    item.applicant_response_text = response_text
    item.applicant_response_status = status
    if item.reviewer_follow_up_status == "not_reviewed":
        item.reviewer_follow_up_status = "needs_reviewer_confirmation"
    item.updated_by_user_id = actor.user_id if actor else None
    item.updated_by_name = _actor_name(actor)
    item.updated_at = _now()

    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="applicant_response_recorded",
        related_entity_type="response_matrix_item",
        related_entity_id=matrix_item_id,
        description="An applicant response was recorded for reviewer review.",
        actor_type="reviewer",
        actor_id=actor.user_id if actor else None,
        actor_display_name=_actor_name(actor),
        metadata={
            "matrix_item_id": matrix_item_id,
            "applicant_response_status": status,
            "response_length": len(response_text),
        },
    )
    db.commit()
    db.refresh(item)
    return item


def link_response_document(
    db: Session,
    project_id: str,
    matrix_item_id: str,
    document_id: str,
    payload: dict | None = None,
    *,
    actor: ActorContext | None = None,
) -> models.MatrixItemDocumentLink:
    """Link a document to a matrix item (applicant response or revised reference)."""

    item = get_matrix_item(db, project_id, matrix_item_id)
    document = db.get(models.Document, document_id)
    if document is None or document.project_id != project_id:
        raise ResponseMatrixError(
            "Document not found for this project.", status_code=404
        )
    payload = payload or {}
    reject_prohibited_language(payload.get("reviewer_note"), field="reviewer_note")
    link_type = payload.get("link_type") or "applicant_response_document"
    if link_type not in ALLOWED_MATRIX_LINK_TYPES:
        raise ResponseMatrixError(
            f"Invalid link_type '{link_type}'.", status_code=422
        )

    now = _now()
    link = models.MatrixItemDocumentLink(
        matrix_item_document_link_id=f"mdl_{_short()}",
        project_id=project_id,
        response_matrix_item_id=matrix_item_id,
        document_id=document_id,
        resubmittal_round_id=payload.get("resubmittal_round_id"),
        link_type=link_type,
        reviewer_note=payload.get("reviewer_note"),
        created_by_user_id=actor.user_id if actor else None,
        created_by_name=_actor_name(actor),
        created_at=now,
    )
    db.add(link)
    related = list(item.related_document_ids or [])
    if document_id not in related:
        related.append(document_id)
        item.related_document_ids = related
    item.updated_at = now
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="response_document_linked",
        related_entity_type="response_matrix_item",
        related_entity_id=matrix_item_id,
        description="Reviewer linked a document to a response matrix item.",
        actor_type="reviewer",
        actor_id=actor.user_id if actor else None,
        actor_display_name=_actor_name(actor),
        metadata={
            "matrix_item_id": matrix_item_id,
            "document_id": document_id,
            "link_type": link_type,
        },
    )
    db.commit()
    db.refresh(link)
    return link


def list_matrix_item_document_links(
    db: Session, project_id: str, matrix_item_id: str
) -> list[models.MatrixItemDocumentLink]:
    get_matrix_item(db, project_id, matrix_item_id)
    return list(
        db.scalars(
            select(models.MatrixItemDocumentLink)
            .where(
                models.MatrixItemDocumentLink.response_matrix_item_id
                == matrix_item_id
            )
            .order_by(models.MatrixItemDocumentLink.created_at)
        ).all()
    )


def carry_forward_matrix_item(
    db: Session,
    project_id: str,
    matrix_item_id: str,
    payload: dict | None = None,
    *,
    actor: ActorContext | None = None,
) -> models.ResponseMatrixItem:
    """Carry a matrix item forward for continued review (not a final resolution)."""

    item = get_matrix_item(db, project_id, matrix_item_id)
    payload = payload or {}
    status = payload.get("carry_forward_status") or "carried_forward_for_review"
    if status not in ALLOWED_CARRY_FORWARD_STATUSES_V2:
        raise ResponseMatrixError(
            f"Invalid carry_forward_status '{status}'.", status_code=422
        )
    reject_prohibited_language(payload.get("reviewer_note"), field="reviewer_note")

    target_round = payload.get("carried_to_round_number")
    if target_round is None:
        target_round = item.current_round_number + 1

    item.carry_forward_status = status
    item.carried_from_round_number = item.current_round_number
    item.carried_to_round_number = int(target_round)
    item.current_round_number = int(target_round)
    if payload.get("reviewer_note") is not None:
        item.reviewer_note = payload["reviewer_note"]
    item.updated_by_user_id = actor.user_id if actor else None
    item.updated_by_name = _actor_name(actor)
    item.updated_at = _now()

    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="response_matrix_item_carried_forward",
        related_entity_type="response_matrix_item",
        related_entity_id=matrix_item_id,
        description="Reviewer carried a response matrix item forward for review.",
        actor_type="reviewer",
        actor_id=actor.user_id if actor else None,
        actor_display_name=_actor_name(actor),
        metadata={
            "matrix_item_id": matrix_item_id,
            "carry_forward_status": status,
            "carried_to_round_number": item.carried_to_round_number,
        },
    )
    db.commit()
    db.refresh(item)
    return item
