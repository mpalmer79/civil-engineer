"""Read-side projections and listings for reviewer response packages."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models

from ._common import _require_package, _require_project


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


def list_package_items(
    db: Session, project_id: str, response_package_id: str
) -> list[models.ReviewerResponsePackageItem]:
    _require_package(db, project_id, response_package_id)
    return _package_items(db, response_package_id)
