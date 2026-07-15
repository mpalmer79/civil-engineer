"""Reviewer evidence links between checklist items and documents.

A reviewer can link a document page, citation, or candidate to a checklist item
as review-support evidence, and list the links for an item. Linking evidence
never finalizes a review outcome.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_CHECKLIST_LINK_STATUSES,
    reject_prohibited_language,
)
from app.db import models
from app.services.checklist_review_service._common import get_checklist_item
from app.services.checklist_review_service.errors import ChecklistReviewError
from app.services.real_intake_service import (
    DEMO_ACTOR_ID,
    DEMO_ACTOR_NAME,
    _now,
    _short,
    ensure_demo_actor,
    record_audit_event,
)


def link_citation_to_checklist_item(
    db: Session,
    project_id: str,
    project_checklist_item_id: str,
    payload: dict,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> models.ChecklistEvidenceLink:
    """Link a document page, citation, or candidate to a checklist item."""

    item = get_checklist_item(db, project_id, project_checklist_item_id)
    ensure_demo_actor(db)
    reject_prohibited_language(payload.get("reviewer_note"), field="reviewer_note")
    reject_prohibited_language(payload.get("quoted_excerpt"), field="quoted_excerpt")

    document_id = (payload.get("document_id") or "").strip()
    if not document_id:
        raise ChecklistReviewError("document_id is required.", status_code=422)
    document = db.get(models.Document, document_id)
    if document is None or document.project_id != project_id:
        raise ChecklistReviewError("Document not found.", status_code=404)

    page_number = payload.get("page_number")
    document_page_id = payload.get("document_page_id")
    if document_page_id:
        page = db.get(models.DocumentPage, document_page_id)
        if page is None or page.document_id != document_id:
            raise ChecklistReviewError(
                "Document page not found for this document.", status_code=422
            )
        page_number = page.page_number

    link_status = payload.get("link_status") or "reviewer_selected"
    if link_status not in ALLOWED_CHECKLIST_LINK_STATUSES:
        raise ChecklistReviewError(
            f"Invalid link_status '{link_status}'.", status_code=422
        )

    # Optionally create an EvidenceCitation in checklist context. This requires a
    # finding, so a citation is only created when create_citation is requested
    # together with a finding_id; otherwise the link stands on its own.
    citation_id = payload.get("evidence_citation_id")

    now = _now()
    link = models.ChecklistEvidenceLink(
        checklist_evidence_link_id=f"clink_{_short()}",
        project_id=project_id,
        project_checklist_item_id=project_checklist_item_id,
        document_id=document_id,
        document_page_id=document_page_id,
        evidence_citation_id=citation_id,
        evidence_candidate_id=payload.get("evidence_candidate_id"),
        page_number=page_number,
        quoted_excerpt=payload.get("quoted_excerpt"),
        reviewer_note=payload.get("reviewer_note"),
        link_status=link_status,
        created_by_actor_id=DEMO_ACTOR_ID,
        created_by_name=actor_name,
        created_at=now,
    )
    db.add(link)

    if item.review_status in ("not_started", "evidence_review_needed"):
        item.review_status = "citation_added"
    item.updated_at = now

    record_audit_event(
        db,
        project_id=project_id,
        event_type="checklist_evidence_linked",
        related_entity_type="project_checklist_item",
        related_entity_id=project_checklist_item_id,
        description=(
            f"Reviewer linked evidence to checklist item {item.item_code}."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "checklist_item_id": project_checklist_item_id,
            "checklist_evidence_link_id": link.checklist_evidence_link_id,
            "document_id": document_id,
            "page_number": page_number,
            "evidence_citation_id": citation_id,
            "evidence_candidate_id": payload.get("evidence_candidate_id"),
            "link_status": link_status,
        },
    )
    db.commit()
    db.refresh(link)
    return link


def list_checklist_item_evidence_links(
    db: Session, project_id: str, project_checklist_item_id: str
) -> list[models.ChecklistEvidenceLink]:
    get_checklist_item(db, project_id, project_checklist_item_id)
    return list(
        db.scalars(
            select(models.ChecklistEvidenceLink)
            .where(
                models.ChecklistEvidenceLink.project_checklist_item_id
                == project_checklist_item_id
            )
            .order_by(models.ChecklistEvidenceLink.created_at)
        ).all()
    )
