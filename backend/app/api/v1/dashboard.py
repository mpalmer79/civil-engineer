"""Reviewer dashboard, organization workload, and operational metrics routes.

Production Foundations Sprint 9. These routes expose cross-project review-support
workload visibility. They return operational indicators only and enforce Sprint 5
access control on every result. They never approve plans, certify compliance,
verify CAD, validate design, resolve issues, or make final engineering decisions.

Reviewer dashboard routes require an authenticated user and return only projects
that user can read. Organization routes require organization membership.
Reviewer workload summaries require org_admin or senior_reviewer. Project
workload requires project read access. Assignment and priority updates require
project admin access.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.safety import ProhibitedLanguageError
from app.db import models
from app.db.database import get_db
from app.schemas.dashboard import (
    DashboardProjectSummary,
    OrganizationDashboardResponse,
    OrganizationReviewerWorkloadResponse,
    OrganizationWorkloadResponse,
    ProjectAssignmentUpdate,
    ProjectPendingActionsResponse,
    ProjectPriorityUpdate,
    ProjectWorkloadSummaryResponse,
    ReviewerDashboardResponse,
    ReviewerQueueResponse,
)
from app.services import dashboard_service
from app.services.access_control_service import (
    get_current_user,
    get_optional_user,
    require_project_admin,
    require_project_read,
)

router = APIRouter(tags=["dashboard"])


def _handle(exc: Exception) -> HTTPException:
    status_code = getattr(exc, "status_code", 422)
    message = getattr(exc, "message", str(exc))
    return HTTPException(status_code=status_code, detail=message)


# ---------------------------------------------------------------------------
# Reviewer dashboard
# ---------------------------------------------------------------------------


@router.get("/dashboard/reviewer", response_model=ReviewerDashboardResponse)
def reviewer_dashboard(
    user: models.UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReviewerDashboardResponse:
    return dashboard_service.get_reviewer_dashboard(db, user)


@router.get(
    "/dashboard/reviewer/queue", response_model=ReviewerQueueResponse
)
def reviewer_queue(
    item_type: str | None = Query(default=None),
    user: models.UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReviewerQueueResponse:
    return dashboard_service.get_reviewer_queue(
        db, user, {"item_type": item_type}
    )


@router.get(
    "/dashboard/reviewer/projects",
    response_model=list[DashboardProjectSummary],
)
def reviewer_dashboard_projects(
    user: models.UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DashboardProjectSummary]:
    return dashboard_service.get_reviewer_dashboard_projects(db, user)


# ---------------------------------------------------------------------------
# Organization dashboard
# ---------------------------------------------------------------------------


@router.get(
    "/organizations/{organization_id}/dashboard",
    response_model=OrganizationDashboardResponse,
)
def organization_dashboard(
    organization_id: str,
    user: models.UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationDashboardResponse:
    return dashboard_service.get_organization_dashboard(
        db, organization_id, user
    )


@router.get(
    "/organizations/{organization_id}/workload",
    response_model=OrganizationWorkloadResponse,
)
def organization_workload(
    organization_id: str,
    user: models.UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationWorkloadResponse:
    return dashboard_service.get_organization_workload(
        db, organization_id, user
    )


@router.get(
    "/organizations/{organization_id}/reviewers/workload",
    response_model=OrganizationReviewerWorkloadResponse,
)
def organization_reviewer_workload(
    organization_id: str,
    user: models.UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationReviewerWorkloadResponse:
    return dashboard_service.get_organization_reviewer_workload(
        db, organization_id, user
    )


# ---------------------------------------------------------------------------
# Project workload
# ---------------------------------------------------------------------------


@router.get(
    "/projects/{project_id}/workload-summary",
    response_model=ProjectWorkloadSummaryResponse,
)
def project_workload_summary(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ProjectWorkloadSummaryResponse:
    actor = require_project_read(db, project_id, user)
    return dashboard_service.get_project_workload_summary(
        db, project_id, actor
    )


@router.get(
    "/projects/{project_id}/pending-actions",
    response_model=ProjectPendingActionsResponse,
)
def project_pending_actions(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ProjectPendingActionsResponse:
    actor = require_project_read(db, project_id, user)
    return dashboard_service.get_project_pending_actions(
        db, project_id, actor
    )


# ---------------------------------------------------------------------------
# Assignment and priority (project admin only)
# ---------------------------------------------------------------------------


@router.patch(
    "/projects/{project_id}/assignment",
    response_model=DashboardProjectSummary,
)
def update_project_assignment(
    project_id: str,
    body: ProjectAssignmentUpdate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> DashboardProjectSummary:
    actor = require_project_admin(db, project_id, user)
    try:
        return dashboard_service.assign_project_reviewer(
            db, project_id, body.model_dump(exclude_unset=True), actor=actor
        )
    except (ProhibitedLanguageError, ValueError) as exc:
        raise _handle(exc) from exc


@router.patch(
    "/projects/{project_id}/priority",
    response_model=DashboardProjectSummary,
)
def update_project_priority(
    project_id: str,
    body: ProjectPriorityUpdate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> DashboardProjectSummary:
    actor = require_project_admin(db, project_id, user)
    try:
        return dashboard_service.update_project_priority(
            db, project_id, body.model_dump(exclude_unset=True), actor=actor
        )
    except (ProhibitedLanguageError, ValueError) as exc:
        raise _handle(exc) from exc
