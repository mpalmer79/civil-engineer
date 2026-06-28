"""Suggest links from real-derived chunks to checklist items and findings.

This populates a chunk's related_checklist_items and related_findings arrays with
reviewer-support suggestions, not facts. A suggested link means the chunk text is
topically close to a checklist item's requirement or a finding's context. It does
not assert that the evidence satisfies a checklist item, does not create or change
findings, and does not change any human review status.

Confidence note: DocumentChunk.related_checklist_items and related_findings are
list[str] columns (aligned with the ChunkRead schema), so only the suggested ids
are persisted. Per-link confidence scores are returned in the response for the
reviewer but are not persisted per link. A future provenance/scoring table could
persist scores; that is out of scope here.

Only real-derived chunks are scanned, so seeded demo chunks are never modified.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services.embedding_service import cosine_similarity, embed_text
from app.services.evidence_retrieval_service import (
    _checklist_query_text,
    _collect_searchable_chunks,
    _finding_query_text,
    _tokens,
)
from app.services.real_intake_service import (
    DEMO_ACTOR_NAME,
    _now,
    ensure_demo_actor,
    record_audit_event,
)

# Minimum combined score for a link to be suggested. Below this, a match is
# treated as too weak/noisy and is excluded.
_MIN_LINK_SCORE = 0.3


def _match_score(
    query_text: str,
    query_vector: list[float] | None,
    chunk: models.DocumentChunk,
    embedding: models.ChunkEmbedding | None,
) -> float:
    """Combined keyword-overlap and semantic score in [0, 1]."""

    q_tokens = set(_tokens(query_text))
    if not q_tokens:
        return 0.0
    c_tokens = set(_tokens(chunk.content or ""))
    for keyword in chunk.keywords or []:
        c_tokens.update(_tokens(keyword))
    overlap = len(q_tokens & c_tokens) / len(q_tokens)

    semantic = 0.0
    if query_vector is not None and embedding is not None:
        semantic = cosine_similarity(query_vector, embedding.vector)
    return max(overlap, semantic)


def suggest_links_for_project(
    db: Session,
    project_id: str,
    *,
    min_score: float = _MIN_LINK_SCORE,
    actor_name: str = DEMO_ACTOR_NAME,
) -> dict:
    """Scan real-derived chunks and suggest checklist/finding links.

    Returns a summary with per-chunk suggestions and their scores. Persists only
    the suggested ids on each chunk's related arrays (deduplicated). Never
    changes a finding or its human review status.
    """

    from app.services import chunk_embedding_service

    ensure_demo_actor(db)
    candidates, _searchable = _collect_searchable_chunks(db, project_id, {})

    checklist_items = list(
        db.scalars(
            select(models.ChecklistItem).where(
                models.ChecklistItem.project_id == project_id
            )
        ).all()
    )
    findings = list(
        db.scalars(
            select(models.Finding).where(
                models.Finding.project_id == project_id
            )
        ).all()
    )
    embeddings = chunk_embedding_service.current_embeddings_by_chunk(
        db, project_id
    )

    # Pre-embed the scoring texts once.
    checklist_q = [
        (item.checklist_item_id, _checklist_query_text(item), item)
        for item in checklist_items
    ]
    finding_q = [
        (finding.finding_id, _finding_query_text(finding), finding)
        for finding in findings
    ]

    def _vec(text: str) -> list[float] | None:
        try:
            return embed_text(text)
        except Exception:  # noqa: BLE001 - empty/non-text scoring text is fine
            return None

    checklist_vectors = {cid: _vec(text) for cid, text, _ in checklist_q}
    finding_vectors = {fid: _vec(text) for fid, text, _ in finding_q}

    suggestions: list[dict] = []
    chunks_with_suggestions = 0
    checklist_links_added = 0
    finding_links_added = 0

    for chunk, _page, _document in candidates:
        embedding = embeddings.get(chunk.chunk_id)
        checklist_scores: dict[str, float] = {}
        for cid, text, _item in checklist_q:
            if not text:
                continue
            score = _match_score(text, checklist_vectors.get(cid), chunk, embedding)
            if score >= min_score:
                checklist_scores[cid] = round(score, 2)
        finding_scores: dict[str, float] = {}
        for fid, text, _finding in finding_q:
            if not text:
                continue
            score = _match_score(text, finding_vectors.get(fid), chunk, embedding)
            if score >= min_score:
                finding_scores[fid] = round(score, 2)

        if not checklist_scores and not finding_scores:
            continue

        existing_checklist = set(chunk.related_checklist_items or [])
        existing_findings = set(chunk.related_findings or [])
        new_checklist = set(checklist_scores) - existing_checklist
        new_findings = set(finding_scores) - existing_findings
        chunk.related_checklist_items = sorted(
            existing_checklist | set(checklist_scores)
        )
        chunk.related_findings = sorted(existing_findings | set(finding_scores))
        checklist_links_added += len(new_checklist)
        finding_links_added += len(new_findings)
        chunks_with_suggestions += 1
        suggestions.append(
            {
                "chunk_id": chunk.chunk_id,
                "page_number": chunk.page_number,
                "checklist_item_ids": sorted(checklist_scores),
                "finding_ids": sorted(finding_scores),
                "checklist_scores": checklist_scores,
                "finding_scores": finding_scores,
            }
        )

    record_audit_event(
        db,
        project_id=project_id,
        event_type="chunk_link_suggestions_generated",
        related_entity_type="project",
        related_entity_id=project_id,
        description=(
            "Reviewer-support link suggestions generated for real-derived "
            f"chunks: {checklist_links_added} checklist and "
            f"{finding_links_added} finding suggestion(s)."
        ),
        actor_type="system",
        actor_display_name=actor_name,
        metadata={
            "chunks_with_suggestions": chunks_with_suggestions,
            "checklist_links_added": checklist_links_added,
            "finding_links_added": finding_links_added,
            "min_score": min_score,
        },
    )
    db.commit()

    return {
        "project_id": project_id,
        "chunks_scanned": len(candidates),
        "chunks_with_suggestions": chunks_with_suggestions,
        "checklist_links_added": checklist_links_added,
        "finding_links_added": finding_links_added,
        "suggestions": suggestions,
    }
