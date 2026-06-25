"""Phase 12 browser DXF upload, parse queue, dashboard, and promotion tests.

These tests exercise the browser upload endpoint, intake validation, the manual
parse queue and CAD intake dashboard, the unpromoted findings endpoint, and
promotion of CAD findings into the workflow board. Upload and parsing are
review-support only; nothing here verifies CAD or validates engineering design.
A parse queue status of "failed" means a technical parse failure, not an
engineering failure.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.safety import (
    ALLOWED_CAD_QUEUE_STATUSES,
    ALLOWED_CAD_VALIDATION_STATUSES,
)

PROJECT_ID = "proj_brookside_meadows"

SAMPLE_DXF = (
    Path(__file__).resolve().parent.parent
    / "app"
    / "cad_samples"
    / "brookside_meadows.dxf"
)

FORBIDDEN_WORDS = [
    "approved",
    "certified",
    "verified",
    "passed",
    "compliant",
    "noncompliant",
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


def _sample_bytes() -> bytes:
    return SAMPLE_DXF.read_bytes()


def _upload(
    client: TestClient,
    *,
    filename: str,
    content: bytes,
    content_type: str = "application/dxf",
    uploaded_by: str = "Town Engineer",
):
    return client.post(
        f"/api/v1/projects/{PROJECT_ID}/cad-files/upload",
        files={"file": (filename, content, content_type)},
        data={"uploaded_by": uploaded_by},
    )


def test_upload_limits_endpoint(client: TestClient) -> None:
    limits = client.get("/api/v1/cad-upload-limits").json()
    assert limits["supported_extensions"] == [".dxf"]
    assert limits["supported_file_types"] == ["dxf"]
    assert limits["max_file_size_bytes"] > 0
    assert set(limits["allowed_validation_statuses"]) == (
        ALLOWED_CAD_VALIDATION_STATUSES
    )
    assert set(limits["allowed_queue_statuses"]) == ALLOWED_CAD_QUEUE_STATUSES


def test_valid_dxf_upload_accepted(client: TestClient) -> None:
    response = _upload(
        client, filename="my_drawing.dxf", content=_sample_bytes()
    )
    assert response.status_code == 200
    body = response.json()
    assert body["validation_status"] == "accepted"
    cad_file = body["cad_file"]
    assert cad_file["file_type"] == "dxf"
    assert cad_file["upload_status"] == "uploaded"
    assert cad_file["upload_source"] == "browser_upload"
    assert cad_file["original_file_name"] == "my_drawing.dxf"
    assert body["next_action"] == "request_parse"


def test_unsupported_extension_rejected(client: TestClient) -> None:
    response = _upload(
        client,
        filename="drawing.dwg",
        content=b"AC1027 fake dwg",
        content_type="application/octet-stream",
    )
    assert response.status_code == 422
    assert "DWG" in response.json()["detail"] or "extension" in (
        response.json()["detail"]
    )


def test_empty_file_rejected(client: TestClient) -> None:
    response = _upload(client, filename="empty.dxf", content=b"")
    assert response.status_code == 422
    assert "empty" in response.json()["detail"].lower()


def test_oversized_file_rejected(client: TestClient) -> None:
    from app.core.config import get_settings

    limit = get_settings().CAD_MAX_UPLOAD_BYTES
    oversized = b"0" * (limit + 1)
    response = _upload(client, filename="big.dxf", content=oversized)
    assert response.status_code == 422
    assert "exceeds" in response.json()["detail"].lower()


def test_unsupported_content_type_rejected(client: TestClient) -> None:
    response = _upload(
        client,
        filename="drawing.dxf",
        content=_sample_bytes(),
        content_type="application/pdf",
    )
    assert response.status_code == 422
    assert "content type" in response.json()["detail"].lower()


def test_unsafe_file_name_does_not_affect_storage_path(
    client: TestClient,
) -> None:
    response = _upload(
        client,
        filename="../../../etc/passwd.dxf",
        content=_sample_bytes(),
    )
    assert response.status_code == 200
    cad_file = response.json()["cad_file"]
    # Original name is reduced to its base name as metadata only.
    assert cad_file["original_file_name"] == "passwd.dxf"
    # The stored file name is generated, not the user name, and the storage path
    # contains no parent traversal.
    assert cad_file["stored_file_name"].startswith("cad_")
    assert cad_file["stored_file_name"].endswith(".dxf")
    assert ".." not in cad_file["storage_path"]
    assert "etc/passwd" not in cad_file["storage_path"]


def test_non_dxf_text_marked_needs_human_review(client: TestClient) -> None:
    response = _upload(
        client,
        filename="not_really.dxf",
        content=b"this is not a dxf file at all",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["validation_status"] == "needs_human_review"
    assert body["cad_file"]["upload_status"] == "needs_human_review"


def test_request_parse_updates_status(client: TestClient) -> None:
    upload = _upload(
        client, filename="parse_me.dxf", content=_sample_bytes()
    ).json()
    cad_file_id = upload["cad_file"]["cad_file_id"]
    run = client.post(
        f"/api/v1/cad-files/{cad_file_id}/request-parse"
    ).json()
    assert run["status"] in {"completed", "completed_with_warnings"}
    assert run["entity_count"] > 0
    # The CAD file now records parse request and completion timestamps.
    context = client.get(
        f"/api/v1/cad-files/{cad_file_id}/review-context"
    ).json()
    assert context["cad_file"]["parse_requested_at"] is not None
    assert context["cad_file"]["parse_completed_at"] is not None
    assert context["cad_file"]["upload_status"] == "parsed"


def test_parse_failure_is_technical(client: TestClient) -> None:
    # A file that passes validation by extension and size but is not a real DXF
    # records a technical parse failure, not an engineering failure.
    upload = _upload(
        client,
        filename="broken.dxf",
        content=b"0\nSECTION\nnot a real dxf body\n0\nEOF\n",
    ).json()
    cad_file_id = upload["cad_file"]["cad_file_id"]
    run = client.post(
        f"/api/v1/cad-files/{cad_file_id}/request-parse"
    ).json()
    assert run["status"] == "failed"
    assert run["error_message"]
    assert run["status"] in ALLOWED_CAD_QUEUE_STATUSES


def test_parse_queue_returns_files_and_runs(client: TestClient) -> None:
    queue = client.get(
        f"/api/v1/projects/{PROJECT_ID}/cad-parse-queue"
    ).json()
    assert isinstance(queue, list)
    assert len(queue) >= 1
    for row in queue:
        assert row["queue_status"] in ALLOWED_CAD_QUEUE_STATUSES
    statuses = {row["queue_status"] for row in queue}
    # At least one completed parse and one technical failure exist by now.
    assert statuses & {"completed", "completed_with_warnings"}
    assert "failed" in statuses


def test_dashboard_counts(client: TestClient) -> None:
    dashboard = client.get(
        f"/api/v1/projects/{PROJECT_ID}/cad-intake/dashboard"
    ).json()
    assert dashboard["total_files"] >= 1
    assert dashboard["total_findings"] >= 1
    assert "queue_status_counts" in dashboard
    assert "validation_status_counts" in dashboard
    assert dashboard["unpromoted_findings_count"] >= 0
    assert dashboard["files_with_parse_failures"] >= 1


def test_unpromoted_findings_endpoint(client: TestClient) -> None:
    findings = client.get(
        f"/api/v1/projects/{PROJECT_ID}/cad-review-findings/unpromoted"
    ).json()
    assert isinstance(findings, list)
    for finding in findings:
        assert finding["linked_workflow_item_id"] is None
        assert finding["promoted_to_workflow"] is False


def test_single_finding_promotion_creates_one_item(client: TestClient) -> None:
    findings = client.get(
        f"/api/v1/projects/{PROJECT_ID}/cad-review-findings/unpromoted"
    ).json()
    assert findings, "expected at least one unpromoted finding"
    target = findings[0]["cad_review_finding_id"]

    before = client.get(
        f"/api/v1/projects/{PROJECT_ID}/workflow-board?source_type=cad_review_finding"
    ).json()
    result = client.post(
        f"/api/v1/cad-review-findings/{target}/promote-to-workflow",
        json={"reviewer_name": "Town Engineer", "reviewer_note": "track this"},
    ).json()
    assert result["created"] is True
    assert result["workflow_item_id"]
    after = client.get(
        f"/api/v1/projects/{PROJECT_ID}/workflow-board?source_type=cad_review_finding"
    ).json()
    assert len(after) == len(before) + 1

    # Duplicate promotion does not create a duplicate workflow item.
    again = client.post(
        f"/api/v1/cad-review-findings/{target}/promote-to-workflow",
        json={"reviewer_name": "Town Engineer"},
    ).json()
    assert again["created"] is False
    assert again["already_promoted"] is True
    after_again = client.get(
        f"/api/v1/projects/{PROJECT_ID}/workflow-board?source_type=cad_review_finding"
    ).json()
    assert len(after_again) == len(after)


def test_selected_promotion_creates_items_no_duplicates(
    client: TestClient,
) -> None:
    findings = client.get(
        f"/api/v1/projects/{PROJECT_ID}/cad-review-findings/unpromoted"
    ).json()
    ids = [f["cad_review_finding_id"] for f in findings[:2]]
    # Include a bogus id to exercise the not-found path.
    payload_ids = ids + ["cadfind_does_not_exist"]
    result = client.post(
        f"/api/v1/projects/{PROJECT_ID}/cad-review-findings/promote-selected",
        json={
            "cad_review_finding_ids": payload_ids,
            "reviewer_name": "Town Engineer",
        },
    ).json()
    assert result["created_count"] == len(ids)
    assert result["not_found_count"] == 1
    assert len(result["workflow_item_ids"]) == len(ids)

    # Re-promoting the same ids creates no duplicates.
    repeat = client.post(
        f"/api/v1/projects/{PROJECT_ID}/cad-review-findings/promote-selected",
        json={"cad_review_finding_ids": ids, "reviewer_name": "Town Engineer"},
    ).json()
    assert repeat["created_count"] == 0
    assert repeat["already_promoted_count"] == len(ids)


def test_no_prohibited_vocabulary_in_phase12_output(client: TestClient) -> None:
    limits = client.get("/api/v1/cad-upload-limits").json()
    assert not _has_forbidden(limits["note"])
    for status in limits["allowed_validation_statuses"]:
        assert not _has_forbidden(status)
    for status in limits["allowed_queue_statuses"]:
        assert not _has_forbidden(status)

    queue = client.get(
        f"/api/v1/projects/{PROJECT_ID}/cad-parse-queue"
    ).json()
    for row in queue:
        assert not _has_forbidden(row["queue_status"])
        assert not _has_forbidden(row["validation_status"])
        assert not _has_forbidden(row["validation_message"])

    dashboard = client.get(
        f"/api/v1/projects/{PROJECT_ID}/cad-intake/dashboard"
    ).json()
    assert not _has_forbidden(dashboard["limitations_note"])
    for status in dashboard["queue_status_counts"]:
        assert not _has_forbidden(status)
    for status in dashboard["validation_status_counts"]:
        assert not _has_forbidden(status)


def test_audit_events_written(client: TestClient) -> None:
    # Drive the audited actions once more to be sure events exist.
    upload = _upload(
        client, filename="audit_me.dxf", content=_sample_bytes()
    ).json()
    cad_file_id = upload["cad_file"]["cad_file_id"]
    client.post(f"/api/v1/cad-files/{cad_file_id}/request-parse")
    client.get(f"/api/v1/projects/{PROJECT_ID}/cad-parse-queue")
    client.get(f"/api/v1/projects/{PROJECT_ID}/cad-intake/dashboard")
    client.get(
        f"/api/v1/projects/{PROJECT_ID}/cad-review-findings/unpromoted"
    )
    # A rejected upload should also write an audit event.
    _upload(client, filename="reject.txt", content=b"nope")

    events = client.get(
        f"/api/v1/projects/{PROJECT_ID}/audit-events"
    ).json()
    types = {e["event_type"] for e in events}
    for expected in [
        "cad_upload_accepted",
        "cad_upload_rejected",
        "cad_parse_requested",
        "cad_parse_queue_viewed",
        "cad_intake_dashboard_viewed",
        "cad_unpromoted_findings_viewed",
        "cad_finding_promoted",
        "cad_findings_promoted_selected",
    ]:
        assert expected in types, expected


def test_upload_to_missing_project_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/projects/proj_missing/cad-files/upload",
        files={"file": ("x.dxf", _sample_bytes(), "application/dxf")},
        data={"uploaded_by": "tester"},
    )
    assert response.status_code == 404
