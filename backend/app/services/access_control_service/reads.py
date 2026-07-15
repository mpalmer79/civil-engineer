"""FastAPI dependencies that resolve the current user from a bearer token.

These dependencies read the Authorization header and resolve the signed-in user.
They enforce authentication only; they never control whether a project satisfies
engineering requirements and never imply approval, certification, or compliance.
"""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core import request_context
from app.db import models
from app.db.database import get_db
from app.services import auth_service
from app.services.auth_service import AuthError


def _token_from_header(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return authorization.strip()


def get_optional_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> models.UserAccount | None:
    """Resolve the signed-in user from the Authorization header, or None."""

    token = _token_from_header(authorization)
    if not token:
        return None
    try:
        user = auth_service.get_current_user_from_token(db, token)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    # Bind the resolved user onto the request context so later application logs
    # and audit rows share the same attribution as the access log.
    request_context.bind_actor(user_id=user.user_id)
    return user


def get_current_user(
    user: models.UserAccount | None = Depends(get_optional_user),
) -> models.UserAccount:
    """Require a signed-in user; raise 401 otherwise."""

    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user
