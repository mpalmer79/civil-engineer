"""Tests for request correlation, safe error handling, and context logging.

These cover the observability layer added on top of the existing safe logger:
a per-request correlation id echoed on the response, a global exception handler
that never leaks internal detail, correlation ids flowing onto audit rows, and
request context appearing in structured log events.
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi.testclient import TestClient

from app.core import request_context
from app.core.logging import log_event
from app.db import models
from app.db.database import SessionLocal
from app.db.seed import PROJECT_ID
from app.main import app


def test_response_carries_a_generated_correlation_id(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    request_id = response.headers.get("X-Request-Id")
    assert request_id
    assert len(request_id) >= 8


def test_inbound_correlation_id_is_echoed(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-Id": "trace-abc_123"})
    assert response.headers.get("X-Request-Id") == "trace-abc_123"


def test_unsafe_inbound_correlation_id_is_replaced(client: TestClient) -> None:
    unsafe = "bad id with spaces and <tags>"
    response = client.get("/health", headers={"X-Request-Id": unsafe})
    echoed = response.headers.get("X-Request-Id")
    assert echoed
    assert echoed != unsafe
    assert " " not in echoed


def test_each_request_gets_a_distinct_correlation_id(client: TestClient) -> None:
    first = client.get("/health").headers.get("X-Request-Id")
    second = client.get("/health").headers.get("X-Request-Id")
    assert first and second and first != second


def test_unhandled_exception_returns_safe_envelope() -> None:
    secret_detail = "boom internal detail 42"

    @app.get("/__test_boom__")
    def _boom() -> None:
        raise RuntimeError(secret_detail)

    try:
        # No context manager: avoid re-running the application lifespan/seed.
        local = TestClient(app, raise_server_exceptions=False)
        response = local.get("/__test_boom__")
        assert response.status_code == 500
        body = response.json()
        assert body["detail"] == "Internal server error."
        # The correlation id is returned so a client can quote it in a report.
        assert body.get("request_id")
        # The internal exception message must never reach the client.
        assert secret_detail not in response.text
        assert "RuntimeError" not in response.text
        assert "Traceback" not in response.text
        assert response.headers.get("X-Request-Id")
    finally:
        app.router.routes = [
            route
            for route in app.router.routes
            if getattr(route, "path", None) != "/__test_boom__"
        ]


def test_audit_events_receive_the_request_correlation_id() -> None:
    request_context.reset()
    request_context.set_request_id("req-correlation-xyz")
    db = SessionLocal()
    try:
        event = models.AuditEvent(
            audit_event_id="audit_test_reqid",
            project_id=PROJECT_ID,
            event_type="request_context_test",
            actor_type="system",
            related_entity_type="test",
            related_entity_id="test",
            description="request id propagation check",
            timestamp=datetime.utcnow(),
        )
        db.add(event)
        db.commit()
        stored = db.get(models.AuditEvent, "audit_test_reqid")
        assert stored is not None
        assert stored.request_id == "req-correlation-xyz"
    finally:
        existing = db.get(models.AuditEvent, "audit_test_reqid")
        if existing is not None:
            db.delete(existing)
            db.commit()
        db.close()
        request_context.reset()


def test_explicit_audit_request_id_is_not_overridden() -> None:
    request_context.reset()
    request_context.set_request_id("context-id")
    db = SessionLocal()
    try:
        event = models.AuditEvent(
            audit_event_id="audit_test_explicit_reqid",
            project_id=PROJECT_ID,
            event_type="request_context_test",
            actor_type="system",
            related_entity_type="test",
            related_entity_id="test",
            description="explicit request id preserved",
            timestamp=datetime.utcnow(),
            request_id="explicit-id",
        )
        db.add(event)
        db.commit()
        stored = db.get(models.AuditEvent, "audit_test_explicit_reqid")
        assert stored is not None
        assert stored.request_id == "explicit-id"
    finally:
        existing = db.get(models.AuditEvent, "audit_test_explicit_reqid")
        if existing is not None:
            db.delete(existing)
            db.commit()
        db.close()
        request_context.reset()


def test_log_event_includes_request_context(caplog) -> None:
    request_context.reset()
    request_context.set_request_id("log-req-1")
    request_context.bind_actor(user_id="user_42")
    try:
        with caplog.at_level(logging.INFO, logger="civil_engineer"):
            log_event("context_check", detail="value")
        message = caplog.records[-1].getMessage()
        assert "request_id=log-req-1" in message
        assert "user_id=user_42" in message
        assert "detail=value" in message
    finally:
        request_context.reset()


def test_log_event_redacts_secret_fields_with_context(caplog) -> None:
    request_context.reset()
    request_context.set_request_id("log-req-2")
    try:
        with caplog.at_level(logging.INFO, logger="civil_engineer"):
            log_event("secret_check", api_key="super-secret-value")
        message = caplog.records[-1].getMessage()
        assert "super-secret-value" not in message
        assert "api_key=[redacted]" in message
        assert "request_id=log-req-2" in message
    finally:
        request_context.reset()
