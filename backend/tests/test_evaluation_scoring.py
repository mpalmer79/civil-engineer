"""Phase 5 evaluation scoring tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

PROJECT_ID = "proj_brookside_meadows"


@pytest.fixture(scope="module")
def ai_run(client: TestClient) -> dict:
    response = client.post(f"/api/v1/projects/{PROJECT_ID}/ai-review-runs")
    assert response.status_code == 200
    return response.json()


@pytest.fixture(scope="module")
def evaluation(client: TestClient, ai_run: dict) -> dict:
    response = client.post(
        f"/api/v1/ai-review-runs/{ai_run['review_run_id']}/evaluate"
    )
    assert response.status_code == 200
    return response.json()


def test_evaluation_runs_for_review_run(evaluation: dict) -> None:
    assert evaluation["evaluation_result_id"]
    assert evaluation["review_run_id"]


def test_evaluation_result_persisted(
    client: TestClient, evaluation: dict
) -> None:
    result_id = evaluation["evaluation_result_id"]
    response = client.get(f"/api/v1/ai-evaluation-results/{result_id}")
    assert response.status_code == 200
    assert response.json()["evaluation_result_id"] == result_id
    assert response.json()["matches"]


def test_evaluation_calculates_recall_and_precision(evaluation: dict) -> None:
    assert 0.0 <= evaluation["recall"] <= 1.0
    assert 0.0 <= evaluation["precision"] <= 1.0
    # The mock provider produces planted-issue drafts, so several expected
    # findings should match.
    assert evaluation["matched_findings_count"] >= 5
    assert evaluation["recall"] > 0.0


def test_evaluation_checks_citation_validity(evaluation: dict) -> None:
    # Valid drafts cite retrieved chunks, so citation validity should be high.
    assert evaluation["citation_validity_rate"] >= 0.9
    assert evaluation["human_review_required_rate"] >= 0.0


def test_evaluation_counts_failures(evaluation: dict) -> None:
    assert evaluation["validation_failure_count"] >= 0
    assert evaluation["safety_failure_count"] >= 0
    assert evaluation["prohibited_word_count"] == 0


def test_evaluation_counts_match_totals(evaluation: dict) -> None:
    expected = evaluation["expected_findings_count"]
    matched = evaluation["matched_findings_count"]
    unmatched = evaluation["unmatched_expected_count"]
    assert matched + unmatched == expected


def test_evaluation_writes_audit_events(
    client: TestClient, evaluation: dict
) -> None:
    events = client.get(
        f"/api/v1/projects/{PROJECT_ID}/audit-events"
    ).json()
    types = {e["event_type"] for e in events}
    assert "evaluation_scoring_started" in types
    assert "evaluation_scoring_completed" in types
    assert "evaluation_match_created" in types


def test_get_run_evaluation_endpoint(
    client: TestClient, ai_run: dict, evaluation: dict
) -> None:
    response = client.get(
        f"/api/v1/ai-review-runs/{ai_run['review_run_id']}/evaluation"
    )
    assert response.status_code == 200
    assert response.json()["review_run_id"] == ai_run["review_run_id"]


def test_project_evaluation_results_endpoint(
    client: TestClient, evaluation: dict
) -> None:
    response = client.get(
        f"/api/v1/projects/{PROJECT_ID}/ai-evaluation-results"
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_evaluate_unknown_run_returns_404(client: TestClient) -> None:
    response = client.post("/api/v1/ai-review-runs/airun_missing/evaluate")
    assert response.status_code == 404
