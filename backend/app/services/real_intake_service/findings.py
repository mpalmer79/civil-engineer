"""Reviewer-owned review-support findings and basic evidence references.

A reviewer can create a review-support finding and attach a basic manual
evidence reference linking the finding to a document. Every finding stays under
human review and carries no final decision.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_EVIDENCE_STATUSES,
    ALLOWED_REVIEWER_FINDING_STATUSES,
    reject_prohibited_language,
)
from app.db import models
from app.services.auth_service import ActorContext, audit_kwargs
from app.services.real_intake_service._common import (
    DEMO_ACTOR_ID,
    DEMO_ACTOR_NAME,
    _now,
    _require_project,
    _short,
    ensure_demo_actor,
    record_audit_event,
)
from app.services.real_intake_service.errors import IntakeError


def create_finding(
    db: Session,
    *,
    project_id: str,
    title: str,
    category: str,
    risk_level: str,
    evidence_status: str,
    evidence_to_find: str,
    reason_it_matters: str,
    recommended_human_action: str,
    related_documents: list[str] | None = None,
    related_checklist_items: list[str] | None = None,
    reviewer_notes: str | None = None,
    human_review_status: str = "needs_reviewer_confirmation",
    created_by_name: str = DEMO_ACTOR_NAME,
    actor: ActorContext | None = None,
) -> models.Finding:
    """Create a reviewer-owned review-support finding and a finding_created
    event. The finding stays under human review and carries no final decision."""

    _require_project(db, project_id)
    if actor is not None:
        created_by_name = actor.display_name
    if not (title or "").strip():
        raise IntakeError("title is required.", status_code=422)
    for field, value in (
        ("title", title),
        ("category", category),
        ("evidence_to_find", evidence_to_find),
        ("reason_it_matters", reason_it_matters),
        ("recommended_human_action", recommended_human_action),
        ("reviewer_notes", reviewer_notes),
    ):
        reject_prohibited_language(value, field=field)

    if evidence_status not in ALLOWED_EVIDENCE_STATUSES:
        raise IntakeError(
            f"Invalid evidence_status '{evidence_status}'. Allowed: "
            f"{', '.join(sorted(ALLOWED_EVIDENCE_STATUSES))}.",
            status_code=422,
        )
    if human_review_status not in ALLOWED_REVIEWER_FINDING_STATUSES:
        raise IntakeError(
            f"Invalid human_review_status '{human_review_status}'. Allowed: "
            f"{', '.join(sorted(ALLOWED_REVIEWER_FINDING_STATUSES))}.",
            status_code=422,
        )

    ensure_demo_actor(db)
    now = _now()
    finding_id = f"find_user_{_short()}"
    finding = models.Finding(
        finding_id=finding_id,
        project_id=project_id,
        planted_issue="",
        title=title.strip(),
        category=(category or "general").strip() or "general",
        risk_level=(risk_level or "medium").strip() or "medium",
        expected_status=evidence_status,
        evidence_status=evidence_status,
        evidence_to_find=(evidence_to_find or "").strip(),
        reason_it_matters=(reason_it_matters or "").strip(),
        recommended_human_action=(recommended_human_action or "").strip(),
        human_review_status=human_review_status,
        related_checklist_items=list(related_checklist_items or []),
        related_documents=list(related_documents or []),
        source_mode="user_created",
        finding_origin="reviewer_created",
        reviewer_notes=reviewer_notes,
        created_by_name=created_by_name,
        created_by_actor_id=DEMO_ACTOR_ID,
        created_at=now,
        updated_at=now,
    )
    db.add(finding)
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="finding_created",
        related_entity_type="finding",
        related_entity_id=finding_id,
        description=(
            f"Reviewer created review-support finding '{finding.title}'."
        ),
        actor_type="reviewer",
        actor_display_name=created_by_name,
        metadata={
            "finding_origin": "reviewer_created",
            "evidence_status": evidence_status,
            "human_review_status": human_review_status,
            "risk_level": finding.risk_level,
        },
    )
    db.commit()
    db.refresh(finding)
    return finding


def create_evidence_reference(
    db: Session,
    *,
    finding_id: str,
    document_id: str,
    reviewer_note: str,
    page_number: int | None = None,
    sheet_number: str | None = None,
    section_label: str | None = None,
    created_by_name: str = DEMO_ACTOR_NAME,
) -> models.FindingSource:
    """Create a basic manual evidence reference linking a finding to a document.

    This is a review-support evidence reference placeholder, not a final
    citation engine. It records where a reviewer can inspect relevant evidence.
    """

    finding = db.get(models.Finding, finding_id)
    if finding is None:
        raise IntakeError("Finding not found.", status_code=404)
    document = db.get(models.Document, document_id)
    if document is None:
        raise IntakeError("Document not found.", status_code=404)
    if document.project_id != finding.project_id:
        raise IntakeError(
            "Document and finding belong to different projects.",
            status_code=422,
        )
    reject_prohibited_language(reviewer_note, field="reviewer_note")

    ensure_demo_actor(db)
    reference_id = f"evref_{_short()}"
    reference = models.FindingSource(
        finding_source_id=reference_id,
        finding_id=finding_id,
        document_id=document_id,
        chunk_id=None,
        page_number=page_number,
        excerpt=(reviewer_note or "").strip(),
        evidence_role="requires_reviewer_confirmation",
        confidence=0.0,
        sheet_number=sheet_number,
        section_label=section_label,
        source_mode="user_created",
        created_at=_now(),
    )
    db.add(reference)
    record_audit_event(
        db,
        project_id=finding.project_id,
        event_type="evidence_reference_created",
        related_entity_type="finding",
        related_entity_id=finding_id,
        description=(
            f"Reviewer linked document '{document.file_name}' as evidence for "
            f"finding '{finding.title}'."
        ),
        actor_type="reviewer",
        actor_display_name=created_by_name,
        metadata={
            "finding_source_id": reference_id,
            "document_id": document_id,
            "page_number": page_number,
            "sheet_number": sheet_number,
            "section_label": section_label,
        },
    )
    db.commit()
    db.refresh(reference)
    return reference


def list_evidence_references(
    db: Session, finding_id: str
) -> list[models.FindingSource]:
    stmt = (
        select(models.FindingSource)
        .where(models.FindingSource.finding_id == finding_id)
        .order_by(models.FindingSource.id)
    )
    return list(db.scalars(stmt).all())
