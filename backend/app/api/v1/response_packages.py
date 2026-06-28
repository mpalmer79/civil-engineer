"""Phase 10 external review response package API routes.

These endpoints generate and read draft external response packages and record
reviewer actions on packages and response items. A response package supports
drafting external communication for a human reviewer. No endpoint sends email,
approves a plan, certifies compliance, stamps a drawing, verifies CAD, or
validates a design, and there is no action called approve.

Read side effects: GET /response-packages/{id}, /print-view, /attachments, and
/history each write an audit event recording the access. This is intentional so
the decision history shows reviewer access.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.response_package import (
    ResponseItemDraftTextUpdate,
    ResponseItemStatusUpdate,
    ResponsePackageActionRead,
    ResponsePackageAttachmentRead,
    ResponsePackageDetail,
    ResponsePackageHistory,
    ResponsePackageItemRead,
    ResponsePackageNoteCreate,
    ResponsePackagePrintView,
    ResponsePackageRead,
    ResponsePackageStatusUpdate,
    ResponsePackageSummary,
)
from app.services import project_service, response_package_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
    require_project_reviewer,
)
from app.services.response_package_service import ResponsePackageError


def _require_package_project(
    db: Session, response_package_id: str
) -> models.ResponsePackage:
    """Resolve a response package to its owning project, 404 if missing."""

    package = response_package_service.get_package(db, response_package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Response package not found")
    return package


router = APIRouter(tags=["response-packages"])


@router.post(
    "/projects/{project_id}/response-packages/generate",
    response_model=ResponsePackageDetail,
)
def generate_response_package(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageDetail:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_reviewer(db, project_id, user)
    try:
        package = response_package_service.generate_response_package(
            db, project_id
        )
    except ResponsePackageError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    detail = response_package_service.assemble_package_detail(db, package)
    return ResponsePackageDetail.model_validate(detail)


@router.get(
    "/projects/{project_id}/response-packages",
    response_model=list[ResponsePackageRead],
)
def list_response_packages(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ResponsePackageRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return response_package_service.list_response_packages(db, project_id)


@router.get(
    "/response-packages/{response_package_id}",
    response_model=ResponsePackageDetail,
)
def get_response_package(
    response_package_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageDetail:
    package = _require_package_project(db, response_package_id)
    require_project_read(db, package.project_id, user)
    detail = response_package_service.get_response_package(
        db, response_package_id
    )
    if detail is None:
        raise HTTPException(status_code=404, detail="Response package not found")
    return ResponsePackageDetail.model_validate(detail)


@router.get(
    "/response-packages/{response_package_id}/print-view",
    response_model=ResponsePackagePrintView,
)
def get_response_package_print_view(
    response_package_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackagePrintView:
    package = _require_package_project(db, response_package_id)
    require_project_read(db, package.project_id, user)
    result = response_package_service.get_response_package_print_view(
        db, response_package_id
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Response package not found")
    return ResponsePackagePrintView.model_validate(result)


@router.get(
    "/response-packages/{response_package_id}/attachments",
    response_model=list[ResponsePackageAttachmentRead],
)
def get_response_package_attachments(
    response_package_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ResponsePackageAttachmentRead]:
    package = _require_package_project(db, response_package_id)
    require_project_read(db, package.project_id, user)
    result = response_package_service.get_response_package_attachments(
        db, response_package_id
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Response package not found")
    return result["attachments"]


@router.get(
    "/response-packages/{response_package_id}/history",
    response_model=ResponsePackageHistory,
)
def get_response_package_history(
    response_package_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageHistory:
    package = _require_package_project(db, response_package_id)
    require_project_read(db, package.project_id, user)
    result = response_package_service.get_response_package_history(
        db, response_package_id
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Response package not found")
    return ResponsePackageHistory.model_validate(result)


@router.get(
    "/response-packages/{response_package_id}/summary",
    response_model=ResponsePackageSummary,
)
def get_response_package_summary(
    response_package_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageSummary:
    package = _require_package_project(db, response_package_id)
    require_project_read(db, package.project_id, user)
    result = response_package_service.summarize_response_package(
        db, response_package_id
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Response package not found")
    return ResponsePackageSummary.model_validate(result)


@router.patch(
    "/response-packages/{response_package_id}/status",
    response_model=ResponsePackageRead,
)
def update_response_package_status(
    response_package_id: str,
    body: ResponsePackageStatusUpdate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageRead:
    package = _require_package_project(db, response_package_id)
    require_project_reviewer(db, package.project_id, user)
    try:
        package = response_package_service.update_response_package_status(
            db,
            response_package_id=response_package_id,
            new_status=body.new_status,
            reviewer_note=body.reviewer_note,
            reviewer_name=body.reviewer_name,
        )
    except ResponsePackageError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return package


@router.patch(
    "/response-packages/{response_package_id}/items/{response_item_id}/status",
    response_model=ResponsePackageItemRead,
)
def update_response_item_status(
    response_package_id: str,
    response_item_id: str,
    body: ResponseItemStatusUpdate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageItemRead:
    package = _require_package_project(db, response_package_id)
    require_project_reviewer(db, package.project_id, user)
    try:
        item = response_package_service.update_response_item_status(
            db,
            response_package_id=response_package_id,
            response_item_id=response_item_id,
            new_status=body.new_status,
            reviewer_note=body.reviewer_note,
            reviewer_name=body.reviewer_name,
        )
    except ResponsePackageError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return item


@router.patch(
    "/response-packages/{response_package_id}/items/{response_item_id}/draft-text",
    response_model=ResponsePackageItemRead,
)
def update_response_item_draft_text(
    response_package_id: str,
    response_item_id: str,
    body: ResponseItemDraftTextUpdate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageItemRead:
    package = _require_package_project(db, response_package_id)
    require_project_reviewer(db, package.project_id, user)
    try:
        item = response_package_service.update_response_item_draft_text(
            db,
            response_package_id=response_package_id,
            response_item_id=response_item_id,
            draft_text=body.draft_text,
            reviewer_note=body.reviewer_note,
            reviewer_name=body.reviewer_name,
        )
    except ResponsePackageError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return item


@router.post(
    "/response-packages/{response_package_id}/items/{response_item_id}/notes",
    response_model=ResponsePackageActionRead,
)
def add_response_item_note(
    response_package_id: str,
    response_item_id: str,
    body: ResponsePackageNoteCreate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponsePackageActionRead:
    package = _require_package_project(db, response_package_id)
    require_project_reviewer(db, package.project_id, user)
    try:
        action = response_package_service.add_response_package_note(
            db,
            response_package_id=response_package_id,
            reviewer_note=body.reviewer_note,
            reviewer_name=body.reviewer_name,
            response_item_id=response_item_id,
        )
    except ResponsePackageError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return action
