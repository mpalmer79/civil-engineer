"""Tests for the Phase 1 PR 1 real chunk pipeline from indexed PDF pages.

These tests build small in-memory PDFs, upload them through the existing upload
endpoint, index them into page records, then rebuild real-derived chunks from
the indexed page text. They confirm that only pages with extractable text
produce chunks, that chunks never span pages, that re-running is idempotent, and
that stormwater keywords populate. They also exercise the chunking helpers
directly for heading detection and multi-chunk splitting.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.safety import PROHIBITED_FINAL_DECISION_WORDS
from app.services import page_chunking_service
from app.services.page_chunking_service import (
    REAL_DERIVED_CHUNK_PREFIX,
    _chunk_page_text,
    _extract_keywords,
    _looks_like_heading,
)


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


def _create_project(client: TestClient, name: str = "Chunking Project") -> str:
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


def _index(client: TestClient, project_id: str, document_id: str) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/documents/{document_id}/index-pdf"
    )
    assert response.status_code == 200, response.text
    return response.json()


def _chunk(client: TestClient, project_id: str, document_id: str) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/documents/{document_id}/chunk-pages"
    )
    assert response.status_code == 200, response.text
    return response.json()


def _document_chunks(client: TestClient, document_id: str) -> list[dict]:
    response = client.get(f"/api/v1/documents/{document_id}/chunks")
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------------------
# API driven tests
# ---------------------------------------------------------------------------


def test_indexed_page_creates_chunks(client: TestClient) -> None:
    pid = _create_project(client)
    did = _upload_pdf(
        client, pid, _make_pdf(["Stormwater detention basin outlet on page one"])
    )
    _index(client, pid, did)
    summary = _chunk(client, pid, did)
    assert summary["chunk_count"] >= 1
    assert summary["pages_chunked"] == 1

    chunks = _document_chunks(client, did)
    assert len(chunks) == summary["chunk_count"]
    first = chunks[0]
    assert first["page_number"] == 1
    assert first["chunk_id"].startswith(REAL_DERIVED_CHUNK_PREFIX)
    assert first["document_type"] == "stormwater_report"
    assert first["file_name"] == "report.pdf"
    assert first["related_checklist_items"] == []
    assert first["related_findings"] == []
    assert first["content"].strip() != ""


def test_no_text_page_creates_no_chunks(client: TestClient) -> None:
    pid = _create_project(client)
    # A single page with no embedded text content stream.
    did = _upload_pdf(client, pid, _make_pdf([None]))
    index_summary = _index(client, pid, did)
    assert index_summary["pages_without_text"] == 1
    assert index_summary["pages_with_text"] == 0

    summary = _chunk(client, pid, did)
    assert summary["chunk_count"] == 0
    assert summary["pages_chunked"] == 0
    assert _document_chunks(client, did) == []


def test_chunks_do_not_span_pages(client: TestClient) -> None:
    pid = _create_project(client)
    did = _upload_pdf(
        client,
        pid,
        _make_pdf(
            [
                "Alpha stormwater grading narrative for page one only",
                "Bravo detention basin narrative for page two only",
            ]
        ),
    )
    _index(client, pid, did)
    _chunk(client, pid, did)

    chunks = _document_chunks(client, did)
    assert {c["page_number"] for c in chunks} == {1, 2}
    for chunk in chunks:
        text = chunk["content"].lower()
        # No chunk may carry content from both pages at once.
        assert not ("alpha" in text and "bravo" in text)
        if chunk["page_number"] == 1:
            assert "bravo" not in text
        if chunk["page_number"] == 2:
            assert "alpha" not in text


def test_rerun_does_not_duplicate_chunks(client: TestClient) -> None:
    pid = _create_project(client)
    did = _upload_pdf(
        client,
        pid,
        _make_pdf(["Stormwater runoff and erosion control on page one"]),
    )
    _index(client, pid, did)

    first = _chunk(client, pid, did)
    first_chunks = _document_chunks(client, did)
    assert first["removed_prior_chunk_count"] == 0

    second = _chunk(client, pid, did)
    second_chunks = _document_chunks(client, did)

    assert second["chunk_count"] == first["chunk_count"]
    assert len(second_chunks) == len(first_chunks)
    assert second["removed_prior_chunk_count"] == first["chunk_count"]
    # Stable, non-duplicated chunk ids across runs.
    assert {c["chunk_id"] for c in second_chunks} == {
        c["chunk_id"] for c in first_chunks
    }


def test_keywords_populate_for_stormwater_terms(client: TestClient) -> None:
    pid = _create_project(client)
    did = _upload_pdf(
        client,
        pid,
        _make_pdf(
            ["Stormwater detention basin and bioretention on page one"]
        ),
    )
    _index(client, pid, did)
    _chunk(client, pid, did)

    chunks = _document_chunks(client, did)
    all_keywords = {kw for chunk in chunks for kw in chunk["keywords"]}
    assert "stormwater" in all_keywords
    assert "detention basin" in all_keywords


def test_rebuild_rejects_unknown_document(client: TestClient) -> None:
    pid = _create_project(client)
    response = client.post(
        f"/api/v1/projects/{pid}/documents/doc_missing/chunk-pages"
    )
    assert response.status_code == 404


def test_chunk_summary_has_no_final_decision_language(
    client: TestClient,
) -> None:
    pid = _create_project(client)
    did = _upload_pdf(
        client, pid, _make_pdf(["Stormwater narrative for the review record"])
    )
    _index(client, pid, did)
    response = client.post(
        f"/api/v1/projects/{pid}/documents/{did}/chunk-pages"
    )
    blob = response.text.lower()
    for word in PROHIBITED_FINAL_DECISION_WORDS:
        assert word.lower() not in blob


# ---------------------------------------------------------------------------
# Unit tests for chunking helpers
# ---------------------------------------------------------------------------


def test_chunk_page_text_splits_long_text_within_a_page() -> None:
    long_text = " ".join(f"word{i}" for i in range(300))
    chunks = _chunk_page_text(long_text)
    assert len(chunks) >= 2
    # Every chunk is non-empty and carries no section heading for plain text.
    for heading, content in chunks:
        assert heading is None
        assert content.strip() != ""


def test_chunk_page_text_detects_section_heading() -> None:
    text = "Stormwater Strategy\n" + " ".join(
        ["the detention basin discharges toward the culvert"] * 5
    )
    chunks = _chunk_page_text(text)
    assert chunks
    assert chunks[0][0] == "Stormwater Strategy"


def test_looks_like_heading_rejects_sentences() -> None:
    assert _looks_like_heading("Project Overview") is True
    assert _looks_like_heading("MAINTENANCE") is True
    assert (
        _looks_like_heading(
            "The stormwater strategy combines several measures together."
        )
        is False
    )


def test_extract_keywords_prefers_domain_terms() -> None:
    keywords = _extract_keywords(
        "The infiltration basin and stormwater runoff feed the culvert."
    )
    assert "infiltration basin" in keywords
    assert "stormwater" in keywords
    assert len(keywords) <= 8


def test_rebuild_is_idempotent_and_keeps_seeded_chunks(client: TestClient) -> None:
    # The seeded Brookside Meadows project carries seeded chunks. Rebuilding a
    # real document's chunks must never remove those seeded chunks.
    seeded = client.get("/api/v1/projects/proj_brookside_meadows/chunks")
    assert seeded.status_code == 200
    seeded_ids = {c["chunk_id"] for c in seeded.json()}
    assert seeded_ids  # the seed fixture provides chunks
    assert not any(
        cid.startswith(REAL_DERIVED_CHUNK_PREFIX) for cid in seeded_ids
    )

    pid = _create_project(client)
    did = _upload_pdf(client, pid, _make_pdf(["Stormwater page one narrative"]))
    _index(client, pid, did)
    _chunk(client, pid, did)
    _chunk(client, pid, did)

    still_seeded = client.get("/api/v1/projects/proj_brookside_meadows/chunks")
    assert {c["chunk_id"] for c in still_seeded.json()} == seeded_ids
