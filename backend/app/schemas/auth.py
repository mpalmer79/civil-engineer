"""Pydantic schemas for authentication and access control (Sprint 5).

These represent the local authentication foundation: user accounts, organization
memberships, and project access. Password hashes and tokens are never returned in
a response body. Nothing here implies a final engineering decision, approval,
certification, or compliance.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserRegisterRequest(BaseModel):
    email: str
    display_name: str
    password: str
    organization_name: str | None = None
    organization_type: str | None = None


class UserLoginRequest(BaseModel):
    email: str
    password: str


class CurrentUserResponse(BaseModel):
    user_id: str
    email: str
    display_name: str
    is_active: bool = True
    is_demo_user: bool = False
    created_at: datetime | None = None
    last_login_at: datetime | None = None


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: CurrentUserResponse


class OrganizationResponse(BaseModel):
    organization_id: str
    organization_name: str
    organization_type: str
    source_mode: str
    role: str | None = None
    membership_id: str | None = None


class MembershipResponse(BaseModel):
    membership_id: str
    organization_id: str
    user_id: str
    user_email: str | None = None
    display_name: str | None = None
    role: str
    is_active: bool = True


class ProjectAccessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_access_id: str
    project_id: str
    organization_id: str | None = None
    user_id: str | None = None
    access_level: str
    granted_by_user_id: str | None = None
    is_active: bool = True
    created_at: datetime | None = None


class ProjectAccessGrantRequest(BaseModel):
    access_level: str
    user_id: str | None = None
    organization_id: str | None = None


class UserProjectSummary(BaseModel):
    project_id: str
    project_name: str
    source_mode: str
    visibility_mode: str
    demo_public: bool = False
    organization_id: str | None = None
    access_level: str | None = None


class PermissionErrorResponse(BaseModel):
    detail: str
