"""Per-request context: a correlation id plus safe actor and tenant identifiers.

Civil Engineer AI attaches a stable request id to every request so an operator
can trace a single request across access logs, application events, and the audit
trail. The context also carries the resolved user, organization, and project
identifiers when they are known, so logs and audit rows share the same
attribution without threading these values through every function signature.

Values are held in context variables, which are isolated per request and per
async task, so concurrent requests never see each other's context. Nothing here
stores secrets, tokens, raw IP addresses, or file paths: only opaque
identifiers that are safe to log.
"""

from __future__ import annotations

import contextvars
import uuid
from typing import Any

_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
_user_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "user_id", default=None
)
_organization_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "organization_id", default=None
)
_project_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "project_id", default=None
)


def new_request_id() -> str:
    """Return a fresh opaque request id."""

    return uuid.uuid4().hex


def set_request_id(request_id: str) -> None:
    """Bind the correlation id for the current request context."""

    _request_id.set(request_id)


def get_request_id() -> str | None:
    """Return the correlation id for the current request, or None."""

    return _request_id.get()


def bind_actor(
    *,
    user_id: str | None = None,
    organization_id: str | None = None,
) -> None:
    """Bind the resolved user and organization for the current request.

    Called after authentication resolves a signed-in user so that later logs
    and audit rows carry the same attribution. Missing values are left unset.
    """

    if user_id is not None:
        _user_id.set(user_id)
    if organization_id is not None:
        _organization_id.set(organization_id)


def bind_project(project_id: str | None) -> None:
    """Bind the project a request is operating on, when known."""

    if project_id is not None:
        _project_id.set(project_id)


def current_context() -> dict[str, Any]:
    """Return the set context identifiers as a dict, omitting unset values."""

    context: dict[str, Any] = {}
    request_id = _request_id.get()
    if request_id:
        context["request_id"] = request_id
    user_id = _user_id.get()
    if user_id:
        context["user_id"] = user_id
    organization_id = _organization_id.get()
    if organization_id:
        context["organization_id"] = organization_id
    project_id = _project_id.get()
    if project_id:
        context["project_id"] = project_id
    return context


def reset() -> None:
    """Clear all request context values.

    Used by the request middleware after a response is produced so a worker
    that reuses the context does not carry stale identifiers.
    """

    _request_id.set(None)
    _user_id.set(None)
    _organization_id.set(None)
    _project_id.set(None)
