"""Safety vocabulary and human-review guarantees.

These tests enforce the professional boundary at the data layer: statuses must
come from the allowed review vocabulary, no status or finding conclusion may use
prohibited final-decision language, and every finding must remain under human
review.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.safety import (
    HUMAN_REVIEW_STATUSES,
    PROHIBITED_FINAL_DECISION_WORDS,
    contains_prohibited_language,
    is_allowed_status,
)

PROJECT_ID = "proj_brookside_meadows"


def test_prohibited_words_constant_is_intact() -> None:
    # Guard against accidental edits that would weaken the boundary.
    for word in ("approved", "certified", "fully compliant", "safe"):
        assert word in PROHIBITED_FINAL_DECISION_WORDS


def test_checklist_statuses_are_allowed_and_clean(client: TestClient) -> None:
    items = client.get(f"/api/v1/projects/{PROJECT_ID}/checklist").json()
    for item in items:
        status = item["expected_status_for_brookside_meadows"]
        assert is_allowed_status(status), status
        assert not contains_prohibited_language(status), status


def test_finding_statuses_are_clean(client: TestClient) -> None:
    findings = client.get(f"/api/v1/projects/{PROJECT_ID}/findings").json()
    for finding in findings:
        assert not contains_prohibited_language(finding["expected_status"])
        assert not contains_prohibited_language(finding["human_review_status"])
        assert not contains_prohibited_language(finding["title"])


def test_every_finding_requires_human_review(client: TestClient) -> None:
    findings = client.get(f"/api/v1/projects/{PROJECT_ID}/findings").json()
    assert len(findings) == 10
    for finding in findings:
        assert finding["human_review_status"] in HUMAN_REVIEW_STATUSES


def test_evaluation_reports_zero_prohibited_wording(client: TestClient) -> None:
    cases = client.get("/api/v1/evaluation-cases").json()
    for case in cases:
        assert case["seeded_result"]["prohibited_wording_count"] == 0
