"""Comment letter draft service (Sprint 8).

Generates a deterministic, reviewer-editable comment letter draft from a response
package. Generation uses fixed templates only. There are NO live AI calls, no
OCR, and no automated engineering conclusions.

A comment letter draft is a reviewer communication artifact. It does not approve
plans, certify compliance, verify CAD, validate design, declare safety, resolve
an issue, or close an issue. A fixed review-support boundary statement is rendered
with every draft and preview and is never an editable section.

Audit metadata records ids, statuses, and counts only. It never records the full
comment letter text, full applicant response text, full extracted page text,
storage keys, raw paths, secrets, or tokens.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_COMMENT_LETTER_DRAFT_STATUSES,
    reject_prohibited_language,
)
from app.db import models
from app.services.auth_service import ActorContext, audit_kwargs
from app.services.real_intake_service import record_audit_event

# The fixed review-support boundary statement. It is rendered with every draft
# and preview and is never an editable section, so it is never validated against
# the prohibited-language guard (it intentionally describes what the draft does
# NOT do).
COMMENT_LETTER_BOUNDARY_STATEMENT = (
    "This draft is prepared for reviewer support. It does not approve plans,"
    " certify compliance, verify design, validate CAD, declare safety, resolve"
    " issues, close issues, or replace the judgment of a licensed Professional"
    " Engineer."
)

# Editable section fields that are checked against the prohibited-language guard
# when a reviewer updates a draft.
_EDITABLE_TEXT_FIELDS = (
    "title",
    "recipient_name",
    "recipient_organization",
    "subject_line",
    "introduction_text",
    "project_summary_text",
    "review_scope_text",
    "comment_items_text",
    "resubmittal_summary_text",
    "closing_text",
)


class CommentLetterError(Exception):
    """Raised when a comment letter operation is not allowed."""

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


def _require_package(
    db: Session, project_id: str, response_package_id: str
) -> models.ReviewerResponsePackage:
    package = db.get(models.ReviewerResponsePackage, response_package_id)
    if package is None or package.project_id != project_id:
        raise CommentLetterError("Response package not found.", status_code=404)
    return package


def _require_draft(
    db: Session, project_id: str, draft_id: str
) -> models.CommentLetterDraft:
    draft = db.get(models.CommentLetterDraft, draft_id)
    if draft is None or draft.project_id != project_id:
        raise CommentLetterError(
            "Comment letter draft not found.", status_code=404
        )
    return draft


def _included_items(
    db: Session, response_package_id: str
) -> list[models.ReviewerResponsePackageItem]:
    items = db.scalars(
        select(models.ReviewerResponsePackageItem)
        .where(
            models.ReviewerResponsePackageItem.response_package_id
            == response_package_id
        )
        .order_by(models.ReviewerResponsePackageItem.sort_order)
    ).all()
    return [item for item in items if item.include_in_letter]


def _format_comment_items(
    items: list[models.ReviewerResponsePackageItem],
) -> str:
    """Format included package items into a deterministic comment block."""

    if not items:
        return (
            "No reviewer-selected items are included yet. Add reviewer-selected"
            " records before previewing the package."
        )
    blocks: list[str] = []
    for index, item in enumerate(items, start=1):
        lines = [f"Comment {item.item_number or index}"]
        if item.category:
            lines.append(f"Category: {item.category}")
        if item.reviewer_comment_text:
            lines.append(f"Reviewer comment: {item.reviewer_comment_text}")
        if item.requested_evidence:
            lines.append(f"Requested evidence: {item.requested_evidence}")
        if item.applicant_response_summary:
            lines.append(
                f"Applicant response summary: {item.applicant_response_summary}"
            )
        if item.reviewer_follow_up_text:
            lines.append(f"Reviewer follow-up: {item.reviewer_follow_up_text}")
        if item.citation_reference:
            lines.append(f"Citation reference: {item.citation_reference}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def generate_comment_letter_draft(
    db: Session,
    project_id: str,
    response_package_id: str,
    payload: dict | None = None,
    *,
    actor: ActorContext | None = None,
) -> dict:
    """Generate a deterministic comment letter draft from a response package."""

    package = _require_package(db, project_id, response_package_id)
    project = db.get(models.Project, project_id)
    payload = payload or {}
    for field in ("recipient_name", "recipient_organization"):
        reject_prohibited_language(payload.get(field), field=field)

    project_name = project.project_name if project else project_id
    items = _included_items(db, response_package_id)

    title = f"{package.package_title} comment letter draft"
    subject_line = f"Stormwater review comments: {project_name}"
    introduction_text = (
        "This comment letter draft compiles review-support comments prepared by"
        " the reviewer for the project named below. It is provided for reviewer"
        " handoff and applicant coordination. Each comment requires human"
        " review."
    )
    project_summary_parts = [f"Project: {project_name}."]
    if project is not None:
        if project.jurisdiction:
            project_summary_parts.append(f"Jurisdiction: {project.jurisdiction}.")
        if project.review_type:
            project_summary_parts.append(f"Review type: {project.review_type}.")
        project_summary_parts.append(
            f"Review round: {project.review_round_current}."
        )
    project_summary_text = " ".join(project_summary_parts)
    review_scope_text = (
        "The reviewer examined the submitted materials and recorded the"
        " review-support comments below. Each comment reflects an item the"
        " reviewer asks the applicant to address or clarify and remains under"
        " human review."
    )
    comment_items_text = _format_comment_items(items)
    resubmittal_summary_text = None
    if package.resubmittal_round_id:
        resubmittal_summary_text = (
            "This package is associated with a resubmittal round. Carried-forward"
            " items remain under reviewer review across rounds."
        )
    closing_text = (
        "Please treat each comment above as a review-support item that needs the"
        " applicant's response. The reviewer will continue the review when"
        " updated materials are provided."
    )

    now = _now()
    draft = models.CommentLetterDraft(
        comment_letter_draft_id=f"cldraft_{_short()}",
        response_package_id=response_package_id,
        project_id=project_id,
        title=title,
        recipient_name=payload.get("recipient_name"),
        recipient_organization=payload.get("recipient_organization"),
        subject_line=subject_line,
        introduction_text=introduction_text,
        project_summary_text=project_summary_text,
        review_scope_text=review_scope_text,
        comment_items_text=comment_items_text,
        resubmittal_summary_text=resubmittal_summary_text,
        closing_text=closing_text,
        status="draft_created",
        revision_number=package.revision_number,
        created_by_user_id=actor.user_id if actor else None,
        created_by_name=_actor_name(actor),
        created_at=now,
        updated_at=now,
    )
    db.add(draft)
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="comment_letter_draft_created",
        related_entity_type="comment_letter_draft",
        related_entity_id=draft.comment_letter_draft_id,
        description="Reviewer generated a deterministic comment letter draft.",
        actor_type="reviewer",
        actor_id=actor.user_id if actor else None,
        actor_display_name=_actor_name(actor),
        metadata={
            "comment_letter_draft_id": draft.comment_letter_draft_id,
            "response_package_id": response_package_id,
            "item_count": len(items),
        },
    )
    db.commit()
    db.refresh(draft)
    return _draft_dict(draft)


def get_comment_letter_draft(
    db: Session, project_id: str, draft_id: str
) -> dict:
    draft = _require_draft(db, project_id, draft_id)
    return _draft_dict(draft)


def list_package_comment_letter_drafts(
    db: Session, project_id: str, response_package_id: str
) -> list[dict]:
    _require_package(db, project_id, response_package_id)
    drafts = db.scalars(
        select(models.CommentLetterDraft)
        .where(
            models.CommentLetterDraft.response_package_id == response_package_id
        )
        .order_by(models.CommentLetterDraft.created_at)
    ).all()
    return [_draft_dict(d) for d in drafts]


def update_comment_letter_draft(
    db: Session,
    project_id: str,
    draft_id: str,
    payload: dict,
    *,
    actor: ActorContext | None = None,
) -> dict:
    draft = _require_draft(db, project_id, draft_id)
    for field in _EDITABLE_TEXT_FIELDS:
        reject_prohibited_language(payload.get(field), field=field)

    for field in _EDITABLE_TEXT_FIELDS:
        if payload.get(field) is not None:
            setattr(draft, field, payload[field])

    status = payload.get("status")
    if status is not None:
        if status not in ALLOWED_COMMENT_LETTER_DRAFT_STATUSES:
            raise CommentLetterError(
                f"Invalid comment letter status '{status}'.", status_code=422
            )
        draft.status = status
    elif draft.status == "draft_created":
        draft.status = "reviewer_editing"

    draft.updated_at = _now()
    event_type = "comment_letter_draft_updated"
    description = "Reviewer updated a comment letter draft."
    if draft.status == "ready_for_reviewer_handoff":
        event_type = "comment_letter_ready_for_handoff"
        description = "Reviewer marked a comment letter draft ready for handoff."
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type=event_type,
        related_entity_type="comment_letter_draft",
        related_entity_id=draft_id,
        description=description,
        actor_type="reviewer",
        actor_id=actor.user_id if actor else None,
        actor_display_name=_actor_name(actor),
        metadata={
            "comment_letter_draft_id": draft_id,
            "status": draft.status,
        },
    )
    db.commit()
    db.refresh(draft)
    return _draft_dict(draft)


def preview_comment_letter(
    db: Session, project_id: str, draft_id: str
) -> dict:
    """Return safe preview text for a comment letter draft.

    The preview never includes storage keys, raw paths, signed URLs, secrets, or
    full extracted page text. It always carries the boundary statement.
    """

    draft = _require_draft(db, project_id, draft_id)
    sections = [
        ("Subject", draft.subject_line),
        ("Introduction", draft.introduction_text),
        ("Project summary", draft.project_summary_text),
        ("Review scope", draft.review_scope_text),
        ("Review-support comments", draft.comment_items_text),
        ("Resubmittal summary", draft.resubmittal_summary_text),
        ("Closing", draft.closing_text),
    ]
    rendered_sections = [
        {"heading": heading, "body": body}
        for heading, body in sections
        if body
    ]
    return {
        "comment_letter_draft_id": draft.comment_letter_draft_id,
        "response_package_id": draft.response_package_id,
        "project_id": project_id,
        "title": draft.title,
        "recipient_name": draft.recipient_name,
        "recipient_organization": draft.recipient_organization,
        "status": draft.status,
        "revision_number": draft.revision_number,
        "boundary_statement": COMMENT_LETTER_BOUNDARY_STATEMENT,
        "sections": rendered_sections,
    }


def _draft_dict(draft: models.CommentLetterDraft) -> dict:
    return {
        "comment_letter_draft_id": draft.comment_letter_draft_id,
        "response_package_id": draft.response_package_id,
        "project_id": draft.project_id,
        "title": draft.title,
        "recipient_name": draft.recipient_name,
        "recipient_organization": draft.recipient_organization,
        "subject_line": draft.subject_line,
        "introduction_text": draft.introduction_text,
        "project_summary_text": draft.project_summary_text,
        "review_scope_text": draft.review_scope_text,
        "comment_items_text": draft.comment_items_text,
        "resubmittal_summary_text": draft.resubmittal_summary_text,
        "closing_text": draft.closing_text,
        "status": draft.status,
        "revision_number": draft.revision_number,
        "boundary_statement": COMMENT_LETTER_BOUNDARY_STATEMENT,
        "created_by_name": draft.created_by_name,
        "created_at": draft.created_at,
        "updated_at": draft.updated_at,
    }
