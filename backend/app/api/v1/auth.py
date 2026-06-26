"""Authentication, organization, and access-control API routes (Sprint 5).

Provides local registration and login, the current-user endpoint, organization
and membership reads, per-project access management, and the current user's
projects and organizations. Tokens are signed and short-lived; they are never
logged or returned outside the login response. Access control protects review
records and improves audit attribution. It never approves plans, certifies
compliance, verifies CAD, validates design, or makes any final engineering
decision.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.safety import ALLOWED_ORGANIZATION_TYPES
from app.db import models
from app.db.database import get_db
from app.schemas.auth import (
    AuthTokenResponse,
    CurrentUserResponse,
    MembershipResponse,
    OrganizationResponse,
    ProjectAccessGrantRequest,
    ProjectAccessResponse,
    UserLoginRequest,
    UserProjectSummary,
    UserRegisterRequest,
)
from app.services import access_control_service, auth_service
from app.services.access_control_service import (
    get_current_user,
    get_optional_user,
    require_project_admin,
    require_project_read,
)
from app.services.auth_service import AuthError

router = APIRouter(tags=["auth"])


def _handle(exc: Exception) -> HTTPException:
    status_code = getattr(exc, "status_code", 422)
    message = getattr(exc, "message", str(exc))
    return HTTPException(status_code=status_code, detail=message)


def _token_response(
    db: Session, user: models.UserAccount
) -> AuthTokenResponse:
    settings = get_settings()
    token = auth_service.create_access_token(user)
    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.AUTH_TOKEN_EXPIRE_MINUTES,
        user=CurrentUserResponse(**auth_service.user_public_dict(user)),
    )


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


@router.post("/auth/register", response_model=AuthTokenResponse, status_code=201)
def register(
    body: UserRegisterRequest, db: Session = Depends(get_db)
) -> AuthTokenResponse:
    try:
        user = auth_service.create_user(
            db,
            email=body.email,
            display_name=body.display_name,
            password=body.password,
        )
        # Optionally create a first organization and an admin membership.
        if body.organization_name and body.organization_name.strip():
            org_type = body.organization_type or "municipality"
            if org_type not in ALLOWED_ORGANIZATION_TYPES:
                raise AuthError(
                    f"Invalid organization_type '{org_type}'.", status_code=422
                )
            org = models.Organization(
                organization_id=f"org_{uuid.uuid4().hex[:12]}",
                organization_name=body.organization_name.strip(),
                organization_type=org_type,
                source_mode="user_created",
            )
            db.add(org)
            db.add(
                models.OrganizationMembership(
                    membership_id=f"mem_{uuid.uuid4().hex[:12]}",
                    organization_id=org.organization_id,
                    user_id=user.user_id,
                    role="org_admin",
                    is_active=True,
                )
            )
        db.commit()
        db.refresh(user)
    except (AuthError, ValueError) as exc:
        raise _handle(exc) from exc
    return _token_response(db, user)


@router.post("/auth/login", response_model=AuthTokenResponse)
def login(
    body: UserLoginRequest, db: Session = Depends(get_db)
) -> AuthTokenResponse:
    try:
        user = auth_service.authenticate_user(
            db, email=body.email, password=body.password
        )
        db.commit()
    except (AuthError, ValueError) as exc:
        raise _handle(exc) from exc
    return _token_response(db, user)


@router.get("/auth/me", response_model=CurrentUserResponse)
def current_user(
    user: models.UserAccount = Depends(get_current_user),
) -> CurrentUserResponse:
    return CurrentUserResponse(**auth_service.user_public_dict(user))


@router.post("/auth/logout")
def logout() -> dict[str, bool | str]:
    # Tokens are stateless; logout is handled client-side by discarding the
    # token. This endpoint documents that contract.
    return {"ok": True, "detail": "Discard the access token on the client."}


# ---------------------------------------------------------------------------
# Current user projects and organizations
# ---------------------------------------------------------------------------


@router.get("/me/organizations", response_model=list[OrganizationResponse])
def my_organizations(
    user: models.UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[OrganizationResponse]:
    return [
        OrganizationResponse(**org)
        for org in access_control_service.list_user_organizations(
            db, user.user_id
        )
    ]


@router.get("/me/projects", response_model=list[UserProjectSummary])
def my_projects(
    user: models.UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UserProjectSummary]:
    projects = access_control_service.list_user_accessible_projects(db, user)
    summaries: list[UserProjectSummary] = []
    for project in projects:
        level = access_control_service.effective_access_level(
            db, project.project_id, user
        )
        summaries.append(
            UserProjectSummary(
                project_id=project.project_id,
                project_name=project.project_name,
                source_mode=project.source_mode or "demo_fixture",
                visibility_mode=project.visibility_mode or "controlled",
                demo_public=bool(project.demo_public),
                organization_id=project.organization_id,
                access_level=level,
            )
        )
    return summaries


# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------


@router.get("/organizations", response_model=list[OrganizationResponse])
def list_organizations(
    user: models.UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[OrganizationResponse]:
    return [
        OrganizationResponse(**org)
        for org in access_control_service.list_user_organizations(
            db, user.user_id
        )
    ]


@router.get(
    "/organizations/{organization_id}", response_model=OrganizationResponse
)
def get_organization(
    organization_id: str,
    user: models.UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationResponse:
    if organization_id not in access_control_service.user_org_ids(
        db, user.user_id
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this organization.",
        )
    org = access_control_service.get_organization(db, organization_id)
    role = next(
        (
            m["role"]
            for m in access_control_service.list_user_organizations(
                db, user.user_id
            )
            if m["organization_id"] == organization_id
        ),
        None,
    )
    return OrganizationResponse(
        organization_id=org.organization_id,
        organization_name=org.organization_name,
        organization_type=org.organization_type,
        source_mode=org.source_mode,
        role=role,
    )


@router.get(
    "/organizations/{organization_id}/members",
    response_model=list[MembershipResponse],
)
def list_members(
    organization_id: str,
    user: models.UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MembershipResponse]:
    if organization_id not in access_control_service.user_org_ids(
        db, user.user_id
    ):
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this organization.",
        )
    return [
        MembershipResponse(**m)
        for m in access_control_service.list_organization_members(
            db, organization_id
        )
    ]


# ---------------------------------------------------------------------------
# Project access
# ---------------------------------------------------------------------------


@router.get(
    "/projects/{project_id}/access",
    response_model=list[ProjectAccessResponse],
)
def list_project_access(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ProjectAccessResponse]:
    # Reading the access list requires at least read access to the project.
    require_project_read(db, project_id, user)
    return access_control_service.list_project_access(db, project_id)


@router.post(
    "/projects/{project_id}/access/grant",
    response_model=ProjectAccessResponse,
    status_code=201,
)
def grant_access(
    project_id: str,
    body: ProjectAccessGrantRequest,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ProjectAccessResponse:
    actor = require_project_admin(db, project_id, user)
    try:
        return access_control_service.grant_project_access(
            db,
            project_id,
            access_level=body.access_level,
            user_id=body.user_id,
            organization_id=body.organization_id,
            granted_by_user_id=actor.user_id,
            granted_by_name=actor.display_name,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise _handle(exc) from exc
