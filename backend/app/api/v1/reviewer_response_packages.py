"""Reviewer response package and comment letter API routes (Sprint 8).

Reviewer-controlled communication output. Read access can view packages, items,
previews, and comment letter drafts; reviewer access can create and update
packages, add items, generate and edit comment letter drafts, mark ready for
handoff, issue packages, and create revisions. Access control from Sprint 5 and
storage security from Sprint 6 are preserved.

Issuing a package records a reviewer communication only. Nothing here approves a
project, certifies compliance, verifies CAD, validates design, resolves an issue,
or closes an issue. Responses never include storage keys, raw paths, signed URLs,
secrets, or full extracted page text.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.reviewer_response_package import (
    AddChecklistItemsToPackageRequest,
    AddCitationsToPackageRequest,
    AddFindingsToPackageRequest,
    AddMatrixItemsToPackageRequest,
    CommentLetterDraftCreate,
    CommentLetterDraftResponse,
    CommentLetterDraftUpdate,
    CommentLetterPreviewResponse,
    CreatePackageRevisionRequest,
    IssueResponsePackageRequest,
    ManualPackageItemCreate,
    ResponsePackageCreate,
    ResponsePackageDetailResponse,
    ResponsePackageItemResponse,
    ResponsePackageItemUpdate,
    ResponsePackagePreviewResponse,
    ResponsePackageResponse,
)
from app.services import comment_letter_service as letters
from app.services import reviewer_response_package_service as packages
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
    require_project_reviewer,
)
from app.services.comment_letter_service import CommentLetterError
from app.services.reviewer_response_package_service import (
    ReviewerResponsePackageError,
)

router = APIRouter(tags=["reviewer-response-packages"])


def _handle(exc: Exception) -> HTTPException:
    status_code = getattr(exc, "status_code", 422)
    message = getattr(exc, "message", str(exc))
    return HTTPException(status_code=status_code, detail=message)


# ---------------------------------------------------------------------------
# Response packages
# ---------------------------------------------------------------------------


@router.get(
    "/projects/{project_id}/reviewer-response-packages",
    response_model=list[ResponsePackageResponse],
)
def list_packages(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ResponsePackageResponse]:
    require_project_read(db, project_id, user)
    try:
        return packages.list_response_packages(db, project_id)
    except (ReviewerResponsePackageError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/reviewer-response-packages",
    response_model=ResponsePackageDetailResponse,
    status_code=201,
)
def create_package(
    project_id: str,
    body: ResponsePackageCreate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageDetailResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return packages.create_response_package(
            db, project_id, body.model_dump(exclude_none=True), actor=actor
        )
    except (ReviewerResponsePackageError, ValueError) as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/reviewer-response-packages/{response_package_id}",
    response_model=ResponsePackageDetailResponse,
)
def get_package(
    project_id: str,
    response_package_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageDetailResponse:
    require_project_read(db, project_id, user)
    try:
        return packages.get_response_package(
            db, project_id, response_package_id
        )
    except (ReviewerResponsePackageError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/reviewer-response-packages/{response_package_id}/items/matrix-items",
    response_model=ResponsePackageDetailResponse,
)
def add_matrix_items(
    project_id: str,
    response_package_id: str,
    body: AddMatrixItemsToPackageRequest,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageDetailResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return packages.add_matrix_items_to_package(
            db, project_id, response_package_id, body.model_dump(), actor=actor
        )
    except (ReviewerResponsePackageError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/reviewer-response-packages/{response_package_id}/items/findings",
    response_model=ResponsePackageDetailResponse,
)
def add_findings(
    project_id: str,
    response_package_id: str,
    body: AddFindingsToPackageRequest,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageDetailResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return packages.add_findings_to_package(
            db, project_id, response_package_id, body.model_dump(), actor=actor
        )
    except (ReviewerResponsePackageError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/reviewer-response-packages/{response_package_id}/items/checklist-items",
    response_model=ResponsePackageDetailResponse,
)
def add_checklist_items(
    project_id: str,
    response_package_id: str,
    body: AddChecklistItemsToPackageRequest,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageDetailResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return packages.add_checklist_items_to_package(
            db, project_id, response_package_id, body.model_dump(), actor=actor
        )
    except (ReviewerResponsePackageError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/reviewer-response-packages/{response_package_id}/items/citations",
    response_model=ResponsePackageDetailResponse,
)
def add_citations(
    project_id: str,
    response_package_id: str,
    body: AddCitationsToPackageRequest,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageDetailResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return packages.add_citations_to_package(
            db, project_id, response_package_id, body.model_dump(), actor=actor
        )
    except (ReviewerResponsePackageError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/reviewer-response-packages/{response_package_id}/items/manual",
    response_model=ResponsePackageDetailResponse,
)
def add_manual_item(
    project_id: str,
    response_package_id: str,
    body: ManualPackageItemCreate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageDetailResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return packages.add_manual_package_item(
            db, project_id, response_package_id, body.model_dump(), actor=actor
        )
    except (ReviewerResponsePackageError, ValueError) as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/reviewer-response-packages/{response_package_id}/preview",
    response_model=ResponsePackagePreviewResponse,
)
def preview_package(
    project_id: str,
    response_package_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackagePreviewResponse:
    require_project_read(db, project_id, user)
    try:
        return packages.preview_response_package(
            db, project_id, response_package_id
        )
    except (ReviewerResponsePackageError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/reviewer-response-packages/{response_package_id}/ready-for-handoff",
    response_model=ResponsePackageDetailResponse,
)
def ready_for_handoff(
    project_id: str,
    response_package_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageDetailResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return packages.mark_package_ready_for_handoff(
            db, project_id, response_package_id, actor=actor
        )
    except (ReviewerResponsePackageError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/reviewer-response-packages/{response_package_id}/issue",
    response_model=ResponsePackageDetailResponse,
)
def issue_package(
    project_id: str,
    response_package_id: str,
    body: IssueResponsePackageRequest,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageDetailResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return packages.issue_response_package(
            db, project_id, response_package_id, body.model_dump(), actor=actor
        )
    except (ReviewerResponsePackageError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/reviewer-response-packages/{response_package_id}/revisions",
    response_model=ResponsePackageDetailResponse,
    status_code=201,
)
def create_revision(
    project_id: str,
    response_package_id: str,
    body: CreatePackageRevisionRequest,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageDetailResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return packages.create_package_revision(
            db, project_id, response_package_id, body.model_dump(), actor=actor
        )
    except (ReviewerResponsePackageError, ValueError) as exc:
        raise _handle(exc) from exc


# ---------------------------------------------------------------------------
# Package items
# ---------------------------------------------------------------------------


@router.patch(
    "/projects/{project_id}/reviewer-response-package-items/{package_item_id}",
    response_model=ResponsePackageItemResponse,
)
def update_item(
    project_id: str,
    package_item_id: str,
    body: ResponsePackageItemUpdate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageItemResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        item = packages.update_package_item(
            db,
            project_id,
            package_item_id,
            body.model_dump(exclude_none=True),
            actor=actor,
        )
        return ResponsePackageItemResponse.model_validate(
            packages._item_dict(item)
        )
    except (ReviewerResponsePackageError, ValueError) as exc:
        raise _handle(exc) from exc


# ---------------------------------------------------------------------------
# Comment letter drafts
# ---------------------------------------------------------------------------


@router.post(
    "/projects/{project_id}/reviewer-response-packages/{response_package_id}/comment-letter-draft",
    response_model=CommentLetterDraftResponse,
    status_code=201,
)
def generate_comment_letter(
    project_id: str,
    response_package_id: str,
    body: CommentLetterDraftCreate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CommentLetterDraftResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return letters.generate_comment_letter_draft(
            db,
            project_id,
            response_package_id,
            body.model_dump(exclude_none=True),
            actor=actor,
        )
    except (CommentLetterError, ReviewerResponsePackageError, ValueError) as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/comment-letter-drafts/{draft_id}",
    response_model=CommentLetterDraftResponse,
)
def get_comment_letter(
    project_id: str,
    draft_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CommentLetterDraftResponse:
    require_project_read(db, project_id, user)
    try:
        return letters.get_comment_letter_draft(db, project_id, draft_id)
    except (CommentLetterError, ValueError) as exc:
        raise _handle(exc) from exc


@router.patch(
    "/projects/{project_id}/comment-letter-drafts/{draft_id}",
    response_model=CommentLetterDraftResponse,
)
def update_comment_letter(
    project_id: str,
    draft_id: str,
    body: CommentLetterDraftUpdate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CommentLetterDraftResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return letters.update_comment_letter_draft(
            db,
            project_id,
            draft_id,
            body.model_dump(exclude_none=True),
            actor=actor,
        )
    except (CommentLetterError, ValueError) as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/comment-letter-drafts/{draft_id}/preview",
    response_model=CommentLetterPreviewResponse,
)
def preview_comment_letter(
    project_id: str,
    draft_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CommentLetterPreviewResponse:
    require_project_read(db, project_id, user)
    try:
        return letters.preview_comment_letter(db, project_id, draft_id)
    except (CommentLetterError, ValueError) as exc:
        raise _handle(exc) from exc
