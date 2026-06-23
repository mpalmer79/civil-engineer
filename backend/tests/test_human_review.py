"""Phase 5 human review queue and review action tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.db import models

PROJECT_ID = "proj_brookside_meadows"


@pytest.fixture(scope="module")
def review_run(client: TestClient) -> dict:
    response = client.post(f"/api/v1/projects/{PROJECT_ID}/ai-review-runs")
    assert response.status_code == 200
    return response.json()


def _valid_drafts(client: TestClient, review_run_id: str) -> list[dict]:
    drafts = client.get(
        f"/api/v1/ai-review-runs/{review_run_id}/draft-findings"
    ).json()
    return [d for d in drafts if d["validation_status"] == "validation_passed"]


def _insert_failed_draft(review_run_id: str, draft_finding_id: str) -> None:
    """Insert a validation-failed draft finding for the run."""

    db = SessionLocal()
    try:
        db.add(
            models.AIDraftFinding(
                draft_finding_id=draft_finding_id,
                review_run_id=review_run_id,
                project_id=PROJECT_ID,
                checklist_item_id="chk_infiltration_testing",
                finding_type="requires_human_review",
                title="Draft finding failed validation",
                summary="This draft output failed validation.",
                risk_level="low",
                confidence=0.0,
                status="validation_failed",
                recommended_human_action="Discard or regenerate.",
                source_chunk_ids=[],
                validation_status="validation_failed",
                safety_check_status="safety_check_failed",
                validation_errors=["safety: no source_chunk_ids cited."],
            )
        )
        db.commit()
    finally:
        db.close()


def test_human_review_queue_returns_drafts(
    client: TestClient, review_run: dict
) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}/human-review-queue")
    assert response.status_code == 200
    queue = response.json()
    assert queue["project_id"] == PROJECT_ID
    assert queue["needs_review_count"] >= 1
    assert len(queue["needs_review"]) == queue["needs_review_count"]
    first = queue["needs_review"][0]
    assert first["draft_finding"]["status"] == "requires_human_review"
    assert first["needs_review"] is True


def test_accept_valid_draft_finding(
    client: TestClient, review_run: dict
) -> None:
    drafts = _valid_drafts(client, review_run["review_run_id"])
    target = drafts[0]
    response = client.post(
        f"/api/v1/draft-findings/{target['draft_finding_id']}/review-actions",
        json={
            "action": "accepted",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "Evidence gap confirmed against the submitted package.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["review_action"]["action"] == "accepted"
    assert body["review_action"]["new_status"] == "accepted_by_reviewer"
    assert body["draft_finding"]["status"] == "accepted_by_reviewer"


def test_edit_valid_draft_finding(
    client: TestClient, review_run: dict
) -> None:
    drafts = _valid_drafts(client, review_run["review_run_id"])
    target = drafts[1]
    response = client.post(
        f"/api/v1/draft-findings/{target['draft_finding_id']}/review-actions",
        json={
            "action": "edited",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "Clarified the recommended follow-up wording.",
            "edited_summary": (
                "Based on the submitted documents, this is a potential issue "
                "that needs human review and reviewer confirmation."
            ),
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["review_action"]["action"] == "edited"
    assert body["draft_finding"]["status"] == "edited_by_reviewer"
    assert "needs human review" in body["draft_finding"]["summary"]


def test_reject_draft_finding(client: TestClient, review_run: dict) -> None:
    drafts = _valid_drafts(client, review_run["review_run_id"])
    target = drafts[2]
    response = client.post(
        f"/api/v1/draft-findings/{target['draft_finding_id']}/review-actions",
        json={
            "action": "rejected",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "Not relevant.",
        },
    )
    assert response.status_code == 200
    assert response.json()["draft_finding"]["status"] == "rejected_by_reviewer"


def test_failed_draft_cannot_be_accepted(
    client: TestClient, review_run: dict
) -> None:
    failed_id = f"draft_failed_{review_run['review_run_id'][6:]}"
    _insert_failed_draft(review_run["review_run_id"], failed_id)
    response = client.post(
        f"/api/v1/draft-findings/{failed_id}/review-actions",
        json={
            "action": "accepted",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "Attempting to accept a failed draft.",
        },
    )
    assert response.status_code == 422
    assert "failed draft finding cannot be" in response.json()["detail"].lower()

    # A failed draft can still be escalated.
    escalate = client.post(
        f"/api/v1/draft-findings/{failed_id}/review-actions",
        json={
            "action": "escalated",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "Escalating the failed draft for regeneration.",
        },
    )
    assert escalate.status_code == 200
    assert escalate.json()["draft_finding"]["status"] == "escalated"


def test_edited_finding_with_prohibited_wording_fails(
    client: TestClient, review_run: dict
) -> None:
    drafts = _valid_drafts(client, review_run["review_run_id"])
    target = drafts[3]
    response = client.post(
        f"/api/v1/draft-findings/{target['draft_finding_id']}/review-actions",
        json={
            "action": "edited",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "Trying to mark this approved.",
            "edited_summary": "The design is fully compliant and approved.",
        },
    )
    assert response.status_code == 422
    assert "prohibited" in response.json()["detail"].lower()

    # The status must not have changed.
    after = client.get(
        f"/api/v1/draft-findings/{target['draft_finding_id']}"
    ).json()
    assert after["status"] == "requires_human_review"


def test_review_action_requires_note(
    client: TestClient, review_run: dict
) -> None:
    drafts = _valid_drafts(client, review_run["review_run_id"])
    target = drafts[4]
    response = client.post(
        f"/api/v1/draft-findings/{target['draft_finding_id']}/review-actions",
        json={
            "action": "marked_unclear",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "",
        },
    )
    assert response.status_code == 422
    assert "reviewer note" in response.json()["detail"].lower()


def test_review_action_history_returned(
    client: TestClient, review_run: dict
) -> None:
    drafts = _valid_drafts(client, review_run["review_run_id"])
    target = drafts[0]
    response = client.get(
        f"/api/v1/draft-findings/{target['draft_finding_id']}/review-actions"
    )
    assert response.status_code == 200
    history = response.json()
    assert len(history) >= 1
    assert history[0]["draft_finding_id"] == target["draft_finding_id"]

    project_actions = client.get(
        f"/api/v1/projects/{PROJECT_ID}/review-actions"
    ).json()
    assert len(project_actions) >= 1


def test_review_actions_write_audit_events(
    client: TestClient, review_run: dict
) -> None:
    events = client.get(f"/api/v1/projects/{PROJECT_ID}/audit-events").json()
    types = {e["event_type"] for e in events}
    assert "human_review_action_started" in types
    assert "human_review_action_recorded" in types
    assert "draft_finding_status_updated" in types


def test_unknown_action_rejected(client: TestClient, review_run: dict) -> None:
    drafts = _valid_drafts(client, review_run["review_run_id"])
    target = drafts[5]
    response = client.post(
        f"/api/v1/draft-findings/{target['draft_finding_id']}/review-actions",
        json={
            "action": "approved",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "Trying a prohibited action name.",
        },
    )
    assert response.status_code == 422
