"""Tests for Production Foundations Sprint 2 PDF page indexing and citations.

These tests build small in-memory PDFs (with and without an embedded text
layer), upload them through the Sprint 1 upload endpoint, index them into page
records, read pages, and create reviewer evidence citations. They confirm the
review-support boundary: no final-decision wording, no raw storage paths in
responses, and no extracted page text in audit metadata.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.safety import PROHIBITED_FINAL_DECISION_WORDS

BROOKSIDE_ID = "proj_brookside_meadows"


def _make_pdf(pages_text: list[str | None]) -> bytes:
    """Build a minimal valid PDF. A None page has no text content stream."""

    n = len(pages_text)
    objects: dict[int, object] = {}
    objects[1] = "<< /Type /Catalog /Pages 2 0 R >>"
    objects[3] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    page_nums: list[int] = []
    num = 4
    for text in pages_text:
        page_num = num
        content_num = num + 1
        num += 2
        page_nums.append(page_num)
        stream = "" if text is None else f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET"
        objects[page_num] = (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_num} 0 R >>"
        )
        objects[content_num] = ("STREAM", stream)
    kids = " ".join(f"{pn} 0 R" for pn in page_nums)
    objects[2] = f"<< /Type /Pages /Kids [{kids}] /Count {n} >>"

    max_num = num - 1
    out = b"%PDF-1.4\n"
    offsets: dict[int, int] = {}
    for i in range(1, max_num + 1):
        if i not in objects:
            continue
        offsets[i] = len(out)
        body = objects[i]
        if isinstance(body, tuple):
            stream = body[1]
            obj = (
                f"{i} 0 obj\n<< /Length {len(stream)} >>\nstream\n"
                f"{stream}\nendstream\nendobj\n"
            )
        else:
            obj = f"{i} 0 obj\n{body}\nendobj\n"
        out += obj.encode("latin-1")
    xref_pos = len(out)
    count = max_num + 1
    xref = f"xref\n0 {count}\n0000000000 65535 f \n"
    for i in range(1, count):
        xref += f"{offsets.get(i, 0):010d} 00000 n \n"
    out += xref.encode("latin-1")
    out += (
        f"trailer\n<< /Size {count} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF"
    ).encode("latin-1")
    return out


def _create_project(client: TestClient, name: str = "PDF Indexing Project") -> str:
    response = client.post(
        "/api/v1/projects",
        json={
            "project_name": name,
            "project_type": "Commercial site plan",
            "jurisdiction": "Town of Riverton",
            "review_type": "Site plan stormwater review",
            "review_domain": "stormwater",
            "location_context": "Infill parcel",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["project_id"]


def _upload_pdf(
    client: TestClient,
    project_id: str,
    pdf_bytes: bytes,
    file_name: str = "report.pdf",
) -> str:
    response = client.post(
        f"/api/v1/projects/{project_id}/documents/upload",
        files={"file": (file_name, pdf_bytes, "application/pdf")},
        data={"document_type": "stormwater_report"},
    )
    assert response.status_code == 201, response.text
    return response.json()["document_id"]


def _create_finding(client: TestClient, project_id: str) -> str:
    response = client.post(
        f"/api/v1/projects/{project_id}/findings",
        json={
            "title": "Detention basin outlet detail missing",
            "category": "stormwater",
            "risk_level": "high",
            "evidence_status": "missing_evidence",
            "evidence_to_find": "Outlet detail",
            "reason_it_matters": "Controls release rate",
            "recommended_human_action": "Request the outlet detail",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["finding_id"]


# ---------------------------------------------------------------------------
# PDF indexing
# ---------------------------------------------------------------------------


def test_index_pdf_with_text_creates_pages(client: TestClient) -> None:
    pid = _create_project(client)
    did = _upload_pdf(
        client,
        pid,
        _make_pdf(["Hello stormwater review page one", "Outlet detail page two"]),
    )
    response = client.post(
        f"/api/v1/projects/{pid}/documents/{did}/index-pdf"
    )
    assert response.status_code == 200, response.text
    summary = response.json()
    assert summary["page_count"] == 2
    assert summary["pages_with_text"] == 2
    assert summary["pages_without_text"] == 0
    assert summary["processing_status"] == "indexed_with_text"
    assert summary["text_extraction_status"] == "text_extracted"
    # Raw storage paths must never appear in the response.
    assert "project_uploads" not in response.text
    assert "/home/" not in response.text

    pages = client.get(
        f"/api/v1/projects/{pid}/documents/{did}/pages"
    ).json()
    assert len(pages) == 2
    assert pages[0]["page_number"] == 1
    assert pages[0]["text_extraction_status"] == "text_extracted"
    assert pages[0]["char_count"] > 0
    assert pages[0]["word_count"] > 0
    assert "stormwater" in pages[0]["extracted_text"]

    # Document now reflects indexed state.
    doc = client.get(f"/api/v1/projects/{pid}/documents").json()[0]
    assert doc["page_count"] == 2
    assert doc["processing_status"] == "indexed_with_text"
    assert doc["indexed_at"] is not None


def test_index_pdf_records_audit_events_without_text(client: TestClient) -> None:
    pid = _create_project(client)
    secret_text = "UNIQUEMARKER stormwater narrative body"
    did = _upload_pdf(client, pid, _make_pdf([secret_text]))
    client.post(f"/api/v1/projects/{pid}/documents/{did}/index-pdf")

    events = client.get(f"/api/v1/projects/{pid}/audit-events").json()
    types = [e["event_type"] for e in events]
    assert "document_indexing_started" in types
    assert "document_indexed" in types
    assert "document_page_text_extracted" in types
    # Full extracted page text must never be written to audit metadata.
    blob = str(events)
    assert "UNIQUEMARKER" not in blob


def test_get_single_page(client: TestClient) -> None:
    pid = _create_project(client)
    did = _upload_pdf(client, pid, _make_pdf(["Only page text here"]))
    client.post(f"/api/v1/projects/{pid}/documents/{did}/index-pdf")
    response = client.get(
        f"/api/v1/projects/{pid}/documents/{did}/pages/1"
    )
    assert response.status_code == 200
    assert response.json()["page_number"] == 1


def test_get_missing_page_404(client: TestClient) -> None:
    pid = _create_project(client)
    did = _upload_pdf(client, pid, _make_pdf(["One page"]))
    client.post(f"/api/v1/projects/{pid}/documents/{did}/index-pdf")
    assert (
        client.get(
            f"/api/v1/projects/{pid}/documents/{did}/pages/99"
        ).status_code
        == 404
    )


def test_index_pdf_without_extractable_text(client: TestClient) -> None:
    pid = _create_project(client)
    did = _upload_pdf(client, pid, _make_pdf([None, None]))
    response = client.post(
        f"/api/v1/projects/{pid}/documents/{did}/index-pdf"
    )
    assert response.status_code == 200, response.text
    summary = response.json()
    assert summary["pages_with_text"] == 0
    assert summary["pages_without_text"] == 2
    assert summary["processing_status"] == "indexed_without_text"
    assert summary["text_extraction_status"] == "no_extractable_text"
    pages = client.get(
        f"/api/v1/projects/{pid}/documents/{did}/pages"
    ).json()
    assert all(p["text_extraction_status"] == "no_extractable_text" for p in pages)


def test_index_rejects_non_pdf_document(client: TestClient) -> None:
    pid = _create_project(client)
    response = client.post(
        f"/api/v1/projects/{pid}/documents/upload",
        files={"file": ("data.csv", b"a,b,c\n1,2,3\n", "text/csv")},
        data={"document_type": "other"},
    )
    did = response.json()["document_id"]
    index = client.post(f"/api/v1/projects/{pid}/documents/{did}/index-pdf")
    assert index.status_code == 422
    assert "not a pdf" in index.json()["detail"].lower()


def test_index_rejects_registered_document_without_file(
    client: TestClient,
) -> None:
    pid = _create_project(client)
    did = client.post(
        f"/api/v1/projects/{pid}/documents/register",
        json={"original_file_name": "plan.pdf", "document_type": "plan_set"},
    ).json()["document_id"]
    index = client.post(f"/api/v1/projects/{pid}/documents/{did}/index-pdf")
    assert index.status_code == 422
    assert "uploaded pdf file" in index.json()["detail"].lower()


def test_index_handles_malformed_pdf(client: TestClient) -> None:
    pid = _create_project(client)
    did = _upload_pdf(client, pid, b"this is not a real pdf", file_name="bad.pdf")
    index = client.post(f"/api/v1/projects/{pid}/documents/{did}/index-pdf")
    assert index.status_code == 422
    assert "could not be opened" in index.json()["detail"].lower()
    # The document records the failure state.
    doc = client.get(f"/api/v1/projects/{pid}/documents").json()[0]
    assert doc["processing_status"] == "indexing_failed"


def test_index_handles_missing_file_on_disk(client: TestClient) -> None:
    from pathlib import Path

    from app.db import models
    from app.db.database import SessionLocal

    pid = _create_project(client)
    did = _upload_pdf(client, pid, _make_pdf(["Will be removed"]))
    # Remove the stored file to simulate missing storage.
    db = SessionLocal()
    try:
        document = db.get(models.Document, did)
        Path(document.storage_path).unlink()
    finally:
        db.close()
    index = client.post(f"/api/v1/projects/{pid}/documents/{did}/index-pdf")
    assert index.status_code == 422
    assert "could not be found" in index.json()["detail"].lower()


def test_seeded_demo_document_cannot_be_indexed(client: TestClient) -> None:
    docs = client.get(f"/api/v1/projects/{BROOKSIDE_ID}/documents").json()
    seeded = docs[0]
    index = client.post(
        f"/api/v1/projects/{BROOKSIDE_ID}/documents/{seeded['document_id']}/index-pdf"
    )
    # Seeded demo documents have no uploaded file, so indexing is rejected.
    assert index.status_code == 422


# ---------------------------------------------------------------------------
# Evidence citations
# ---------------------------------------------------------------------------


def test_create_citation_to_page(client: TestClient) -> None:
    pid = _create_project(client)
    did = _upload_pdf(client, pid, _make_pdf(["Outlet detail on page one"]))
    client.post(f"/api/v1/projects/{pid}/documents/{did}/index-pdf")
    fid = _create_finding(client, pid)
    response = client.post(
        f"/api/v1/projects/{pid}/findings/{fid}/citations",
        json={
            "document_id": did,
            "page_number": 1,
            "section_label": "Outlet detail",
            "quoted_excerpt": "Outlet detail on page one",
            "reviewer_note": "Supports the missing outlet detail finding",
        },
    )
    assert response.status_code == 201, response.text
    citation = response.json()
    assert citation["evidence_citation_id"].startswith("cite_")
    assert citation["page_number"] == 1
    assert citation["document_page_id"] is not None
    assert citation["citation_type"] == "reviewer_selected"
    assert citation["citation_status"] == "needs_reviewer_confirmation"

    events = client.get(f"/api/v1/projects/{pid}/audit-events").json()
    assert any(e["event_type"] == "evidence_citation_created" for e in events)

    listed = client.get(
        f"/api/v1/projects/{pid}/findings/{fid}/citations"
    ).json()
    assert len(listed) == 1
    project_citations = client.get(
        f"/api/v1/projects/{pid}/evidence-citations"
    ).json()
    assert len(project_citations) == 1


def test_citation_to_no_text_page_is_page_reference_only(
    client: TestClient,
) -> None:
    pid = _create_project(client)
    did = _upload_pdf(client, pid, _make_pdf([None]))
    client.post(f"/api/v1/projects/{pid}/documents/{did}/index-pdf")
    fid = _create_finding(client, pid)
    response = client.post(
        f"/api/v1/projects/{pid}/findings/{fid}/citations",
        json={"document_id": did, "page_number": 1, "reviewer_note": "scan page"},
    )
    assert response.status_code == 201
    assert response.json()["citation_status"] == "page_reference_only"


def test_citation_rejects_missing_finding(client: TestClient) -> None:
    pid = _create_project(client)
    did = _upload_pdf(client, pid, _make_pdf(["x"]))
    response = client.post(
        f"/api/v1/projects/{pid}/findings/find_missing/citations",
        json={"document_id": did, "reviewer_note": "n/a"},
    )
    assert response.status_code == 404


def test_citation_rejects_missing_document(client: TestClient) -> None:
    pid = _create_project(client)
    fid = _create_finding(client, pid)
    response = client.post(
        f"/api/v1/projects/{pid}/findings/{fid}/citations",
        json={"document_id": "doc_missing", "reviewer_note": "n/a"},
    )
    assert response.status_code == 404


def test_citation_rejects_prohibited_language(client: TestClient) -> None:
    pid = _create_project(client)
    did = _upload_pdf(client, pid, _make_pdf(["x"]))
    fid = _create_finding(client, pid)
    response = client.post(
        f"/api/v1/projects/{pid}/findings/{fid}/citations",
        json={
            "document_id": did,
            "reviewer_note": "This citation confirms the design is certified",
        },
    )
    assert response.status_code == 422


def test_update_and_delete_citation(client: TestClient) -> None:
    pid = _create_project(client)
    did = _upload_pdf(client, pid, _make_pdf(["page text"]))
    client.post(f"/api/v1/projects/{pid}/documents/{did}/index-pdf")
    fid = _create_finding(client, pid)
    cid = client.post(
        f"/api/v1/projects/{pid}/findings/{fid}/citations",
        json={"document_id": did, "page_number": 1, "reviewer_note": "note"},
    ).json()["evidence_citation_id"]

    patched = client.patch(
        f"/api/v1/projects/{pid}/findings/{fid}/citations/{cid}",
        json={"citation_status": "reviewer_selected", "reviewer_note": "updated"},
    )
    assert patched.status_code == 200
    assert patched.json()["citation_status"] == "reviewer_selected"

    deleted = client.delete(
        f"/api/v1/projects/{pid}/findings/{fid}/citations/{cid}"
    )
    assert deleted.status_code == 200
    assert (
        len(
            client.get(
                f"/api/v1/projects/{pid}/findings/{fid}/citations"
            ).json()
        )
        == 0
    )


def test_citation_payloads_have_no_prohibited_language(client: TestClient) -> None:
    pid = _create_project(client)
    did = _upload_pdf(client, pid, _make_pdf(["page text"]))
    client.post(f"/api/v1/projects/{pid}/documents/{did}/index-pdf")
    fid = _create_finding(client, pid)
    client.post(
        f"/api/v1/projects/{pid}/findings/{fid}/citations",
        json={"document_id": did, "page_number": 1, "reviewer_note": "ok note"},
    )
    blob = (
        client.get(f"/api/v1/projects/{pid}/evidence-citations").text
        + client.get(f"/api/v1/projects/{pid}/documents/{did}/pages").text
    ).lower()
    for word in PROHIBITED_FINAL_DECISION_WORDS:
        assert word not in blob, f"prohibited word in payload: {word}"


def test_update_missing_citation_404(client: TestClient) -> None:
    pid = _create_project(client)
    fid = _create_finding(client, pid)
    response = client.patch(
        f"/api/v1/projects/{pid}/findings/{fid}/citations/cite_missing",
        json={"reviewer_note": "x"},
    )
    assert response.status_code == 404


def test_delete_missing_citation_404(client: TestClient) -> None:
    pid = _create_project(client)
    fid = _create_finding(client, pid)
    response = client.delete(
        f"/api/v1/projects/{pid}/findings/{fid}/citations/cite_missing"
    )
    assert response.status_code == 404


def test_citation_with_explicit_page_id(client: TestClient) -> None:
    pid = _create_project(client)
    did = _upload_pdf(client, pid, _make_pdf(["page one text"]))
    client.post(f"/api/v1/projects/{pid}/documents/{did}/index-pdf")
    fid = _create_finding(client, pid)
    page = client.get(
        f"/api/v1/projects/{pid}/documents/{did}/pages/1"
    ).json()
    response = client.post(
        f"/api/v1/projects/{pid}/findings/{fid}/citations",
        json={
            "document_id": did,
            "document_page_id": page["document_page_id"],
            "reviewer_note": "explicit page id",
        },
    )
    assert response.status_code == 201
    assert response.json()["document_page_id"] == page["document_page_id"]


def test_citation_without_page_is_extraction_unavailable(
    client: TestClient,
) -> None:
    pid = _create_project(client)
    did = _upload_pdf(client, pid, _make_pdf(["page one text"]))
    fid = _create_finding(client, pid)
    # No indexing and no page_number: the citation is a general document
    # reference with no indexed text behind it.
    response = client.post(
        f"/api/v1/projects/{pid}/findings/{fid}/citations",
        json={"document_id": did, "reviewer_note": "general reference"},
    )
    assert response.status_code == 201
    assert response.json()["citation_status"] == "extraction_unavailable"


# ---------------------------------------------------------------------------
# Regression
# ---------------------------------------------------------------------------


def test_health_still_works(client: TestClient) -> None:
    assert client.get("/health").status_code == 200


def test_brookside_demo_still_loads(client: TestClient) -> None:
    project = client.get(f"/api/v1/projects/{BROOKSIDE_ID}").json()
    assert project["project_name"] == "Brookside Meadows Residential Subdivision"
    assert project["source_mode"] == "demo_fixture"
