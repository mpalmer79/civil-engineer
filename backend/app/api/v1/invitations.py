"""Organization team invitation API routes (Production Phase 4B).

An org_admin can invite a teammate by email with a role, list invitations, and
revoke a pending invitation. A signed-in user can accept an invitation with the
token, which creates an active membership. A public lookup returns a safe preview
for the accept page. Invitation tokens are never echoed except as a dev token
outside production.

These routes control team membership and audit attribution only. They never grant
engineering authority and never imply approval, certification, or compliance.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models
from app.db.database import get_db
from app.schemas.invitation import (
    InvitationAcceptRequest,
    InvitationAcceptResponse,
    InvitationCreateRequest,
    InvitationCreateResponse,
    InvitationLookupResponse,
    InvitationResponse,
)
from app.services import access_control_service, invitation_service, mailer
from app.services.access_control_service import (
    get_current_user,
    get_optional_user,
    require_org_admin,
)

router = APIRouter(tags=["invitations"])


@router.post(
    "/organizations/{organization_id}/invitations",
    response_model=InvitationCreateResponse,
    status_code=201,
)
def create_invitation(
    organization_id: str,
    body: InvitationCreateRequest,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> InvitationCreateResponse:
    """Invite a teammate to the organization. Requires org_admin."""

    admin = require_org_admin(db, organization_id, user)
    record, token = invitation_service.create_invitation(
        db,
        organization_id=organization_id,
        email=body.email,
        role=body.role,
        invited_by_user_id=admin.user_id,
    )
    db.commit()
    delivery = mailer.send_email(
        to=record.email,
        category="team_invitation",
        subject="You're invited to a Civil Engineer AI workspace",
        body=(
            "You have been invited to join a workspace. Use this token to "
            f"accept the invitation. Token: {token}"
        ),
    )
    settings = get_settings()
    return InvitationCreateResponse(
        invitation=InvitationResponse(
            **invitation_service.invitation_public_dict(record)
        ),
        dev_invite_token=token if settings.expose_dev_tokens else None,
        email_sent=bool(delivery.get("sent")),
    )


@router.get(
    "/organizations/{organization_id}/invitations",
    response_model=list[InvitationResponse],
)
def list_invitations(
    organization_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[InvitationResponse]:
    """List the organization's invitations. Requires org_admin."""

    require_org_admin(db, organization_id, user)
    return [
        InvitationResponse(**invitation_service.invitation_public_dict(inv))
        for inv in invitation_service.list_invitations(db, organization_id)
    ]


@router.post(
    "/organizations/{organization_id}/invitations/{invitation_id}/revoke",
    response_model=InvitationResponse,
)
def revoke_invitation(
    organization_id: str,
    invitation_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> InvitationResponse:
    """Revoke a pending invitation. Requires org_admin."""

    require_org_admin(db, organization_id, user)
    record = invitation_service.revoke_invitation(
        db, organization_id=organization_id, invitation_id=invitation_id
    )
    db.commit()
    return InvitationResponse(
        **invitation_service.invitation_public_dict(record)
    )


@router.get("/invitations/lookup", response_model=InvitationLookupResponse)
def lookup_invitation(
    token: str = Query(...), db: Session = Depends(get_db)
) -> InvitationLookupResponse:
    """Return a safe preview of an invitation for the accept page (public)."""

    return InvitationLookupResponse(
        **invitation_service.lookup_invitation(db, token)
    )


@router.post("/invitations/accept", response_model=InvitationAcceptResponse)
def accept_invitation(
    body: InvitationAcceptRequest,
    user: models.UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InvitationAcceptResponse:
    """Accept an invitation for the signed-in user, creating a membership."""

    membership = invitation_service.accept_invitation(
        db, token=body.token, user=user
    )
    db.commit()
    org = access_control_service.get_organization(
        db, membership.organization_id
    )
    return InvitationAcceptResponse(
        organization_id=membership.organization_id,
        role=membership.role,
        membership_id=membership.membership_id,
        detail=f"You have joined {org.organization_name}.",
    )
