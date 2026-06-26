"""Tests for Production Foundations Sprint 1 real project intake.

These tests cover real project creation, document registration and upload,
reviewer-created findings, evidence references, and audit events, and confirm
the review-support professional boundary is preserved (no final-decision
wording, no document approval language, no secrets in audit events).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.safety import PROHIBITED_FINAL_DECISION_WORDS

BROOKSIDE_ID = "proj_brookside_meadows"


def _create_project(client: TestClient, **overrides) -> dict:
    payload = {
        "project_name": "Maple Commons Stormwater Review",
        "project_type": "Commercial site plan",
        "jurisdiction": "Town of Riverton",
        "review_type": "Site plan stormwater review",
        "review_domain": "stormwater",
        "location_context": "Infill commercial parcel",
        "acreage": 4.2,
        "disturbed_area": 3.1,
        "proposed_lots": 1,
        "summary": "A small commercial redevelopment with a new detention basin.",
        "applicant_name": "Jane Applicant",
        "design_engineer_name": "Sam Engineer",
        "parcel_ids": ["12-34-567"],
    }
    payload.update(overrides)
    response = client.post("/api/v1/projects", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Project creation and listing
# ---------------------------------------------------------------------------


def test_create_project_returns_user_created_record(client: TestClient) -> None:
    project = _create_project(client)
    assert project["project_id"].startswith("proj_user_")
    assert project["source_mode"] == "user_created"
    assert project["status"] == "intake_started"
    assert project["review_round_current"] == 1
    assert project["created_by_name"] == "Demo Reviewer"
    assert project["created_at"] is not None
    assert project["document_count"] == 0
    assert project["finding_count"] == 0
    # A project_created audit event is recorded.
    assert project["audit_event_count"] >= 1


def test_create_project_uses_safe_generated_id(client: TestClient) -> None:
    a = _create_project(client, project_name="Project A")
    b = _create_project(client, project_name="Project B")
    assert a["project_id"] != b["project_id"]
    assert a["project_id"].startswith("proj_user_")


def test_create_project_writes_audit_event(client: TestClient) -> None:
    project = _create_project(client)
    events = client.get(
        f"/api/v1/projects/{project['project_id']}/audit-events"
    ).json()
    types = [e["event_type"] for e in events]
    assert "project_created" in types
    created = next(e for e in events if e["event_type"] == "project_created")
    assert created["actor_type"] == "reviewer"
    assert created["actor_display_name"] == "Demo Reviewer"


def test_create_project_rejects_prohibited_language(client: TestClient) -> None:
    response = client.post(
        "/api/v1/projects",
        json={
            "project_name": "Project that is fully compliant",
            "project_type": "Residential",
            "jurisdiction": "Town",
            "review_type": "Review",
            "review_domain": "stormwater",
            "location_context": "Site",
        },
    )
    assert response.status_code == 422
    assert "prohibited" in response.json()["detail"].lower()


def test_create_project_requires_name(client: TestClient) -> None:
    response = client.post(
        "/api/v1/projects",
        json={"project_name": "   ", "project_type": "Residential"},
    )
    assert response.status_code == 422


def test_list_projects_includes_demo_and_user_created(
    client: TestClient,
) -> None:
    project = _create_project(client, project_name="Listed Project")
    projects = client.get("/api/v1/projects").json()
    ids = {p["project_id"] for p in projects}
    assert BROOKSIDE_ID in ids
    assert project["project_id"] in ids


def test_list_projects_filter_by_source_mode(client: TestClient) -> None:
    _create_project(client, project_name="Filtered Project")
    demo = client.get(
        "/api/v1/projects", params={"source_mode": "demo_fixture"}
    ).json()
    assert all(p["source_mode"] == "demo_fixture" for p in demo)
    assert any(p["project_id"] == BROOKSIDE_ID for p in demo)

    user = client.get(
        "/api/v1/projects", params={"source_mode": "user_created"}
    ).json()
    assert all(p["source_mode"] == "user_created" for p in user)
    assert all(p["project_id"] != BROOKSIDE_ID for p in user)


def test_project_detail_includes_counts(client: TestClient) -> None:
    project = _create_project(client)
    pid = project["project_id"]
    client.post(
        f"/api/v1/projects/{pid}/documents/register",
        json={"original_file_name": "plan.pdf", "document_type": "plan_set"},
    )
    detail = client.get(f"/api/v1/projects/{pid}").json()
    assert detail["document_count"] == 1
    assert detail["audit_event_count"] >= 2


def test_get_unknown_project_is_404(client: TestClient) -> None:
    assert client.get("/api/v1/projects/proj_does_not_exist").status_code == 404


# ---------------------------------------------------------------------------
# Document registration and upload
# ---------------------------------------------------------------------------


def test_register_document_records_metadata(client: TestClient) -> None:
    project = _create_project(client)
    pid = project["project_id"]
    response = client.post(
        f"/api/v1/projects/{pid}/documents/register",
        json={
            "original_file_name": "Stormwater Report.pdf",
            "document_type": "stormwater_report",
            "purpose": "Post-construction stormwater management narrative",
            "expected_key_information": "Detention basin sizing",
            "revision_label": "Rev A",
        },
    )
    assert response.status_code == 201, response.text
    doc = response.json()
    assert doc["document_id"].startswith("doc_user_")
    assert doc["source_mode"] == "user_registered"
    assert doc["processing_status"] == "metadata_recorded"
    assert doc["status"] == "registered"
    assert doc["revision_label"] == "Rev A"
    # Document registration must not imply approval.
    assert doc["status"] not in {"approved", "certified", "verified"}

    events = client.get(f"/api/v1/projects/{pid}/audit-events").json()
    assert any(e["event_type"] == "document_registered" for e in events)

    docs = client.get(f"/api/v1/projects/{pid}/documents").json()
    assert any(d["document_id"] == doc["document_id"] for d in docs)


def test_register_document_requires_file_name(client: TestClient) -> None:
    project = _create_project(client)
    pid = project["project_id"]
    response = client.post(
        f"/api/v1/projects/{pid}/documents/register",
        json={"original_file_name": "", "document_type": "plan_set"},
    )
    assert response.status_code == 422


def test_register_document_unknown_project_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/projects/proj_missing/documents/register",
        json={"original_file_name": "x.pdf", "document_type": "plan_set"},
    )
    assert response.status_code == 404


def test_upload_document_accepts_allowed_type(client: TestClient) -> None:
    project = _create_project(client)
    pid = project["project_id"]
    response = client.post(
        f"/api/v1/projects/{pid}/documents/upload",
        files={"file": ("report.pdf", b"%PDF-1.4 sample bytes", "application/pdf")},
        data={"document_type": "stormwater_report", "purpose": "narrative"},
    )
    assert response.status_code == 201, response.text
    doc = response.json()
    assert doc["source_mode"] == "user_uploaded"
    assert doc["upload_status"] == "stored"
    assert doc["processing_status"] == "parsing_not_available"
    assert doc["file_size_bytes"] == len(b"%PDF-1.4 sample bytes")
    # A sha256 checksum is computed and stored.
    assert doc["checksum_sha256"] and len(doc["checksum_sha256"]) == 64
    # The stored file name is generated, never the raw user file name.
    assert doc["original_file_name"] == "report.pdf"
    assert doc["file_name"] != "report.pdf"
    assert doc["file_name"].startswith("doc_")

    events = client.get(f"/api/v1/projects/{pid}/audit-events").json()
    # Sprint 6 records a document_stored event when the file is persisted through
    # the storage provider.
    uploaded = [e for e in events if e["event_type"] == "document_stored"]
    assert uploaded
    # The audit metadata records the checksum but never raw secrets.
    assert uploaded[-1]["event_metadata"]["checksum_sha256"] == doc[
        "checksum_sha256"
    ]


def test_upload_document_rejects_disallowed_extension(
    client: TestClient,
) -> None:
    project = _create_project(client)
    pid = project["project_id"]
    response = client.post(
        f"/api/v1/projects/{pid}/documents/upload",
        files={"file": ("malware.exe", b"MZ executable", "application/octet-stream")},
    )
    assert response.status_code == 422
    assert "extension" in response.json()["detail"].lower()
    # A rejection audit event is recorded and no document is created.
    events = client.get(f"/api/v1/projects/{pid}/audit-events").json()
    assert any(e["event_type"] == "document_upload_rejected" for e in events)
    docs = client.get(f"/api/v1/projects/{pid}/documents").json()
    assert all(d["original_file_name"] != "malware.exe" for d in docs)


def test_upload_document_rejects_oversized_file(
    client: TestClient, monkeypatch
) -> None:
    from app.services import real_intake_service

    project = _create_project(client)
    pid = project["project_id"]

    real_settings = real_intake_service.get_settings()

    class _Tiny:
        MAX_PROJECT_UPLOAD_BYTES = 5
        PROJECT_UPLOAD_DIR = real_settings.PROJECT_UPLOAD_DIR
        allowed_project_upload_extensions_set = (
            real_settings.allowed_project_upload_extensions_set
        )

    monkeypatch.setattr(
        real_intake_service, "get_settings", lambda: _Tiny()
    )
    response = client.post(
        f"/api/v1/projects/{pid}/documents/upload",
        files={"file": ("big.pdf", b"way too many bytes", "application/pdf")},
    )
    assert response.status_code == 422
    assert "exceeds" in response.json()["detail"].lower()


def test_upload_document_rejects_empty_file(client: TestClient) -> None:
    project = _create_project(client)
    pid = project["project_id"]
    response = client.post(
        f"/api/v1/projects/{pid}/documents/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Reviewer findings
# ---------------------------------------------------------------------------


def _create_finding(client: TestClient, pid: str, **overrides) -> dict:
    payload = {
        "title": "Detention basin outlet detail missing",
        "category": "stormwater",
        "risk_level": "high",
        "evidence_status": "missing_evidence",
        "evidence_to_find": "Outlet control structure detail and sizing",
        "reason_it_matters": "Outlet sizing controls the release rate",
        "recommended_human_action": "Reviewer should request the outlet detail",
        "reviewer_notes": "Noticed during intake triage",
    }
    payload.update(overrides)
    response = client.post(f"/api/v1/projects/{pid}/findings", json=payload)
    return response


def test_create_finding_is_reviewer_owned(client: TestClient) -> None:
    project = _create_project(client)
    pid = project["project_id"]
    response = _create_finding(client, pid)
    assert response.status_code == 201, response.text
    finding = response.json()
    assert finding["finding_id"].startswith("find_user_")
    assert finding["finding_origin"] == "reviewer_created"
    assert finding["source_mode"] == "user_created"
    assert finding["human_review_status"] == "needs_reviewer_confirmation"
    assert finding["evidence_status"] == "missing_evidence"
    assert finding["created_by_name"] == "Demo Reviewer"

    events = client.get(f"/api/v1/projects/{pid}/audit-events").json()
    assert any(e["event_type"] == "finding_created" for e in events)


def test_create_finding_links_related_documents(client: TestClient) -> None:
    project = _create_project(client)
    pid = project["project_id"]
    doc = client.post(
        f"/api/v1/projects/{pid}/documents/register",
        json={"original_file_name": "grading.pdf", "document_type": "grading_plan"},
    ).json()
    response = _create_finding(
        client, pid, related_documents=[doc["document_id"]]
    )
    assert response.status_code == 201
    assert response.json()["related_documents"] == [doc["document_id"]]


def test_create_finding_rejects_prohibited_status(client: TestClient) -> None:
    project = _create_project(client)
    pid = project["project_id"]
    response = _create_finding(
        client, pid, human_review_status="approved"
    )
    assert response.status_code == 422


def test_create_finding_rejects_invalid_evidence_status(
    client: TestClient,
) -> None:
    project = _create_project(client)
    pid = project["project_id"]
    response = _create_finding(client, pid, evidence_status="passed")
    assert response.status_code == 422


def test_create_finding_rejects_prohibited_language(client: TestClient) -> None:
    project = _create_project(client)
    pid = project["project_id"]
    response = _create_finding(
        client, pid, title="Design validated and certified"
    )
    assert response.status_code == 422


def test_list_findings_includes_reviewer_findings(client: TestClient) -> None:
    project = _create_project(client)
    pid = project["project_id"]
    _create_finding(client, pid, title="First reviewer finding")
    findings = client.get(f"/api/v1/projects/{pid}/findings").json()
    assert any(f["title"] == "First reviewer finding" for f in findings)


# ---------------------------------------------------------------------------
# Evidence references
# ---------------------------------------------------------------------------


def test_create_evidence_reference(client: TestClient) -> None:
    project = _create_project(client)
    pid = project["project_id"]
    doc = client.post(
        f"/api/v1/projects/{pid}/documents/register",
        json={"original_file_name": "drainage.pdf", "document_type": "plan_set"},
    ).json()
    finding = _create_finding(client, pid).json()
    response = client.post(
        f"/api/v1/findings/{finding['finding_id']}/evidence-references",
        json={
            "document_id": doc["document_id"],
            "reviewer_note": "Sheet C-3 shows the basin outlet area",
            "page_number": 3,
            "sheet_number": "C-3.0",
            "section_label": "Outlet detail",
        },
    )
    assert response.status_code == 201, response.text
    ref = response.json()
    assert ref["finding_source_id"].startswith("evref_")
    assert ref["evidence_role"] == "requires_reviewer_confirmation"
    assert ref["sheet_number"] == "C-3.0"
    assert ref["source_mode"] == "user_created"

    refs = client.get(
        f"/api/v1/findings/{finding['finding_id']}/evidence-references"
    ).json()
    assert len(refs) == 1


def test_evidence_reference_unknown_finding_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/findings/find_missing/evidence-references",
        json={"document_id": "doc_x", "reviewer_note": "n/a"},
    )
    assert response.status_code == 404


def test_evidence_reference_cross_project_rejected(client: TestClient) -> None:
    project_a = _create_project(client, project_name="Evidence A")
    project_b = _create_project(client, project_name="Evidence B")
    doc_b = client.post(
        f"/api/v1/projects/{project_b['project_id']}/documents/register",
        json={"original_file_name": "b.pdf", "document_type": "plan_set"},
    ).json()
    finding_a = _create_finding(client, project_a["project_id"]).json()
    response = client.post(
        f"/api/v1/findings/{finding_a['finding_id']}/evidence-references",
        json={
            "document_id": doc_b["document_id"],
            "reviewer_note": "mismatched project",
        },
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Audit events and professional boundary
# ---------------------------------------------------------------------------


def test_audit_events_carry_actor_attribution(client: TestClient) -> None:
    project = _create_project(client)
    events = client.get(
        f"/api/v1/projects/{project['project_id']}/audit-events"
    ).json()
    assert events
    for event in events:
        assert event["actor_type"]
        assert "timestamp" in event
        # No raw IP or user agent is ever exposed.
        assert "source_ip" not in event
        assert "user_agent" not in event
        # Metadata must not leak secrets.
        meta_text = str(event.get("event_metadata", {})).lower()
        assert "api_key" not in meta_text
        assert "openai" not in meta_text


def test_no_prohibited_language_in_intake_payloads(client: TestClient) -> None:
    project = _create_project(client, project_name="Boundary Check Project")
    pid = project["project_id"]
    client.post(
        f"/api/v1/projects/{pid}/documents/register",
        json={"original_file_name": "x.pdf", "document_type": "plan_set"},
    )
    _create_finding(client, pid)

    blob = (
        client.get(f"/api/v1/projects/{pid}").text
        + client.get(f"/api/v1/projects/{pid}/documents").text
        + client.get(f"/api/v1/projects/{pid}/findings").text
    ).lower()
    for word in PROHIBITED_FINAL_DECISION_WORDS:
        assert word not in blob, f"prohibited word in payload: {word}"


def test_seeded_brookside_demo_still_intact(client: TestClient) -> None:
    project = client.get(f"/api/v1/projects/{BROOKSIDE_ID}").json()
    assert project["project_name"] == "Brookside Meadows Residential Subdivision"
    assert project["source_mode"] == "demo_fixture"
    assert project["acreage"] == 38.5
    documents = client.get(f"/api/v1/projects/{BROOKSIDE_ID}/documents").json()
    assert len(documents) >= 1
    assert all(d["source_mode"] == "demo_fixture" for d in documents)
    findings = client.get(f"/api/v1/projects/{BROOKSIDE_ID}/findings").json()
    assert len(findings) >= 1
    assert all(f["finding_origin"] == "seeded_demo" for f in findings)
