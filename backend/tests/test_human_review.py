"""Phase 5 human review queue and review action tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

PROJECT_ID = "proj_brookside_meadows"


@pytest.fixture(scope="module")
def ai_run(client: TestClient) -> dict:
    response = client.post(f"/api/v1/projects/{PROJECT_ID}/ai-review-runs")
    assert response.status_code == 200
    return response.json()


def _drafts(client: TestClient, run_id: str) -> list[dict]:
    return client.get(f"/api/v1/ai-review-runs/{run_id}/draft-findings").json()


def _first_valid(client: TestClient, run_id: str) -> dict:
    drafts = _drafts(client, run_id)
    valid = [d for d in drafts if d["validation_status"] == "validation_passed"]
    assert valid
    return valid[0]


def test_human_review_queue_returns_drafts(
    client: TestClient, ai_run: dict
) -> None:
    response = client.get(
        f"/api/v1/projects/{PROJECT_ID}/human-review-queue"
    )
    assert response.status_code == 200
    queue = response.json()
    assert len(queue) >= 5
    statuses = {d["status"] for d in queue}
    assert "requires_human_review" in statuses


def test_review_action_accepts_valid_draft(
    client: TestClient, ai_run: dict
) -> None:
    draft = _first_valid(client, ai_run["review_run_id"])
    response = client.post(
        f"/api/v1/draft-findings/{draft['draft_finding_id']}/review-actions",
        json={
            "action": "accepted",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "Evidence inspected; route to comment letter.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["action"]["action"] == "accepted"
    assert body["draft_finding"]["status"] == "accepted_by_reviewer"
    assert body["action"]["previous_status"] == "requires_human_review"


def test_review_action_edits_valid_draft(
    client: TestClient, ai_run: dict
) -> None:
    drafts = _drafts(client, ai_run["review_run_id"])
    valid = [d for d in drafts if d["validation_status"] == "validation_passed"]
    draft = valid[1]
    response = client.post(
        f"/api/v1/draft-findings/{draft['draft_finding_id']}/review-actions",
        json={
            "action": "edited",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "Tightened the summary wording.",
            "edited_summary": (
                "Based on the submitted documents, this is a potential issue "
                "that requires reviewer confirmation."
            ),
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["draft_finding"]["status"] == "edited_by_reviewer"
    assert "requires reviewer confirmation" in body["draft_finding"]["summary"]


def test_review_action_rejects_draft(
    client: TestClient, ai_run: dict
) -> None:
    drafts = _drafts(client, ai_run["review_run_id"])
    valid = [d for d in drafts if d["validation_status"] == "validation_passed"]
    draft = valid[2]
    response = client.post(
        f"/api/v1/draft-findings/{draft['draft_finding_id']}/review-actions",
        json={
            "action": "rejected",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "Duplicate of another finding.",
        },
    )
    assert response.status_code == 200
    assert response.json()["draft_finding"]["status"] == "rejected_by_reviewer"


def test_review_action_requires_reviewer_note(
    client: TestClient, ai_run: dict
) -> None:
    draft = _first_valid(client, ai_run["review_run_id"])
    response = client.post(
        f"/api/v1/draft-findings/{draft['draft_finding_id']}/review-actions",
        json={
            "action": "escalated",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "   ",
        },
    )
    assert response.status_code == 422


def test_edited_finding_with_prohibited_wording_fails(
    client: TestClient, ai_run: dict
) -> None:
    drafts = _drafts(client, ai_run["review_run_id"])
    valid = [d for d in drafts if d["validation_status"] == "validation_passed"]
    draft = valid[3]
    response = client.post(
        f"/api/v1/draft-findings/{draft['draft_finding_id']}/review-actions",
        json={
            "action": "edited",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "Attempting prohibited wording.",
            "edited_summary": "The design is fully compliant and approved.",
        },
    )
    assert response.status_code == 422
    assert "prohibited" in response.json()["detail"].lower()


def test_failed_draft_cannot_be_accepted(client: TestClient) -> None:
    # Force-create a run and locate a failed draft. The seeded chunks ensure at
    # least the items without retrievable evidence fail citation validation, but
    # to be robust we look for any validation_failed draft for the project.
    drafts = client.get(
        f"/api/v1/projects/{PROJECT_ID}/draft-findings"
    ).json()
    failed = [d for d in drafts if d["validation_status"] == "validation_failed"]
    if not failed:
        pytest.skip("No failed draft finding available in seed run.")
    draft = failed[0]
    response = client.post(
        f"/api/v1/draft-findings/{draft['draft_finding_id']}/review-actions",
        json={
            "action": "accepted",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "Should not be allowed.",
        },
    )
    assert response.status_code == 409


def test_failed_draft_rule_at_service_level() -> None:
    # Deterministic check of the rule that a failed draft can be rejected,
    # escalated, or marked unclear, but never accepted or edited. A failed draft
    # is created directly so the test does not depend on mock provider output.
    from app.db.database import SessionLocal
    from app.db import models
    from app.services import human_review_service
    from app.services.human_review_service import ReviewActionError

    db = SessionLocal()
    try:
        draft_id = "draft_test_failed_rule"
        db.add(
            models.AIDraftFinding(
                draft_finding_id=draft_id,
                review_run_id="airun_test_failed",
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
                safety_check_status="safety_check_passed",
                validation_errors=["safety: no source_chunk_ids cited."],
            )
        )
        db.commit()

        with pytest.raises(ReviewActionError) as accepted_exc:
            human_review_service.apply_review_action(
                db,
                draft_finding_id=draft_id,
                action="accepted",
                reviewer_name="Town Engineer",
                reviewer_note="Should be rejected by the rule.",
            )
        assert accepted_exc.value.status_code == 409

        action, draft = human_review_service.apply_review_action(
            db,
            draft_finding_id=draft_id,
            action="rejected",
            reviewer_name="Town Engineer",
            reviewer_note="Failed draft, discarding.",
        )
        assert draft.status == "rejected_by_reviewer"
        assert action.action == "rejected"
    finally:
        db.close()


def test_review_action_history_returned(
    client: TestClient, ai_run: dict
) -> None:
    draft = _first_valid(client, ai_run["review_run_id"])
    history = client.get(
        f"/api/v1/draft-findings/{draft['draft_finding_id']}/review-actions"
    )
    assert history.status_code == 200
    assert len(history.json()) >= 1


def test_review_action_writes_audit_events(
    client: TestClient, ai_run: dict
) -> None:
    events = client.get(
        f"/api/v1/projects/{PROJECT_ID}/audit-events"
    ).json()
    types = {e["event_type"] for e in events}
    assert "human_review_action_started" in types
    assert "human_review_action_recorded" in types
    assert "draft_finding_status_updated" in types


def test_project_review_actions_endpoint(
    client: TestClient, ai_run: dict
) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}/review-actions")
    assert response.status_code == 200
    assert len(response.json()) >= 1
