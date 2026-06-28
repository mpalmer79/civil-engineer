"""Tests for durable DocumentChunk provenance (chunk_origin).

Real-derived chunks built from indexed page text are marked real_derived, seeded
demo chunks are marked seeded_demo, and real-derived chunk search prefers the
provenance field while still honoring legacy rows that only carry the rdc_
chunk_id prefix.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.db import models
from app.db.database import SessionLocal
from app.services import evidence_retrieval_service as retrieval
from app.services.page_chunking_service import (
    CHUNK_ORIGIN_REAL_DERIVED,
    CHUNK_ORIGIN_SEEDED_DEMO,
    REAL_DERIVED_CHUNK_PREFIX,
)

from tests.test_chunk_evidence_retrieval import (
    _create_project,
    _index,
    _indexed_chunked_document,
    _make_pdf,
    _upload_pdf,
)

BROOKSIDE_ID = "proj_brookside_meadows"


def test_real_derived_chunks_marked_real_derived(client: TestClient) -> None:
    pid, did = _indexed_chunked_document(
        client, ["Stormwater detention basin on page one"]
    )
    chunks = client.get(f"/api/v1/documents/{did}/chunks").json()
    assert chunks
    for chunk in chunks:
        assert chunk["chunk_origin"] == CHUNK_ORIGIN_REAL_DERIVED


def test_seeded_chunks_marked_seeded_demo(client: TestClient) -> None:
    seeded = client.get(f"/api/v1/projects/{BROOKSIDE_ID}/chunks").json()
    assert seeded
    for chunk in seeded:
        assert chunk["chunk_origin"] == CHUNK_ORIGIN_SEEDED_DEMO


def test_real_derived_search_excludes_seeded_chunks(client: TestClient) -> None:
    # Searching the seeded project's chunk evidence returns only real-derived
    # chunks; seeded chunks are never surfaced as real-derived evidence.
    result = client.post(
        f"/api/v1/projects/{BROOKSIDE_ID}/evidence-retrieval/chunk-search",
        json={"query_text": "stormwater"},
    ).json()
    for r in result["results"]:
        assert r["chunk_id"].startswith(REAL_DERIVED_CHUNK_PREFIX)


def test_legacy_rdc_chunk_without_origin_still_searchable(
    client: TestClient,
) -> None:
    # Simulate a row created before chunk_origin existed: rdc_ prefix, null
    # origin. It must still be returned by real-derived chunk search.
    pid = _create_project(client, "Legacy Chunk Project")
    did = _upload_pdf(client, pid, _make_pdf(["Culvert capacity on page one"]))
    _index(client, pid, did)

    db = SessionLocal()
    try:
        page = (
            db.query(models.DocumentPage)
            .filter(models.DocumentPage.document_id == did)
            .first()
        )
        legacy = models.DocumentChunk(
            chunk_id=f"{REAL_DERIVED_CHUNK_PREFIX}{did}_legacy_0",
            project_id=pid,
            document_id=did,
            document_type="stormwater_report",
            file_name="legacy.pdf",
            page_number=page.page_number,
            section_heading=None,
            chunk_index=0,
            content="Legacy culvert capacity analysis text.",
            keywords=["culvert", "capacity"],
            related_checklist_items=[],
            related_findings=[],
            chunk_origin=None,
        )
        db.add(legacy)
        db.commit()
    finally:
        db.close()

    result = client.post(
        f"/api/v1/projects/{pid}/evidence-retrieval/chunk-search",
        json={"query_text": "culvert capacity"},
    ).json()
    chunk_ids = {r["chunk_id"] for r in result["results"]}
    assert f"{REAL_DERIVED_CHUNK_PREFIX}{did}_legacy_0" in chunk_ids


def test_real_derived_chunks_helper_prefers_origin() -> None:
    # The helper returns rows by provenance field and by legacy prefix fallback.
    db = SessionLocal()
    try:
        rows = retrieval._real_derived_chunks(db, BROOKSIDE_ID)
        # Brookside has only seeded_demo chunks, so none are real-derived.
        assert rows == []
    finally:
        db.close()
