"""Keyword and metadata based retrieval over seeded document chunks.

Phase 3 retrieval is intentionally simple and transparent. It ranks chunks by
keyword overlap, checklist linkage, finding linkage, and document type, and it
reports a plain relevance reason for each result. It does not use embeddings or
a vector store, and it does not pretend to be perfect. Every result is framed as
source evidence for a human reviewer, not a conclusion.
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import EVIDENCE_SAFETY_NOTE
from app.db import models

# Order from strongest to weakest evidence role for ranking finding sources.
_ROLE_ORDER = {
    "shows_conflict": 5,
    "shows_missing_evidence": 4,
    "supports_finding": 3,
    "requires_reviewer_confirmation": 2,
    "context_only": 1,
}


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) >= 3]


def list_project_chunks(db: Session, project_id: str) -> list[models.DocumentChunk]:
    stmt = (
        select(models.DocumentChunk)
        .where(models.DocumentChunk.project_id == project_id)
        .order_by(models.DocumentChunk.document_id, models.DocumentChunk.chunk_index)
    )
    return list(db.scalars(stmt).all())


def list_document_chunks(
    db: Session, document_id: str
) -> list[models.DocumentChunk]:
    stmt = (
        select(models.DocumentChunk)
        .where(models.DocumentChunk.document_id == document_id)
        .order_by(models.DocumentChunk.chunk_index)
    )
    return list(db.scalars(stmt).all())


def get_chunk(db: Session, chunk_id: str) -> models.DocumentChunk | None:
    stmt = select(models.DocumentChunk).where(
        models.DocumentChunk.chunk_id == chunk_id
    )
    return db.scalars(stmt).first()


def list_finding_sources(db: Session, finding_id: str) -> list[models.FindingSource]:
    stmt = (
        select(models.FindingSource)
        .where(models.FindingSource.finding_id == finding_id)
        .order_by(models.FindingSource.finding_source_id)
    )
    return list(db.scalars(stmt).all())


def _excerpt(content: str, limit: int = 240) -> str:
    content = content.strip()
    if len(content) <= limit:
        return content
    return content[: limit - 3].rstrip() + "..."


def _score_chunk(query: str, chunk: models.DocumentChunk) -> tuple[float, str]:
    """Return a (score, relevance_reason) for a chunk against a query.

    Score is bounded to a maximum below 1.0 so the system never implies a
    perfect or certain match.
    """

    q = query.strip().lower()
    q_tokens = _tokens(q)
    keyword_text = " ".join(chunk.keywords).lower()
    content = chunk.content.lower()
    section = (chunk.section_heading or "").lower()

    matched_keywords = [
        kw for kw in chunk.keywords if any(t in kw.lower() for t in q_tokens)
    ]
    token_kw = len(matched_keywords)
    token_content = sum(1 for t in q_tokens if t in content)
    phrase_hit = bool(q) and (q in keyword_text or q in content)
    section_hit = any(t in section for t in q_tokens)

    if token_kw == 0 and token_content == 0 and not phrase_hit:
        return 0.0, ""

    score = 0.5
    score += 0.12 * token_kw
    score += 0.06 * token_content
    if phrase_hit:
        score += 0.15
    if section_hit:
        score += 0.05
    score = round(min(score, 0.96), 2)

    reasons: list[str] = []
    if matched_keywords:
        reasons.append("keyword match: " + ", ".join(matched_keywords[:3]))
    if phrase_hit:
        reasons.append("phrase appears in the chunk text")
    if section_hit and chunk.section_heading:
        reasons.append(f"section heading '{chunk.section_heading}'")
    if not reasons:
        reasons.append("text overlap with the query")
    reason = "Matches on " + "; ".join(reasons) + "."
    return score, reason


def _to_result(
    chunk: models.DocumentChunk,
    score: float,
    relevance_reason: str,
    *,
    excerpt: str | None = None,
    evidence_role: str | None = None,
) -> dict:
    return {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "file_name": chunk.file_name,
        "document_type": chunk.document_type,
        "page_number": chunk.page_number,
        "section_heading": chunk.section_heading,
        "excerpt": excerpt if excerpt is not None else _excerpt(chunk.content),
        "relevance_reason": relevance_reason,
        "score": score,
        "evidence_role": evidence_role,
        "safety_note": EVIDENCE_SAFETY_NOTE,
    }


def search(
    db: Session,
    project_id: str,
    query: str,
    *,
    document_type: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Search project chunks by keyword and metadata, ranked by relevance."""

    chunks = list_project_chunks(db, project_id)
    results: list[dict] = []
    for chunk in chunks:
        if document_type and chunk.document_type != document_type:
            continue
        score, reason = _score_chunk(query, chunk)
        if score <= 0:
            continue
        results.append(_to_result(chunk, score, reason))
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


def evidence_for_checklist_item(
    db: Session, project_id: str, checklist_item_id: str
) -> list[dict]:
    """Return chunks linked to a checklist item as source evidence."""

    chunks = list_project_chunks(db, project_id)
    results: list[dict] = []
    for chunk in chunks:
        if checklist_item_id not in (chunk.related_checklist_items or []):
            continue
        # Linked chunks get a strong but not perfect score. Chunks that also
        # carry a related finding are ranked slightly higher.
        score = 0.85 + (0.05 if chunk.related_findings else 0.0)
        reason = f"Linked to checklist item {checklist_item_id}."
        results.append(_to_result(chunk, round(score, 2), reason))
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def evidence_for_finding(
    db: Session, finding_id: str
) -> list[dict]:
    """Return source evidence for a finding, merged with chunk metadata."""

    sources = list_finding_sources(db, finding_id)
    results: list[dict] = []
    for source in sources:
        chunk = get_chunk(db, source.chunk_id) if source.chunk_id else None
        reason = (
            f"Evidence role: {source.evidence_role.replace('_', ' ')}."
        )
        if chunk is not None:
            results.append(
                _to_result(
                    chunk,
                    round(source.confidence, 2),
                    reason,
                    excerpt=source.excerpt,
                    evidence_role=source.evidence_role,
                )
            )
        else:
            results.append(
                {
                    "chunk_id": source.chunk_id,
                    "document_id": source.document_id,
                    "file_name": source.document_id,
                    "document_type": "unknown",
                    "page_number": source.page_number,
                    "section_heading": None,
                    "excerpt": source.excerpt,
                    "relevance_reason": reason,
                    "score": round(source.confidence, 2),
                    "evidence_role": source.evidence_role,
                    "safety_note": EVIDENCE_SAFETY_NOTE,
                }
            )
    results.sort(
        key=lambda r: (
            _ROLE_ORDER.get(r.get("evidence_role") or "", 0),
            r["score"],
        ),
        reverse=True,
    )
    return results
