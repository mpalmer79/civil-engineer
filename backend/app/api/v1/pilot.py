"""Public pilot / design-partner request API routes.

POST /api/v1/pilot-requests is public and needs no login: a civil/AEC firm can
submit a pilot request after seeing the guided demo. The endpoint stores the
lead locally, sends no email, and contacts no external service.

The list, detail, status-update, notes-update, and CSV-export routes require a
signed-in organization admin. Pilot requests are public leads, not tenant-owned
project data, so these are never exposed anonymously, and a non-admin
authenticated user cannot read or change them either. There is no public list
endpoint. Operator-only internal notes are never returned by the public POST.
Finer-grained, dedicated pilot-operator roles are future work; org admin is the
current operator gate.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.pilot import (
    PilotRequestAck,
    PilotRequestCreate,
    PilotRequestNotesUpdate,
    PilotRequestRead,
    PilotRequestStatusUpdate,
)
from app.services import pilot_request_service
from app.services.access_control_service import get_optional_user, require_admin_user

router = APIRouter(tags=["pilot"])


@router.post(
    "/pilot-requests",
    response_model=PilotRequestAck,
    status_code=201,
)
def create_pilot_request(
    body: PilotRequestCreate,
    db: Session = Depends(get_db),
) -> PilotRequestAck:
    record = pilot_request_service.create_pilot_request(db, body, source="pilot_page")
    return PilotRequestAck(pilot_request_id=record.pilot_request_id)


@router.get(
    "/pilot-requests",
    response_model=list[PilotRequestRead],
)
def list_pilot_requests(
    status: str | None = Query(default=None),
    interest_level: str | None = Query(default=None),
    has_sample_package: bool | None = Query(default=None),
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[PilotRequestRead]:
    # require_admin_user raises 401 for anonymous callers and 403 for a signed-in
    # non-admin, so the public cannot list stored leads and only an operator can.
    require_admin_user(db, user)
    records = pilot_request_service.list_pilot_requests(
        db,
        status=status,
        interest_level=interest_level,
        has_sample_package=has_sample_package,
    )
    return [PilotRequestRead.model_validate(r) for r in records]


@router.get(
    "/pilot-requests/export",
    response_class=Response,
)
def export_pilot_requests(
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> Response:
    """Operator-only CSV export of pilot leads. No file content, no secrets."""

    require_admin_user(db, user)
    csv_text = pilot_request_service.export_pilot_requests_csv(db)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=pilot-requests.csv"
        },
    )


@router.get(
    "/pilot-requests/{pilot_request_id}",
    response_model=PilotRequestRead,
)
def get_pilot_request(
    pilot_request_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> PilotRequestRead:
    require_admin_user(db, user)
    record = pilot_request_service.get_pilot_request(db, pilot_request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Pilot request not found")
    return PilotRequestRead.model_validate(record)


@router.patch(
    "/pilot-requests/{pilot_request_id}/status",
    response_model=PilotRequestRead,
)
def update_pilot_request_status(
    pilot_request_id: str,
    body: PilotRequestStatusUpdate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> PilotRequestRead:
    require_admin_user(db, user)
    record = pilot_request_service.update_status(
        db,
        pilot_request_id,
        status=body.status,
        mark_contacted=body.mark_contacted,
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Pilot request not found")
    return PilotRequestRead.model_validate(record)


@router.patch(
    "/pilot-requests/{pilot_request_id}/notes",
    response_model=PilotRequestRead,
)
def update_pilot_request_notes(
    pilot_request_id: str,
    body: PilotRequestNotesUpdate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> PilotRequestRead:
    require_admin_user(db, user)
    record = pilot_request_service.update_internal_notes(
        db, pilot_request_id, internal_notes=body.internal_notes
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Pilot request not found")
    return PilotRequestRead.model_validate(record)
