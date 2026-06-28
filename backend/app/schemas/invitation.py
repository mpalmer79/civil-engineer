"""Pydantic schemas for organization team invitations (Production Phase 4B).

Invitation tokens are never returned except as a dev token outside production, so
local development and tests can complete the accept flow without an email
provider. Nothing here implies a final engineering decision, approval,
certification, or compliance.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class InvitationCreateRequest(BaseModel):
    email: str
    role: str = "reviewer"


class InvitationResponse(BaseModel):
    invitation_id: str
    organization_id: str
    email: str
    role: str
    status: str
    invited_by_user_id: str | None = None
    accepted_by_user_id: str | None = None
    expires_at: datetime | None = None
    accepted_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime | None = None


class InvitationCreateResponse(BaseModel):
    invitation: InvitationResponse
    # Populated only outside production when AUTH_EXPOSE_DEV_TOKENS is on. Null in
    # production, where the token is delivered by email instead.
    dev_invite_token: str | None = None
    email_sent: bool = False


class InvitationLookupResponse(BaseModel):
    organization_id: str
    organization_name: str | None = None
    email: str
    role: str
    status: str
    acceptable: bool
    expires_at: datetime | None = None


class InvitationAcceptRequest(BaseModel):
    token: str


class InvitationAcceptResponse(BaseModel):
    organization_id: str
    role: str
    membership_id: str
    detail: str
