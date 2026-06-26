"""Applicant response matrix and resubmittal API routes (Sprint 7).

Reviewer-controlled response tracking across resubmittal rounds. Read access can
view matrices, items, and rounds; reviewer access can create and update them,
record applicant responses, link documents, and carry items forward. Access
control from Sprint 5 and storage security from Sprint 6 are preserved.

An applicant response is recorded for reviewer review, never as proof and never
as a final outcome. Carry-forward means continued review, not resolution. Nothing
here approves plans, certifies compliance, verifies CAD, validates design,
resolves or closes an issue, or makes any final engineering decision. Responses
never include storage keys, raw paths, secrets, or full extracted page text.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.response_matrix import (
    ApplicantResponseRecord,
    CarryForwardItemsToRoundRequest,
    CarryForwardMatrixItemRequest,
    MatrixItemDocumentLinkCreate,
    MatrixItemDocumentLinkResponse,
    ResponseMatrixCreate,
    ResponseMatrixDetailResponse,
    ResponseMatrixItemCreateFromChecklist,
    ResponseMatrixItemCreateFromFinding,
    ResponseMatrixItemResponse,
    ResponseMatrixItemUpdate,
    ResponseMatrixResponse,
    ResubmittalDocumentLinkRequest,
    ResubmittalRoundCreate,
    ResubmittalRoundResponse,
    ResubmittalRoundSummaryResponse,
)
from app.services import response_matrix_service as matrix
from app.services import resubmittal_service as resub
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
    require_project_reviewer,
)
from app.services.resubmittal_service import ResubmittalError
from app.services.response_matrix_service import ResponseMatrixError

router = APIRouter(tags=["response-matrix"])


def _handle(exc: Exception) -> HTTPException:
    status_code = getattr(exc, "status_code", 422)
    message = getattr(exc, "message", str(exc))
    return HTTPException(status_code=status_code, detail=message)


# ---------------------------------------------------------------------------
# Response matrices
# ---------------------------------------------------------------------------


@router.get(
    "/projects/{project_id}/response-matrices",
    response_model=list[ResponseMatrixResponse],
)
def list_matrices(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ResponseMatrixResponse]:
    require_project_read(db, project_id, user)
    try:
        return matrix.list_response_matrices(db, project_id)
    except (ResponseMatrixError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/response-matrices",
    response_model=ResponseMatrixResponse,
    status_code=201,
)
def create_matrix(
    project_id: str,
    body: ResponseMatrixCreate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponseMatrixResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return matrix.create_response_matrix(
            db, project_id, body.model_dump(exclude_none=True), actor=actor
        )
    except (ResponseMatrixError, ValueError) as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/response-matrices/{response_matrix_id}",
    response_model=ResponseMatrixDetailResponse,
)
def get_matrix(
    project_id: str,
    response_matrix_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponseMatrixDetailResponse:
    require_project_read(db, project_id, user)
    try:
        return ResponseMatrixDetailResponse.model_validate(
            matrix.get_response_matrix(db, project_id, response_matrix_id)
        )
    except (ResponseMatrixError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/response-matrices/{response_matrix_id}/items/from-finding/{finding_id}",
    response_model=ResponseMatrixItemResponse,
    status_code=201,
)
def add_finding_item(
    project_id: str,
    response_matrix_id: str,
    finding_id: str,
    body: ResponseMatrixItemCreateFromFinding,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponseMatrixItemResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return ResponseMatrixItemResponse.model_validate(
            matrix.add_finding_to_matrix(
                db,
                project_id,
                response_matrix_id,
                finding_id,
                body.model_dump(exclude_none=True),
                actor=actor,
            )
        )
    except (ResponseMatrixError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/response-matrices/{response_matrix_id}/items/from-checklist-item/{checklist_item_id}",
    response_model=ResponseMatrixItemResponse,
    status_code=201,
)
def add_checklist_item(
    project_id: str,
    response_matrix_id: str,
    checklist_item_id: str,
    body: ResponseMatrixItemCreateFromChecklist,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponseMatrixItemResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return ResponseMatrixItemResponse.model_validate(
            matrix.add_checklist_item_to_matrix(
                db,
                project_id,
                response_matrix_id,
                checklist_item_id,
                body.model_dump(exclude_none=True),
                actor=actor,
            )
        )
    except (ResponseMatrixError, ValueError) as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/response-matrices/{response_matrix_id}/items",
    response_model=list[ResponseMatrixItemResponse],
)
def list_items(
    project_id: str,
    response_matrix_id: str,
    applicant_response_status: str | None = Query(default=None),
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ResponseMatrixItemResponse]:
    require_project_read(db, project_id, user)
    try:
        return matrix.list_matrix_items(
            db,
            project_id,
            response_matrix_id,
            applicant_response_status=applicant_response_status,
        )
    except (ResponseMatrixError, ValueError) as exc:
        raise _handle(exc) from exc


# ---------------------------------------------------------------------------
# Matrix items
# ---------------------------------------------------------------------------


@router.get(
    "/projects/{project_id}/response-matrix-items/{matrix_item_id}",
    response_model=ResponseMatrixItemResponse,
)
def get_item(
    project_id: str,
    matrix_item_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponseMatrixItemResponse:
    require_project_read(db, project_id, user)
    try:
        return matrix.get_matrix_item(db, project_id, matrix_item_id)
    except (ResponseMatrixError, ValueError) as exc:
        raise _handle(exc) from exc


@router.patch(
    "/projects/{project_id}/response-matrix-items/{matrix_item_id}",
    response_model=ResponseMatrixItemResponse,
)
def update_item(
    project_id: str,
    matrix_item_id: str,
    body: ResponseMatrixItemUpdate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponseMatrixItemResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return matrix.update_matrix_item(
            db,
            project_id,
            matrix_item_id,
            body.model_dump(exclude_none=True),
            actor=actor,
        )
    except (ResponseMatrixError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/response-matrix-items/{matrix_item_id}/applicant-response",
    response_model=ResponseMatrixItemResponse,
    status_code=201,
)
def record_response(
    project_id: str,
    matrix_item_id: str,
    body: ApplicantResponseRecord,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponseMatrixItemResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return matrix.record_applicant_response(
            db,
            project_id,
            matrix_item_id,
            body.model_dump(exclude_none=True),
            actor=actor,
        )
    except (ResponseMatrixError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/response-matrix-items/{matrix_item_id}/documents/{document_id}",
    response_model=MatrixItemDocumentLinkResponse,
    status_code=201,
)
def link_document(
    project_id: str,
    matrix_item_id: str,
    document_id: str,
    body: MatrixItemDocumentLinkCreate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> MatrixItemDocumentLinkResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return matrix.link_response_document(
            db,
            project_id,
            matrix_item_id,
            document_id,
            body.model_dump(exclude_none=True),
            actor=actor,
        )
    except (ResponseMatrixError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/response-matrix-items/{matrix_item_id}/carry-forward",
    response_model=ResponseMatrixItemResponse,
    status_code=201,
)
def carry_forward_item(
    project_id: str,
    matrix_item_id: str,
    body: CarryForwardMatrixItemRequest,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponseMatrixItemResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return matrix.carry_forward_matrix_item(
            db,
            project_id,
            matrix_item_id,
            body.model_dump(exclude_none=True),
            actor=actor,
        )
    except (ResponseMatrixError, ValueError) as exc:
        raise _handle(exc) from exc


# ---------------------------------------------------------------------------
# Resubmittal rounds
# ---------------------------------------------------------------------------


@router.get(
    "/projects/{project_id}/resubmittal-rounds",
    response_model=list[ResubmittalRoundResponse],
)
def list_rounds(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ResubmittalRoundResponse]:
    require_project_read(db, project_id, user)
    try:
        return resub.list_resubmittal_rounds(db, project_id)
    except (ResubmittalError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/resubmittal-rounds",
    response_model=ResubmittalRoundResponse,
    status_code=201,
)
def register_round(
    project_id: str,
    body: ResubmittalRoundCreate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResubmittalRoundResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return resub.register_resubmittal_round(
            db, project_id, body.model_dump(exclude_none=True), actor=actor
        )
    except (ResubmittalError, ValueError) as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/resubmittal-rounds/{round_id}",
    response_model=ResubmittalRoundResponse,
)
def get_round(
    project_id: str,
    round_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResubmittalRoundResponse:
    require_project_read(db, project_id, user)
    try:
        return resub.get_resubmittal_round(db, project_id, round_id)
    except (ResubmittalError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/resubmittal-rounds/{round_id}/documents/{document_id}",
    response_model=ResubmittalRoundResponse,
    status_code=201,
)
def link_round_document(
    project_id: str,
    round_id: str,
    document_id: str,
    body: ResubmittalDocumentLinkRequest,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResubmittalRoundResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return resub.link_document_to_resubmittal_round(
            db,
            project_id,
            round_id,
            document_id,
            body.model_dump(exclude_none=True),
            actor=actor,
        )
    except (ResubmittalError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/resubmittal-rounds/{round_id}/carry-forward-items",
    response_model=ResubmittalRoundResponse,
    status_code=201,
)
def carry_forward_items(
    project_id: str,
    round_id: str,
    body: CarryForwardItemsToRoundRequest,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResubmittalRoundResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return resub.carry_forward_items_to_round(
            db,
            project_id,
            round_id,
            body.model_dump(exclude_none=True),
            actor=actor,
        )
    except (ResubmittalError, ValueError) as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/resubmittal-rounds/{round_id}/summary",
    response_model=ResubmittalRoundSummaryResponse,
)
def round_summary(
    project_id: str,
    round_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResubmittalRoundSummaryResponse:
    require_project_read(db, project_id, user)
    try:
        return resub.summarize_resubmittal_round(db, project_id, round_id)
    except (ResubmittalError, ValueError) as exc:
        raise _handle(exc) from exc
