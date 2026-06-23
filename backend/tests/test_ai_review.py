"""Phase 4 AI Review Assistant tests (mock provider)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.ai.validators import validate_ai_output

PROJECT_ID = "proj_brookside_meadows"

ALLOWED = {"chunk_swm_001", "chunk_muni_002"}


def _valid_raw() -> dict:
    return {
        "checklist_item_id": "chk_design_storm_consistent",
        "finding_type": "conflicting_evidence",
        "title": "Design storm assumption may conflict with the town standard",
        "summary": "Based on the submitted documents, the events appear to differ.",
        "risk_level": "high",
        "confidence": 0.8,
        "source_chunk_ids": ["chunk_swm_001"],
        "recommended_human_action": "Confirm the applicable town standard.",
        "requires_human_review": True,
        "safety_boundary_acknowledged": True,
    }


@pytest.fixture(scope="module")
def ai_run(client: TestClient) -> dict:
    response = client.post(f"/api/v1/projects/{PROJECT_ID}/ai-review-runs")
    assert response.status_code == 200
    return response.json()


def test_provider_mode_is_mock(client: TestClient) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}/ai-provider-mode")
    assert response.status_code == 200
    assert response.json()["provider"] == "mock"


def test_ai_review_run_starts_with_mock(ai_run: dict) -> None:
    assert ai_run["provider"] == "mock"
    assert ai_run["status"] == "completed"
    assert ai_run["checklist_item_count"] == 19


def test_ai_review_run_record_exists(client: TestClient, ai_run: dict) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}/ai-review-runs")
    assert response.status_code == 200
    ids = {r["review_run_id"] for r in response.json()}
    assert ai_run["review_run_id"] in ids


def test_mock_returns_structured_draft_findings(
    client: TestClient, ai_run: dict
) -> None:
    response = client.get(
        f"/api/v1/ai-review-runs/{ai_run['review_run_id']}/draft-findings"
    )
    assert response.status_code == 200
    drafts = response.json()
    valid = [d for d in drafts if d["validation_status"] == "validation_passed"]
    assert len(valid) >= 5
    assert ai_run["draft_findings_created"] >= 5


def test_draft_findings_pass_schema_validation(
    client: TestClient, ai_run: dict
) -> None:
    drafts = client.get(
        f"/api/v1/ai-review-runs/{ai_run['review_run_id']}/draft-findings"
    ).json()
    valid = [d for d in drafts if d["validation_status"] == "validation_passed"]
    for d in valid:
        assert d["safety_check_status"] == "safety_check_passed"
        assert d["validation_errors"] == []


def test_draft_findings_require_human_review(
    client: TestClient, ai_run: dict
) -> None:
    drafts = client.get(
        f"/api/v1/ai-review-runs/{ai_run['review_run_id']}/draft-findings"
    ).json()
    valid = [d for d in drafts if d["validation_status"] == "validation_passed"]
    assert valid
    for d in valid:
        assert d["status"] == "requires_human_review"


def test_draft_findings_cite_valid_source_chunks(
    client: TestClient, ai_run: dict
) -> None:
    chunks = client.get(f"/api/v1/projects/{PROJECT_ID}/chunks").json()
    chunk_ids = {c["chunk_id"] for c in chunks}
    drafts = client.get(
        f"/api/v1/ai-review-runs/{ai_run['review_run_id']}/draft-findings"
    ).json()
    valid = [d for d in drafts if d["validation_status"] == "validation_passed"]
    for d in valid:
        assert d["source_chunk_ids"]
        assert all(cid in chunk_ids for cid in d["source_chunk_ids"])


def test_prohibited_words_fail_safety_validation() -> None:
    raw = _valid_raw()
    raw["summary"] = "The design is fully compliant and approved."
    outcome = validate_ai_output(raw, ALLOWED)
    assert not outcome.ok
    assert any("prohibited wording" in e for e in outcome.errors)


def test_invalid_source_chunk_ids_fail_validation() -> None:
    raw = _valid_raw()
    raw["source_chunk_ids"] = ["chunk_does_not_exist"]
    outcome = validate_ai_output(raw, ALLOWED)
    assert not outcome.ok
    assert any("not in retrieved evidence" in e for e in outcome.errors)


def test_missing_human_review_fails_schema() -> None:
    raw = _valid_raw()
    raw["requires_human_review"] = False
    outcome = validate_ai_output(raw, ALLOWED)
    assert not outcome.ok
    assert not outcome.schema_ok


def test_ai_review_writes_audit_events(client: TestClient, ai_run: dict) -> None:
    events = client.get(
        f"/api/v1/projects/{PROJECT_ID}/audit-events"
    ).json()
    types = {e["event_type"] for e in events}
    assert "ai_review_run_started" in types
    assert "ai_review_run_completed" in types
    assert "draft_finding_generated" in types


def test_project_draft_findings_endpoint(client: TestClient, ai_run: dict) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}/draft-findings")
    assert response.status_code == 200
    assert len(response.json()) >= 5


def test_no_prohibited_language_in_saved_drafts(
    client: TestClient, ai_run: dict
) -> None:
    from app.core.safety import contains_prohibited_language

    drafts = client.get(
        f"/api/v1/ai-review-runs/{ai_run['review_run_id']}/draft-findings"
    ).json()
    valid = [d for d in drafts if d["validation_status"] == "validation_passed"]
    for d in valid:
        assert not contains_prohibited_language(d["title"])
        assert not contains_prohibited_language(d["summary"])
        assert not contains_prohibited_language(d["recommended_human_action"])
