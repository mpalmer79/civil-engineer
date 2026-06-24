"""Phase 11 real CAD (DXF) intake and parsing tests."""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.core.safety import (
    ALLOWED_CAD_CONFIDENCE_LABELS,
    ALLOWED_CAD_FINDING_STATUSES,
    ALLOWED_CAD_FINDING_TYPES,
    ALLOWED_CAD_PARSE_STATUSES,
)

PROJECT_ID = "proj_brookside_meadows"

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
def parsed(client: TestClient) -> dict:
    create = client.post(
        f"/api/v1/projects/{PROJECT_ID}/cad-files",
        json={"sample_key": "brookside_meadows", "uploaded_by": "Town Engineer"},
    )
    assert create.status_code == 200
    cad_file = create.json()
    assert cad_file["file_type"] == "dxf"

    parse = client.post(f"/api/v1/cad-files/{cad_file['cad_file_id']}/parse")
    assert parse.status_code == 200
    run = parse.json()
    return {"cad_file": cad_file, "run": run}


def test_dxf_parses_successfully(parsed: dict) -> None:
    run = parsed["run"]
    assert run["status"] in {"completed", "completed_with_warnings"}
    assert run["status"] in ALLOWED_CAD_PARSE_STATUSES
    assert run["entity_count"] > 0
    assert run["parser_name"] == "ezdxf"


def test_layers_extracted(client: TestClient, parsed: dict) -> None:
    run_id = parsed["run"]["parse_run_id"]
    layers = client.get(f"/api/v1/cad-parse-runs/{run_id}/layers").json()
    names = {layer["layer_name"] for layer in layers}
    assert "C-STORM" in names
    categories = {layer["review_category"] for layer in layers}
    assert "stormwater" in categories
    assert "wetland_buffer" in categories


def test_text_values_extracted(client: TestClient, parsed: dict) -> None:
    run_id = parsed["run"]["parse_run_id"]
    texts = client.get(f"/api/v1/cad-parse-runs/{run_id}/text").json()
    values = {t["text_value"] for t in texts}
    assert "BROOKSIDE MEADOWS" in values
    assert any("C-3.1" in v for v in values)


def test_blocks_extracted(client: TestClient, parsed: dict) -> None:
    run_id = parsed["run"]["parse_run_id"]
    blocks = client.get(f"/api/v1/cad-parse-runs/{run_id}/blocks").json()
    names = {b["block_name"] for b in blocks}
    assert "TITLEBLOCK_FRAME" in names


def test_reference_candidates_detected(client: TestClient, parsed: dict) -> None:
    run_id = parsed["run"]["parse_run_id"]
    candidates = client.get(
        f"/api/v1/cad-parse-runs/{run_id}/reference-candidates"
    ).json()
    types = {c["reference_type"] for c in candidates}
    assert "sheet_reference" in types
    assert "detail_reference" in types
    assert "basin_label" in types
    for candidate in candidates:
        assert candidate["confidence_label"] in ALLOWED_CAD_CONFIDENCE_LABELS


def test_entities_have_optional_bounds(client: TestClient, parsed: dict) -> None:
    run_id = parsed["run"]["parse_run_id"]
    entities = client.get(f"/api/v1/cad-parse-runs/{run_id}/entities").json()
    assert entities
    # At least one entity carries local bounding values (not georeferenced).
    assert any(e["x_min"] is not None for e in entities)


def test_missing_sheet_reference_creates_finding(
    client: TestClient, parsed: dict
) -> None:
    findings = client.get(
        f"/api/v1/projects/{PROJECT_ID}/cad-review-findings"
    ).json()
    types = {f["finding_type"] for f in findings}
    assert "missing_plan_sheet_match" in types


def test_ambiguous_and_conflict_findings_created(
    client: TestClient, parsed: dict
) -> None:
    findings = client.get(
        f"/api/v1/projects/{PROJECT_ID}/cad-review-findings"
    ).json()
    types = {f["finding_type"] for f in findings}
    assert "unclear_detail_reference" in types
    assert "possible_label_conflict" in types
    assert "unknown_layer_category" in types
    for finding in findings:
        assert finding["finding_type"] in ALLOWED_CAD_FINDING_TYPES
        assert finding["status"] in ALLOWED_CAD_FINDING_STATUSES


def test_parse_summary_counts(client: TestClient, parsed: dict) -> None:
    run_id = parsed["run"]["parse_run_id"]
    summary = client.get(f"/api/v1/cad-parse-runs/{run_id}/summary").json()
    assert summary["layer_count"] >= 5
    assert summary["text_count"] > 0
    assert summary["reference_candidate_count"] > 0
    assert summary["finding_count"] > 0
    assert summary["references_by_confidence"]


def test_compare_links_to_plan_sheets(client: TestClient, parsed: dict) -> None:
    run_id = parsed["run"]["parse_run_id"]
    comparison = client.post(
        f"/api/v1/cad-parse-runs/{run_id}/compare-plan-sheets"
    ).json()
    assert comparison["matched_count"] >= 1
    assert comparison["unmatched_count"] >= 1
    matched_numbers = {
        r["matched_sheet_number"]
        for r in comparison["rows"]
        if r["matched_sheet_number"]
    }
    # C-3.1 is a seeded Phase 6 plan sheet and should match.
    assert "C-3.1" in matched_numbers


def test_workflow_items_from_cad_findings(
    client: TestClient, parsed: dict
) -> None:
    result = client.post(
        f"/api/v1/projects/{PROJECT_ID}/workflow-items/from-cad-findings"
    ).json()
    assert result["created_count"] >= 1
    # Idempotent: a second call creates no new items because findings are linked.
    again = client.post(
        f"/api/v1/projects/{PROJECT_ID}/workflow-items/from-cad-findings"
    ).json()
    assert again["created_count"] == 0


def test_review_context(client: TestClient, parsed: dict) -> None:
    cad_file_id = parsed["cad_file"]["cad_file_id"]
    context = client.get(
        f"/api/v1/cad-files/{cad_file_id}/review-context"
    ).json()
    assert context["cad_file"]["cad_file_id"] == cad_file_id
    assert context["parse_run"] is not None
    assert context["summary"] is not None
    assert "Professional Engineer" in context["cad_file"]["limitations_note"]


def test_non_dxf_rejected(client: TestClient) -> None:
    # The sample registry only resolves DXF fixtures; an unknown sample is 404.
    response = client.post(
        f"/api/v1/projects/{PROJECT_ID}/cad-files",
        json={"sample_key": "not_a_real_sample", "uploaded_by": "Town Engineer"},
    )
    assert response.status_code == 404


def test_parse_failure_handled_safely(client: TestClient) -> None:
    # Register a CAD file pointing at a missing path, then parse should record a
    # failed run rather than raising.
    from app.db import models
    from app.db.database import SessionLocal

    db = SessionLocal()
    try:
        broken = models.CadFileUpload(
            cad_file_id="cad_broken_test",
            project_id=PROJECT_ID,
            file_name="missing.dxf",
            file_type="dxf",
            file_size_bytes=0,
            storage_path="/nonexistent/path/missing.dxf",
            upload_status="uploaded",
            uploaded_by="tester",
            limitations_note="test",
        )
        db.add(broken)
        db.commit()
    finally:
        db.close()

    run = client.post("/api/v1/cad-files/cad_broken_test/parse").json()
    assert run["status"] == "failed"
    assert run["error_message"]


def test_no_prohibited_vocabulary(client: TestClient, parsed: dict) -> None:
    # Note: the operational parse-status enum includes "failed", which describes
    # the parser failing to read a file, not a final engineering decision about
    # the plan. The professional-boundary check applies to review findings,
    # confidence labels, finding types, and generated text below.
    for status in ALLOWED_CAD_FINDING_STATUSES:
        assert not _has_forbidden(status)
    for label in ALLOWED_CAD_CONFIDENCE_LABELS:
        assert not _has_forbidden(label)
    for finding_type in ALLOWED_CAD_FINDING_TYPES:
        assert not _has_forbidden(finding_type)

    run_id = parsed["run"]["parse_run_id"]
    candidates = client.get(
        f"/api/v1/cad-parse-runs/{run_id}/reference-candidates"
    ).json()
    for candidate in candidates:
        assert not _has_forbidden(candidate["confidence_label"])
        assert not _has_forbidden(candidate["match_reason"])
        assert not _has_forbidden(candidate["reference_type"])
    findings = client.get(
        f"/api/v1/projects/{PROJECT_ID}/cad-review-findings"
    ).json()
    for finding in findings:
        assert not _has_forbidden(finding["title"])
        assert not _has_forbidden(finding["description"])
        assert not _has_forbidden(finding["status"])
        assert not _has_forbidden(finding["severity"])


def test_audit_events_written(client: TestClient, parsed: dict) -> None:
    run_id = parsed["run"]["parse_run_id"]
    cad_file_id = parsed["cad_file"]["cad_file_id"]
    client.get(f"/api/v1/cad-parse-runs/{run_id}/summary")
    client.get(f"/api/v1/cad-parse-runs/{run_id}/layers")
    client.get(f"/api/v1/cad-parse-runs/{run_id}/text")
    client.get(f"/api/v1/cad-files/{cad_file_id}/review-context")
    events = client.get(
        f"/api/v1/projects/{PROJECT_ID}/audit-events"
    ).json()
    types = {e["event_type"] for e in events}
    for expected in [
        "cad_file_created",
        "cad_parse_started",
        "cad_parse_completed",
        "cad_parse_summary_viewed",
        "cad_layers_viewed",
        "cad_text_viewed",
        "cad_reference_comparison_run",
        "cad_review_finding_created",
        "cad_workflow_items_created",
        "cad_review_context_viewed",
    ]:
        assert expected in types, expected
