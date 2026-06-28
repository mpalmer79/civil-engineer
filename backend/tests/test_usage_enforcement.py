"""Tests for Production Phase 4D usage enforcement.

Enforcement is off by default (advisory), and on (USAGE_ENFORCEMENT_ENABLED) it
hard-blocks the selected categories for real organizations while never blocking
the public Brookside demo or the demo organization. A blocked action returns a
402 limit_exceeded error and leaves no partial state.
"""

from __future__ import annotations

import uuid
from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.database import SessionLocal
from app.services import usage_service

BROOKSIDE = "proj_brookside_meadows"


@contextmanager
def _enforcement(enabled: bool):
    settings = get_settings()
    saved = settings.USAGE_ENFORCEMENT_ENABLED
    settings.USAGE_ENFORCEMENT_ENABLED = enabled
    try:
        yield
    finally:
        settings.USAGE_ENFORCEMENT_ENABLED = saved


def _email() -> str:
    return f"user_{uuid.uuid4().hex[:10]}@example.com"


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_with_org(client: TestClient) -> dict[str, str]:
    admin = client.post(
        "/api/v1/auth/register",
        json={
            "email": _email(),
            "password": "password123",
            "display_name": "Usage Admin",
            "organization_name": "Usage Org",
        },
    ).json()
    return {"token": admin["access_token"]}


def _new_project(client: TestClient, token: str, name: str):
    return client.post(
        "/api/v1/projects",
        headers=_headers(token),
        json={
            "project_name": name,
            "project_type": "subdivision",
            "jurisdiction": "Town",
            "review_type": "site",
            "review_domain": "stormwater",
            "location_context": "x",
        },
    )


# ---------------------------------------------------------------------------
# Advisory (default) does not block
# ---------------------------------------------------------------------------


def test_advisory_mode_does_not_block_projects(client: TestClient):
    admin = _admin_with_org(client)
    with _enforcement(False):
        assert _new_project(client, admin["token"], "A1").status_code == 201
        # The demo plan limits projects to 1, but advisory mode never blocks.
        assert _new_project(client, admin["token"], "A2").status_code == 201


# ---------------------------------------------------------------------------
# Enforcement blocks over-limit actions
# ---------------------------------------------------------------------------


def test_enforcement_blocks_project_over_limit(client: TestClient):
    admin = _admin_with_org(client)
    with _enforcement(True):
        first = _new_project(client, admin["token"], "P1")
        assert first.status_code == 201
        second = _new_project(client, admin["token"], "P2")
        assert second.status_code == 402
        detail = second.json()["detail"]
        assert detail["code"] == "limit_exceeded"
        assert detail["category"] == "project_created"


def test_blocked_project_does_not_partially_mutate(client: TestClient):
    admin = _admin_with_org(client)
    with _enforcement(True):
        _new_project(client, admin["token"], "Only1")
        blocked = _new_project(client, admin["token"], "ShouldFail")
        assert blocked.status_code == 402
    # Only the first project exists for this user.
    projects = client.get(
        "/api/v1/me/projects", headers=_headers(admin["token"])
    ).json()
    real = [p for p in projects if not p["demo_public"]] if projects else []
    names = [p["project_name"] for p in real]
    assert "ShouldFail" not in names
    assert names.count("Only1") == 1


def test_enforcement_blocks_documents_over_limit(client: TestClient):
    admin = _admin_with_org(client)
    with _enforcement(True):
        proj = _new_project(client, admin["token"], "DocProj").json()
        project_id = proj["project_id"]
        # The demo plan allows 5 documents.
        for i in range(5):
            r = client.post(
                f"/api/v1/projects/{project_id}/documents/register",
                headers=_headers(admin["token"]),
                json={"original_file_name": f"doc{i}.pdf", "document_type": "other"},
            )
            assert r.status_code == 201, r.text
        blocked = client.post(
            f"/api/v1/projects/{project_id}/documents/register",
            headers=_headers(admin["token"]),
            json={"original_file_name": "doc6.pdf", "document_type": "other"},
        )
        assert blocked.status_code == 402
        assert blocked.json()["detail"]["category"] == "document_uploaded"


def test_enforcement_blocks_review_packets_over_limit(client: TestClient):
    admin = _admin_with_org(client)
    with _enforcement(True):
        project_id = _new_project(client, admin["token"], "PacketProj").json()[
            "project_id"
        ]
        # The demo plan allows 2 review packets.
        for _ in range(2):
            r = client.post(
                f"/api/v1/projects/{project_id}/review-packets/generate",
                headers=_headers(admin["token"]),
            )
            assert r.status_code == 200, r.text
        blocked = client.post(
            f"/api/v1/projects/{project_id}/review-packets/generate",
            headers=_headers(admin["token"]),
        )
        assert blocked.status_code == 402
        assert blocked.json()["detail"]["category"] == "review_packet_generated"


# ---------------------------------------------------------------------------
# Public demo and demo org are never enforced
# ---------------------------------------------------------------------------


def test_public_demo_packet_generation_is_not_blocked(client: TestClient):
    # The Brookside demo project belongs to the excluded demo organization, so
    # even with enforcement on and existing packets, generation is never blocked.
    with _enforcement(True):
        resp = client.post(
            f"/api/v1/projects/{BROOKSIDE}/review-packets/generate"
        )
    assert resp.status_code == 200


def test_demo_org_is_never_enforced_at_service_level(client: TestClient):
    # check_limit is a no-op for the demo organization even far over any limit.
    with _enforcement(True):
        usage_service.check_limit(
            SessionLocal(),
            category="project_created",
            organization_id="org_internal_demo",
        )  # does not raise


# ---------------------------------------------------------------------------
# Advisory categories never block, even with enforcement on
# ---------------------------------------------------------------------------


def test_advisory_category_never_blocks(client: TestClient):
    org_id = f"org_adv_{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    try:
        # Record pages_indexed far above any plan limit.
        for _ in range(5):
            usage_service.record_usage(
                db, category="pages_indexed", organization_id=org_id, quantity=1000
            )
        db.commit()
        with _enforcement(True):
            # pages_indexed is not an enforced category, so this never raises.
            usage_service.check_limit(
                db, category="pages_indexed", organization_id=org_id
            )
    finally:
        db.close()


def test_usage_summary_reports_enforced_flag(client: TestClient):
    admin = _admin_with_org(client)
    org_id = client.get(
        "/api/v1/me/organizations", headers=_headers(admin["token"])
    ).json()[0]["organization_id"]
    with _enforcement(True):
        summary = client.get(
            f"/api/v1/organizations/{org_id}/usage", headers=_headers(admin["token"])
        ).json()
    assert summary["enforcement"] == "enforced"
    by_key = {limit["key"]: limit for limit in summary["limits"]}
    assert by_key["projects"]["enforced"] is True
    # AI calls remain advisory even with enforcement enabled.
    assert by_key["ai_calls"]["enforced"] is False
