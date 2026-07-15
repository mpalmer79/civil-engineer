"""Resubmittal packages: intake, status, and document linking.

A reviewer can record a resubmittal package, link uploaded DXF CAD files, and
attach applicant response notes. Resubmittal intake organizes review-support
evidence for a human reviewer. It does not approve plans or certify compliance.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import ALLOWED_RESUBMITTAL_STATUSES
from app.db import models
from app.services import cad_intake_service
from app.services.review_cycle_service._common import (
    _audit,
    _now,
    _require_project,
    _short,
)
from app.services.review_cycle_service.errors import ReviewCycleError
from app.services.review_cycle_service.lifecycle import (
    _active_cycle,
    _require_cycle,
    create_review_cycle,
)


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
