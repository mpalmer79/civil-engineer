"""Tests for Production Foundations Sprint 9 reviewer dashboard and metrics.

These tests exercise the reviewer dashboard, reviewer queue, organization
dashboard and reviewer workload, project workload summary and pending actions,
and the project assignment and priority foundation. They confirm access control
on every dashboard result, safe aging buckets, safe metric labels, the security
boundary (no storage keys, raw paths, tokens, or secrets, and no full record
text), and that no final-decision wording appears in dashboard responses.

Some precise metric states (checklist evidence status, applicant response
review, carry-forward, package handoff readiness) are seeded directly through the
database session so the queue and count assertions are deterministic. Metrics
query by project_id, so the seeded child records exercise the same code paths a
full workflow would reach.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.safety import (
    ALLOWED_AGING_BUCKETS,
    ALLOWED_QUEUE_ITEM_TYPES,
)

BROOKSIDE_ID = "proj_brookside_meadows"
DEMO_ORG_ID = "org_internal_demo"

# Final-decision and outcome words that must never appear in dashboard responses.
FORBIDDEN_WORDS = [
    "approved",
    "certified",
    "compliant",
    "noncompliant",
    "verified",
    "validated",
    "passed review",
    "failed review",
    "resolved",
    "closed",
    "safe",
    "unsafe",
    "pe stamped",
]

# Tokens that would indicate a leak of storage internals or secrets.
LEAK_TOKENS = [
    "storage_key",
    "storage_path",
    "storage_bucket",
    "signed_url",
    "password",
    "pbkdf2",
    "secret",
    "aws_access",
    "/var/",
    "/home/",
    "/tmp/",
]


def _email() -> str:
    return f"user_{uuid.uuid4().hex[:10]}@example.com"


def _register(client: TestClient, *, organization_name: str | None = None) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": _email(),
            "password": "password123",
            "display_name": "Dashboard Reviewer",
            "organization_name": organization_name,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_project(client: TestClient, token: str, name: str = "Workload Project") -> str:
    response = client.post(
        "/api/v1/projects",
        headers=_headers(token),
        json={
            "project_name": name,
            "project_type": "Subdivision",
            "jurisdiction": "Town",
            "review_type": "Review",
            "review_domain": "stormwater",
            "location_context": "Parcel",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["project_id"]


def _assert_no_forbidden_words(text: str) -> None:
    lowered = text.lower()
    for word in FORBIDDEN_WORDS:
        assert (
            re.search(rf"\b{re.escape(word)}\b", lowered) is None
        ), f"forbidden word '{word}' found in dashboard response"


def _assert_no_leaks(text: str) -> None:
    lowered = text.lower()
    for token in LEAK_TOKENS:
        assert token not in lowered, f"leak token '{token}' found in response"


def _seed_workload(project_id: str) -> None:
    """Seed deterministic pending-action records directly for a project."""

    from app.db import models
    from app.db.database import SessionLocal

    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        suffix = uuid.uuid4().hex[:8]
        # A registered, not-yet-indexed document.
        db.add(
            models.Document(
                document_id=f"doc_{suffix}",
                project_id=project_id,
                file_name="stormwater_report.pdf",
                document_type="report",
                status="registered",
                purpose="Stormwater management report for review.",
                expected_key_information="Detention basin sizing.",
                source_mode="user_registered",
                indexed_at=None,
                text_extraction_status="not_indexed",
            )
        )
        # An evidence candidate needing triage.
        db.add(
            models.EvidenceCandidate(
                evidence_candidate_id=f"cand_{suffix}",
                project_id=project_id,
                document_id=f"doc_{suffix}",
                candidate_title="Possible detention basin outlet reference",
                candidate_status="retrieval_candidate",
                candidate_origin="keyword_search",
            )
        )
        # Checklist items with missing and unclear evidence.
        db.add(
            models.ProjectChecklistItem(
                project_checklist_item_id=f"pci_missing_{suffix}",
                project_checklist_id=f"chk_{suffix}",
                project_id=project_id,
                item_code="SW-1",
                category="stormwater",
                requirement_text="Detention basin sizing provided.",
                expected_evidence="Basin sizing calculations.",
                evidence_status="missing_evidence",
            )
        )
        db.add(
            models.ProjectChecklistItem(
                project_checklist_item_id=f"pci_unclear_{suffix}",
                project_checklist_id=f"chk_{suffix}",
                project_id=project_id,
                item_code="SW-2",
                category="stormwater",
                requirement_text="Outlet structure detail provided.",
                expected_evidence="Outlet detail sheet.",
                evidence_status="unclear_evidence",
            )
        )
        # A response matrix item with an applicant response awaiting review and a
        # carry-forward status.
        db.add(
            models.ResponseMatrixItem(
                response_matrix_item_id=f"rmi_{suffix}",
                response_matrix_id=f"rm_{suffix}",
                project_id=project_id,
                category="stormwater",
                reviewer_comment_draft="Reviewer requests basin sizing.",
                applicant_response_status="applicant_response_received",
                reviewer_follow_up_status="not_reviewed",
                carry_forward_status="carried_forward_for_review",
            )
        )
        # A resubmittal round.
        db.add(
            models.ResubmittalRound(
                resubmittal_round_id=f"rr_{suffix}",
                project_id=project_id,
                round_number=2,
                round_label="Round 2",
                status="round_registered",
            )
        )
        # A response package ready for reviewer handoff.
        db.add(
            models.ReviewerResponsePackage(
                response_package_id=f"rpkg_{suffix}",
                project_id=project_id,
                package_title="Reviewer response package",
                status="ready_for_reviewer_handoff",
            )
        )
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Reviewer dashboard
# ---------------------------------------------------------------------------


def test_reviewer_dashboard_requires_authentication(client: TestClient):
    assert client.get("/api/v1/dashboard/reviewer").status_code == 401


def test_authenticated_user_can_fetch_reviewer_dashboard(client: TestClient):
    token = _register(client)["access_token"]
    response = client.get("/api/v1/dashboard/reviewer", headers=_headers(token))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["scope"] == "reviewer"
    assert "totals" in body
    assert "projects" in body
    assert "queue" in body
    assert "generated_at" in body


def test_dashboard_only_includes_accessible_projects(client: TestClient):
    owner = _register(client)
    project_id = _create_project(client, owner["access_token"], "Owner Project")
    other = _register(client)
    # The owner sees their project; the other user does not.
    owner_view = client.get(
        "/api/v1/dashboard/reviewer", headers=_headers(owner["access_token"])
    ).json()
    other_view = client.get(
        "/api/v1/dashboard/reviewer", headers=_headers(other["access_token"])
    ).json()
    owner_ids = {p["project_id"] for p in owner_view["projects"]}
    other_ids = {p["project_id"] for p in other_view["projects"]}
    assert project_id in owner_ids
    assert project_id not in other_ids


def test_dashboard_includes_all_metric_counts(client: TestClient):
    token = _register(client)["access_token"]
    project_id = _create_project(client, token, "Seeded Workload")
    _seed_workload(project_id)
    body = client.get(
        "/api/v1/dashboard/reviewer", headers=_headers(token)
    ).json()
    summary = next(p for p in body["projects"] if p["project_id"] == project_id)
    metrics = summary["metrics"]
    assert metrics["documents_uploaded"] >= 1
    assert metrics["documents_needing_indexing"] >= 1
    assert metrics["evidence_candidates_needing_triage"] >= 1
    assert metrics["checklist_items_missing_evidence"] >= 1
    assert metrics["checklist_items_unclear_evidence"] >= 1
    assert metrics["applicant_responses_needing_review"] >= 1
    assert metrics["matrix_items_carried_forward"] >= 1
    assert metrics["resubmittal_rounds_registered"] >= 1
    assert metrics["response_packages_ready_for_handoff"] >= 1
    assert summary["pending_reviewer_action_count"] >= 1
    assert summary["has_pending_reviewer_action"] is True
    # Totals reflect the per-project counts.
    assert body["totals"]["pending_reviewer_action_count"] >= 1
    assert body["projects_with_pending_action_count"] >= 1


def test_dashboard_findings_pending_count(client: TestClient):
    token = _register(client)["access_token"]
    project_id = _create_project(client, token, "Findings Workload")
    client.post(
        f"/api/v1/projects/{project_id}/findings",
        headers=_headers(token),
        json={
            "title": "Detention basin outlet needs reviewer confirmation",
            "category": "stormwater",
            "risk_level": "medium",
            "evidence_status": "needs_reviewer_confirmation",
            "evidence_to_find": "Outlet sizing",
            "reason_it_matters": "Downstream capacity",
            "recommended_human_action": "Reviewer confirms sizing",
        },
    )
    body = client.get(
        "/api/v1/dashboard/reviewer", headers=_headers(token)
    ).json()
    summary = next(p for p in body["projects"] if p["project_id"] == project_id)
    assert summary["metrics"]["findings_needing_reviewer_confirmation"] >= 1


def test_dashboard_uses_safe_labels_and_no_leaks(client: TestClient):
    token = _register(client)["access_token"]
    project_id = _create_project(client, token, "Reviewer Labels Project")
    _seed_workload(project_id)
    text = client.get(
        "/api/v1/dashboard/reviewer", headers=_headers(token)
    ).text
    _assert_no_forbidden_words(text)
    _assert_no_leaks(text)
    assert token.lower() not in text.lower()


def test_dashboard_aging_buckets_are_safe(client: TestClient):
    token = _register(client)["access_token"]
    project_id = _create_project(client, token, "Aging Project")
    body = client.get(
        "/api/v1/dashboard/reviewer", headers=_headers(token)
    ).json()
    summary = next(p for p in body["projects"] if p["project_id"] == project_id)
    assert summary["age_bucket"] in ALLOWED_AGING_BUCKETS


# ---------------------------------------------------------------------------
# Reviewer queue
# ---------------------------------------------------------------------------


def test_reviewer_queue_lists_all_action_types(client: TestClient):
    token = _register(client)["access_token"]
    project_id = _create_project(client, token, "Queue Project")
    _seed_workload(project_id)
    body = client.get(
        "/api/v1/dashboard/reviewer/queue", headers=_headers(token)
    ).json()
    project_items = [q for q in body["items"] if q["project_id"] == project_id]
    types = {q["item_type"] for q in project_items}
    assert "document_indexing" in types
    assert "evidence_candidate_triage" in types
    assert "checklist_evidence_review" in types
    assert "applicant_response_review" in types
    assert "carried_forward_matrix_item" in types
    assert "response_package_handoff" in types
    # Age buckets and targets are safe and point at accessible project records.
    for item in project_items:
        assert item["item_type"] in ALLOWED_QUEUE_ITEM_TYPES
        assert item["age_bucket"] in ALLOWED_AGING_BUCKETS
        assert item["target_path"].startswith(f"/projects/{project_id}/")


def test_reviewer_queue_requires_authentication(client: TestClient):
    assert client.get("/api/v1/dashboard/reviewer/queue").status_code == 401


def test_reviewer_queue_filter_by_item_type(client: TestClient):
    token = _register(client)["access_token"]
    project_id = _create_project(client, token, "Queue Filter Project")
    _seed_workload(project_id)
    body = client.get(
        "/api/v1/dashboard/reviewer/queue?item_type=document_indexing",
        headers=_headers(token),
    ).json()
    assert all(q["item_type"] == "document_indexing" for q in body["items"])


def test_reviewer_dashboard_projects_route(client: TestClient):
    token = _register(client)["access_token"]
    project_id = _create_project(client, token, "Projects Route")
    body = client.get(
        "/api/v1/dashboard/reviewer/projects", headers=_headers(token)
    ).json()
    assert any(p["project_id"] == project_id for p in body)


# ---------------------------------------------------------------------------
# Organization dashboard
# ---------------------------------------------------------------------------


def test_org_member_can_fetch_organization_dashboard(client: TestClient):
    # The seeded demo admin is an org_admin of the demo organization.
    token = _login(client, "admin@example.com", "demo-admin-pass")
    response = client.get(
        f"/api/v1/organizations/{DEMO_ORG_ID}/dashboard",
        headers=_headers(token),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["organization_id"] == DEMO_ORG_ID
    # Brookside Meadows belongs to the demo org and is readable by the admin.
    ids = {p["project_id"] for p in body["projects"]}
    assert BROOKSIDE_ID in ids
    _assert_no_forbidden_words(response.text)
    _assert_no_leaks(response.text)


def test_non_member_cannot_fetch_organization_dashboard(client: TestClient):
    outsider = _register(client)
    response = client.get(
        f"/api/v1/organizations/{DEMO_ORG_ID}/dashboard",
        headers=_headers(outsider["access_token"]),
    )
    assert response.status_code == 403


def test_org_admin_can_fetch_reviewer_workload(client: TestClient):
    token = _login(client, "admin@example.com", "demo-admin-pass")
    response = client.get(
        f"/api/v1/organizations/{DEMO_ORG_ID}/reviewers/workload",
        headers=_headers(token),
    )
    assert response.status_code == 200, response.text
    assert "reviewers" in response.json()


def test_reviewer_role_cannot_fetch_reviewer_workload(client: TestClient):
    # The seeded demo reviewer has the reviewer role (not org_admin/senior).
    token = _login(client, "reviewer@example.com", "demo-reviewer-pass")
    # A reviewer-role member can read the org dashboard.
    dashboard = client.get(
        f"/api/v1/organizations/{DEMO_ORG_ID}/dashboard",
        headers=_headers(token),
    )
    assert dashboard.status_code == 200
    # But not the admin reviewer-workload summary.
    workload = client.get(
        f"/api/v1/organizations/{DEMO_ORG_ID}/reviewers/workload",
        headers=_headers(token),
    )
    assert workload.status_code == 403


def test_organization_workload_summary_route(client: TestClient):
    token = _login(client, "admin@example.com", "demo-admin-pass")
    response = client.get(
        f"/api/v1/organizations/{DEMO_ORG_ID}/workload",
        headers=_headers(token),
    )
    assert response.status_code == 200
    assert "totals" in response.json()


def test_unknown_organization_returns_404(client: TestClient):
    token = _login(client, "admin@example.com", "demo-admin-pass")
    response = client.get(
        "/api/v1/organizations/org_does_not_exist/dashboard",
        headers=_headers(token),
    )
    assert response.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Project workload
# ---------------------------------------------------------------------------


def test_project_read_access_can_fetch_workload_summary(client: TestClient):
    token = _register(client)["access_token"]
    project_id = _create_project(client, token, "Workload Summary Project")
    _seed_workload(project_id)
    response = client.get(
        f"/api/v1/projects/{project_id}/workload-summary",
        headers=_headers(token),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["project_id"] == project_id
    metrics = body["metrics"]
    assert metrics["documents_uploaded"] >= 1
    assert metrics["resubmittal_rounds_registered"] >= 1
    assert "queue" in body
    _assert_no_forbidden_words(response.text)
    _assert_no_leaks(response.text)


def test_workload_summary_unauthorized_user_gets_403(client: TestClient):
    owner = _register(client)
    project_id = _create_project(client, owner["access_token"], "Private Workload")
    other = _register(client)
    response = client.get(
        f"/api/v1/projects/{project_id}/workload-summary",
        headers=_headers(other["access_token"]),
    )
    assert response.status_code == 403


def test_project_pending_actions_route(client: TestClient):
    token = _register(client)["access_token"]
    project_id = _create_project(client, token, "Pending Actions Project")
    _seed_workload(project_id)
    response = client.get(
        f"/api/v1/projects/{project_id}/pending-actions",
        headers=_headers(token),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["pending_reviewer_action_count"] >= 1
    assert len(body["items"]) >= 1
    _assert_no_forbidden_words(response.text)


def test_brookside_workload_summary_public(client: TestClient):
    # Brookside Meadows is a public demo; its workload summary is readable.
    response = client.get(f"/api/v1/projects/{BROOKSIDE_ID}/workload-summary")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Assignment and priority
# ---------------------------------------------------------------------------


def test_admin_can_assign_reviewer_and_audit_written(client: TestClient):
    user = _register(client)
    token = user["access_token"]
    project_id = _create_project(client, token, "Assignment Project")
    response = client.patch(
        f"/api/v1/projects/{project_id}/assignment",
        headers=_headers(token),
        json={
            "assigned_reviewer_user_id": user["user"]["user_id"],
            "assigned_reviewer_name": "Dashboard Reviewer",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["assigned_reviewer_name"] == "Dashboard Reviewer"
    events = client.get(
        f"/api/v1/projects/{project_id}/audit-events", headers=_headers(token)
    ).json()
    assert "project_assignment_updated" in {e["event_type"] for e in events}


def test_admin_can_set_priority_and_reject_invalid(client: TestClient):
    token = _register(client)["access_token"]
    project_id = _create_project(client, token, "Priority Project")
    ok = client.patch(
        f"/api/v1/projects/{project_id}/priority",
        headers=_headers(token),
        json={"review_priority": "elevated"},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["review_priority"] == "elevated"
    bad = client.patch(
        f"/api/v1/projects/{project_id}/priority",
        headers=_headers(token),
        json={"review_priority": "urgent"},
    )
    assert bad.status_code == 422
    events = client.get(
        f"/api/v1/projects/{project_id}/audit-events", headers=_headers(token)
    ).json()
    assert "project_priority_updated" in {e["event_type"] for e in events}


def test_priority_note_rejects_prohibited_language(client: TestClient):
    token = _register(client)["access_token"]
    project_id = _create_project(client, token, "Priority Language Project")
    response = client.patch(
        f"/api/v1/projects/{project_id}/priority",
        headers=_headers(token),
        json={"review_priority": "standard", "note": "Plan is approved and safe"},
    )
    assert response.status_code == 422


def test_unauthorized_user_cannot_assign(client: TestClient):
    owner = _register(client)
    project_id = _create_project(client, owner["access_token"], "Assign Guard")
    # Grant another user reviewer (not admin) access.
    other = _register(client)
    client.post(
        f"/api/v1/projects/{project_id}/access/grant",
        headers=_headers(owner["access_token"]),
        json={"access_level": "reviewer", "user_id": other["user"]["user_id"]},
    )
    response = client.patch(
        f"/api/v1/projects/{project_id}/assignment",
        headers=_headers(other["access_token"]),
        json={"assigned_reviewer_name": "Someone"},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Regression
# ---------------------------------------------------------------------------


def test_health_and_demo_preserved(client: TestClient):
    assert client.get("/health").status_code == 200
    assert client.get(f"/api/v1/projects/{BROOKSIDE_ID}").status_code == 200


# ---------------------------------------------------------------------------
# Unit tests for safe aging and due-date helpers
# ---------------------------------------------------------------------------


def test_aging_bucket_thresholds():
    from datetime import timedelta

    from app.core.safety import ALLOWED_AGING_BUCKETS
    from app.services import operational_metrics_service as oms

    now = datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc)
    assert oms.aging_bucket(now, now=now) == "updated_today"
    assert (
        oms.aging_bucket(now - timedelta(days=2), now=now)
        == "waiting_1_to_3_days"
    )
    assert (
        oms.aging_bucket(now - timedelta(days=5), now=now)
        == "waiting_4_to_7_days"
    )
    assert (
        oms.aging_bucket(now - timedelta(days=30), now=now)
        == "waiting_more_than_7_days"
    )
    # A missing timestamp falls back to the oldest safe bucket.
    assert oms.aging_bucket(None, now=now) == "waiting_more_than_7_days"
    # A naive timestamp is treated as UTC, not rejected.
    assert oms.aging_bucket(now.replace(tzinfo=None), now=now) in (
        ALLOWED_AGING_BUCKETS
    )


def test_due_date_indicators():
    from datetime import timedelta

    from app.core.safety import ALLOWED_DUE_DATE_INDICATORS
    from app.services import operational_metrics_service as oms

    now = datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc)
    assert oms.due_date_indicators(None, now=now) == []
    soon = oms.due_date_indicators(now + timedelta(days=1), now=now)
    assert "due_date_set" in soon and "due_soon" in soon
    past = oms.due_date_indicators(now - timedelta(days=1), now=now)
    assert "past_due_for_reviewer_attention" in past
    later = oms.due_date_indicators(now + timedelta(days=30), now=now)
    assert later == ["due_date_set"]
    for indicators in (soon, past, later):
        for indicator in indicators:
            assert indicator in ALLOWED_DUE_DATE_INDICATORS
