"""Tests for the local embedding service and chunk embedding backfill."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.db import models
from app.db.database import SessionLocal
from app.services import chunk_embedding_service
from app.services.embedding_service import (
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL,
    EMBEDDING_MODEL_VERSION,
    EMBEDDING_PROVIDER,
    EmbeddingError,
    cosine_similarity,
    embed_text,
)
from app.services.page_chunking_service import CHUNK_ORIGIN_REAL_DERIVED

from tests.test_chunk_evidence_retrieval import (
    _create_project,
    _index,
    _indexed_chunked_document,
    _make_pdf,
    _upload_pdf,
)


def _embed(client: TestClient, project_id: str) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-retrieval/embed-chunks"
    )
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Embedding service unit behavior
# ---------------------------------------------------------------------------


def test_embed_text_is_deterministic_and_normalized() -> None:
    a = embed_text("Stormwater detention basin outlet")
    b = embed_text("Stormwater detention basin outlet")
    assert a == b
    assert len(a) == EMBEDDING_DIMENSION
    # L2-normalized: self cosine is 1.0.
    assert abs(cosine_similarity(a, a) - 1.0) < 1e-9


def test_embed_text_rejects_empty_content() -> None:
    for bad in ["", "   ", "\n\t"]:
        try:
            embed_text(bad)
            raise AssertionError("expected EmbeddingError")
        except EmbeddingError:
            pass


def test_synonym_style_similarity_without_shared_tokens() -> None:
    # "pond" and "detention basin" share no tokens but share the impoundment
    # concept, so similarity is positive (semantic-style recall).
    pond = embed_text("retention pond design")
    basin = embed_text("detention basin grading")
    assert cosine_similarity(pond, basin) > 0.0


# ---------------------------------------------------------------------------
# Backfill behavior
# ---------------------------------------------------------------------------


def test_backfill_embeds_real_derived_chunks_with_metadata(
    client: TestClient,
) -> None:
    pid, did = _indexed_chunked_document(
        client, ["Stormwater detention basin outlet on page one"]
    )
    summary = _embed(client, pid)
    assert summary["embedded"] >= 1
    assert summary["provider"] == EMBEDDING_PROVIDER
    assert summary["model_name"] == EMBEDDING_MODEL
    assert summary["model_version"] == EMBEDDING_MODEL_VERSION
    assert summary["dimension"] == EMBEDDING_DIMENSION

    db = SessionLocal()
    try:
        rows = (
            db.query(models.ChunkEmbedding)
            .filter(models.ChunkEmbedding.project_id == pid)
            .all()
        )
        assert rows
        for row in rows:
            assert row.provider == EMBEDDING_PROVIDER
            assert row.model_name == EMBEDDING_MODEL
            assert row.model_version == EMBEDDING_MODEL_VERSION
            assert row.dimension == EMBEDDING_DIMENSION
            assert len(row.vector) == EMBEDDING_DIMENSION
            assert row.content_hash
    finally:
        db.close()


def test_backfill_is_idempotent(client: TestClient) -> None:
    pid, did = _indexed_chunked_document(
        client, ["Infiltration basin drawdown on page one"]
    )
    first = _embed(client, pid)
    assert first["embedded"] >= 1
    second = _embed(client, pid)
    assert second["embedded"] == 0
    assert second["skipped_current"] == first["embedded"]


def test_stale_model_version_is_ignored_then_refreshed(client: TestClient) -> None:
    pid, did = _indexed_chunked_document(
        client, ["Culvert capacity analysis on page one"]
    )
    _embed(client, pid)

    db = SessionLocal()
    try:
        row = (
            db.query(models.ChunkEmbedding)
            .filter(models.ChunkEmbedding.project_id == pid)
            .first()
        )
        row.model_version = "0"  # mark stale
        db.commit()
        # Stale-model vectors are excluded from the current-model lookup.
        current = chunk_embedding_service.current_embeddings_by_chunk(db, pid)
        assert row.chunk_id not in current
    finally:
        db.close()

    # Re-running the backfill refreshes the stale vector to the current model.
    refreshed = _embed(client, pid)
    assert refreshed["refreshed"] >= 1
    db = SessionLocal()
    try:
        current = chunk_embedding_service.current_embeddings_by_chunk(db, pid)
        assert current  # the refreshed vector is now current
    finally:
        db.close()


def test_empty_chunk_content_is_skipped(client: TestClient) -> None:
    pid = _create_project(client, "Empty Chunk Project")
    did = _upload_pdf(client, pid, _make_pdf(["Real content on page one"]))
    _index(client, pid, did)

    db = SessionLocal()
    try:
        page = (
            db.query(models.DocumentPage)
            .filter(models.DocumentPage.document_id == did)
            .first()
        )
        # A real-derived chunk with whitespace-only content must never embed.
        db.add(
            models.DocumentChunk(
                chunk_id=f"rdc_{did}_empty_0",
                project_id=pid,
                document_id=did,
                document_type="stormwater_report",
                file_name="empty.pdf",
                page_number=page.page_number,
                section_heading=None,
                chunk_index=99,
                content="   ",
                keywords=[],
                related_checklist_items=[],
                related_findings=[],
                chunk_origin=CHUNK_ORIGIN_REAL_DERIVED,
            )
        )
        db.commit()
    finally:
        db.close()

    summary = _embed(client, pid)
    assert summary["skipped_empty"] >= 1


def test_keyword_search_still_works_after_embedding(client: TestClient) -> None:
    pid, did = _indexed_chunked_document(
        client, ["Stormwater detention basin outlet on page one"]
    )
    _embed(client, pid)
    # Keyword chunk search is unaffected by embedding backfill.
    result = client.post(
        f"/api/v1/projects/{pid}/evidence-retrieval/chunk-search",
        json={"query_text": "detention basin"},
    ).json()
    assert result["result_count"] >= 1
