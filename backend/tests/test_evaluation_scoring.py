"""Phase 5 evaluation scoring tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.db import models

PROJECT_ID = "proj_brookside_meadows"


@pytest.fixture(scope="module")
def evaluated_run(client: TestClient) -> dict:
    """Create a review run, inject one failed draft, then evaluate it."""

    run = client.post(
        f"/api/v1/projects/{PROJECT_ID}/ai-review-runs"
    ).json()
    review_run_id = run["review_run_id"]

    db = SessionLocal()
    try:
        db.add(
            models.AIDraftFinding(
                draft_finding_id=f"draft_failed_eval_{review_run_id[6:]}",
                review_run_id=review_run_id,
                project_id=PROJECT_ID,
                checklist_item_id="chk_downstream_capacity",
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

    result = client.post(f"/api/v1/ai-review-runs/{review_run_id}/evaluate")
    assert result.status_code == 200
    payload = result.json()
    payload["_review_run_id"] = review_run_id
    return payload


def test_evaluation_runs_and_stores_result(evaluated_run: dict) -> None:
    assert evaluated_run["evaluation_result_id"].startswith("eval_")
    assert evaluated_run["review_run_id"] == evaluated_run["_review_run_id"]


def test_evaluation_result_is_retrievable(
    client: TestClient, evaluated_run: dict
) -> None:
    result_id = evaluated_run["evaluation_result_id"]
    by_id = client.get(f"/api/v1/ai-evaluation-results/{result_id}")
    assert by_id.status_code == 200
    assert by_id.json()["evaluation_result_id"] == result_id

    by_run = client.get(
        f"/api/v1/ai-review-runs/{evaluated_run['_review_run_id']}/evaluation"
    )
    assert by_run.status_code == 200
    assert by_run.json()["evaluation_result_id"] == result_id

    project_results = client.get(
        f"/api/v1/projects/{PROJECT_ID}/ai-evaluation-results"
    )
    assert project_results.status_code == 200
    ids = {r["evaluation_result_id"] for r in project_results.json()}
    assert result_id in ids


def test_evaluation_calculates_recall_and_precision(evaluated_run: dict) -> None:
    assert evaluated_run["expected_findings_count"] == 10
    assert evaluated_run["draft_findings_count"] >= 5
    assert evaluated_run["matched_findings_count"] >= 5
    assert 0.0 <= evaluated_run["recall"] <= 1.0
    assert 0.0 <= evaluated_run["precision"] <= 1.0
    # Every planted issue maps to a checklist item the mock provider covers, so
    # recall should be strong.
    assert evaluated_run["recall"] >= 0.5


def test_evaluation_validates_source_citations(evaluated_run: dict) -> None:
    # All valid mock drafts cite chunk ids drawn from retrieved evidence.
    assert evaluated_run["citation_validity_rate"] == 1.0


def test_evaluation_counts_validation_and_safety_failures(
    evaluated_run: dict,
) -> None:
    # The injected failed draft must be counted, and never as a match.
    assert evaluated_run["validation_failure_count"] >= 1
    assert evaluated_run["safety_failure_count"] >= 1
    assert evaluated_run["prohibited_word_count"] == 0
    assert evaluated_run["human_review_required_rate"] == 1.0


def test_evaluation_match_records_present(evaluated_run: dict) -> None:
    matches = evaluated_run["matches"]
    assert len(matches) >= 1
    types = {m["match_type"] for m in matches}
    assert types & {
        "related_checklist_match",
        "exact_category_match",
        "title_similarity_match",
    }
    matched = [m for m in matches if m["draft_finding_id"] and m["expected_finding_id"]]
    assert matched


def test_evaluation_writes_audit_events(
    client: TestClient, evaluated_run: dict
) -> None:
    events = client.get(f"/api/v1/projects/{PROJECT_ID}/audit-events").json()
    types = {e["event_type"] for e in events}
    assert "evaluation_scoring_started" in types
    assert "evaluation_match_created" in types
    assert "evaluation_scoring_completed" in types


def test_evaluate_unknown_run_returns_404(client: TestClient) -> None:
    response = client.post("/api/v1/ai-review-runs/airun_does_not_exist/evaluate")
    assert response.status_code == 404


def test_overall_score_in_range(evaluated_run: dict) -> None:
    assert 0.0 <= evaluated_run["overall_score"] <= 1.0
