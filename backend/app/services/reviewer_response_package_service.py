"""Reviewer response package service (Sprint 8).

Production Foundations Sprint 8 adds the first reviewer-controlled output
workflow. A reviewer assembles selected review-support records (findings,
checklist items, response matrix items, citations, document references,
resubmittal summaries, and manual reviewer notes) into a response package, then
generates a deterministic comment letter draft from the package.

Everything here is review-support communication. Issuing a package records that a
reviewer issued a communication. It never approves a project, certifies
compliance, verifies CAD, validates design, declares safety, resolves an issue,
or closes an issue. A revision never overwrites a prior issued record. Nothing
here makes a final engineering decision.

Audit metadata records ids, statuses, and counts only. It never records full
comment letter text, full applicant response text, full extracted page text,
storage keys, raw server file paths, secrets, or tokens.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_REVIEWER_PACKAGE_ITEM_STATUSES,
    ALLOWED_REVIEWER_PACKAGE_TYPES,
    reject_prohibited_language,
)
from app.db import models
from app.services.auth_service import ActorContext, audit_kwargs
from app.services.real_intake_service import record_audit_event


class ReviewerResponsePackageError(Exception):
    """Raised when a response package operation is not allowed."""

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
        raise ReviewerResponsePackageError("Project not found.", status_code=404)
    return project


def _require_package(
    db: Session, project_id: str, response_package_id: str
) -> models.ReviewerResponsePackage:
    package = db.get(models.ReviewerResponsePackage, response_package_id)
    if package is None or package.project_id != project_id:
        raise ReviewerResponsePackageError(
            "Response package not found.", status_code=404
        )
    return package


def _require_item(
    db: Session, project_id: str, response_package_item_id: str
) -> models.ReviewerResponsePackageItem:
    item = db.get(models.ReviewerResponsePackageItem, response_package_item_id)
    if item is None or item.project_id != project_id:
        raise ReviewerResponsePackageError(
            "Response package item not found.", status_code=404
        )
    return item


# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------


def create_response_package(
    db: Session,
    project_id: str,
    payload: dict | None = None,
    *,
    actor: ActorContext | None = None,
) -> dict:
    """Create a response package for a project."""

    project = _require_project(db, project_id)
    payload = payload or {}
    title = (payload.get("package_title") or "Reviewer response package").strip()
    reject_prohibited_language(title, field="package_title")

    package_type = payload.get("package_type") or "initial_review_comment_letter"
    if package_type not in ALLOWED_REVIEWER_PACKAGE_TYPES:
        raise ReviewerResponsePackageError(
            f"Invalid package_type '{package_type}'.", status_code=422
        )

    existing = db.scalar(
        select(func.count())
        .select_from(models.ReviewerResponsePackage)
        .where(models.ReviewerResponsePackage.project_id == project_id)
    )
    now = _now()
    package = models.ReviewerResponsePackage(
        response_package_id=f"rpkg_{_short()}",
        project_id=project_id,
        response_matrix_id=payload.get("response_matrix_id"),
        resubmittal_round_id=payload.get("resubmittal_round_id"),
        package_title=title,
        package_number=int(existing or 0) + 1,
        revision_number=0,
        status="package_draft",
        package_type=package_type,
        source_mode="user_created",
        prepared_by_user_id=actor.user_id if actor else None,
        prepared_by_name=_actor_name(actor),
        organization_id=actor.organization_id if actor else None,
        created_at=now,
        updated_at=now,
    )
    db.add(package)
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="response_package_created",
        related_entity_type="reviewer_response_package",
        related_entity_id=package.response_package_id,
        description=f"Reviewer created response package '{title}'.",
        actor_type="reviewer",
        actor_id=actor.user_id if actor else None,
        actor_display_name=_actor_name(actor),
        metadata={
            "response_package_id": package.response_package_id,
            "package_type": package_type,
            "package_number": package.package_number,
        },
    )
    db.commit()
    db.refresh(package)
    # Reference project so a missing project is caught before commit.
    _ = project.project_id
    return _package_detail(db, package)


def list_response_packages(db: Session, project_id: str) -> list[dict]:
    _require_project(db, project_id)
    packages = db.scalars(
        select(models.ReviewerResponsePackage)
        .where(models.ReviewerResponsePackage.project_id == project_id)
        .order_by(models.ReviewerResponsePackage.created_at)
    ).all()
    return [_package_dict(db, p) for p in packages]


def get_response_package(
    db: Session, project_id: str, response_package_id: str
) -> dict:
    package = _require_package(db, project_id, response_package_id)
    return _package_detail(db, package)


def _package_items(
    db: Session, response_package_id: str
) -> list[models.ReviewerResponsePackageItem]:
    return list(
        db.scalars(
            select(models.ReviewerResponsePackageItem)
            .where(
                models.ReviewerResponsePackageItem.response_package_id
                == response_package_id
            )
            .order_by(models.ReviewerResponsePackageItem.sort_order)
        ).all()
    )


def _package_dict(db: Session, package: models.ReviewerResponsePackage) -> dict:
    items = _package_items(db, package.response_package_id)
    included = sum(1 for item in items if item.include_in_letter)
    return {
        "response_package_id": package.response_package_id,
        "project_id": package.project_id,
        "response_matrix_id": package.response_matrix_id,
        "resubmittal_round_id": package.resubmittal_round_id,
        "package_title": package.package_title,
        "package_number": package.package_number,
        "revision_number": package.revision_number,
        "status": package.status,
        "package_type": package.package_type,
        "source_mode": package.source_mode,
        "prepared_by_name": package.prepared_by_name,
        "issued_by_name": package.issued_by_name,
        "organization_id": package.organization_id,
        "issued_at": package.issued_at,
        "created_at": package.created_at,
        "updated_at": package.updated_at,
        "item_count": len(items),
        "included_item_count": included,
    }


def _item_dict(item: models.ReviewerResponsePackageItem) -> dict:
    return {
        "response_package_item_id": item.response_package_item_id,
        "response_package_id": item.response_package_id,
        "project_id": item.project_id,
        "source_type": item.source_type,
        "source_finding_id": item.source_finding_id,
        "source_checklist_item_id": item.source_checklist_item_id,
        "source_matrix_item_id": item.source_matrix_item_id,
        "source_citation_id": item.source_citation_id,
        "source_document_id": item.source_document_id,
        "item_number": item.item_number,
        "category": item.category,
        "reviewer_comment_text": item.reviewer_comment_text,
        "applicant_response_summary": item.applicant_response_summary,
        "reviewer_follow_up_text": item.reviewer_follow_up_text,
        "requested_evidence": item.requested_evidence,
        "citation_reference": item.citation_reference,
        "include_in_letter": item.include_in_letter,
        "sort_order": item.sort_order,
        "item_status": item.item_status,
        "created_by_name": item.created_by_name,
        "updated_by_name": item.updated_by_name,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _package_detail(db: Session, package: models.ReviewerResponsePackage) -> dict:
    detail = _package_dict(db, package)
    detail["items"] = [
        _item_dict(item)
        for item in _package_items(db, package.response_package_id)
    ]
    return detail


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------


def _next_sort_order(db: Session, response_package_id: str) -> int:
    count = db.scalar(
        select(func.count())
        .select_from(models.ReviewerResponsePackageItem)
        .where(
            models.ReviewerResponsePackageItem.response_package_id
            == response_package_id
        )
    )
    return int(count or 0)


def _add_item(
    db: Session,
    *,
    package: models.ReviewerResponsePackage,
    source_type: str,
    reviewer_comment_text: str,
    category: str | None = None,
    source_finding_id: str | None = None,
    source_checklist_item_id: str | None = None,
    source_matrix_item_id: str | None = None,
    source_citation_id: str | None = None,
    source_document_id: str | None = None,
    applicant_response_summary: str | None = None,
    reviewer_follow_up_text: str | None = None,
    requested_evidence: str | None = None,
    citation_reference: str | None = None,
    actor: ActorContext | None = None,
) -> models.ReviewerResponsePackageItem:
    now = _now()
    sort_order = _next_sort_order(db, package.response_package_id)
    item = models.ReviewerResponsePackageItem(
        response_package_item_id=f"rpi_{_short()}",
        response_package_id=package.response_package_id,
        project_id=package.project_id,
        source_type=source_type,
        source_finding_id=source_finding_id,
        source_checklist_item_id=source_checklist_item_id,
        source_matrix_item_id=source_matrix_item_id,
        source_citation_id=source_citation_id,
        source_document_id=source_document_id,
        item_number=str(sort_order + 1),
        category=category,
        reviewer_comment_text=reviewer_comment_text,
        applicant_response_summary=applicant_response_summary,
        reviewer_follow_up_text=reviewer_follow_up_text,
        requested_evidence=requested_evidence,
        citation_reference=citation_reference,
        include_in_letter=True,
        sort_order=sort_order,
        item_status="item_draft",
        created_by_user_id=actor.user_id if actor else None,
        created_by_name=_actor_name(actor),
        created_at=now,
        updated_at=now,
    )
    db.add(item)
    return item


def _finalize_added(
    db: Session,
    package: models.ReviewerResponsePackage,
    items: list[models.ReviewerResponsePackageItem],
    *,
    actor: ActorContext | None,
) -> dict:
    if package.status == "package_draft":
        package.status = "package_in_review"
    package.updated_at = _now()
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=package.project_id,
        event_type="response_package_item_added",
        related_entity_type="reviewer_response_package",
        related_entity_id=package.response_package_id,
        description=(
            f"Reviewer added {len(items)} item(s) to the response package."
        ),
        actor_type="reviewer",
        actor_id=actor.user_id if actor else None,
        actor_display_name=_actor_name(actor),
        metadata={
            "response_package_id": package.response_package_id,
            "added_count": len(items),
            "item_ids": [i.response_package_item_id for i in items],
        },
    )
    db.commit()
    db.refresh(package)
    return _package_detail(db, package)


def add_matrix_items_to_package(
    db: Session,
    project_id: str,
    response_package_id: str,
    payload: dict,
    *,
    actor: ActorContext | None = None,
) -> dict:
    package = _require_package(db, project_id, response_package_id)
    matrix_item_ids = payload.get("matrix_item_ids") or []
    if not matrix_item_ids:
        raise ReviewerResponsePackageError(
            "matrix_item_ids is required.", status_code=422
        )
    created: list[models.ReviewerResponsePackageItem] = []
    for matrix_item_id in matrix_item_ids:
        matrix_item = db.get(models.ResponseMatrixItem, matrix_item_id)
        if matrix_item is None or matrix_item.project_id != project_id:
            raise ReviewerResponsePackageError(
                f"Matrix item '{matrix_item_id}' not found for this project.",
                status_code=404,
            )
        created.append(
            _add_item(
                db,
                package=package,
                source_type="response_matrix_item",
                source_matrix_item_id=matrix_item_id,
                category=matrix_item.category,
                reviewer_comment_text=matrix_item.reviewer_comment_draft or "",
                applicant_response_summary=matrix_item.applicant_response_text,
                reviewer_follow_up_text=matrix_item.reviewer_follow_up_status,
                requested_evidence=matrix_item.requested_evidence,
                actor=actor,
            )
        )
    return _finalize_added(db, package, created, actor=actor)


def add_findings_to_package(
    db: Session,
    project_id: str,
    response_package_id: str,
    payload: dict,
    *,
    actor: ActorContext | None = None,
) -> dict:
    package = _require_package(db, project_id, response_package_id)
    finding_ids = payload.get("finding_ids") or []
    if not finding_ids:
        raise ReviewerResponsePackageError(
            "finding_ids is required.", status_code=422
        )
    created: list[models.ReviewerResponsePackageItem] = []
    for finding_id in finding_ids:
        finding = db.get(models.Finding, finding_id)
        if finding is None or finding.project_id != project_id:
            raise ReviewerResponsePackageError(
                f"Finding '{finding_id}' not found for this project.",
                status_code=404,
            )
        created.append(
            _add_item(
                db,
                package=package,
                source_type="finding",
                source_finding_id=finding_id,
                category=finding.category,
                reviewer_comment_text=finding.title or "",
                requested_evidence=finding.evidence_to_find,
                applicant_response_summary=finding.applicant_response_summary,
                actor=actor,
            )
        )
    return _finalize_added(db, package, created, actor=actor)


def add_checklist_items_to_package(
    db: Session,
    project_id: str,
    response_package_id: str,
    payload: dict,
    *,
    actor: ActorContext | None = None,
) -> dict:
    package = _require_package(db, project_id, response_package_id)
    checklist_item_ids = payload.get("checklist_item_ids") or []
    if not checklist_item_ids:
        raise ReviewerResponsePackageError(
            "checklist_item_ids is required.", status_code=422
        )
    created: list[models.ReviewerResponsePackageItem] = []
    for checklist_item_id in checklist_item_ids:
        checklist_item = db.get(models.ProjectChecklistItem, checklist_item_id)
        if checklist_item is None or checklist_item.project_id != project_id:
            raise ReviewerResponsePackageError(
                f"Checklist item '{checklist_item_id}' not found for this"
                " project.",
                status_code=404,
            )
        comment = (
            f"{checklist_item.item_code}: {checklist_item.requirement_text}"
        )
        created.append(
            _add_item(
                db,
                package=package,
                source_type="checklist_item",
                source_checklist_item_id=checklist_item_id,
                category=checklist_item.category,
                reviewer_comment_text=comment,
                requested_evidence=checklist_item.expected_evidence,
                actor=actor,
            )
        )
    return _finalize_added(db, package, created, actor=actor)


def add_citations_to_package(
    db: Session,
    project_id: str,
    response_package_id: str,
    payload: dict,
    *,
    actor: ActorContext | None = None,
) -> dict:
    package = _require_package(db, project_id, response_package_id)
    citation_ids = payload.get("citation_ids") or []
    if not citation_ids:
        raise ReviewerResponsePackageError(
            "citation_ids is required.", status_code=422
        )
    created: list[models.ReviewerResponsePackageItem] = []
    for citation_id in citation_ids:
        citation = db.get(models.EvidenceCitation, citation_id)
        if citation is None or citation.project_id != project_id:
            raise ReviewerResponsePackageError(
                f"Citation '{citation_id}' not found for this project.",
                status_code=404,
            )
        reference_parts = [
            part
            for part in (
                citation.page_label
                or (f"Page {citation.page_number}" if citation.page_number else None),
                citation.section_label,
            )
            if part
        ]
        citation_reference = ", ".join(reference_parts) or "Document reference"
        comment = citation.reviewer_note or "Reviewer-cited evidence reference."
        created.append(
            _add_item(
                db,
                package=package,
                source_type="citation",
                source_citation_id=citation_id,
                source_document_id=citation.document_id,
                reviewer_comment_text=comment,
                citation_reference=citation_reference,
                actor=actor,
            )
        )
    return _finalize_added(db, package, created, actor=actor)


def add_manual_package_item(
    db: Session,
    project_id: str,
    response_package_id: str,
    payload: dict,
    *,
    actor: ActorContext | None = None,
) -> dict:
    package = _require_package(db, project_id, response_package_id)
    comment = (payload.get("reviewer_comment_text") or "").strip()
    if not comment:
        raise ReviewerResponsePackageError(
            "reviewer_comment_text is required.", status_code=422
        )
    for field in ("reviewer_comment_text", "requested_evidence", "category"):
        reject_prohibited_language(payload.get(field), field=field)
    item = _add_item(
        db,
        package=package,
        source_type="manual_reviewer_note",
        category=payload.get("category"),
        reviewer_comment_text=comment,
        requested_evidence=payload.get("requested_evidence"),
        actor=actor,
    )
    return _finalize_added(db, package, [item], actor=actor)


def update_package_item(
    db: Session,
    project_id: str,
    response_package_item_id: str,
    payload: dict,
    *,
    actor: ActorContext | None = None,
) -> models.ReviewerResponsePackageItem:
    item = _require_item(db, project_id, response_package_item_id)
    for field in (
        "reviewer_comment_text",
        "reviewer_follow_up_text",
        "requested_evidence",
    ):
        reject_prohibited_language(payload.get(field), field=field)

    if payload.get("reviewer_comment_text") is not None:
        item.reviewer_comment_text = payload["reviewer_comment_text"]
    if payload.get("reviewer_follow_up_text") is not None:
        item.reviewer_follow_up_text = payload["reviewer_follow_up_text"]
    if payload.get("requested_evidence") is not None:
        item.requested_evidence = payload["requested_evidence"]
    if payload.get("include_in_letter") is not None:
        item.include_in_letter = bool(payload["include_in_letter"])
    if payload.get("sort_order") is not None:
        item.sort_order = int(payload["sort_order"])
    item_status = payload.get("item_status")
    if item_status is not None:
        if item_status not in ALLOWED_REVIEWER_PACKAGE_ITEM_STATUSES:
            raise ReviewerResponsePackageError(
                f"Invalid item_status '{item_status}'.", status_code=422
            )
        item.item_status = item_status

    item.updated_by_name = _actor_name(actor)
    item.updated_at = _now()
    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="response_package_item_updated",
        related_entity_type="reviewer_response_package_item",
        related_entity_id=response_package_item_id,
        description="Reviewer updated a response package item.",
        actor_type="reviewer",
        actor_id=actor.user_id if actor else None,
        actor_display_name=_actor_name(actor),
        metadata={
            "response_package_item_id": response_package_item_id,
            "item_status": item.item_status,
            "include_in_letter": item.include_in_letter,
        },
    )
    db.commit()
    db.refresh(item)
    return item


# ---------------------------------------------------------------------------
# Preview, handoff, issuance, revisions
# ---------------------------------------------------------------------------

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


def list_package_items(
    db: Session, project_id: str, response_package_id: str
) -> list[models.ReviewerResponsePackageItem]:
    _require_package(db, project_id, response_package_id)
    return _package_items(db, response_package_id)
