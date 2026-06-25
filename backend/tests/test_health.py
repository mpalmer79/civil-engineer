"""Health endpoint test."""

from __future__ import annotations

import re

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "Civil Engineer AI Backend"
    # The health payload reports a product version, not a development phase
    # number, so the public health URL carries no phase chronology.
    assert "phase" not in body
    assert re.match(r"^\d+\.\d+\.\d+$", body["version"])
    assert isinstance(body["demo_mode"], bool)
