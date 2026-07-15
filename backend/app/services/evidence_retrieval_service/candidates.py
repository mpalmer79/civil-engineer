"""Reviewer-controlled evidence candidate queue and draft finding promotion.

A reviewer saves a retrieval result into the queue as a candidate, updates or
dismisses it, and can promote it into a reviewer draft finding plus a page-level
citation. The system never auto-promotes and never reaches a final engineering
decision. Promotion creates a draft finding with a safe human_review_status and
a page-level citation; it never finalizes a review outcome. Reviewer-entered
content is checked against prohibited final-decision language.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_CANDIDATE_ORIGINS,
    ALLOWED_CANDIDATE_STATUSES,
    ALLOWED_EVIDENCE_STATUSES,
    ALLOWED_REVIEWER_FINDING_STATUSES,
    reject_prohibited_language,
)
from app.db import models
from app.services.evidence_retrieval_service._common import (
    _EXCERPT_LIMIT,
    _require_project,
)
from app.services.evidence_retrieval_service.errors import RetrievalError
from app.services.pdf_indexing_service import create_evidence_citation
from app.services.real_intake_service import (
    DEMO_ACTOR_ID,
    DEMO_ACTOR_NAME,
    _now,
    _short,
    ensure_demo_actor,
    record_audit_event,
)


def save_candidate(
    db: Session,
    project_id: str,
    payload: dict,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> models.EvidenceCandidate:
    """Save a retrieval result into the reviewer draft queue as a candidate."""

    _require_project(db, project_id)
    ensure_demo_actor(db)

    document_id = (payload.get("document_id") or "").strip()
    if not document_id:
        raise RetrievalError("document_id is required.", status_code=422)
    document = db.get(models.Document, document_id)
    if document is None or document.project_id != project_id:
        raise RetrievalError("Document not found.", status_code=404)

    candidate_title = (payload.get("candidate_title") or "").strip()
    if not candidate_title:
        raise RetrievalError("candidate_title is required.", status_code=422)
    for field in ("candidate_title", "candidate_excerpt", "reviewer_note"):
        reject_prohibited_language(payload.get(field), field=field)

    candidate_status = payload.get("candidate_status") or "saved_for_review"
    if candidate_status not in ALLOWED_CANDIDATE_STATUSES:
        raise RetrievalError(
            f"Invalid candidate_status '{candidate_status}'. Allowed: "
            f"{', '.join(sorted(ALLOWED_CANDIDATE_STATUSES))}.",
            status_code=422,
        )
    candidate_origin = payload.get("candidate_origin") or "manual_save"
    if candidate_origin not in ALLOWED_CANDIDATE_ORIGINS:
        raise RetrievalError(
            f"Invalid candidate_origin '{candidate_origin}'. Allowed: "
            f"{', '.join(sorted(ALLOWED_CANDIDATE_ORIGINS))}.",
            status_code=422,
        )

    page = None
    document_page_id = payload.get("document_page_id")
    page_number = payload.get("page_number")
    if document_page_id:
        page = db.get(models.DocumentPage, document_page_id)
        if page is None or page.document_id != document_id:
            raise RetrievalError(
                "Document page not found for this document.", status_code=422
            )
    elif page_number is not None:
        # Citation integrity: when a candidate (for example a chunk-derived
        # result) supplies only a page number, resolve the matching DocumentPage
        # so the saved candidate carries a real document_page_id. If no page
        # matches, the candidate is still saved with the page number alone.
        page = db.scalars(
            select(models.DocumentPage).where(
                models.DocumentPage.document_id == document_id,
                models.DocumentPage.page_number == int(page_number),
            )
        ).first()
    if page is not None:
        page_number = page.page_number

    finding_id = payload.get("finding_id")
    if finding_id:
        finding = db.get(models.Finding, finding_id)
        if finding is None or finding.project_id != project_id:
            raise RetrievalError(
                "Finding not found for this project.", status_code=422
            )

    now = _now()
    excerpt = payload.get("candidate_excerpt")
    if excerpt:
        excerpt = excerpt[:_EXCERPT_LIMIT]
    candidate = models.EvidenceCandidate(
        evidence_candidate_id=f"cand_{_short()}",
        project_id=project_id,
        retrieval_query_id=payload.get("retrieval_query_id"),
        document_id=document_id,
        document_page_id=page.document_page_id if page else document_page_id,
        page_number=page_number,
        finding_id=finding_id,
        checklist_item_id=payload.get("checklist_item_id"),
        candidate_title=candidate_title,
        candidate_excerpt=excerpt,
        match_terms=list(payload.get("match_terms") or []),
        ranking_score=float(payload.get("ranking_score") or 0.0),
        ranking_reason=payload.get("ranking_reason"),
        candidate_status=candidate_status,
        candidate_origin=candidate_origin,
        reviewer_note=payload.get("reviewer_note"),
        created_by_actor_id=DEMO_ACTOR_ID,
        created_by_name=actor_name,
        created_at=now,
        updated_at=now,
    )
    db.add(candidate)
    record_audit_event(
        db,
        project_id=project_id,
        event_type="evidence_candidate_saved",
        related_entity_type="evidence_candidate",
        related_entity_id=candidate.evidence_candidate_id,
        description=(
            f"Reviewer saved evidence candidate '{candidate_title}' "
            f"({candidate_origin})."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "candidate_id": candidate.evidence_candidate_id,
            "document_id": document_id,
            "page_number": page_number,
            "candidate_status": candidate_status,
            "candidate_origin": candidate_origin,
        },
    )
    db.commit()
    db.refresh(candidate)
    return candidate


def list_project_candidates(
    db: Session,
    project_id: str,
    *,
    candidate_status: str | None = None,
    finding_id: str | None = None,
) -> list[models.EvidenceCandidate]:
    """List saved candidates for a project, newest first, with optional filters."""

    stmt = select(models.EvidenceCandidate).where(
        models.EvidenceCandidate.project_id == project_id
    )
    if candidate_status:
        stmt = stmt.where(
            models.EvidenceCandidate.candidate_status == candidate_status
        )
    if finding_id:
        stmt = stmt.where(models.EvidenceCandidate.finding_id == finding_id)
    stmt = stmt.order_by(models.EvidenceCandidate.created_at.desc())
    return list(db.scalars(stmt).all())


def list_retrieval_queries(
    db: Session, project_id: str
) -> list[models.RetrievalQuery]:
    """List retrieval query history for a project, newest first."""

    stmt = (
        select(models.RetrievalQuery)
        .where(models.RetrievalQuery.project_id == project_id)
        .order_by(models.RetrievalQuery.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_candidate(
    db: Session, project_id: str, candidate_id: str
) -> models.EvidenceCandidate:
    candidate = db.get(models.EvidenceCandidate, candidate_id)
    if candidate is None or candidate.project_id != project_id:
        raise RetrievalError("Evidence candidate not found.", status_code=404)
    return candidate


def update_candidate_status(
    db: Session,
    project_id: str,
    candidate_id: str,
    payload: dict,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> models.EvidenceCandidate:
    """Update a candidate's reviewer note and/or status under reviewer control."""

    candidate = get_candidate(db, project_id, candidate_id)
    reject_prohibited_language(payload.get("reviewer_note"), field="reviewer_note")

    new_status = payload.get("candidate_status")
    if new_status is not None:
        if new_status not in ALLOWED_CANDIDATE_STATUSES:
            raise RetrievalError(
                f"Invalid candidate_status '{new_status}'. Allowed: "
                f"{', '.join(sorted(ALLOWED_CANDIDATE_STATUSES))}.",
                status_code=422,
            )
        candidate.candidate_status = new_status
    if payload.get("reviewer_note") is not None:
        candidate.reviewer_note = payload.get("reviewer_note")
    candidate.updated_at = _now()

    record_audit_event(
        db,
        project_id=project_id,
        event_type="evidence_candidate_updated",
        related_entity_type="evidence_candidate",
        related_entity_id=candidate_id,
        description=f"Reviewer updated evidence candidate {candidate_id}.",
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "candidate_id": candidate_id,
            "candidate_status": candidate.candidate_status,
        },
    )
    db.commit()
    db.refresh(candidate)
    return candidate


def dismiss_candidate(
    db: Session,
    project_id: str,
    candidate_id: str,
    *,
    note: str | None = None,
    actor_name: str = DEMO_ACTOR_NAME,
) -> models.EvidenceCandidate:
    """Mark a candidate as dismissed_by_reviewer. The record is retained."""

    candidate = get_candidate(db, project_id, candidate_id)
    reject_prohibited_language(note, field="reviewer_note")

    candidate.candidate_status = "dismissed_by_reviewer"
    if note is not None:
        candidate.reviewer_note = note
    candidate.dismissed_at = _now()
    candidate.updated_at = candidate.dismissed_at

    record_audit_event(
        db,
        project_id=project_id,
        event_type="evidence_candidate_dismissed",
        related_entity_type="evidence_candidate",
        related_entity_id=candidate_id,
        description=f"Reviewer dismissed evidence candidate {candidate_id}.",
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "candidate_id": candidate_id,
            "candidate_status": "dismissed_by_reviewer",
        },
    )
    db.commit()
    db.refresh(candidate)
    return candidate


def promote_candidate_to_draft_finding(
    db: Session,
    project_id: str,
    candidate_id: str,
    payload: dict,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> dict:
    """Promote a candidate into a reviewer draft finding plus a citation.

    Creates a Finding with finding_origin retrieval_candidate and a safe draft
    human_review_status, links the source document/page through an
    EvidenceCitation, updates the candidate status to promoted_to_draft, and
    writes audit events. The system never decides severity or a final outcome;
    reviewer-entered content is validated against final-decision language.
    """

    candidate = get_candidate(db, project_id, candidate_id)
    ensure_demo_actor(db)

    if candidate.candidate_status == "promoted_to_draft":
        raise RetrievalError(
            "This candidate was already promoted to a draft finding.",
            status_code=422,
        )
    if candidate.candidate_status == "dismissed_by_reviewer":
        raise RetrievalError(
            "A dismissed candidate cannot be promoted. Re-save it first.",
            status_code=422,
        )

    title = (payload.get("title") or candidate.candidate_title or "").strip()
    if not title:
        raise RetrievalError("title is required.", status_code=422)
    category = (payload.get("category") or "general").strip() or "general"
    risk_level = (payload.get("risk_level") or "medium").strip() or "medium"
    evidence_status = payload.get("evidence_status") or "needs_reviewer_confirmation"
    evidence_to_find = (payload.get("evidence_to_find") or "").strip()
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
        raise RetrievalError(
            f"Invalid evidence_status '{evidence_status}'. Allowed: "
            f"{', '.join(sorted(ALLOWED_EVIDENCE_STATUSES))}.",
            status_code=422,
        )
    if human_review_status not in ALLOWED_REVIEWER_FINDING_STATUSES:
        raise RetrievalError(
            f"Invalid human_review_status '{human_review_status}'. Allowed: "
            f"{', '.join(sorted(ALLOWED_REVIEWER_FINDING_STATUSES))}.",
            status_code=422,
        )

    now = _now()
    finding_id = f"find_draft_{_short()}"
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
        related_checklist_items=(
            [candidate.checklist_item_id] if candidate.checklist_item_id else []
        ),
        related_documents=[candidate.document_id],
        source_mode="user_created",
        finding_origin="retrieval_candidate",
        reviewer_notes=reviewer_note,
        created_by_name=actor_name,
        created_by_actor_id=DEMO_ACTOR_ID,
        created_at=now,
        updated_at=now,
    )
    db.add(finding)
    db.flush()

    record_audit_event(
        db,
        project_id=project_id,
        event_type="draft_finding_created_from_candidate",
        related_entity_type="finding",
        related_entity_id=finding_id,
        description=(
            f"Reviewer promoted candidate {candidate_id} into draft finding "
            f"'{title}'."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "candidate_id": candidate_id,
            "finding_id": finding_id,
            "finding_origin": "retrieval_candidate",
            "evidence_status": evidence_status,
            "human_review_status": human_review_status,
            "risk_level": risk_level,
        },
    )

    # Link the source document/page as a page-level evidence citation. The
    # excerpt the reviewer reviewed becomes the citation quote when provided.
    citation_excerpt = (
        payload.get("citation_excerpt") or candidate.candidate_excerpt
    )
    citation = create_evidence_citation(
        db,
        project_id=project_id,
        finding_id=finding_id,
        document_id=candidate.document_id,
        document_page_id=candidate.document_page_id,
        page_number=candidate.page_number,
        quoted_excerpt=citation_excerpt,
        reviewer_note=(
            "Promoted from evidence retrieval candidate "
            f"{candidate_id}."
        ),
        citation_type="reviewer_selected",
        created_by_name=actor_name,
    )
    record_audit_event(
        db,
        project_id=project_id,
        event_type="citation_created_from_candidate",
        related_entity_type="evidence_citation",
        related_entity_id=citation.evidence_citation_id,
        description=(
            f"Citation {citation.evidence_citation_id} created from candidate "
            f"{candidate_id}."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "candidate_id": candidate_id,
            "finding_id": finding_id,
            "evidence_citation_id": citation.evidence_citation_id,
            "document_id": candidate.document_id,
            "page_number": candidate.page_number,
        },
    )

    candidate.candidate_status = "promoted_to_draft"
    candidate.promoted_finding_id = finding_id
    candidate.updated_at = now
    record_audit_event(
        db,
        project_id=project_id,
        event_type="evidence_candidate_promoted_to_draft",
        related_entity_type="evidence_candidate",
        related_entity_id=candidate_id,
        description=(
            f"Candidate {candidate_id} promoted to draft finding {finding_id}."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "candidate_id": candidate_id,
            "finding_id": finding_id,
            "candidate_status": "promoted_to_draft",
        },
    )

    db.commit()
    db.refresh(finding)
    db.refresh(citation)
    db.refresh(candidate)
    return {
        "finding": finding,
        "citation": citation,
        "candidate": candidate,
    }
