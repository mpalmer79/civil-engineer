"""Checklist-driven review and rule pack API routes (Sprint 4).

These endpoints expose reusable review-support rule packs, apply a rule pack to a
real project as a checklist, search indexed evidence for a checklist requirement,
link evidence, update reviewer-controlled checklist status, and create draft
findings from checklist items.

A rule pack is a review-support template, not a legal ordinance and not a
compliance standard. Checklist status is review-support only. Nothing here
approves plans, certifies compliance, verifies CAD, validates design, declares a
project safe, resolves or closes an issue, or makes a final engineering
decision. Draft findings require reviewer confirmation. Responses never include
full extracted page text or raw server file paths.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
    require_project_reviewer,
)
from app.schemas.checklist_review import (
    ChecklistDraftFindingCreate,
    ChecklistDraftFindingResponse,
    ChecklistEvidenceLinkCreate,
    ChecklistEvidenceLinkResponse,
    ChecklistEvidenceSearchRequest,
    ProjectChecklistCreateFromRulePack,
    ProjectChecklistDetailResponse,
    ProjectChecklistItemResponse,
    ProjectChecklistItemUpdate,
    ProjectChecklistResponse,
    RulePackDetailResponse,
    RulePackResponse,
)
from app.schemas.evidence_retrieval import EvidenceSearchResponse
from app.services import checklist_review_service as checklist
from app.services.checklist_review_service import ChecklistReviewError

router = APIRouter(tags=["checklist-review"])


def _handle(exc: Exception) -> HTTPException:
    status_code = getattr(exc, "status_code", 422)
    message = getattr(exc, "message", str(exc))
    return HTTPException(status_code=status_code, detail=message)


# ---------------------------------------------------------------------------
# Rule packs
# ---------------------------------------------------------------------------


@router.get("/rule-packs", response_model=list[RulePackResponse])
def list_rule_packs(db: Session = Depends(get_db)) -> list[RulePackResponse]:
    return checklist.list_rule_packs(db)


@router.get("/rule-packs/{rule_pack_id}", response_model=RulePackDetailResponse)
def get_rule_pack(
    rule_pack_id: str, db: Session = Depends(get_db)
) -> RulePackDetailResponse:
    try:
        return RulePackDetailResponse.model_validate(
            checklist.get_rule_pack(db, rule_pack_id)
        )
    except (ChecklistReviewError, ValueError) as exc:
        raise _handle(exc) from exc


# ---------------------------------------------------------------------------
# Project checklists
# ---------------------------------------------------------------------------


@router.get(
    "/projects/{project_id}/checklists",
    response_model=list[ProjectChecklistResponse],
)
def list_project_checklists(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ProjectChecklistResponse]:
    require_project_read(db, project_id, user)
    try:
        return checklist.list_project_checklists(db, project_id)
    except (ChecklistReviewError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/checklists/from-rule-pack",
    response_model=ProjectChecklistResponse,
    status_code=201,
)
def create_checklist_from_rule_pack(
    project_id: str,
    body: ProjectChecklistCreateFromRulePack,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ProjectChecklistResponse:
    actor = require_project_reviewer(db, project_id, user)
    try:
        return checklist.create_project_checklist_from_rule_pack(
            db, project_id, body.rule_pack_id, name=body.name, actor=actor
        )
    except (ChecklistReviewError, ValueError) as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/checklists/{project_checklist_id}",
    response_model=ProjectChecklistDetailResponse,
)
def get_project_checklist(
    project_id: str,
    project_checklist_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ProjectChecklistDetailResponse:
    require_project_read(db, project_id, user)
    try:
        detail = checklist.get_project_checklist(
            db, project_id, project_checklist_id
        )
        items = checklist.list_project_checklist_items(
            db, project_id, project_checklist_id
        )
    except (ChecklistReviewError, ValueError) as exc:
        raise _handle(exc) from exc
    detail["items"] = [
        ProjectChecklistItemResponse.model_validate(i) for i in items
    ]
    return ProjectChecklistDetailResponse.model_validate(detail)


@router.get(
    "/projects/{project_id}/checklists/{project_checklist_id}/items",
    response_model=list[ProjectChecklistItemResponse],
)
def list_checklist_items(
    project_id: str,
    project_checklist_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ProjectChecklistItemResponse]:
    require_project_read(db, project_id, user)
    try:
        return checklist.list_project_checklist_items(
            db, project_id, project_checklist_id
        )
    except (ChecklistReviewError, ValueError) as exc:
        raise _handle(exc) from exc


# ---------------------------------------------------------------------------
# Checklist item review
# ---------------------------------------------------------------------------


@router.patch(
    "/projects/{project_id}/checklist-items/{project_checklist_item_id}",
    response_model=ProjectChecklistItemResponse,
)
def update_checklist_item(
    project_id: str,
    project_checklist_item_id: str,
    body: ProjectChecklistItemUpdate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ProjectChecklistItemResponse:
    require_project_reviewer(db, project_id, user)
    try:
        return checklist.update_project_checklist_item(
            db,
            project_id,
            project_checklist_item_id,
            body.model_dump(exclude_none=True),
        )
    except (ChecklistReviewError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/checklist-items/{project_checklist_item_id}/evidence-search",
    response_model=EvidenceSearchResponse,
)
def search_checklist_item_evidence(
    project_id: str,
    project_checklist_item_id: str,
    body: ChecklistEvidenceSearchRequest,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> EvidenceSearchResponse:
    require_project_reviewer(db, project_id, user)
    try:
        result = checklist.search_evidence_for_checklist_item(
            db,
            project_id,
            project_checklist_item_id,
            body.model_dump(exclude_none=True),
        )
    except (ChecklistReviewError, ValueError) as exc:
        raise _handle(exc) from exc
    return EvidenceSearchResponse.model_validate(result)


@router.post(
    "/projects/{project_id}/checklist-items/{project_checklist_item_id}/evidence-links",
    response_model=ChecklistEvidenceLinkResponse,
    status_code=201,
)
def link_checklist_evidence(
    project_id: str,
    project_checklist_item_id: str,
    body: ChecklistEvidenceLinkCreate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ChecklistEvidenceLinkResponse:
    require_project_reviewer(db, project_id, user)
    try:
        return checklist.link_citation_to_checklist_item(
            db,
            project_id,
            project_checklist_item_id,
            body.model_dump(exclude_none=True),
        )
    except (ChecklistReviewError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/checklist-items/{project_checklist_item_id}/draft-finding",
    response_model=ChecklistDraftFindingResponse,
    status_code=201,
)
def create_checklist_draft_finding(
    project_id: str,
    project_checklist_item_id: str,
    body: ChecklistDraftFindingCreate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ChecklistDraftFindingResponse:
    require_project_reviewer(db, project_id, user)
    try:
        result = checklist.create_draft_finding_from_checklist_item(
            db,
            project_id,
            project_checklist_item_id,
            body.model_dump(exclude_none=True),
        )
    except (ChecklistReviewError, ValueError) as exc:
        raise _handle(exc) from exc
    return ChecklistDraftFindingResponse.model_validate(
        {
            "finding": result["finding"],
            "citation": result["citation"],
            "checklist_item": result["checklist_item"],
        }
    )
