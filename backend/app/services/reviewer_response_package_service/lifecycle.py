"""Preview, handoff, issuance, and revisions for reviewer response packages."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import reject_prohibited_language
from app.db import models
from app.services.auth_service import ActorContext, audit_kwargs
from app.services.real_intake_service import record_audit_event

from ._common import _actor_name, _now, _require_package, _short
from .reads import _package_detail, _package_items

PACKAGE_BOUNDARY_STATEMENT = (
    "This response package is prepared for reviewer support. It does not approve"
    " plans, certify compliance, verify design, validate CAD, declare safety,"
    " resolve issues, close issues, or replace the judgment of a licensed"
    " Professional Engineer."
)


def preview_response_package(
    db: Session, project_id: str, response_package_id: str
) -> dict:
    """Return safe, structured preview data for a response package.

    The preview never includes storage keys, raw file paths, signed URLs,
    secrets, or full extracted page text.
    """

    package = _require_package(db, project_id, response_package_id)
    project = db.get(models.Project, project_id)
    items = [
        item
        for item in _package_items(db, response_package_id)
        if item.include_in_letter
    ]
    preview_items = [
        {
            "item_number": item.item_number,
            "category": item.category,
            "reviewer_comment_text": item.reviewer_comment_text,
            "requested_evidence": item.requested_evidence,
            "applicant_response_summary": item.applicant_response_summary,
            "reviewer_follow_up_text": item.reviewer_follow_up_text,
            "citation_reference": item.citation_reference,
            "item_status": item.item_status,
        }
        for item in items
    ]
    return {
        "response_package_id": package.response_package_id,
        "project_id": project_id,
        "project_name": project.project_name if project else project_id,
        "package_title": package.package_title,
        "package_type": package.package_type,
        "package_number": package.package_number,
        "revision_number": package.revision_number,
        "status": package.status,
        "issued_by_name": package.issued_by_name,
        "issued_at": package.issued_at,
        "boundary_statement": PACKAGE_BOUNDARY_STATEMENT,
        "item_count": len(preview_items),
        "items": preview_items,
    }


def mark_package_ready_for_handoff(
    db: Session,
    project_id: str,
    response_package_id: str,
    *,
    actor: ActorContext | None = None,
) -> dict:
    package = _require_package(db, project_id, response_package_id)
    package.status = "ready_for_reviewer_handoff"
    package.updated_at = _now()
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="response_package_ready_for_handoff",
        related_entity_type="reviewer_response_package",
        related_entity_id=response_package_id,
        description="Reviewer marked a response package ready for handoff.",
        actor_type="reviewer",
        actor_id=actor.user_id if actor else None,
        actor_display_name=_actor_name(actor),
        metadata={"response_package_id": response_package_id},
    )
    db.commit()
    db.refresh(package)
    return _package_detail(db, package)


def issue_response_package(
    db: Session,
    project_id: str,
    response_package_id: str,
    payload: dict | None = None,
    *,
    actor: ActorContext | None = None,
) -> dict:
    """Record that a reviewer issued the response package communication.

    Issuance is a communication record only. It does not approve a project,
    certify compliance, validate design, resolve an issue, or close an issue.
    """

    package = _require_package(db, project_id, response_package_id)
    payload = payload or {}
    reject_prohibited_language(payload.get("reviewer_note"), field="reviewer_note")

    package.status = "issued_by_reviewer"
    package.issued_by_user_id = actor.user_id if actor else None
    package.issued_by_name = _actor_name(actor)
    package.issued_at = _now()
    package.updated_at = _now()
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="response_package_issued",
        related_entity_type="reviewer_response_package",
        related_entity_id=response_package_id,
        description="Reviewer issued a response package communication record.",
        actor_type="reviewer",
        actor_id=actor.user_id if actor else None,
        actor_display_name=_actor_name(actor),
        metadata={
            "response_package_id": response_package_id,
            "package_number": package.package_number,
            "revision_number": package.revision_number,
        },
    )
    db.commit()
    db.refresh(package)
    return _package_detail(db, package)


def create_package_revision(
    db: Session,
    project_id: str,
    response_package_id: str,
    payload: dict | None = None,
    *,
    actor: ActorContext | None = None,
) -> dict:
    """Start a package revision without overwriting the prior issued record."""

    package = _require_package(db, project_id, response_package_id)
    payload = payload or {}
    reject_prohibited_language(
        payload.get("revision_reason"), field="revision_reason"
    )

    prior_status = package.status
    now = _now()
    package.revision_number = (package.revision_number or 0) + 1
    package.status = "revision_started"
    package.updated_at = now
    revision = models.ReviewerResponsePackageRevision(
        response_package_revision_id=f"rpkgrev_{_short()}",
        response_package_id=response_package_id,
        project_id=project_id,
        revision_number=package.revision_number,
        revision_reason=payload.get("revision_reason"),
        prior_status=prior_status,
        created_by_user_id=actor.user_id if actor else None,
        created_by_name=_actor_name(actor),
        created_at=now,
    )
    db.add(revision)

    # Preserve prior issued comment letter drafts by marking them superseded.
    drafts = db.scalars(
        select(models.CommentLetterDraft).where(
            models.CommentLetterDraft.response_package_id == response_package_id
        )
    ).all()
    for draft in drafts:
        if draft.status in ("issued_by_reviewer", "ready_for_reviewer_handoff"):
            draft.status = "superseded_by_revision"
            draft.updated_at = now

    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="response_package_revision_created",
        related_entity_type="reviewer_response_package",
        related_entity_id=response_package_id,
        description="Reviewer started a response package revision.",
        actor_type="reviewer",
        actor_id=actor.user_id if actor else None,
        actor_display_name=_actor_name(actor),
        metadata={
            "response_package_id": response_package_id,
            "revision_number": package.revision_number,
            "prior_status": prior_status,
        },
    )
    db.commit()
    db.refresh(package)
    detail = _package_detail(db, package)
    detail["revision_number"] = package.revision_number
    return detail
