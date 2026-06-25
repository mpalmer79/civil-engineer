"""Phase 13 multi-round resubmittal, revision comparison, and response cycle.

This service tracks multiple review rounds for a project. A reviewer can create
or load a review cycle, record a resubmittal package, link uploaded DXF files and
applicant responses, compare the current DXF parse metadata against a previous
round, map applicant responses to prior response package or workflow items, mark
review-support resolution statuses, carry unresolved items forward, and prepare
the next review cycle.

Everything here is review-support and evidence-organization. It does not approve
plans, certify compliance, stamp drawings, verify CAD, validate design, or make
final engineering decisions. Revision comparison compares extracted DXF metadata
(layers, references, blocks, and review findings) only; it never compares geometry
in a way that implies engineering validation, and there is no action called
approve. Resolution statuses such as addressed_for_review are review-support
states, never final decisions like resolved, closed, approved, or certified.

Read side effects: get_review_cycle, get_review_cycle_dashboard,
get_revision_comparison_run, list_revision_change_records, get_response_mapping_summary,
get_carry_forward_summary, get_resolution_summary, and get_next_cycle_preparation
each write an audit event recording reviewer access. This is intentional so the
decision history shows reviewer access.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_APPLICANT_RESPONSE_STATUSES,
    ALLOWED_CARRY_FORWARD_STATUSES,
    ALLOWED_MAPPING_CONFIDENCE_LABELS,
    ALLOWED_NEXT_CYCLE_STATUSES,
    ALLOWED_RESOLUTION_STATUSES,
    ALLOWED_RESUBMITTAL_STATUSES,
    ALLOWED_REVIEW_CYCLE_STATUSES,
    ALLOWED_REVISION_COMPARISON_STATUSES,
)
from app.db import models
from app.services import cad_intake_service, response_package_service, workflow_service

LIMITATIONS_NOTE = (
    "Revision comparison compares extracted DXF metadata only (layers, "
    "references, blocks, and review findings). It does not verify CAD, validate "
    "geometry or design, certify compliance, approve plans, or replace a "
    "licensed Professional Engineer. All statuses are review-support statuses, "
    "not final engineering decisions."
)

# Reference candidate type to revision source category.
REF_TYPE_TO_CATEGORY: dict[str, str] = {
    "sheet_reference": "sheet_reference",
    "detail_reference": "detail_reference",
    "pipe_label": "pipe_label",
    "basin_label": "basin_label",
    "outfall_label": "outfall_label",
    "wetland_buffer_label": "wetland_buffer_label",
    "revision_note": "text_reference",
    "general_note": "text_reference",
    "unknown": "unknown",
}

# CAD finding type to revision source category.
FINDING_TYPE_TO_CATEGORY: dict[str, str] = {
    "missing_plan_sheet_match": "sheet_reference",
    "missing_sheet_reference": "sheet_reference",
    "unclear_detail_reference": "detail_reference",
    "possible_label_conflict": "basin_label",
    "unknown_layer_category": "layer",
    "parse_warning": "unknown",
}

# Categories whose identity tolerates a value change (so a changed distance or
# number reads as a changed item rather than a remove plus add).
STEM_CATEGORIES = {"basin_label", "wetland_buffer_label", "text_reference"}

_STOPWORDS = {
    "the",
    "and",
    "for",
    "see",
    "with",
    "this",
    "that",
    "from",
    "per",
    "has",
    "have",
    "been",
    "will",
    "should",
    "needs",
    "need",
    "review",
    "reviewer",
    "plan",
    "sheet",
    "detail",
    "note",
    "item",
}


class ReviewCycleError(Exception):
    """Raised when a review cycle operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


def _audit(
    db: Session,
    *,
    project_id: str,
    event_type: str,
    related_entity_type: str,
    related_entity_id: str,
    description: str,
    actor_type: str = "reviewer",
    metadata: dict | None = None,
) -> None:
    db.add(
        models.AuditEvent(
            audit_event_id=f"audit_cycle_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            event_type=event_type,
            actor_type=actor_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            description=description,
            timestamp=_now(),
            event_metadata=metadata or {},
        )
    )


def _require_project(db: Session, project_id: str) -> None:
    if db.get(models.Project, project_id) is None:
        raise ReviewCycleError("Project not found.", status_code=404)


def _keywords(text: str | None) -> set[str]:
    if not text:
        return set()
    tokens = re.findall(r"[a-z0-9][a-z0-9\.\-/]*", text.lower())
    return {t for t in tokens if len(t) >= 3 and t not in _STOPWORDS}


def _stem(normalized: str) -> str:
    stem = re.sub(r"\b\d+\b", "", normalized)
    stem = re.sub(r"\s+", " ", stem).strip()
    return stem or normalized


# ---------------------------------------------------------------------------
# Review cycle
# ---------------------------------------------------------------------------


def _latest_response_package(
    db: Session, project_id: str
) -> models.ResponsePackage | None:
    return db.scalars(
        select(models.ResponsePackage)
        .where(models.ResponsePackage.project_id == project_id)
        .order_by(models.ResponsePackage.created_at.desc())
    ).first()


def create_review_cycle(
    db: Session,
    *,
    project_id: str,
    cycle_number: int | None = None,
    cycle_name: str | None = None,
    source_response_package_id: str | None = None,
    source_workflow_board_id: str | None = None,
    summary: str | None = None,
) -> models.ReviewCycle:
    _require_project(db, project_id)
    existing = list_review_cycles(db, project_id)
    if cycle_number is None:
        cycle_number = (max((c.cycle_number for c in existing), default=0)) + 1
    if cycle_name is None:
        cycle_name = (
            "Initial review" if cycle_number == 1 else f"Review round {cycle_number}"
        )
    if source_response_package_id is None:
        package = _latest_response_package(db, project_id)
        source_response_package_id = (
            package.response_package_id if package is not None else None
        )
    if source_workflow_board_id is None:
        source_workflow_board_id = project_id

    cycle = models.ReviewCycle(
        review_cycle_id=f"cycle_{_short()}",
        project_id=project_id,
        cycle_number=cycle_number,
        cycle_name=cycle_name,
        status="active",
        started_at=_now(),
        source_response_package_id=source_response_package_id,
        source_workflow_board_id=source_workflow_board_id,
        summary=summary
        or (
            f"Review cycle {cycle_number} for the project. Tracks resubmittals, "
            "applicant responses, DXF revision comparison, and carry-forward "
            "items under human review."
        ),
        requires_human_review=True,
    )
    db.add(cycle)
    _audit(
        db,
        project_id=project_id,
        event_type="review_cycle_created",
        related_entity_type="review_cycle",
        related_entity_id=cycle.review_cycle_id,
        description=f"Review cycle {cycle_number} created.",
        metadata={"review_cycle_id": cycle.review_cycle_id, "cycle_number": cycle_number},
    )
    db.commit()
    db.refresh(cycle)
    return cycle


def ensure_review_cycle(db: Session, project_id: str) -> None:
    """Create the initial review cycle once if none exists for the project."""

    if db.get(models.Project, project_id) is None:
        return
    existing = (
        db.query(models.ReviewCycle)
        .filter(models.ReviewCycle.project_id == project_id)
        .first()
    )
    if existing is None:
        create_review_cycle(db, project_id=project_id, cycle_number=1)


def list_review_cycles(db: Session, project_id: str) -> list[models.ReviewCycle]:
    return list(
        db.scalars(
            select(models.ReviewCycle)
            .where(models.ReviewCycle.project_id == project_id)
            .order_by(models.ReviewCycle.cycle_number)
        ).all()
    )


def get_review_cycle_record(
    db: Session, review_cycle_id: str
) -> models.ReviewCycle | None:
    return db.scalars(
        select(models.ReviewCycle).where(
            models.ReviewCycle.review_cycle_id == review_cycle_id
        )
    ).first()


def get_review_cycle(
    db: Session, review_cycle_id: str
) -> models.ReviewCycle | None:
    cycle = get_review_cycle_record(db, review_cycle_id)
    if cycle is None:
        return None
    _audit(
        db,
        project_id=cycle.project_id,
        event_type="review_cycle_viewed",
        related_entity_type="review_cycle",
        related_entity_id=review_cycle_id,
        description="Review cycle viewed.",
        metadata={"review_cycle_id": review_cycle_id},
    )
    db.commit()
    return cycle


def _active_cycle(db: Session, project_id: str) -> models.ReviewCycle | None:
    cycles = list_review_cycles(db, project_id)
    if not cycles:
        return None
    for cycle in reversed(cycles):
        if cycle.status in {"active", "draft"}:
            return cycle
    return cycles[-1]


def get_review_cycle_summary(db: Session, project_id: str) -> dict:
    _require_project(db, project_id)
    cycles = list_review_cycles(db, project_id)
    statuses: dict[str, int] = {}
    for cycle in cycles:
        statuses[cycle.status] = statuses.get(cycle.status, 0) + 1
    active = _active_cycle(db, project_id)
    return {
        "project_id": project_id,
        "cycle_count": len(cycles),
        "active_cycle_id": active.review_cycle_id if active else None,
        "active_cycle_number": active.cycle_number if active else None,
        "statuses": statuses,
        "note": (
            "Review cycles organize multi-round review-support work. They do not "
            "approve plans, certify compliance, or make final engineering decisions."
        ),
    }


def _require_cycle(db: Session, review_cycle_id: str) -> models.ReviewCycle:
    cycle = get_review_cycle_record(db, review_cycle_id)
    if cycle is None:
        raise ReviewCycleError("Review cycle not found.", status_code=404)
    return cycle


# ---------------------------------------------------------------------------
# Resubmittal package
# ---------------------------------------------------------------------------


def create_resubmittal_package(
    db: Session,
    *,
    project_id: str,
    review_cycle_id: str | None,
    package_name: str,
    submitted_by: str = "applicant",
    summary: str | None = None,
) -> models.ResubmittalPackage:
    _require_project(db, project_id)
    if review_cycle_id is None:
        cycle = _active_cycle(db, project_id)
        if cycle is None:
            cycle = create_review_cycle(db, project_id=project_id)
        review_cycle_id = cycle.review_cycle_id
    else:
        _require_cycle(db, review_cycle_id)

    package = models.ResubmittalPackage(
        resubmittal_package_id=f"resub_{_short()}",
        project_id=project_id,
        review_cycle_id=review_cycle_id,
        package_name=package_name,
        submitted_by=submitted_by,
        submitted_at=_now(),
        received_at=_now(),
        status="received",
        summary=summary
        or "Resubmittal package received for review-support intake.",
        requires_human_review=True,
    )
    db.add(package)
    _audit(
        db,
        project_id=project_id,
        event_type="resubmittal_created",
        related_entity_type="resubmittal_package",
        related_entity_id=package.resubmittal_package_id,
        description=f"Resubmittal package '{package_name}' created.",
        metadata={
            "resubmittal_package_id": package.resubmittal_package_id,
            "review_cycle_id": review_cycle_id,
        },
    )
    db.commit()
    db.refresh(package)
    return package


def list_resubmittal_packages(
    db: Session, project_id: str
) -> list[models.ResubmittalPackage]:
    return list(
        db.scalars(
            select(models.ResubmittalPackage)
            .where(models.ResubmittalPackage.project_id == project_id)
            .order_by(models.ResubmittalPackage.created_at)
        ).all()
    )


def get_resubmittal_package_record(
    db: Session, resubmittal_package_id: str
) -> models.ResubmittalPackage | None:
    return db.scalars(
        select(models.ResubmittalPackage).where(
            models.ResubmittalPackage.resubmittal_package_id
            == resubmittal_package_id
        )
    ).first()


def list_resubmittal_documents(
    db: Session, resubmittal_package_id: str
) -> list[models.ResubmittalDocument]:
    return list(
        db.scalars(
            select(models.ResubmittalDocument)
            .where(
                models.ResubmittalDocument.resubmittal_package_id
                == resubmittal_package_id
            )
            .order_by(models.ResubmittalDocument.created_at)
        ).all()
    )


def get_resubmittal_package(
    db: Session, resubmittal_package_id: str
) -> dict | None:
    package = get_resubmittal_package_record(db, resubmittal_package_id)
    if package is None:
        return None
    documents = list_resubmittal_documents(db, resubmittal_package_id)
    responses = list(
        db.scalars(
            select(models.ApplicantResponse)
            .where(
                models.ApplicantResponse.resubmittal_package_id
                == resubmittal_package_id
            )
            .order_by(models.ApplicantResponse.created_at)
        ).all()
    )
    _audit(
        db,
        project_id=package.project_id,
        event_type="resubmittal_viewed",
        related_entity_type="resubmittal_package",
        related_entity_id=resubmittal_package_id,
        description="Resubmittal package viewed.",
        metadata={"resubmittal_package_id": resubmittal_package_id},
    )
    db.commit()
    data = {
        c.name: getattr(package, c.name)
        for c in package.__table__.columns
    }
    data["documents"] = documents
    data["applicant_responses"] = responses
    data["note"] = (
        "Resubmittal intake organizes review-support evidence for a human "
        "reviewer. It does not approve plans or certify compliance."
    )
    return data


def update_resubmittal_package_status(
    db: Session,
    resubmittal_package_id: str,
    *,
    status: str,
    reviewer_note: str | None = None,
) -> models.ResubmittalPackage:
    package = get_resubmittal_package_record(db, resubmittal_package_id)
    if package is None:
        raise ReviewCycleError("Resubmittal package not found.", status_code=404)
    if status not in ALLOWED_RESUBMITTAL_STATUSES:
        raise ReviewCycleError(
            f"Invalid resubmittal status '{status}'.", status_code=422
        )
    previous = package.status
    package.status = status
    if reviewer_note is not None:
        package.reviewer_note = reviewer_note
    package.updated_at = _now()
    _audit(
        db,
        project_id=package.project_id,
        event_type="resubmittal_status_changed",
        related_entity_type="resubmittal_package",
        related_entity_id=resubmittal_package_id,
        description=f"Resubmittal status changed from {previous} to {status}.",
        metadata={"previous_status": previous, "new_status": status},
    )
    db.commit()
    db.refresh(package)
    return package


def link_cad_file_to_resubmittal(
    db: Session, resubmittal_package_id: str, cad_file_id: str
) -> models.ResubmittalDocument:
    package = get_resubmittal_package_record(db, resubmittal_package_id)
    if package is None:
        raise ReviewCycleError("Resubmittal package not found.", status_code=404)
    cad_file = cad_intake_service.get_cad_file(db, cad_file_id)
    if cad_file is None:
        raise ReviewCycleError("CAD file not found.", status_code=404)

    existing = db.scalars(
        select(models.ResubmittalDocument).where(
            models.ResubmittalDocument.resubmittal_package_id
            == resubmittal_package_id,
            models.ResubmittalDocument.source_type == "cad_file",
            models.ResubmittalDocument.source_id == cad_file_id,
        )
    ).first()
    if existing is not None:
        return existing

    document = models.ResubmittalDocument(
        resubmittal_document_id=f"resubdoc_{_short()}",
        project_id=package.project_id,
        review_cycle_id=package.review_cycle_id,
        resubmittal_package_id=resubmittal_package_id,
        document_type="dxf_cad_file",
        source_type="cad_file",
        source_id=cad_file_id,
        file_name=cad_file.original_file_name or cad_file.file_name,
        description=(
            f"DXF CAD file '{cad_file.original_file_name or cad_file.file_name}' "
            "linked to the resubmittal for revision comparison."
        ),
        status="linked",
    )
    db.add(document)
    _audit(
        db,
        project_id=package.project_id,
        event_type="resubmittal_cad_file_linked",
        related_entity_type="resubmittal_package",
        related_entity_id=resubmittal_package_id,
        description="CAD file linked to resubmittal package.",
        metadata={
            "resubmittal_package_id": resubmittal_package_id,
            "cad_file_id": cad_file_id,
        },
    )
    db.commit()
    db.refresh(document)
    return document


def link_applicant_response_to_resubmittal(
    db: Session,
    resubmittal_package_id: str,
    *,
    response_text: str,
    response_topic: str = "general",
    submitted_by: str = "applicant",
    target_response_item_id: str | None = None,
    target_workflow_item_id: str | None = None,
) -> models.ApplicantResponse:
    package = get_resubmittal_package_record(db, resubmittal_package_id)
    if package is None:
        raise ReviewCycleError("Resubmittal package not found.", status_code=404)

    response = models.ApplicantResponse(
        applicant_response_id=f"aresp_{_short()}",
        project_id=package.project_id,
        review_cycle_id=package.review_cycle_id,
        resubmittal_package_id=resubmittal_package_id,
        response_text=response_text,
        response_topic=response_topic,
        submitted_by=submitted_by,
        target_response_item_id=target_response_item_id,
        target_workflow_item_id=target_workflow_item_id,
        status="received",
        requires_human_review=True,
    )
    db.add(response)
    db.add(
        models.ResubmittalDocument(
            resubmittal_document_id=f"resubdoc_{_short()}",
            project_id=package.project_id,
            review_cycle_id=package.review_cycle_id,
            resubmittal_package_id=resubmittal_package_id,
            document_type="applicant_response_note",
            source_type="applicant_response",
            source_id=response.applicant_response_id,
            file_name=None,
            description=f"Applicant response note: {response_topic}.",
            status="linked",
        )
    )
    _audit(
        db,
        project_id=package.project_id,
        event_type="applicant_response_created",
        related_entity_type="applicant_response",
        related_entity_id=response.applicant_response_id,
        description="Applicant response created.",
        metadata={
            "applicant_response_id": response.applicant_response_id,
            "resubmittal_package_id": resubmittal_package_id,
        },
    )
    db.commit()
    db.refresh(response)
    return response


# ---------------------------------------------------------------------------
# Applicant response mapping
# ---------------------------------------------------------------------------


def list_applicant_responses(
    db: Session, project_id: str
) -> list[models.ApplicantResponse]:
    return list(
        db.scalars(
            select(models.ApplicantResponse)
            .where(models.ApplicantResponse.project_id == project_id)
            .order_by(models.ApplicantResponse.created_at)
        ).all()
    )


def _get_applicant_response(
    db: Session, applicant_response_id: str
) -> models.ApplicantResponse | None:
    return db.scalars(
        select(models.ApplicantResponse).where(
            models.ApplicantResponse.applicant_response_id == applicant_response_id
        )
    ).first()


def list_response_mappings_for_cycle(
    db: Session, review_cycle_id: str
) -> list[models.ApplicantResponseMapping]:
    return list(
        db.scalars(
            select(models.ApplicantResponseMapping)
            .where(
                models.ApplicantResponseMapping.review_cycle_id == review_cycle_id
            )
            .order_by(models.ApplicantResponseMapping.created_at)
        ).all()
    )


def create_applicant_response_mapping(
    db: Session,
    applicant_response_id: str,
    *,
    response_package_item_id: str | None = None,
    workflow_item_id: str | None = None,
    mapping_confidence: str = "medium",
    mapping_reason: str | None = None,
    commit: bool = True,
) -> models.ApplicantResponseMapping:
    response = _get_applicant_response(db, applicant_response_id)
    if response is None:
        raise ReviewCycleError("Applicant response not found.", status_code=404)
    if mapping_confidence not in ALLOWED_MAPPING_CONFIDENCE_LABELS:
        raise ReviewCycleError(
            f"Invalid mapping confidence '{mapping_confidence}'.", status_code=422
        )

    mapping = models.ApplicantResponseMapping(
        mapping_id=f"map_{_short()}",
        project_id=response.project_id,
        review_cycle_id=response.review_cycle_id,
        applicant_response_id=applicant_response_id,
        response_package_item_id=response_package_item_id,
        workflow_item_id=workflow_item_id,
        mapping_confidence=mapping_confidence,
        mapping_reason=mapping_reason
        or "Reviewer mapping between an applicant response and a prior item.",
        requires_human_review=True,
    )
    db.add(mapping)
    response.status = "mapped_to_issue"
    response.target_response_item_id = (
        response_package_item_id or response.target_response_item_id
    )
    response.target_workflow_item_id = (
        workflow_item_id or response.target_workflow_item_id
    )
    response.updated_at = _now()
    _audit(
        db,
        project_id=response.project_id,
        event_type="applicant_response_mapping_created",
        related_entity_type="applicant_response_mapping",
        related_entity_id=mapping.mapping_id,
        description="Applicant response mapping created.",
        metadata={
            "applicant_response_id": applicant_response_id,
            "mapping_id": mapping.mapping_id,
            "mapping_confidence": mapping_confidence,
        },
    )
    if commit:
        db.commit()
        db.refresh(mapping)
    return mapping


def _response_package_items(db: Session, project_id: str) -> list:
    package = _latest_response_package(db, project_id)
    if package is None:
        return []
    return list(
        db.scalars(
            select(models.ResponsePackageItem).where(
                models.ResponsePackageItem.response_package_id
                == package.response_package_id
            )
        ).all()
    )


def auto_suggest_response_mappings(
    db: Session, review_cycle_id: str
) -> list[models.ApplicantResponseMapping]:
    """Create deterministic mapping suggestions for unmapped applicant responses.

    Matching uses shared keywords between the applicant response and prior
    response package items and workflow items. No live AI calls and no vector
    search are used. Every suggestion carries a confidence label and a reason and
    requires human review.
    """

    cycle = _require_cycle(db, review_cycle_id)
    project_id = cycle.project_id
    responses = [
        r
        for r in list_applicant_responses(db, project_id)
        if r.review_cycle_id == review_cycle_id and r.status == "received"
    ]
    existing_response_ids = {
        m.applicant_response_id
        for m in list_response_mappings_for_cycle(db, review_cycle_id)
    }

    response_items = _response_package_items(db, project_id)
    workflow_items = workflow_service.list_workflow_items(db, project_id)

    candidates: list[tuple[str, str, str, set[str]]] = []
    for item in response_items:
        candidates.append(
            (
                "response_package_item",
                item.item_id,
                item.title,
                _keywords(f"{item.title} {item.draft_text or ''}"),
            )
        )
    for item in workflow_items:
        candidates.append(
            (
                "workflow_item",
                item.workflow_item_id,
                item.title,
                _keywords(f"{item.title} {item.description or ''}"),
            )
        )

    created: list[models.ApplicantResponseMapping] = []
    for response in responses:
        if response.applicant_response_id in existing_response_ids:
            continue
        response_keywords = _keywords(
            f"{response.response_text} {response.response_topic}"
        )
        best = None
        best_overlap: set[str] = set()
        for kind, item_id, title, item_keywords in candidates:
            overlap = response_keywords & item_keywords
            # An explicit applicant target is a strong signal.
            explicit = item_id in {
                response.target_response_item_id,
                response.target_workflow_item_id,
            }
            score = len(overlap) + (5 if explicit else 0)
            if best is None or score > best[0]:
                best = (score, kind, item_id, title, explicit)
                best_overlap = overlap

        if best is None or best[0] == 0:
            # No prior item to map to; flag for human review.
            mapping = create_applicant_response_mapping(
                db,
                response.applicant_response_id,
                mapping_confidence="needs_human_review",
                mapping_reason=(
                    "No prior response or workflow item matched this response by "
                    "keyword. Reviewer should map it manually."
                ),
                commit=False,
            )
            created.append(mapping)
            continue

        _score, kind, item_id, title, explicit = best
        if explicit or _score >= 4:
            confidence = "high"
        elif _score >= 2:
            confidence = "medium"
        else:
            confidence = "low"
        shared = ", ".join(sorted(best_overlap)[:5]) or "topic"
        reason = (
            f"Suggested mapping to {kind.replace('_', ' ')} '{title}' based on "
            f"shared terms ({shared})."
        )
        mapping = create_applicant_response_mapping(
            db,
            response.applicant_response_id,
            response_package_item_id=(
                item_id if kind == "response_package_item" else None
            ),
            workflow_item_id=item_id if kind == "workflow_item" else None,
            mapping_confidence=confidence,
            mapping_reason=reason,
            commit=False,
        )
        created.append(mapping)

    _audit(
        db,
        project_id=project_id,
        event_type="response_mappings_suggested",
        related_entity_type="review_cycle",
        related_entity_id=review_cycle_id,
        description=f"{len(created)} response mapping suggestion(s) created.",
        metadata={"review_cycle_id": review_cycle_id, "suggested": len(created)},
    )
    db.commit()
    for mapping in created:
        db.refresh(mapping)
    return created


def get_response_mapping_summary(db: Session, review_cycle_id: str) -> dict:
    cycle = _require_cycle(db, review_cycle_id)
    responses = [
        r
        for r in list_applicant_responses(db, cycle.project_id)
        if r.review_cycle_id == review_cycle_id
    ]
    mappings = list_response_mappings_for_cycle(db, review_cycle_id)
    mapped_ids = {m.applicant_response_id for m in mappings}
    confidence_counts: dict[str, int] = {}
    for mapping in mappings:
        confidence_counts[mapping.mapping_confidence] = (
            confidence_counts.get(mapping.mapping_confidence, 0) + 1
        )
    _audit(
        db,
        project_id=cycle.project_id,
        event_type="response_mapping_summary_viewed",
        related_entity_type="review_cycle",
        related_entity_id=review_cycle_id,
        description="Response mapping summary viewed.",
        metadata={"review_cycle_id": review_cycle_id},
    )
    db.commit()
    return {
        "review_cycle_id": review_cycle_id,
        "project_id": cycle.project_id,
        "response_count": len(responses),
        "mapped_count": len(mapped_ids),
        "unmapped_count": len([r for r in responses if r.applicant_response_id not in mapped_ids]),
        "suggested_count": len(mappings),
        "confidence_counts": confidence_counts,
        "note": (
            "Mappings are review-support suggestions, not verified matches. Every "
            "mapping needs human review."
        ),
    }


# ---------------------------------------------------------------------------
# Revision comparison
# ---------------------------------------------------------------------------


def _findings_for_run(db: Session, parse_run_id: str) -> list:
    return list(
        db.scalars(
            select(models.CadReviewFinding).where(
                models.CadReviewFinding.parse_run_id == parse_run_id
            )
        ).all()
    )


def _round_metadata(db: Session, parse_run_id: str) -> dict:
    layers = {
        layer.layer_name: layer.review_category
        for layer in cad_intake_service.list_cad_layers(
            db, parse_run_id, audit=False
        )
    }
    blocks = {
        block.block_name: block.block_name
        for block in cad_intake_service.list_cad_blocks(db, parse_run_id)
    }
    references: dict[str, dict[str, str]] = {}
    for candidate in cad_intake_service.list_cad_reference_candidates(
        db, parse_run_id
    ):
        category = REF_TYPE_TO_CATEGORY.get(
            candidate.reference_type, "text_reference"
        )
        key = (
            _stem(candidate.normalized_reference)
            if category in STEM_CATEGORIES
            else candidate.normalized_reference
        )
        references.setdefault(category, {})[key] = candidate.reference_text
    findings = {}
    for finding in _findings_for_run(db, parse_run_id):
        # Key by the full title (not stemmed) so distinct findings such as a
        # missing C-9.9 sheet and a missing C-8.8 sheet stay separate.
        key = (finding.finding_type, finding.title.strip().upper())
        findings[key] = finding
    return {"layers": layers, "blocks": blocks, "references": references, "findings": findings}


def _change_severity(change_type: str) -> str:
    return {
        "added": "low",
        "removed": "medium",
        "changed": "medium",
        "carried_forward": "medium",
        "unchanged": "low",
    }.get(change_type, "low")


def run_revision_comparison(
    db: Session,
    *,
    project_id: str,
    review_cycle_id: str,
    previous_parse_run_id: str,
    current_parse_run_id: str,
    resubmittal_package_id: str | None = None,
) -> models.RevisionComparisonRun:
    """Compare extracted DXF metadata between two parse runs.

    Compares layers and review categories, reference candidates (sheet, detail,
    pipe, basin, outfall, and wetland buffer references and other text), block
    names, and CAD review findings. It does not compare geometry in a way that
    implies engineering validation and never verifies CAD or validates design.
    """

    _require_project(db, project_id)
    cycle = _require_cycle(db, review_cycle_id)
    previous = cad_intake_service.get_cad_parse_run(db, previous_parse_run_id)
    current = cad_intake_service.get_cad_parse_run(db, current_parse_run_id)
    if previous is None or current is None:
        raise ReviewCycleError("Parse run not found.", status_code=404)

    run = models.RevisionComparisonRun(
        comparison_run_id=f"rev_{_short()}",
        project_id=project_id,
        review_cycle_id=review_cycle_id,
        resubmittal_package_id=resubmittal_package_id,
        previous_parse_run_id=previous_parse_run_id,
        current_parse_run_id=current_parse_run_id,
        status="draft",
        summary="",
        limitations_note=LIMITATIONS_NOTE,
        requires_human_review=True,
    )
    db.add(run)
    db.flush()

    prev_meta = _round_metadata(db, previous_parse_run_id)
    cur_meta = _round_metadata(db, current_parse_run_id)

    counts = {"added": 0, "removed": 0, "changed": 0, "unchanged": 0, "carried_forward": 0}

    def add_record(
        change_type: str,
        source_category: str,
        normalized_key: str,
        *,
        previous_value: str | None = None,
        current_value: str | None = None,
        layer_name: str | None = None,
        reference_type: str | None = None,
        severity: str | None = None,
        reviewer_status: str = "draft",
        linked_cad_review_finding_id: str | None = None,
    ) -> None:
        counts[change_type] = counts.get(change_type, 0) + 1
        db.add(
            models.RevisionChangeRecord(
                change_record_id=f"chg_{_short()}",
                project_id=project_id,
                review_cycle_id=review_cycle_id,
                comparison_run_id=run.comparison_run_id,
                change_type=change_type,
                source_category=source_category,
                previous_value=previous_value,
                current_value=current_value,
                normalized_key=normalized_key,
                layer_name=layer_name,
                reference_type=reference_type,
                severity=severity or _change_severity(change_type),
                linked_cad_review_finding_id=linked_cad_review_finding_id,
                reviewer_status=reviewer_status,
                requires_human_review=change_type != "unchanged",
            )
        )

    # Layers (key = layer name, value = review category).
    prev_layers = prev_meta["layers"]
    cur_layers = cur_meta["layers"]
    for name in sorted(set(prev_layers) | set(cur_layers)):
        if name not in prev_layers:
            add_record("added", "layer", name, current_value=cur_layers[name], layer_name=name)
        elif name not in cur_layers:
            add_record("removed", "layer", name, previous_value=prev_layers[name], layer_name=name)
        elif prev_layers[name] != cur_layers[name]:
            add_record(
                "changed",
                "layer",
                name,
                previous_value=prev_layers[name],
                current_value=cur_layers[name],
                layer_name=name,
            )
        else:
            add_record("unchanged", "layer", name, previous_value=prev_layers[name], current_value=cur_layers[name], layer_name=name)

    # Blocks (key = block name).
    prev_blocks = prev_meta["blocks"]
    cur_blocks = cur_meta["blocks"]
    for name in sorted(set(prev_blocks) | set(cur_blocks)):
        if name not in prev_blocks:
            add_record("added", "block", name, current_value=name)
        elif name not in cur_blocks:
            add_record("removed", "block", name, previous_value=name)
        else:
            add_record("unchanged", "block", name, previous_value=name, current_value=name)

    # Reference candidates by category.
    prev_refs = prev_meta["references"]
    cur_refs = cur_meta["references"]
    for category in sorted(set(prev_refs) | set(cur_refs)):
        prev_map = prev_refs.get(category, {})
        cur_map = cur_refs.get(category, {})
        for key in sorted(set(prev_map) | set(cur_map)):
            if key not in prev_map:
                add_record(
                    "added",
                    category,
                    key,
                    current_value=cur_map[key],
                    reference_type=category,
                )
            elif key not in cur_map:
                add_record(
                    "removed",
                    category,
                    key,
                    previous_value=prev_map[key],
                    reference_type=category,
                )
            elif prev_map[key] != cur_map[key]:
                add_record(
                    "changed",
                    category,
                    key,
                    previous_value=prev_map[key],
                    current_value=cur_map[key],
                    reference_type=category,
                )
            else:
                add_record(
                    "unchanged",
                    category,
                    key,
                    previous_value=prev_map[key],
                    current_value=cur_map[key],
                    reference_type=category,
                )

    # CAD review findings (key = finding type + normalized title).
    prev_findings = prev_meta["findings"]
    cur_findings = cur_meta["findings"]
    for key in sorted(set(prev_findings) | set(cur_findings), key=lambda k: (k[0], k[1])):
        finding_type, _title = key
        category = FINDING_TYPE_TO_CATEGORY.get(finding_type, "unknown")
        if key not in prev_findings:
            finding = cur_findings[key]
            add_record(
                "added",
                category,
                finding.title,
                current_value=finding.title,
                severity=finding.severity,
                linked_cad_review_finding_id=finding.cad_review_finding_id,
            )
        elif key not in cur_findings:
            finding = prev_findings[key]
            add_record(
                "removed",
                category,
                finding.title,
                previous_value=finding.title,
                severity="low",
            )
        else:
            finding = cur_findings[key]
            add_record(
                "carried_forward",
                category,
                finding.title,
                previous_value=prev_findings[key].title,
                current_value=finding.title,
                severity=finding.severity,
                reviewer_status="carried_forward",
                linked_cad_review_finding_id=finding.cad_review_finding_id,
            )

    warning_count = counts["carried_forward"]
    run.compared_layer_count = len(set(prev_layers) | set(cur_layers))
    run.compared_text_count = sum(
        len(set(prev_refs.get(c, {})) | set(cur_refs.get(c, {})))
        for c in set(prev_refs) | set(cur_refs)
    )
    run.added_count = counts["added"]
    run.removed_count = counts["removed"]
    run.changed_count = counts["changed"]
    run.unchanged_count = counts["unchanged"]
    run.warning_count = warning_count
    run.completed_at = _now()
    run.status = "completed_with_warnings" if warning_count else "completed"
    run.summary = (
        f"Compared DXF metadata: {counts['added']} added, {counts['removed']} "
        f"removed, {counts['changed']} changed, {counts['carried_forward']} "
        f"carried forward, {counts['unchanged']} unchanged references. Review-support only."
    )

    # Mark the resubmittal as comparison complete if linked.
    if resubmittal_package_id:
        package = get_resubmittal_package_record(db, resubmittal_package_id)
        if package is not None and package.status in {
            "received",
            "intake_review",
            "ready_for_comparison",
        }:
            package.status = "comparison_complete"
            package.updated_at = _now()

    _audit(
        db,
        project_id=project_id,
        event_type="revision_comparison_run",
        related_entity_type="revision_comparison_run",
        related_entity_id=run.comparison_run_id,
        description="DXF revision comparison run.",
        metadata={
            "comparison_run_id": run.comparison_run_id,
            "review_cycle_id": review_cycle_id,
            "added": counts["added"],
            "removed": counts["removed"],
            "changed": counts["changed"],
            "carried_forward": counts["carried_forward"],
        },
    )
    db.commit()
    db.refresh(run)
    return run


def get_revision_comparison_run_record(
    db: Session, comparison_run_id: str
) -> models.RevisionComparisonRun | None:
    return db.scalars(
        select(models.RevisionComparisonRun).where(
            models.RevisionComparisonRun.comparison_run_id == comparison_run_id
        )
    ).first()


def get_revision_comparison_run(
    db: Session, comparison_run_id: str
) -> models.RevisionComparisonRun | None:
    run = get_revision_comparison_run_record(db, comparison_run_id)
    if run is None:
        return None
    _audit(
        db,
        project_id=run.project_id,
        event_type="revision_comparison_viewed",
        related_entity_type="revision_comparison_run",
        related_entity_id=comparison_run_id,
        description="Revision comparison run viewed.",
        metadata={"comparison_run_id": comparison_run_id},
    )
    db.commit()
    return run


def list_revision_comparison_runs(
    db: Session, project_id: str
) -> list[models.RevisionComparisonRun]:
    return list(
        db.scalars(
            select(models.RevisionComparisonRun)
            .where(models.RevisionComparisonRun.project_id == project_id)
            .order_by(models.RevisionComparisonRun.started_at.desc())
        ).all()
    )


def list_revision_change_records(
    db: Session, comparison_run_id: str, *, audit: bool = True
) -> list[models.RevisionChangeRecord]:
    records = list(
        db.scalars(
            select(models.RevisionChangeRecord)
            .where(
                models.RevisionChangeRecord.comparison_run_id == comparison_run_id
            )
            .order_by(models.RevisionChangeRecord.id)
        ).all()
    )
    if audit and records:
        run = get_revision_comparison_run_record(db, comparison_run_id)
        if run is not None:
            _audit(
                db,
                project_id=run.project_id,
                event_type="revision_changes_viewed",
                related_entity_type="revision_comparison_run",
                related_entity_id=comparison_run_id,
                description="Revision change records viewed.",
                metadata={"comparison_run_id": comparison_run_id, "count": len(records)},
            )
            db.commit()
    return records


def summarize_revision_changes(db: Session, comparison_run_id: str) -> dict | None:
    run = get_revision_comparison_run_record(db, comparison_run_id)
    if run is None:
        return None
    records = list_revision_change_records(db, comparison_run_id, audit=False)
    by_category: dict[str, int] = {}
    by_type: dict[str, int] = {}
    carried = 0
    for record in records:
        by_category[record.source_category] = (
            by_category.get(record.source_category, 0) + 1
        )
        by_type[record.change_type] = by_type.get(record.change_type, 0) + 1
        if record.change_type == "carried_forward":
            carried += 1
    return {
        "comparison_run_id": comparison_run_id,
        "project_id": run.project_id,
        "review_cycle_id": run.review_cycle_id,
        "status": run.status,
        "added_count": run.added_count,
        "removed_count": run.removed_count,
        "changed_count": run.changed_count,
        "unchanged_count": run.unchanged_count,
        "carried_forward_count": carried,
        "changes_by_category": by_category,
        "changes_by_type": by_type,
        "limitations_note": run.limitations_note,
        "note": (
            "Counts describe extracted DXF metadata differences for review "
            "support. They do not verify CAD or validate the design."
        ),
    }


# ---------------------------------------------------------------------------
# Issue carry-forward
# ---------------------------------------------------------------------------


def _existing_carry_forward_sources(
    db: Session, review_cycle_id: str
) -> set[tuple[str, str]]:
    sources: set[tuple[str, str]] = set()
    for cf in db.scalars(
        select(models.IssueCarryForward).where(
            models.IssueCarryForward.review_cycle_id == review_cycle_id
        )
    ).all():
        if cf.source_workflow_item_id:
            sources.add(("workflow_item", cf.source_workflow_item_id))
        if cf.source_response_item_id:
            sources.add(("response_item", cf.source_response_item_id))
        if cf.source_cad_finding_id:
            sources.add(("cad_finding", cf.source_cad_finding_id))
        if cf.source_revision_change_id:
            sources.add(("revision_change", cf.source_revision_change_id))
    return sources


def _add_carry_forward(
    db: Session,
    *,
    project_id: str,
    review_cycle_id: str,
    title: str,
    reason: str,
    carried_forward_status: str = "carried_forward",
    source_workflow_item_id: str | None = None,
    source_response_item_id: str | None = None,
    source_cad_finding_id: str | None = None,
    source_revision_change_id: str | None = None,
    reviewer_name: str = "reviewer",
    reviewer_note: str | None = None,
) -> models.IssueCarryForward:
    carry = models.IssueCarryForward(
        carry_forward_id=f"cf_{_short()}",
        project_id=project_id,
        review_cycle_id=review_cycle_id,
        source_workflow_item_id=source_workflow_item_id,
        source_response_item_id=source_response_item_id,
        source_cad_finding_id=source_cad_finding_id,
        source_revision_change_id=source_revision_change_id,
        title=title,
        reason=reason,
        carried_forward_status=carried_forward_status,
        reviewer_name=reviewer_name,
        reviewer_note=reviewer_note,
        requires_human_review=True,
    )
    db.add(carry)
    return carry


def carry_forward_unresolved_items(
    db: Session, review_cycle_id: str, *, reviewer_name: str = "reviewer"
) -> dict:
    """Carry unresolved review-support items forward without duplication."""

    cycle = _require_cycle(db, review_cycle_id)
    project_id = cycle.project_id
    existing = _existing_carry_forward_sources(db, review_cycle_id)
    created: list[models.IssueCarryForward] = []
    skipped = 0

    # Workflow items still needing attention.
    for item in workflow_service.list_workflow_items(db, project_id):
        if item.status not in {"needs_follow_up", "needs_more_information"}:
            continue
        if ("workflow_item", item.workflow_item_id) in existing:
            skipped += 1
            continue
        created.append(
            _add_carry_forward(
                db,
                project_id=project_id,
                review_cycle_id=review_cycle_id,
                title=item.title,
                reason=f"Workflow item still in '{item.status}'.",
                carried_forward_status=(
                    "needs_more_information"
                    if item.status == "needs_more_information"
                    else "needs_follow_up"
                ),
                source_workflow_item_id=item.workflow_item_id,
                reviewer_name=reviewer_name,
            )
        )

    # Response package items still in needs_revision or draft.
    for item in _response_package_items(db, project_id):
        if item.status not in {"needs_revision", "draft"}:
            continue
        if ("response_item", item.item_id) in existing:
            skipped += 1
            continue
        created.append(
            _add_carry_forward(
                db,
                project_id=project_id,
                review_cycle_id=review_cycle_id,
                title=item.title,
                reason=f"Response package item still in '{item.status}'.",
                source_response_item_id=item.item_id,
                reviewer_name=reviewer_name,
            )
        )

    # CAD review findings not promoted or still needing review.
    for finding in cad_intake_service.list_cad_review_findings(db, project_id):
        if finding.promoted_to_workflow or not finding.requires_human_review:
            continue
        if finding.status == "excluded_from_packet":
            continue
        if ("cad_finding", finding.cad_review_finding_id) in existing:
            skipped += 1
            continue
        created.append(
            _add_carry_forward(
                db,
                project_id=project_id,
                review_cycle_id=review_cycle_id,
                title=finding.title,
                reason="CAD review finding not yet promoted and needs review.",
                source_cad_finding_id=finding.cad_review_finding_id,
                reviewer_name=reviewer_name,
            )
        )

    # Revision change records marked needs_follow_up or carried_forward.
    change_records = db.scalars(
        select(models.RevisionChangeRecord).where(
            models.RevisionChangeRecord.review_cycle_id == review_cycle_id,
            models.RevisionChangeRecord.reviewer_status.in_(
                ["needs_follow_up", "carried_forward"]
            ),
        )
    ).all()
    for record in change_records:
        if ("revision_change", record.change_record_id) in existing:
            skipped += 1
            continue
        created.append(
            _add_carry_forward(
                db,
                project_id=project_id,
                review_cycle_id=review_cycle_id,
                title=f"Revision change: {record.normalized_key}",
                reason=(
                    f"Revision change record ({record.change_type}, "
                    f"{record.source_category}) still needs review."
                ),
                carried_forward_status="needs_follow_up",
                source_revision_change_id=record.change_record_id,
                reviewer_name=reviewer_name,
            )
        )

    _audit(
        db,
        project_id=project_id,
        event_type="issue_carried_forward",
        related_entity_type="review_cycle",
        related_entity_id=review_cycle_id,
        description=f"{len(created)} item(s) carried forward.",
        metadata={
            "review_cycle_id": review_cycle_id,
            "created": len(created),
            "skipped": skipped,
        },
    )
    db.commit()
    for carry in created:
        db.refresh(carry)
    return {
        "review_cycle_id": review_cycle_id,
        "project_id": project_id,
        "created_count": len(created),
        "skipped_count": skipped,
        "carry_forward_ids": [c.carry_forward_id for c in created],
        "note": (
            "Unresolved review-support items carried forward for the next round. "
            "Nothing here is a final decision."
        ),
    }


def create_issue_carry_forward(
    db: Session,
    review_cycle_id: str,
    *,
    source_workflow_item_id: str | None = None,
    source_response_item_id: str | None = None,
    source_cad_finding_id: str | None = None,
    source_revision_change_id: str | None = None,
    title: str | None = None,
    reason: str,
    reviewer_name: str = "reviewer",
    reviewer_note: str | None = None,
) -> models.IssueCarryForward:
    cycle = _require_cycle(db, review_cycle_id)
    carry = _add_carry_forward(
        db,
        project_id=cycle.project_id,
        review_cycle_id=review_cycle_id,
        title=title or "Carried-forward review-support item",
        reason=reason,
        source_workflow_item_id=source_workflow_item_id,
        source_response_item_id=source_response_item_id,
        source_cad_finding_id=source_cad_finding_id,
        source_revision_change_id=source_revision_change_id,
        reviewer_name=reviewer_name,
        reviewer_note=reviewer_note,
    )
    _audit(
        db,
        project_id=cycle.project_id,
        event_type="issue_carried_forward",
        related_entity_type="issue_carry_forward",
        related_entity_id=carry.carry_forward_id,
        description="Issue carried forward by reviewer.",
        metadata={"carry_forward_id": carry.carry_forward_id},
    )
    db.commit()
    db.refresh(carry)
    return carry


def list_issue_carry_forwards(
    db: Session, project_id: str
) -> list[models.IssueCarryForward]:
    return list(
        db.scalars(
            select(models.IssueCarryForward)
            .where(models.IssueCarryForward.project_id == project_id)
            .order_by(models.IssueCarryForward.created_at)
        ).all()
    )


def get_carry_forward_summary(db: Session, review_cycle_id: str) -> dict:
    cycle = _require_cycle(db, review_cycle_id)
    items = [
        c
        for c in list_issue_carry_forwards(db, cycle.project_id)
        if c.review_cycle_id == review_cycle_id
    ]
    statuses: dict[str, int] = {}
    for item in items:
        statuses[item.carried_forward_status] = (
            statuses.get(item.carried_forward_status, 0) + 1
        )
    _audit(
        db,
        project_id=cycle.project_id,
        event_type="carry_forward_summary_viewed",
        related_entity_type="review_cycle",
        related_entity_id=review_cycle_id,
        description="Carry-forward summary viewed.",
        metadata={"review_cycle_id": review_cycle_id},
    )
    db.commit()
    return {
        "review_cycle_id": review_cycle_id,
        "project_id": cycle.project_id,
        "total": len(items),
        "statuses": statuses,
        "note": "Carried-forward items remain under human review.",
    }


# ---------------------------------------------------------------------------
# Response resolution
# ---------------------------------------------------------------------------


def create_response_resolution_record(
    db: Session,
    review_cycle_id: str,
    *,
    response_package_item_id: str | None = None,
    workflow_item_id: str | None = None,
    applicant_response_id: str | None = None,
    revision_change_record_id: str | None = None,
    status: str = "still_open",
    reviewer_note: str | None = None,
    reviewer_name: str = "reviewer",
) -> models.ResponseResolutionRecord:
    cycle = _require_cycle(db, review_cycle_id)
    if status not in ALLOWED_RESOLUTION_STATUSES:
        raise ReviewCycleError(
            f"Invalid resolution status '{status}'.", status_code=422
        )
    record = models.ResponseResolutionRecord(
        resolution_record_id=f"res_{_short()}",
        project_id=cycle.project_id,
        review_cycle_id=review_cycle_id,
        response_package_item_id=response_package_item_id,
        workflow_item_id=workflow_item_id,
        applicant_response_id=applicant_response_id,
        revision_change_record_id=revision_change_record_id,
        status=status,
        reviewer_note=reviewer_note,
        reviewer_name=reviewer_name,
        requires_human_review=True,
    )
    db.add(record)
    _audit(
        db,
        project_id=cycle.project_id,
        event_type="response_resolution_created",
        related_entity_type="response_resolution_record",
        related_entity_id=record.resolution_record_id,
        description=f"Response resolution record created with status {status}.",
        metadata={
            "resolution_record_id": record.resolution_record_id,
            "status": status,
        },
    )
    db.commit()
    db.refresh(record)
    return record


def update_response_resolution_status(
    db: Session,
    resolution_record_id: str,
    *,
    status: str,
    reviewer_note: str | None = None,
    reviewer_name: str = "reviewer",
) -> models.ResponseResolutionRecord:
    record = db.scalars(
        select(models.ResponseResolutionRecord).where(
            models.ResponseResolutionRecord.resolution_record_id
            == resolution_record_id
        )
    ).first()
    if record is None:
        raise ReviewCycleError("Resolution record not found.", status_code=404)
    if status not in ALLOWED_RESOLUTION_STATUSES:
        raise ReviewCycleError(
            f"Invalid resolution status '{status}'.", status_code=422
        )
    previous = record.status
    record.status = status
    if reviewer_note is not None:
        record.reviewer_note = reviewer_note
    record.reviewer_name = reviewer_name
    record.updated_at = _now()
    _audit(
        db,
        project_id=record.project_id,
        event_type="response_resolution_status_changed",
        related_entity_type="response_resolution_record",
        related_entity_id=resolution_record_id,
        description=f"Resolution status changed from {previous} to {status}.",
        metadata={"previous_status": previous, "new_status": status},
    )
    db.commit()
    db.refresh(record)
    return record


def list_response_resolution_records(
    db: Session, project_id: str
) -> list[models.ResponseResolutionRecord]:
    return list(
        db.scalars(
            select(models.ResponseResolutionRecord)
            .where(models.ResponseResolutionRecord.project_id == project_id)
            .order_by(models.ResponseResolutionRecord.created_at)
        ).all()
    )


def get_resolution_summary(db: Session, review_cycle_id: str) -> dict:
    cycle = _require_cycle(db, review_cycle_id)
    records = [
        r
        for r in list_response_resolution_records(db, cycle.project_id)
        if r.review_cycle_id == review_cycle_id
    ]
    statuses: dict[str, int] = {}
    for record in records:
        statuses[record.status] = statuses.get(record.status, 0) + 1
    _audit(
        db,
        project_id=cycle.project_id,
        event_type="resolution_summary_viewed",
        related_entity_type="review_cycle",
        related_entity_id=review_cycle_id,
        description="Resolution summary viewed.",
        metadata={"review_cycle_id": review_cycle_id},
    )
    db.commit()
    return {
        "review_cycle_id": review_cycle_id,
        "project_id": cycle.project_id,
        "total": len(records),
        "statuses": statuses,
        "note": (
            "Resolution statuses are review-support states. addressed_for_review "
            "means an item appears addressed for human review, never resolved, "
            "approved, or certified."
        ),
    }


# ---------------------------------------------------------------------------
# Next-cycle preparation
# ---------------------------------------------------------------------------


def prepare_next_cycle(
    db: Session, review_cycle_id: str
) -> models.NextCyclePreparation:
    cycle = _require_cycle(db, review_cycle_id)
    project_id = cycle.project_id

    carry_forwards = [
        c
        for c in list_issue_carry_forwards(db, project_id)
        if c.review_cycle_id == review_cycle_id
    ]
    resolutions = [
        r
        for r in list_response_resolution_records(db, project_id)
        if r.review_cycle_id == review_cycle_id
    ]
    responses_needing_clarification = [
        r
        for r in list_applicant_responses(db, project_id)
        if r.review_cycle_id == review_cycle_id and r.status == "needs_clarification"
    ]
    changes_needing_review = db.scalars(
        select(models.RevisionChangeRecord).where(
            models.RevisionChangeRecord.review_cycle_id == review_cycle_id,
            models.RevisionChangeRecord.reviewer_status.in_(
                ["needs_follow_up", "needs_more_information", "carried_forward"]
            ),
        )
    ).all()

    needs_more_information_count = len(
        [r for r in resolutions if r.status == "needs_more_information"]
    ) + len(responses_needing_clarification)
    reviewer_checked_count = len(
        [r for r in resolutions if r.status == "reviewer_checked"]
    )
    open_resolution_count = len(
        [r for r in resolutions if r.status in {"still_open", "carried_forward"}]
    )
    carried_forward_count = len(carry_forwards)

    next_ready = (
        carried_forward_count + needs_more_information_count + open_resolution_count
        > 0
    )

    summary = (
        f"Next-cycle preparation: {carried_forward_count} carried-forward item(s), "
        f"{needs_more_information_count} needing more information, "
        f"{len(changes_needing_review)} revision change(s) needing review, "
        f"{reviewer_checked_count} reviewer checked. This summary organizes "
        "review-support work for the next round and is not a final decision."
    )

    existing = db.scalars(
        select(models.NextCyclePreparation).where(
            models.NextCyclePreparation.review_cycle_id == review_cycle_id
        )
    ).first()
    if existing is None:
        prep = models.NextCyclePreparation(
            next_cycle_preparation_id=f"next_{_short()}",
            project_id=project_id,
            review_cycle_id=review_cycle_id,
            status="ready_for_next_cycle" if next_ready else "draft",
            summary=summary,
            carried_forward_count=carried_forward_count,
            needs_more_information_count=needs_more_information_count,
            reviewer_checked_count=reviewer_checked_count,
            next_response_package_ready=next_ready,
            requires_human_review=True,
        )
        db.add(prep)
    else:
        prep = existing
        prep.status = "ready_for_next_cycle" if next_ready else "draft"
        prep.summary = summary
        prep.carried_forward_count = carried_forward_count
        prep.needs_more_information_count = needs_more_information_count
        prep.reviewer_checked_count = reviewer_checked_count
        prep.next_response_package_ready = next_ready
        prep.updated_at = _now()

    if next_ready and cycle.status == "active":
        cycle.status = "ready_for_next_cycle"
        cycle.updated_at = _now()

    _audit(
        db,
        project_id=project_id,
        event_type="next_cycle_prepared",
        related_entity_type="review_cycle",
        related_entity_id=review_cycle_id,
        description="Next cycle preparation generated.",
        metadata={
            "review_cycle_id": review_cycle_id,
            "carried_forward_count": carried_forward_count,
            "needs_more_information_count": needs_more_information_count,
        },
    )
    db.commit()
    db.refresh(prep)
    return prep


def get_next_cycle_preparation(
    db: Session, review_cycle_id: str
) -> models.NextCyclePreparation | None:
    cycle = _require_cycle(db, review_cycle_id)
    prep = db.scalars(
        select(models.NextCyclePreparation).where(
            models.NextCyclePreparation.review_cycle_id == review_cycle_id
        )
    ).first()
    if prep is None:
        return None
    _audit(
        db,
        project_id=cycle.project_id,
        event_type="next_cycle_preparation_viewed",
        related_entity_type="review_cycle",
        related_entity_id=review_cycle_id,
        description="Next cycle preparation viewed.",
        metadata={"review_cycle_id": review_cycle_id},
    )
    db.commit()
    return prep


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


def get_review_cycle_dashboard(db: Session, project_id: str) -> dict:
    _require_project(db, project_id)
    cycles = list_review_cycles(db, project_id)
    active = _active_cycle(db, project_id)
    resubmittals = list_resubmittal_packages(db, project_id)
    resubmittal_statuses: dict[str, int] = {}
    for package in resubmittals:
        resubmittal_statuses[package.status] = (
            resubmittal_statuses.get(package.status, 0) + 1
        )
    responses = list_applicant_responses(db, project_id)
    mapped_ids = {
        m.applicant_response_id
        for m in db.scalars(
            select(models.ApplicantResponseMapping).where(
                models.ApplicantResponseMapping.project_id == project_id
            )
        ).all()
    }
    comparison_runs = list_revision_comparison_runs(db, project_id)
    change_count = (
        db.query(models.RevisionChangeRecord)
        .filter(models.RevisionChangeRecord.project_id == project_id)
        .count()
    )
    carry_forwards = list_issue_carry_forwards(db, project_id)
    resolutions = list_response_resolution_records(db, project_id)
    resolution_statuses: dict[str, int] = {}
    for record in resolutions:
        resolution_statuses[record.status] = (
            resolution_statuses.get(record.status, 0) + 1
        )
    open_item_count = len(
        [r for r in resolutions if r.status in {"still_open", "needs_more_information", "carried_forward"}]
    )
    next_prep = None
    if active is not None:
        next_prep = db.scalars(
            select(models.NextCyclePreparation).where(
                models.NextCyclePreparation.review_cycle_id
                == active.review_cycle_id
            )
        ).first()

    _audit(
        db,
        project_id=project_id,
        event_type="review_cycle_dashboard_viewed",
        related_entity_type="project",
        related_entity_id=project_id,
        description="Review cycle dashboard viewed.",
        metadata={"cycle_count": len(cycles)},
    )
    db.commit()
    return {
        "project_id": project_id,
        "cycle_count": len(cycles),
        "active_cycle_id": active.review_cycle_id if active else None,
        "active_cycle_number": active.cycle_number if active else None,
        "review_cycles": cycles,
        "resubmittal_count": len(resubmittals),
        "resubmittal_statuses": resubmittal_statuses,
        "applicant_response_count": len(responses),
        "unmapped_response_count": len(
            [r for r in responses if r.applicant_response_id not in mapped_ids]
        ),
        "comparison_run_count": len(comparison_runs),
        "revision_change_count": change_count,
        "carry_forward_count": len(carry_forwards),
        "resolution_count": len(resolutions),
        "resolution_statuses": resolution_statuses,
        "open_item_count": open_item_count,
        "next_cycle_ready": bool(next_prep and next_prep.next_response_package_ready),
        "limitations_note": LIMITATIONS_NOTE,
    }
