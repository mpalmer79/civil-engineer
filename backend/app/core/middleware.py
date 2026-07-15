"""Request middleware: correlation id, access logging, and timing.

Every request is assigned a correlation id (reusing an inbound X-Request-Id
when the caller supplies one) that is bound to the request context, echoed back
on the response, and shared with the audit trail. A single safe access log
event is emitted per request with the method, route, status, and duration. No
secret, credential, raw path, request body, or client IP is logged.
"""

from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core import request_context
from app.core.logging import log_event

_REQUEST_ID_HEADER = "X-Request-Id"

# Inbound ids are echoed for tracing, but only if they look like a safe opaque
# token. This stops a caller from injecting log-breaking or oversized values.
_MAX_INBOUND_REQUEST_ID = 128


def _safe_inbound_request_id(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    if not candidate or len(candidate) > _MAX_INBOUND_REQUEST_ID:
        return None
    if not all(ch.isalnum() or ch in "-_" for ch in candidate):
        return None
    return candidate


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Bind a correlation id, time the request, and emit one access log event."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_context.reset()
        request_id = _safe_inbound_request_id(
            request.headers.get(_REQUEST_ID_HEADER)
        ) or request_context.new_request_id()
        request_context.set_request_id(request_id)

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # The global exception handler produces the client response and its
            # own log line. Here we only record that the request failed with
            # timing and correlation, then re-raise so the handler runs. The
            # context is cleared at the start of the next request.
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            log_event(
                "request_failed",
                level=logging.ERROR,
                method=request.method,
                route=request.url.path,
                duration_ms=duration_ms,
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log_event(
            "request_completed",
            method=request.method,
            route=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        response.headers[_REQUEST_ID_HEADER] = request_id
        request_context.reset()
        return response
