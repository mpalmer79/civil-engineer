"""Public pilot / design-partner request API routes.

POST /api/v1/pilot-requests is public and needs no login: a civil/AEC firm can
submit a pilot request after seeing the guided demo. The endpoint stores the
lead locally, sends no email, and contacts no external service.

GET /api/v1/pilot-requests requires an authenticated user. Pilot requests are
public leads, not tenant-owned project data, so this list is never exposed
anonymously. There is no public list endpoint and no admin UI in this phase.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.pilot import PilotRequestAck, PilotRequestCreate, PilotRequestRead
from app.services import pilot_request_service
from app.services.access_control_service import get_current_user

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
    user: models.UserAccount = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PilotRequestRead]:
    # get_current_user raises 401 for anonymous callers, so the public cannot
    # list stored leads.
    records = pilot_request_service.list_pilot_requests(db)
    return [PilotRequestRead.model_validate(r) for r in records]
