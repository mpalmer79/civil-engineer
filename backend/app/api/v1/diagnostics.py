"""Deployment readiness and diagnostics API routes (Sprint 10).

Operational endpoints that help an operator confirm a deployment is configured
and connected. Readiness is public but carefully sanitized. Detailed environment
diagnostics require an organization admin. Storage diagnostics require an
authenticated user. None of these routes returns a secret value, a database URL,
an auth secret, object storage credentials, a token, a signed URL, or a raw file
system path.

These checks describe operational readiness only. They do not approve a project,
certify compliance, verify CAD, validate design, declare safety, resolve an
issue, or close an issue.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.diagnostics import (
    EnvironmentValidationResponse,
    FrontendConfigDiagnosticsResponse,
    ReadinessResponse,
    SecurityBoundaryDiagnosticsResponse,
    StorageDiagnosticsResponse,
)
from app.services import environment_validation_service as envval
from app.services.access_control_service import (
    get_current_user,
    get_optional_user,
    require_admin_user,
)

router = APIRouter(tags=["diagnostics"])


@router.get("/readiness", response_model=ReadinessResponse)
def readiness(db: Session = Depends(get_db)) -> ReadinessResponse:
    """Public, sanitized readiness summary (database, config, storage)."""

    return ReadinessResponse(**envval.get_readiness(db))


@router.get(
    "/diagnostics/environment",
    response_model=EnvironmentValidationResponse,
)
def environment_diagnostics(
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> EnvironmentValidationResponse:
    """Admin-only environment validation summary. No secret values."""

    require_admin_user(db, user)
    return EnvironmentValidationResponse(**envval.validate_environment())


@router.get(
    "/diagnostics/storage",
    response_model=StorageDiagnosticsResponse,
)
def storage_diagnostics(
    user: models.UserAccount = Depends(get_current_user),
) -> StorageDiagnosticsResponse:
    """Authenticated storage provider diagnostics. No credentials or paths."""

    return StorageDiagnosticsResponse(**envval.get_storage_diagnostics())


@router.get(
    "/diagnostics/frontend-config",
    response_model=FrontendConfigDiagnosticsResponse,
)
def frontend_config_diagnostics() -> FrontendConfigDiagnosticsResponse:
    """Public backend-side frontend integration hints. No secrets."""

    return FrontendConfigDiagnosticsResponse(
        **envval.get_frontend_config_diagnostics()
    )


@router.get(
    "/diagnostics/security-boundary",
    response_model=SecurityBoundaryDiagnosticsResponse,
)
def security_boundary_diagnostics() -> SecurityBoundaryDiagnosticsResponse:
    """Public static professional-boundary summary for UI self-checks."""

    return SecurityBoundaryDiagnosticsResponse(
        **envval.get_security_boundary_diagnostics()
    )
