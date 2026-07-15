"""Reviewer draft findings created from checklist items.

A reviewer can create a draft finding from a checklist item, optionally with a
page-level citation. The system never decides a final outcome; reviewer-entered
content is validated against final-decision language and draft findings require
reviewer confirmation.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_EVIDENCE_STATUSES,
    ALLOWED_REVIEWER_FINDING_STATUSES,
    reject_prohibited_language,
)
from app.db import models
from app.services.checklist_review_service._common import get_checklist_item
from app.services.checklist_review_service.errors import ChecklistReviewError
from app.services.pdf_indexing_service import create_evidence_citation
from app.services.real_intake_service import (
    DEMO_ACTOR_ID,
    DEMO_ACTOR_NAME,
    _now,
    _short,
    ensure_demo_actor,
    record_audit_event,
)


def create_draft_finding_from_checklist_item(
    db: Session,
    project_id: str,
    project_checklist_item_id: str,
    payload: dict,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> dict:
    """Create a reviewer draft finding from a checklist item.

    Creates a Finding with finding_origin checklist_review and a safe draft
    human_review_status, links the related checklist item, optionally creates a
    page-level citation, updates the checklist item review_status to
    draft_finding_created, and writes audit events. The system never decides a
    final outcome; reviewer-entered content is validated against final-decision
    language.
    """

    item = get_checklist_item(db, project_id, project_checklist_item_id)
    ensure_demo_actor(db)

    title = (
        payload.get("title")
        or f"{item.item_code}: {item.requirement_text}"
    ).strip()
    category = (payload.get("category") or item.category or "general").strip()
    risk_level = (payload.get("risk_level") or item.risk_level or "medium").strip()
    evidence_status = payload.get("evidence_status") or "needs_reviewer_confirmation"
    evidence_to_find = (
        payload.get("evidence_to_find") or item.expected_evidence or ""
    ).strip()
    reason_it_matters = (payload.get("reason_it_matters") or "").strip()
    recommended_human_action = (
        payload.get("recommended_human_action") or ""
    ).strip()
    reviewer_note = payload.get("reviewer_note")
    human_review_status = payload.get("human_review_status") or "draft"

    for field, value in (
        ("title", title),
        ("category", category),
        ("risk_level", risk_level),
        ("evidence_to_find", evidence_to_find),
        ("reason_it_matters", reason_it_matters),
        ("recommended_human_action", recommended_human_action),
        ("reviewer_note", reviewer_note),
    ):
        reject_prohibited_language(value, field=field)

    if evidence_status not in ALLOWED_EVIDENCE_STATUSES:
        raise ChecklistReviewError(
            f"Invalid evidence_status '{evidence_status}'.", status_code=422
        )
    if human_review_status not in ALLOWED_REVIEWER_FINDING_STATUSES:
        raise ChecklistReviewError(
            f"Invalid human_review_status '{human_review_status}'.",
            status_code=422,
        )

    now = _now()
    finding_id = f"find_checklist_{_short()}"
    finding = models.Finding(
        finding_id=finding_id,
        project_id=project_id,
        planted_issue="",
        title=title,
        category=category,
        risk_level=risk_level,
        expected_status=evidence_status,
        evidence_status=evidence_status,
        evidence_to_find=evidence_to_find,
        reason_it_matters=reason_it_matters,
        recommended_human_action=recommended_human_action,
        human_review_status=human_review_status,
        related_checklist_items=[project_checklist_item_id],
        related_documents=[],
        source_mode="user_created",
        finding_origin="checklist_review",
        reviewer_notes=reviewer_note,
        created_by_name=actor_name,
        created_by_actor_id=DEMO_ACTOR_ID,
        created_at=now,
        updated_at=now,
    )
    db.add(finding)
    db.flush()

    citation = None
    document_id = payload.get("document_id")
    if document_id:
        document = db.get(models.Document, document_id)
        if document is None or document.project_id != project_id:
            raise ChecklistReviewError(
                "Document not found for citation.", status_code=422
            )
        citation = create_evidence_citation(
            db,
            project_id=project_id,
            finding_id=finding_id,
            document_id=document_id,
            document_page_id=payload.get("document_page_id"),
            page_number=payload.get("page_number"),
            quoted_excerpt=payload.get("citation_excerpt"),
            reviewer_note=(
                f"Linked from checklist item {item.item_code}."
            ),
            citation_type="reviewer_selected",
            created_by_name=actor_name,
        )
        citation.citation_context = "checklist_evidence"
        citation.project_checklist_item_id = project_checklist_item_id
        citation.rule_pack_item_id = item.rule_pack_item_id

    item.related_finding_id = finding_id
    item.review_status = "draft_finding_created"
    item.updated_at = now

    record_audit_event(
        db,
        project_id=project_id,
        event_type="checklist_draft_finding_created",
        related_entity_type="finding",
        related_entity_id=finding_id,
        description=(
            f"Reviewer created draft finding from checklist item "
            f"{item.item_code}."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "checklist_item_id": project_checklist_item_id,
            "finding_id": finding_id,
            "finding_origin": "checklist_review",
            "evidence_status": evidence_status,
            "human_review_status": human_review_status,
            "evidence_citation_id": (
                citation.evidence_citation_id if citation else None
            ),
        },
    )
    db.commit()
    db.refresh(finding)
    db.refresh(item)
    if citation is not None:
        db.refresh(citation)
    return {"finding": finding, "citation": citation, "checklist_item": item}
