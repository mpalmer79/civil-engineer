"""Phase 14 reviewer command center and project health dashboard tests.

These tests exercise command center snapshot generation, health metrics,
reviewer attention items aggregated from multiple modules, the project timeline,
readiness checks, reviewer notes, next steps, module links, and the health
summary. The dashboard aggregates review-support data and never approves plans,
certifies compliance, verifies CAD, validates design, or closes or resolves
issues. No status uses final-decision language.
"""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.core.safety import (
    ALLOWED_ATTENTION_ITEM_STATUSES,
    ALLOWED_COMMAND_CENTER_STATUSES,
    ALLOWED_DASHBOARD_SEVERITIES,
    ALLOWED_READINESS_STATUSES,
)

PROJECT_ID = "proj_brookside_meadows"

FORBIDDEN_WORDS = [
    "approved",
    "certified",
    "verified",
    "passed",
    "compliant",
    "noncompliant",
    "unsafe",
    "design validated",
    "resolved",
    "closed",
    "complete",
    "completed",
]
_FORBIDDEN_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in FORBIDDEN_WORDS) + r")\b"
)


def _has_forbidden(text: str | None) -> bool:
    if not text:
        return False
    return bool(_FORBIDDEN_RE.search(text.lower()))


def _parse_sample(client: TestClient, sample_key: str) -> str:
    created = client.post(
        f"/api/v1/projects/{PROJECT_ID}/cad-files",
        json={"sample_key": sample_key, "uploaded_by": "Town Engineer"},
    ).json()
    run = client.post(
        f"/api/v1/cad-files/{created['cad_file_id']}/parse"
    ).json()
    return run["parse_run_id"]


@pytest.fixture(scope="module")
def state(client: TestClient) -> dict:
    """Set up multi-module state, then generate a command center snapshot."""

    # Transition a workflow item to needs_follow_up.
    board = client.get(
        f"/api/v1/projects/{PROJECT_ID}/workflow-board"
    ).json()
    workflow_item_id = board[0]["workflow_item_id"]
    client.patch(
        f"/api/v1/workflow-items/{workflow_item_id}/status",
        json={
            "new_status": "needs_follow_up",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "Confirm basin detail.",
        },
    )

    # Review cycle and two parsed DXF rounds for a revision comparison.
    cycle_id = client.get(
        f"/api/v1/projects/{PROJECT_ID}/review-cycles"
    ).json()[0]["review_cycle_id"]
    previous_run = client.get(
        f"/api/v1/projects/{PROJECT_ID}/cad-parse-runs"
    ).json()[0]["parse_run_id"]
    current_run = _parse_sample(client, "brookside_meadows_r2")
    comparison = client.post(
        f"/api/v1/review-cycles/{cycle_id}/revision-comparisons",
        json={
            "previous_parse_run_id": previous_run,
            "current_parse_run_id": current_run,
        },
    ).json()

    # A resubmittal that still needs comparison.
    resubmittal = client.post(
        f"/api/v1/projects/{PROJECT_ID}/resubmittals",
        json={"review_cycle_id": cycle_id, "package_name": "Resubmittal A"},
    ).json()

    # An applicant response with no mapping.
    client.post(
        f"/api/v1/resubmittals/{resubmittal['resubmittal_package_id']}/applicant-responses",
        json={
            "response_text": "Updated grading per the comment.",
            "response_topic": "grading",
        },
    )

    snapshot = client.post(
        f"/api/v1/projects/{PROJECT_ID}/command-center/snapshot"
    ).json()
    return {
        "snapshot": snapshot,
        "cycle_id": cycle_id,
        "comparison_run_id": comparison["comparison_run_id"],
        "workflow_item_id": workflow_item_id,
    }


def test_snapshot_generation(state: dict) -> None:
    snapshot = state["snapshot"]
    assert snapshot["overall_status"] in ALLOWED_COMMAND_CENTER_STATUSES
    assert snapshot["attention_count"] >= 1
    assert snapshot["requires_human_review"] is True
    assert not _has_forbidden(snapshot["summary"])


def test_latest_snapshot(client: TestClient, state: dict) -> None:
    latest = client.get(
        f"/api/v1/projects/{PROJECT_ID}/command-center/latest"
    ).json()
    assert latest["snapshot_id"] == state["snapshot"]["snapshot_id"]


def test_command_center_payload(client: TestClient, state: dict) -> None:
    payload = client.get(
        f"/api/v1/projects/{PROJECT_ID}/command-center"
    ).json()
    assert payload["snapshot"]["snapshot_id"]
    assert payload["health_metrics"]
    assert payload["attention_items"]
    assert payload["timeline"]
    assert payload["readiness_checks"]
    assert payload["next_steps"]["steps"]
    assert payload["module_links"]["links"]
    assert not _has_forbidden(payload["limitations_note"])


def test_health_metrics_from_multiple_modules(
    client: TestClient, state: dict
) -> None:
    metrics = client.get(
        f"/api/v1/projects/{PROJECT_ID}/command-center/health-metrics"
    ).json()
    modules = {m["source_module"] for m in metrics}
    assert "workflow_board" in modules
    assert "cad_intake" in modules
    assert "review_cycles" in modules
    for metric in metrics:
        assert metric["severity"] in ALLOWED_DASHBOARD_SEVERITIES


def test_attention_items_from_modules(client: TestClient, state: dict) -> None:
    items = client.get(
        f"/api/v1/projects/{PROJECT_ID}/command-center/attention-items"
    ).json()
    types = {i["attention_type"] for i in items}
    assert "workflow_item_needs_follow_up" in types
    assert "cad_finding_unpromoted" in types
    assert "applicant_response_needs_mapping" in types
    assert "resubmittal_needs_comparison" in types
    assert "revision_change_needs_review" in types


def test_duplicate_attention_prevention(client: TestClient, state: dict) -> None:
    client.post(f"/api/v1/projects/{PROJECT_ID}/command-center/snapshot")
    items = client.get(
        f"/api/v1/projects/{PROJECT_ID}/command-center/attention-items"
    ).json()
    keys = [(i["source_type"], i["source_id"]) for i in items]
    assert len(keys) == len(set(keys))


def test_attention_status_update(client: TestClient, state: dict) -> None:
    items = client.get(
        f"/api/v1/projects/{PROJECT_ID}/command-center/attention-items"
    ).json()
    target = items[0]["attention_item_id"]
    updated = client.patch(
        f"/api/v1/command-center/attention-items/{target}/status",
        json={"status": "reviewer_checked", "reviewer_name": "Town Engineer"},
    ).json()
    assert updated["status"] == "reviewer_checked"
    assert updated["status"] in ALLOWED_ATTENTION_ITEM_STATUSES

    bad = client.patch(
        f"/api/v1/command-center/attention-items/{target}/status",
        json={"status": "approved"},
    )
    assert bad.status_code == 422


def test_attention_status_persists_across_regeneration(
    client: TestClient, state: dict
) -> None:
    # The reviewer_checked status set above should survive a regenerate, since
    # status is preserved by source. Open items drop out of the default view.
    client.post(f"/api/v1/projects/{PROJECT_ID}/command-center/snapshot")
    checked = client.get(
        f"/api/v1/projects/{PROJECT_ID}/command-center/attention-items?status=reviewer_checked"
    ).json()
    assert len(checked) >= 1


def test_timeline(client: TestClient, state: dict) -> None:
    timeline = client.get(
        f"/api/v1/projects/{PROJECT_ID}/command-center/timeline"
    ).json()
    types = {e["event_type"] for e in timeline}
    assert "cad_parse_completed" in types
    assert "revision_comparison_completed" in types
    assert "resubmittal_received" in types
    for event in timeline:
        assert not _has_forbidden(event["event_title"])


def test_readiness_checks(client: TestClient, state: dict) -> None:
    checks = client.get(
        f"/api/v1/projects/{PROJECT_ID}/command-center/readiness-checks"
    ).json()
    assert len(checks) >= 5
    for check in checks:
        assert check["status"] in ALLOWED_READINESS_STATUSES
        assert not _has_forbidden(check["status"])
        assert not _has_forbidden(check["label"])
    # Human review signoff is always required and never marked complete.
    signoff = [c for c in checks if c["check_type"] == "human_review_signoff"]
    assert signoff and signoff[0]["status"] == "ready_for_human_review"


def test_reviewer_notes(client: TestClient, state: dict) -> None:
    note = client.post(
        f"/api/v1/projects/{PROJECT_ID}/command-center/notes",
        json={
            "note_text": "Coordinate the basin detail with the design engineer.",
            "reviewer_name": "Town Engineer",
            "source_context": "attention",
        },
    ).json()
    assert note["note_id"]
    notes = client.get(
        f"/api/v1/projects/{PROJECT_ID}/command-center/notes"
    ).json()
    assert any(n["note_id"] == note["note_id"] for n in notes)


def test_next_steps(client: TestClient, state: dict) -> None:
    steps = client.get(
        f"/api/v1/projects/{PROJECT_ID}/command-center/next-steps"
    ).json()
    assert steps["steps"]
    for step in steps["steps"]:
        assert step["target_route"].startswith("/")
        assert step["severity"] in ALLOWED_DASHBOARD_SEVERITIES
        assert not _has_forbidden(step["title"])


def test_module_links(client: TestClient, state: dict) -> None:
    links = client.get(
        f"/api/v1/projects/{PROJECT_ID}/command-center/module-links"
    ).json()
    modules = {link["module"] for link in links["links"]}
    assert "cad_intake" in modules
    assert "review_cycles" in modules
    assert "workflow_board" in modules
    assert "response_package" in modules


def test_health_summary(client: TestClient, state: dict) -> None:
    summary = client.get(
        f"/api/v1/projects/{PROJECT_ID}/command-center/health-summary"
    ).json()
    assert summary["overall_status"] in ALLOWED_COMMAND_CENTER_STATUSES
    assert summary["readiness_ready_count"] >= 1
    assert not _has_forbidden(summary["summary"])
    assert not _has_forbidden(summary["limitations_note"])


def test_no_prohibited_vocabulary(client: TestClient, state: dict) -> None:
    for status in (
        ALLOWED_COMMAND_CENTER_STATUSES
        | ALLOWED_ATTENTION_ITEM_STATUSES
        | ALLOWED_READINESS_STATUSES
        | ALLOWED_DASHBOARD_SEVERITIES
    ):
        assert not _has_forbidden(status), status

    payload = client.get(
        f"/api/v1/projects/{PROJECT_ID}/command-center"
    ).json()
    for item in payload["attention_items"]:
        assert not _has_forbidden(item["title"])
        assert not _has_forbidden(item["recommended_next_step"])
        assert not _has_forbidden(item["status"])
        assert not _has_forbidden(item["attention_type"])
    for metric in payload["health_metrics"]:
        assert not _has_forbidden(metric["label"])
    for check in payload["readiness_checks"]:
        assert not _has_forbidden(check["recommended_next_step"])


def test_audit_events_written(client: TestClient, state: dict) -> None:
    client.get(f"/api/v1/projects/{PROJECT_ID}/command-center")
    client.get(f"/api/v1/projects/{PROJECT_ID}/command-center/timeline")
    client.get(f"/api/v1/projects/{PROJECT_ID}/command-center/next-steps")
    client.get(f"/api/v1/projects/{PROJECT_ID}/command-center/module-links")
    client.get(f"/api/v1/projects/{PROJECT_ID}/command-center/health-summary")
    events = client.get(
        f"/api/v1/projects/{PROJECT_ID}/audit-events"
    ).json()
    types = {e["event_type"] for e in events}
    for expected in [
        "command_center_snapshot_generated",
        "command_center_viewed",
        "command_center_attention_status_changed",
        "command_center_note_added",
        "command_center_timeline_viewed",
        "command_center_next_steps_viewed",
        "command_center_module_links_viewed",
        "command_center_health_summary_viewed",
    ]:
        assert expected in types, expected


def test_missing_project_returns_404(client: TestClient) -> None:
    response = client.get(
        "/api/v1/projects/proj_missing/command-center"
    )
    assert response.status_code == 404
