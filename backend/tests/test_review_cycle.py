"""Phase 13 multi-round resubmittal, revision comparison, and response cycle tests.

These tests exercise review cycles, resubmittal intake, applicant responses and
mappings, DXF metadata revision comparison between two parse rounds, issue
carry-forward, response resolution, and next-cycle preparation. Everything here
is review-support only. Revision comparison compares extracted DXF metadata and
never verifies CAD or validates engineering design. No status uses final-decision
language.
"""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.core.safety import (
    ALLOWED_CARRY_FORWARD_STATUSES,
    ALLOWED_MAPPING_CONFIDENCE_LABELS,
    ALLOWED_RESOLUTION_STATUSES,
    ALLOWED_RESUBMITTAL_STATUSES,
    ALLOWED_REVIEW_CYCLE_STATUSES,
    ALLOWED_REVISION_CHANGE_TYPES,
)

PROJECT_ID = "proj_brookside_meadows"

# Final-decision language that must never appear in Phase 13 statuses or output.
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
    "fixed",
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
def cycle(client: TestClient) -> dict:
    """A review cycle with two parsed DXF rounds and a resubmittal package."""

    cycles = client.get(
        f"/api/v1/projects/{PROJECT_ID}/review-cycles"
    ).json()
    review_cycle_id = cycles[0]["review_cycle_id"]
    previous_run = _parse_sample(client, "brookside_meadows")
    current_run = _parse_sample(client, "brookside_meadows_r2")
    return {
        "review_cycle_id": review_cycle_id,
        "previous_run": previous_run,
        "current_run": current_run,
    }


def test_initial_review_cycle_exists(client: TestClient) -> None:
    cycles = client.get(
        f"/api/v1/projects/{PROJECT_ID}/review-cycles"
    ).json()
    assert len(cycles) >= 1
    first = cycles[0]
    assert first["cycle_number"] == 1
    assert first["status"] in ALLOWED_REVIEW_CYCLE_STATUSES


def test_create_review_cycle_increments(client: TestClient) -> None:
    created = client.post(
        f"/api/v1/projects/{PROJECT_ID}/review-cycles",
        json={"cycle_name": "Second round"},
    ).json()
    assert created["cycle_number"] >= 2
    assert created["status"] == "active"
    summary = client.get(
        f"/api/v1/projects/{PROJECT_ID}/review-cycle-summary"
    ).json()
    assert summary["cycle_count"] >= 2


def test_review_cycle_dashboard(client: TestClient) -> None:
    dashboard = client.get(
        f"/api/v1/projects/{PROJECT_ID}/review-cycle-dashboard"
    ).json()
    assert dashboard["cycle_count"] >= 1
    assert "resubmittal_statuses" in dashboard
    assert "resolution_statuses" in dashboard
    assert not _has_forbidden(dashboard["limitations_note"])


def test_resubmittal_creation_and_status(client: TestClient, cycle: dict) -> None:
    package = client.post(
        f"/api/v1/projects/{PROJECT_ID}/resubmittals",
        json={
            "review_cycle_id": cycle["review_cycle_id"],
            "package_name": "Brookside Meadows resubmittal 1",
            "submitted_by": "Design Engineer",
        },
    ).json()
    assert package["status"] == "received"
    cycle["resubmittal_id"] = package["resubmittal_package_id"]

    updated = client.patch(
        f"/api/v1/resubmittals/{package['resubmittal_package_id']}/status",
        json={"status": "intake_review", "reviewer_note": "Logged in."},
    ).json()
    assert updated["status"] == "intake_review"

    # Invalid status is rejected.
    bad = client.patch(
        f"/api/v1/resubmittals/{package['resubmittal_package_id']}/status",
        json={"status": "approved"},
    )
    assert bad.status_code == 422


def test_link_cad_file_to_resubmittal(client: TestClient, cycle: dict) -> None:
    files = client.get(
        f"/api/v1/projects/{PROJECT_ID}/cad-files"
    ).json()
    cad_file_id = files[0]["cad_file_id"]
    detail = client.post(
        f"/api/v1/resubmittals/{cycle['resubmittal_id']}/cad-files/{cad_file_id}"
    ).json()
    assert any(
        d["source_id"] == cad_file_id and d["document_type"] == "dxf_cad_file"
        for d in detail["documents"]
    )
    # Linking the same file again does not duplicate the document.
    detail2 = client.post(
        f"/api/v1/resubmittals/{cycle['resubmittal_id']}/cad-files/{cad_file_id}"
    ).json()
    cad_docs = [
        d
        for d in detail2["documents"]
        if d["source_id"] == cad_file_id and d["document_type"] == "dxf_cad_file"
    ]
    assert len(cad_docs) == 1


def test_applicant_response_and_mapping(client: TestClient, cycle: dict) -> None:
    response = client.post(
        f"/api/v1/resubmittals/{cycle['resubmittal_id']}/applicant-responses",
        json={
            "response_text": "Revised the basin outlet detail and updated sheet C-3.1 per the stormwater comment.",
            "response_topic": "stormwater basin",
            "submitted_by": "Design Engineer",
        },
    ).json()
    assert response["status"] == "received"
    cycle["applicant_response_id"] = response["applicant_response_id"]

    listed = client.get(
        f"/api/v1/projects/{PROJECT_ID}/applicant-responses"
    ).json()
    assert any(
        r["applicant_response_id"] == response["applicant_response_id"]
        for r in listed
    )

    # Manual mapping with an invalid confidence is rejected.
    bad = client.post(
        f"/api/v1/applicant-responses/{response['applicant_response_id']}/mappings",
        json={"mapping_confidence": "verified"},
    )
    assert bad.status_code == 422

    mapping = client.post(
        f"/api/v1/applicant-responses/{response['applicant_response_id']}/mappings",
        json={"mapping_confidence": "medium", "mapping_reason": "Reviewer mapped."},
    ).json()
    assert mapping["mapping_confidence"] in ALLOWED_MAPPING_CONFIDENCE_LABELS


def test_suggest_response_mappings(client: TestClient, cycle: dict) -> None:
    # Add a fresh response, then ask for deterministic suggestions.
    client.post(
        f"/api/v1/resubmittals/{cycle['resubmittal_id']}/applicant-responses",
        json={
            "response_text": "Addressed the wetland buffer setback note.",
            "response_topic": "wetland buffer",
        },
    )
    suggestions = client.post(
        f"/api/v1/review-cycles/{cycle['review_cycle_id']}/suggest-response-mappings"
    ).json()
    assert isinstance(suggestions, list)
    for mapping in suggestions:
        assert mapping["mapping_confidence"] in ALLOWED_MAPPING_CONFIDENCE_LABELS
        assert mapping["requires_human_review"] is True
        assert mapping["mapping_reason"]

    mapping_summary = client.get(
        f"/api/v1/review-cycles/{cycle['review_cycle_id']}/response-mapping-summary"
    ).json()
    assert mapping_summary["response_count"] >= 1


def test_revision_comparison(client: TestClient, cycle: dict) -> None:
    comparison = client.post(
        f"/api/v1/review-cycles/{cycle['review_cycle_id']}/revision-comparisons",
        json={
            "previous_parse_run_id": cycle["previous_run"],
            "current_parse_run_id": cycle["current_run"],
            "resubmittal_package_id": cycle["resubmittal_id"],
        },
    ).json()
    assert comparison["status"] in {"completed", "completed_with_warnings"}
    assert comparison["added_count"] >= 2
    assert comparison["removed_count"] >= 1
    assert comparison["changed_count"] >= 1
    assert comparison["unchanged_count"] >= 3
    cycle["comparison_run_id"] = comparison["comparison_run_id"]

    changes = client.get(
        f"/api/v1/revision-comparisons/{comparison['comparison_run_id']}/changes"
    ).json()
    types = {c["change_type"] for c in changes}
    assert "added" in types
    assert "removed" in types
    assert "unchanged" in types
    assert "carried_forward" in types
    for change in changes:
        assert change["change_type"] in ALLOWED_REVISION_CHANGE_TYPES

    # A previously missing sheet reference still missing is carried forward.
    carried_sheet = [
        c
        for c in changes
        if c["change_type"] == "carried_forward"
        and c["source_category"] == "sheet_reference"
    ]
    assert carried_sheet

    summary = client.get(
        f"/api/v1/revision-comparisons/{comparison['comparison_run_id']}/summary"
    ).json()
    assert summary["carried_forward_count"] >= 1
    assert not _has_forbidden(summary["limitations_note"])

    # Added and removed references are present.
    added = [c for c in changes if c["change_type"] == "added"]
    removed = [c for c in changes if c["change_type"] == "removed"]
    assert any(c["current_value"] for c in added)
    assert any(c["previous_value"] for c in removed)


def test_resolution_records(client: TestClient, cycle: dict) -> None:
    record = client.post(
        f"/api/v1/review-cycles/{cycle['review_cycle_id']}/resolution-records",
        json={
            "status": "addressed_for_review",
            "reviewer_note": "Basin detail appears addressed; needs human review.",
            "reviewer_name": "Town Engineer",
        },
    ).json()
    assert record["status"] == "addressed_for_review"
    cycle["resolution_id"] = record["resolution_record_id"]

    # Invalid resolution status is rejected.
    bad = client.post(
        f"/api/v1/review-cycles/{cycle['review_cycle_id']}/resolution-records",
        json={"status": "resolved"},
    )
    assert bad.status_code == 422

    updated = client.patch(
        f"/api/v1/resolution-records/{record['resolution_record_id']}/status",
        json={"status": "still_open", "reviewer_name": "Town Engineer"},
    ).json()
    assert updated["status"] == "still_open"

    records = client.get(
        f"/api/v1/projects/{PROJECT_ID}/resolution-records"
    ).json()
    assert any(
        r["resolution_record_id"] == record["resolution_record_id"]
        for r in records
    )

    resolution_summary = client.get(
        f"/api/v1/review-cycles/{cycle['review_cycle_id']}/resolution-summary"
    ).json()
    assert resolution_summary["total"] >= 1
    for status in resolution_summary["statuses"]:
        assert status in ALLOWED_RESOLUTION_STATUSES


def test_carry_forward_without_duplication(client: TestClient, cycle: dict) -> None:
    first = client.post(
        f"/api/v1/review-cycles/{cycle['review_cycle_id']}/carry-forward"
    ).json()
    assert first["created_count"] >= 1

    second = client.post(
        f"/api/v1/review-cycles/{cycle['review_cycle_id']}/carry-forward"
    ).json()
    # Re-running does not duplicate the same source items.
    assert second["created_count"] == 0
    assert second["skipped_count"] >= first["created_count"]

    carry_forwards = client.get(
        f"/api/v1/projects/{PROJECT_ID}/carry-forwards"
    ).json()
    assert len(carry_forwards) >= 1
    for item in carry_forwards:
        assert item["carried_forward_status"] in ALLOWED_CARRY_FORWARD_STATUSES

    cf_summary = client.get(
        f"/api/v1/review-cycles/{cycle['review_cycle_id']}/carry-forward-summary"
    ).json()
    assert cf_summary["total"] >= 1


def test_prepare_next_cycle(client: TestClient, cycle: dict) -> None:
    prep = client.post(
        f"/api/v1/review-cycles/{cycle['review_cycle_id']}/prepare-next-cycle"
    ).json()
    assert prep["carried_forward_count"] >= 1
    assert prep["status"] in {"draft", "ready_for_next_cycle", "needs_human_review", "archived"}

    fetched = client.get(
        f"/api/v1/review-cycles/{cycle['review_cycle_id']}/next-cycle-preparation"
    ).json()
    assert (
        fetched["next_cycle_preparation_id"] == prep["next_cycle_preparation_id"]
    )
    assert not _has_forbidden(fetched["summary"])


def test_no_prohibited_vocabulary(client: TestClient, cycle: dict) -> None:
    for status in (
        ALLOWED_REVIEW_CYCLE_STATUSES
        | ALLOWED_RESUBMITTAL_STATUSES
        | ALLOWED_RESOLUTION_STATUSES
        | ALLOWED_CARRY_FORWARD_STATUSES
        | ALLOWED_REVISION_CHANGE_TYPES
        | ALLOWED_MAPPING_CONFIDENCE_LABELS
    ):
        assert not _has_forbidden(status), status

    changes = client.get(
        f"/api/v1/revision-comparisons/{cycle['comparison_run_id']}/changes"
    ).json()
    for change in changes:
        assert not _has_forbidden(change["change_type"])
        assert not _has_forbidden(change["reviewer_status"])
        assert not _has_forbidden(change["source_category"])

    records = client.get(
        f"/api/v1/projects/{PROJECT_ID}/resolution-records"
    ).json()
    for record in records:
        assert not _has_forbidden(record["status"])

    carry_forwards = client.get(
        f"/api/v1/projects/{PROJECT_ID}/carry-forwards"
    ).json()
    for item in carry_forwards:
        assert not _has_forbidden(item["carried_forward_status"])
        assert not _has_forbidden(item["title"])


def test_audit_events_written(client: TestClient, cycle: dict) -> None:
    # View endpoints to ensure their read side effects fire.
    client.get(f"/api/v1/review-cycles/{cycle['review_cycle_id']}")
    client.get(f"/api/v1/projects/{PROJECT_ID}/review-cycle-dashboard")
    client.get(
        f"/api/v1/revision-comparisons/{cycle['comparison_run_id']}/summary"
    )

    events = client.get(
        f"/api/v1/projects/{PROJECT_ID}/audit-events"
    ).json()
    types = {e["event_type"] for e in events}
    for expected in [
        "review_cycle_created",
        "review_cycle_viewed",
        "review_cycle_dashboard_viewed",
        "resubmittal_created",
        "resubmittal_status_changed",
        "resubmittal_cad_file_linked",
        "applicant_response_created",
        "applicant_response_mapping_created",
        "response_mappings_suggested",
        "revision_comparison_run",
        "issue_carried_forward",
        "response_resolution_created",
        "response_resolution_status_changed",
        "next_cycle_prepared",
    ]:
        assert expected in types, expected
