"""Tests for semantic and hybrid retrieval over real-derived chunks."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.services.page_chunking_service import REAL_DERIVED_CHUNK_PREFIX

from tests.test_chunk_evidence_retrieval import (
    _create_project,
    _index,
    _chunk,
    _indexed_chunked_document,
    _make_pdf,
    _upload_pdf,
)

BROOKSIDE_ID = "proj_brookside_meadows"


def _embed(client: TestClient, project_id: str) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-retrieval/embed-chunks"
    )
    assert response.status_code == 200, response.text
    return response.json()


def _search(client: TestClient, project_id: str, query: str, mode: str, **filters) -> dict:
    body: dict = {"query_text": query, "mode": mode}
    if filters:
        body["filters"] = filters
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-retrieval/chunk-search",
        json=body,
    )
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Semantic
# ---------------------------------------------------------------------------


def test_semantic_search_returns_embedded_chunks(client: TestClient) -> None:
    pid, did = _indexed_chunked_document(
        client, ["Detention basin outlet structure grading slope on page one"]
    )
    _embed(client, pid)
    result = _search(client, pid, "detention basin", "semantic")
    assert result["query_type"] == "chunk_semantic"
    assert result["result_count"] >= 1
    first = result["results"][0]
    assert first["chunk_id"].startswith(REAL_DERIVED_CHUNK_PREFIX)
    assert first["ranking_reason"] == (
        "Ranked by semantic similarity using chunk embedding."
    )
    assert first["candidate_origin"] == "chunk_search"
    assert 0.0 < first["ranking_score"] < 1.0


def test_semantic_matches_synonyms_without_keyword_overlap(
    client: TestClient,
) -> None:
    pid, did = _indexed_chunked_document(
        client, ["Detention basin outlet structure grading slope on page one"]
    )
    _embed(client, pid)
    # "retention pond" shares no tokens with "detention basin" but shares the
    # impoundment concept, so semantic search still surfaces the chunk.
    result = _search(client, pid, "retention pond", "semantic")
    assert result["result_count"] >= 1
    first = result["results"][0]
    # A semantic-only match does not fake keyword terms.
    assert first["match_terms"] == []
    # Page citation context is still present.
    assert first["page_number"] == 1
    assert first["document_page_id"] is not None
    assert first["text_extraction_status"] == "text_extracted"


def test_semantic_search_excludes_seeded_chunks(client: TestClient) -> None:
    # Brookside has only seeded chunks and no embeddings; semantic search returns
    # nothing and an honest message, never a seeded chunk.
    result = _search(client, BROOKSIDE_ID, "stormwater", "semantic")
    assert result["result_count"] == 0
    assert "not a finding about the document content" in result["message"].lower()


def test_semantic_search_without_embeddings_is_honest(client: TestClient) -> None:
    # Chunks exist but were never embedded: semantic search returns no results
    # and does not imply absence.
    pid, did = _indexed_chunked_document(
        client, ["Stormwater detention basin on page one"]
    )
    result = _search(client, pid, "detention basin", "semantic")
    assert result["result_count"] == 0
    assert "not a finding about the document content" in result["message"].lower()


# ---------------------------------------------------------------------------
# Hybrid
# ---------------------------------------------------------------------------


def _long_page_text() -> str:
    # More than the chunk word target so a single page yields multiple chunks.
    sentence = (
        "The detention basin outlet and stormwater drainage culvert convey "
        "runoff toward the infiltration basin and bioretention area. "
    )
    return sentence * 20


def test_hybrid_returns_one_result_per_page(client: TestClient) -> None:
    pid = _create_project(client, "Hybrid Dedup Project")
    did = _upload_pdf(client, pid, _make_pdf([_long_page_text()]))
    _index(client, pid, did)
    summary = _chunk(client, pid, did)
    assert summary["chunk_count"] >= 2  # one page, multiple chunks
    _embed(client, pid)

    result = _search(client, pid, "detention basin culvert", "hybrid")
    assert result["query_type"] == "chunk_hybrid"
    assert result["result_count"] >= 1
    pages = [(r["document_id"], r["page_number"]) for r in result["results"]]
    assert len(pages) == len(set(pages))  # deduplicated to one result per page
    first = result["results"][0]
    assert first["ranking_reason"] == (
        "Ranked by keyword and semantic signals from real-derived page chunks."
    )


def test_hybrid_filters_narrow_results(client: TestClient) -> None:
    pid, did = _indexed_chunked_document(
        client, ["Detention basin outlet on page one"]
    )
    _embed(client, pid)
    # A document filter that excludes the only document yields no results.
    result = _search(
        client, pid, "detention basin", "hybrid", document_id="doc_does_not_exist"
    )
    assert result["result_count"] == 0


def test_hybrid_result_saves_and_promotes_with_citation(client: TestClient) -> None:
    pid, did = _indexed_chunked_document(
        client, ["Detention basin outlet structure on page one"]
    )
    _embed(client, pid)
    result = _search(client, pid, "detention basin outlet", "hybrid")
    assert result["results"]
    r = result["results"][0]

    save = client.post(
        f"/api/v1/projects/{pid}/evidence-candidates",
        json={
            "document_id": r["document_id"],
            "page_number": r["page_number"],
            "candidate_title": "Hybrid detention basin outlet",
            "candidate_excerpt": r["excerpt"],
            "candidate_origin": "chunk_search",
        },
    )
    assert save.status_code == 201, save.text
    candidate = save.json()
    assert candidate["document_page_id"] is not None

    promote = client.post(
        f"/api/v1/projects/{pid}/evidence-candidates/"
        f"{candidate['evidence_candidate_id']}/promote-to-draft-finding",
        json={
            "title": "Detention basin outlet needs reviewer follow-up",
            "category": "stormwater",
            "risk_level": "medium",
        },
    )
    assert promote.status_code == 201, promote.text
    citation = promote.json()["citation"]
    assert citation["document_id"] == did
    assert citation["page_number"] == 1
    assert citation["document_page_id"] is not None
