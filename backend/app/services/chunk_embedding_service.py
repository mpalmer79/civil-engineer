"""Backfill and lookup for chunk embeddings (backend only).

Embeds real-derived chunks with the active local embedding model and stores the
vectors plus model identity. The backfill is idempotent: a chunk already embedded
with the current provider, model, version, and unchanged content is skipped; a
chunk embedded with a stale model/version or whose content changed is re-embedded;
empty content is never embedded. Per-chunk failures are recorded and counted, so a
failure never breaks keyword retrieval.

This module never runs in or reaches frontend code and stores no provider secrets.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services.embedding_service import (
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL,
    EMBEDDING_MODEL_VERSION,
    EMBEDDING_PROVIDER,
    EmbeddingError,
    content_hash,
    embed_text,
)
from app.services.evidence_retrieval_service import _real_derived_chunks
from app.services.real_intake_service import (
    DEMO_ACTOR_NAME,
    _now,
    ensure_demo_actor,
    record_audit_event,
)


def _is_current(embedding: models.ChunkEmbedding, *, text_hash: str) -> bool:
    return (
        embedding.provider == EMBEDDING_PROVIDER
        and embedding.model_name == EMBEDDING_MODEL
        and embedding.model_version == EMBEDDING_MODEL_VERSION
        and embedding.content_hash == text_hash
    )


def backfill_project_chunk_embeddings(
    db: Session,
    project_id: str,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> dict:
    """Embed a project's real-derived chunks with the active model.

    Returns a summary of counts only. Never raises for a single bad chunk: an
    empty chunk is counted as skipped_empty and an unexpected error as failed.
    """

    ensure_demo_actor(db)
    chunks = _real_derived_chunks(db, project_id)

    embedded = 0
    refreshed = 0
    skipped_current = 0
    skipped_empty = 0
    failed = 0

    for chunk in chunks:
        text = chunk.content or ""
        text_hash = content_hash(text)
        existing = db.scalars(
            select(models.ChunkEmbedding).where(
                models.ChunkEmbedding.chunk_id == chunk.chunk_id
            )
        ).first()
        if existing is not None and _is_current(existing, text_hash=text_hash):
            skipped_current += 1
            continue
        try:
            vector = embed_text(text)
        except EmbeddingError:
            skipped_empty += 1
            continue
        except Exception:  # noqa: BLE001 - one bad chunk must not break the run
            failed += 1
            continue

        now = _now()
        if existing is None:
            db.add(
                models.ChunkEmbedding(
                    chunk_id=chunk.chunk_id,
                    project_id=project_id,
                    provider=EMBEDDING_PROVIDER,
                    model_name=EMBEDDING_MODEL,
                    model_version=EMBEDDING_MODEL_VERSION,
                    dimension=EMBEDDING_DIMENSION,
                    vector=vector,
                    content_hash=text_hash,
                    created_at=now,
                    updated_at=now,
                )
            )
            embedded += 1
        else:
            existing.provider = EMBEDDING_PROVIDER
            existing.model_name = EMBEDDING_MODEL
            existing.model_version = EMBEDDING_MODEL_VERSION
            existing.dimension = EMBEDDING_DIMENSION
            existing.vector = vector
            existing.content_hash = text_hash
            existing.updated_at = now
            refreshed += 1

    record_audit_event(
        db,
        project_id=project_id,
        event_type="chunk_embeddings_backfilled",
        related_entity_type="project",
        related_entity_id=project_id,
        description=(
            f"Reviewer backfilled chunk embeddings: {embedded} new, "
            f"{refreshed} refreshed, {skipped_current} current, "
            f"{skipped_empty} empty skipped, {failed} failed."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "embedded": embedded,
            "refreshed": refreshed,
            "skipped_current": skipped_current,
            "skipped_empty": skipped_empty,
            "failed": failed,
            "provider": EMBEDDING_PROVIDER,
            "model_name": EMBEDDING_MODEL,
            "model_version": EMBEDDING_MODEL_VERSION,
        },
    )
    db.commit()

    return {
        "project_id": project_id,
        "provider": EMBEDDING_PROVIDER,
        "model_name": EMBEDDING_MODEL,
        "model_version": EMBEDDING_MODEL_VERSION,
        "dimension": EMBEDDING_DIMENSION,
        "chunk_count": len(chunks),
        "embedded": embedded,
        "refreshed": refreshed,
        "skipped_current": skipped_current,
        "skipped_empty": skipped_empty,
        "failed": failed,
    }


def current_embeddings_by_chunk(
    db: Session, project_id: str
) -> dict[str, models.ChunkEmbedding]:
    """Return current-model embeddings for a project, keyed by chunk_id.

    Only embeddings matching the active provider, model, and version are
    returned, so stale-model vectors are ignored by retrieval.
    """

    stmt = select(models.ChunkEmbedding).where(
        models.ChunkEmbedding.project_id == project_id,
        models.ChunkEmbedding.provider == EMBEDDING_PROVIDER,
        models.ChunkEmbedding.model_name == EMBEDDING_MODEL,
        models.ChunkEmbedding.model_version == EMBEDDING_MODEL_VERSION,
    )
    return {row.chunk_id: row for row in db.scalars(stmt).all()}
