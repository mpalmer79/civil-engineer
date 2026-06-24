"""Phase 9 reviewer workflow board tests."""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.core.safety import (
    ALLOWED_FOLLOW_UP_STATUSES,
    ALLOWED_WORKFLOW_ACTIONS,
    ALLOWED_WORKFLOW_STATUSES,
)

PROJECT_ID = "proj_brookside_meadows"

# Forbidden final-decision vocabulary that must not appear in statuses, action
# names, roles, labels, or generated output.
FORBIDDEN_WORDS = [
    "approved",
    "certified",
    "verified",
    "passed",
    "failed",
    "compliant",
    "noncompliant",
    "safe",
    "unsafe",
    "design validated",
]
_FORBIDDEN_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in FORBIDDEN_WORDS) + r")\b"
)


def _has_forbidden(text: str | None) -> bool:
    if not text:
        return False
    return bool(_FORBIDDEN_RE.search(text.lower()))


@pytest.fixture(scope="module")
def board(client: TestClient) -> list[dict]:
    response = client.post(
        f"/api/v1/projects/{PROJECT_ID}/workflow-board/generate"
    )
    assert response.status_code == 200
    return response.json()


def test_board_generation_creates_items(board: list[dict]) -> None:
    assert len(board) > 0
    for item in board:
        assert item["status"] == "draft"
        assert item["requires_human_review"] is True
        assert item["status"] in ALLOWED_WORKFLOW_STATUSES
        assert item["assigned_role"]
        assert item["section_type"]


def test_board_items_carry_evidence_types(board: list[dict]) -> None:
    # At least one promoted item should carry evidence type tags drawn from the
    # source packet item evidence links.
    assert any(item["evidence_types"] for item in board)


def test_list_with_filters(client: TestClient, board: list[dict]) -> None:
    section_type = board[0]["section_type"]
    response = client.get(
        f"/api/v1/projects/{PROJECT_ID}/workflow-board",
        params={"section_type": section_type},
    )
    assert response.status_code == 200
    items = response.json()
    assert items
    for item in items:
        assert item["section_type"] == section_type


def test_list_with_other_filters(
    client: TestClient, board: list[dict]
) -> None:
    sample = board[0]
    for key in ("severity", "assigned_role", "source_type"):
        value = sample[key]
        if value is None:
            continue
        response = client.get(
            f"/api/v1/projects/{PROJECT_ID}/workflow-board",
            params={key: value},
        )
        assert response.status_code == 200
        for item in response.json():
            assert item[key] == value


def test_unknown_project_paths(client: TestClient) -> None:
    assert (
        client.get(
            "/api/v1/projects/proj_missing/workflow-board/summary"
        ).status_code
        == 404
    )
    assert (
        client.get(
            "/api/v1/projects/proj_missing/workflow-board/ready-for-handoff"
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/projects/proj_missing/workflow-board/generate"
        ).status_code
        == 404
    )


def test_item_detail_includes_evidence_and_history(
    client: TestClient, board: list[dict]
) -> None:
    item_id = board[0]["workflow_item_id"]
    response = client.get(f"/api/v1/workflow-items/{item_id}")
    assert response.status_code == 200
    detail = response.json()
    assert detail["workflow_item_id"] == item_id
    assert "evidence_links" in detail
    assert "follow_ups" in detail
    assert "actions" in detail


def test_status_transition_records_action(
    client: TestClient, board: list[dict]
) -> None:
    item_id = board[1]["workflow_item_id"]
    response = client.patch(
        f"/api/v1/workflow-items/{item_id}/status",
        json={
            "new_status": "needs_triage",
            "reviewer_note": "Starting triage on this item.",
            "reviewer_name": "Town Engineer",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "needs_triage"

    history = client.get(
        f"/api/v1/workflow-items/{item_id}/history"
    ).json()
    action_types = {a["action_type"] for a in history["actions"]}
    assert "triage_started" in action_types
    for action in history["actions"]:
        assert action["action_type"] in ALLOWED_WORKFLOW_ACTIONS


def test_status_progression_to_handoff(
    client: TestClient, board: list[dict]
) -> None:
    item_id = board[2]["workflow_item_id"]
    for status in ["needs_triage", "reviewer_checked", "ready_for_handoff"]:
        response = client.patch(
            f"/api/v1/workflow-items/{item_id}/status",
            json={"new_status": status, "reviewer_name": "Town Engineer"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == status

    handoff = client.get(
        f"/api/v1/projects/{PROJECT_ID}/workflow-board/ready-for-handoff"
    ).json()
    ready_ids = {i["workflow_item_id"] for i in handoff["items"]}
    assert item_id in ready_ids
    assert handoff["ready_count"] >= 1


def test_add_note_records_action(
    client: TestClient, board: list[dict]
) -> None:
    item_id = board[3]["workflow_item_id"]
    response = client.post(
        f"/api/v1/workflow-items/{item_id}/notes",
        json={
            "reviewer_note": "Reviewer needs to check the basin outlet detail.",
            "reviewer_name": "Town Engineer",
        },
    )
    assert response.status_code == 200
    assert response.json()["reviewer_note"].startswith("Reviewer needs")

    actions = client.get(
        f"/api/v1/workflow-items/{item_id}/actions"
    ).json()
    assert any(a["action_type"] == "note_added" for a in actions)


def test_follow_up_request_moves_item(
    client: TestClient, board: list[dict]
) -> None:
    item_id = board[4]["workflow_item_id"]
    response = client.post(
        f"/api/v1/workflow-items/{item_id}/follow-ups",
        json={
            "requested_from": "Applicant",
            "request_reason": "Need the updated drainage report.",
            "requested_information": "Revised drainage report with basin sizing.",
            "reviewer_name": "Town Engineer",
            "target_date": "2026-07-15",
        },
    )
    assert response.status_code == 200
    follow_up = response.json()
    assert follow_up["status"] == "open"
    assert follow_up["status"] in ALLOWED_FOLLOW_UP_STATUSES

    detail = client.get(f"/api/v1/workflow-items/{item_id}").json()
    assert detail["status"] == "needs_follow_up"
    assert len(detail["follow_ups"]) >= 1

    listed = client.get(
        f"/api/v1/workflow-items/{item_id}/follow-ups"
    ).json()
    assert len(listed) >= 1


def test_summary_counts(client: TestClient, board: list[dict]) -> None:
    summary = client.get(
        f"/api/v1/projects/{PROJECT_ID}/workflow-board/summary"
    ).json()
    assert summary["total_items"] == len(board)
    assert sum(summary["items_by_status"].values()) == len(board)
    assert summary["open_follow_up_count"] >= 1
    assert summary["items_by_assigned_role"]


def test_invalid_status_rejected(
    client: TestClient, board: list[dict]
) -> None:
    item_id = board[0]["workflow_item_id"]
    response = client.patch(
        f"/api/v1/workflow-items/{item_id}/status",
        json={"new_status": "approved", "reviewer_name": "Town Engineer"},
    )
    assert response.status_code == 422


def test_draft_is_not_a_manual_transition(
    client: TestClient, board: list[dict]
) -> None:
    item_id = board[0]["workflow_item_id"]
    response = client.patch(
        f"/api/v1/workflow-items/{item_id}/status",
        json={"new_status": "draft", "reviewer_name": "Town Engineer"},
    )
    assert response.status_code == 422


def test_prohibited_note_rejected(
    client: TestClient, board: list[dict]
) -> None:
    item_id = board[0]["workflow_item_id"]
    response = client.post(
        f"/api/v1/workflow-items/{item_id}/notes",
        json={
            "reviewer_note": "This plan is approved and fully compliant.",
            "reviewer_name": "Town Engineer",
        },
    )
    assert response.status_code == 422


def test_missing_item_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/workflow-items/wfi_missing")
    assert response.status_code == 404
    response = client.patch(
        "/api/v1/workflow-items/wfi_missing/status",
        json={"new_status": "needs_triage", "reviewer_name": "Town Engineer"},
    )
    assert response.status_code == 404


def test_no_prohibited_vocabulary(
    client: TestClient, board: list[dict]
) -> None:
    for status in ALLOWED_WORKFLOW_STATUSES:
        assert not _has_forbidden(status)
    for action in ALLOWED_WORKFLOW_ACTIONS:
        assert not _has_forbidden(action)
    for follow_up_status in ALLOWED_FOLLOW_UP_STATUSES:
        assert not _has_forbidden(follow_up_status)
    for item in board:
        assert not _has_forbidden(item["status"])
        assert not _has_forbidden(item["severity"])
        assert not _has_forbidden(item["assigned_role"])
        assert not _has_forbidden(item["section_type"])
        assert not _has_forbidden(item["title"])
        assert not _has_forbidden(item["description"])
    summary = client.get(
        f"/api/v1/projects/{PROJECT_ID}/workflow-board/summary"
    ).json()
    assert not _has_forbidden(summary["note"])
    handoff = client.get(
        f"/api/v1/projects/{PROJECT_ID}/workflow-board/ready-for-handoff"
    ).json()
    assert not _has_forbidden(handoff["note"])


def test_stored_action_types_are_in_allowed_set(
    client: TestClient, board: list[dict]
) -> None:
    from app.db import models
    from app.db.database import SessionLocal

    db = SessionLocal()
    try:
        actions = db.query(models.WorkflowAction).all()
        assert actions
        for action in actions:
            assert action.action_type in ALLOWED_WORKFLOW_ACTIONS
    finally:
        db.close()


def test_audit_events_written(client: TestClient, board: list[dict]) -> None:
    item_id = board[0]["workflow_item_id"]
    client.get(f"/api/v1/workflow-items/{item_id}")
    client.get(f"/api/v1/workflow-items/{item_id}/history")
    client.get(f"/api/v1/projects/{PROJECT_ID}/workflow-board/summary")
    client.get(
        f"/api/v1/projects/{PROJECT_ID}/workflow-board/ready-for-handoff"
    )
    events = client.get(
        f"/api/v1/projects/{PROJECT_ID}/audit-events"
    ).json()
    types = {e["event_type"] for e in events}
    assert "workflow_board_generated" in types
    assert "workflow_item_viewed" in types
    assert "workflow_item_status_updated" in types
    assert "workflow_note_added" in types
    assert "workflow_follow_up_requested" in types
    assert "workflow_item_history_requested" in types
    assert "workflow_board_summary_requested" in types
    assert "workflow_ready_for_handoff_requested" in types
