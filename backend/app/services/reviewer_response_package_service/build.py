"""Package creation, item assembly, and item updates."""

from __future__ import annotations

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

from ._common import (
    _actor_name,
    _next_sort_order,
    _now,
    _require_item,
    _require_package,
    _require_project,
    _short,
)
from .errors import ReviewerResponsePackageError
from .reads import _package_detail


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


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------


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
