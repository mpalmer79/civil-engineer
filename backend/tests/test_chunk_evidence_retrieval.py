"""Tests for keyword retrieval over real-derived document chunks.

These tests build a small PDF, upload and index it, build real-derived chunks
from the indexed page text, then search those chunks through the chunk retrieval
path. They confirm that real-derived chunks are searchable evidence with
page-level citation context, that seeded chunks are never returned by this path,
that non-indexed pages do not produce chunk results, that the empty response is
honest, and that a chunk-derived result flows into the existing candidate and
citation workflow.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.safety import PROHIBITED_FINAL_DECISION_WORDS
from app.services.page_chunking_service import REAL_DERIVED_CHUNK_PREFIX

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


def _create_project(client: TestClient, name: str = "Chunk Retrieval Project") -> str:
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
    file_name: str = "stormwater_report.pdf",
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


def _chunk_search(
    client: TestClient, project_id: str, query: str, **filters
) -> dict:
    body: dict = {"query_text": query}
    if filters:
        body["filters"] = filters
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-retrieval/chunk-search",
        json=body,
    )
    assert response.status_code == 200, response.text
    return response.json()


def _indexed_chunked_document(
    client: TestClient,
    pages: list[str | None],
    name: str = "Chunk Retrieval Project",
) -> tuple[str, str]:
    pid = _create_project(client, name)
    did = _upload_pdf(client, pid, _make_pdf(pages))
    _index(client, pid, did)
    _chunk(client, pid, did)
    return pid, did


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def test_real_derived_chunks_returned_by_keyword_search(client: TestClient) -> None:
    pid, did = _indexed_chunked_document(
        client, ["Stormwater detention basin outlet on page one"]
    )
    result = _chunk_search(client, pid, "detention basin")
    assert result["result_count"] >= 1
    first = result["results"][0]
    assert first["document_id"] == did
    assert first["chunk_id"].startswith(REAL_DERIVED_CHUNK_PREFIX)
    assert first["candidate_origin"] == "chunk_search"
    assert "real-derived page chunk" in first["ranking_reason"]
    assert 0.0 < first["ranking_score"] < 1.0


def test_result_includes_page_citation_fields(client: TestClient) -> None:
    pid, did = _indexed_chunked_document(
        client, ["Infiltration basin drawdown time on page one"]
    )
    result = _chunk_search(client, pid, "infiltration drawdown")
    assert result["results"]
    r = result["results"][0]
    for field in (
        "document_id",
        "document_name",
        "document_type",
        "chunk_id",
        "document_page_id",
        "page_number",
        "page_label",
        "text_extraction_status",
        "excerpt",
        "match_terms",
        "ranking_score",
        "ranking_reason",
        "candidate_origin",
    ):
        assert field in r, f"missing field {field}"
    assert r["document_name"] == "stormwater_report.pdf"
    assert r["document_type"] == "stormwater_report"
    assert r["page_number"] == 1
    assert r["text_extraction_status"] == "text_extracted"
    assert r["match_terms"]


def test_document_page_id_resolves_when_page_exists(client: TestClient) -> None:
    pid, did = _indexed_chunked_document(
        client, ["Culvert capacity analysis on page one"]
    )
    # The document page list gives the canonical document_page_id for page 1.
    pages = client.get(
        f"/api/v1/projects/{pid}/documents/{did}/pages"
    ).json()
    page_one_id = next(p["document_page_id"] for p in pages if p["page_number"] == 1)

    result = _chunk_search(client, pid, "culvert capacity")
    assert result["results"]
    assert result["results"][0]["document_page_id"] == page_one_id


def test_not_indexed_page_produces_no_chunk_results(client: TestClient) -> None:
    # A single page with no embedded text. Indexing marks it no_extractable_text,
    # so chunking produces nothing and chunk search finds no searchable chunks.
    pid = _create_project(client, "No Text Project")
    did = _upload_pdf(client, pid, _make_pdf([None]))
    index_summary = _index(client, pid, did)
    assert index_summary["pages_with_text"] == 0
    chunk_summary = _chunk(client, pid, did)
    assert chunk_summary["chunk_count"] == 0

    result = _chunk_search(client, pid, "stormwater")
    assert result["result_count"] == 0
    assert "not available yet" in result["message"]
    # Honest: never implies a negative evidence conclusion.
    assert "not a finding" in result["message"].lower()


def test_empty_match_message_is_honest(client: TestClient) -> None:
    pid, did = _indexed_chunked_document(
        client, ["Stormwater grading narrative on page one"]
    )
    result = _chunk_search(client, pid, "zzzznonexistentterm")
    assert result["result_count"] == 0
    assert "did not" not in result["message"].lower()
    assert "no real-derived chunk text matched" in result["message"].lower()
    assert "not a finding" in result["message"].lower()


def test_seeded_chunks_not_returned_as_real_derived(client: TestClient) -> None:
    # The seeded Brookside project carries seeded chunks (chunk_*). The chunk
    # search path must never return them: they have no real-derived prefix and
    # their pages are not indexed DocumentPage rows.
    result = _chunk_search(client, BROOKSIDE_ID, "stormwater")
    for r in result["results"]:
        assert r["chunk_id"].startswith(REAL_DERIVED_CHUNK_PREFIX)
    # Confirm the seeded project still exposes seeded chunks via the chunk list,
    # so we know they exist and were simply excluded from real-derived search.
    seeded = client.get(f"/api/v1/projects/{BROOKSIDE_ID}/chunks").json()
    assert seeded
    assert not any(
        c["chunk_id"].startswith(REAL_DERIVED_CHUNK_PREFIX) for c in seeded
    )


# ---------------------------------------------------------------------------
# Candidate and citation flow
# ---------------------------------------------------------------------------


def test_chunk_result_saves_candidate_and_resolves_page_id(
    client: TestClient,
) -> None:
    pid, did = _indexed_chunked_document(
        client, ["Detention basin outlet structure on page one"]
    )
    search = _chunk_search(client, pid, "detention basin outlet")
    result = search["results"][0]

    # Save a candidate from the chunk result. Pass only document_id + page_number
    # (as a chunk-derived result would); the service resolves document_page_id.
    save = client.post(
        f"/api/v1/projects/{pid}/evidence-candidates",
        json={
            "document_id": result["document_id"],
            "page_number": result["page_number"],
            "candidate_title": "Detention basin outlet structure",
            "candidate_excerpt": result["excerpt"],
            "match_terms": result["match_terms"],
            "ranking_score": result["ranking_score"],
            "ranking_reason": result["ranking_reason"],
            "candidate_origin": "chunk_search",
            "retrieval_query_id": result["retrieval_query_id"],
        },
    )
    assert save.status_code == 201, save.text
    candidate = save.json()
    assert candidate["candidate_origin"] == "chunk_search"
    assert candidate["document_page_id"] is not None
    assert candidate["page_number"] == 1


def test_chunk_candidate_promotes_to_draft_with_page_citation(
    client: TestClient,
) -> None:
    pid, did = _indexed_chunked_document(
        client, ["Infiltration basin drawdown time on page one"]
    )
    result = _chunk_search(client, pid, "infiltration drawdown")["results"][0]
    candidate = client.post(
        f"/api/v1/projects/{pid}/evidence-candidates",
        json={
            "document_id": result["document_id"],
            "page_number": result["page_number"],
            "candidate_title": "Infiltration basin drawdown",
            "candidate_excerpt": result["excerpt"],
            "candidate_origin": "chunk_search",
        },
    ).json()

    promote = client.post(
        f"/api/v1/projects/{pid}/evidence-candidates/"
        f"{candidate['evidence_candidate_id']}/promote-to-draft-finding",
        json={
            "title": "Infiltration basin drawdown needs reviewer follow-up",
            "category": "stormwater",
            "risk_level": "medium",
            "evidence_to_find": "Drawdown time calculation",
            "reason_it_matters": "Drawdown affects function",
            "recommended_human_action": "Request the drawdown calculation",
        },
    )
    assert promote.status_code == 201, promote.text
    body = promote.json()
    assert body["finding"]["finding_origin"] == "retrieval_candidate"
    citation = body["citation"]
    assert citation["document_id"] == did
    assert citation["page_number"] == 1
    # The citation resolves the real indexed page for citation integrity.
    assert citation["document_page_id"] is not None
    assert body["candidate"]["candidate_status"] == "promoted_to_draft"


def test_chunk_search_introduces_no_prohibited_language(client: TestClient) -> None:
    pid, did = _indexed_chunked_document(
        client, ["Stormwater detention basin on page one"]
    )
    response = client.post(
        f"/api/v1/projects/{pid}/evidence-retrieval/chunk-search",
        json={"query_text": "detention basin"},
    )
    blob = response.text.lower()
    for word in PROHIBITED_FINAL_DECISION_WORDS:
        assert word.lower() not in blob

    # The honest empty-state message also avoids prohibited vocabulary.
    empty = client.post(
        f"/api/v1/projects/{pid}/evidence-retrieval/chunk-search",
        json={"query_text": "zzzznope"},
    )
    empty_blob = empty.text.lower()
    for word in PROHIBITED_FINAL_DECISION_WORDS:
        assert word.lower() not in empty_blob
