"""Real chunk pipeline from indexed PDF page text (Phase 1, PR 1).

This service reads real ``DocumentPage`` rows produced by the existing PDF page
indexing step and derives ``DocumentChunk`` rows from the pages that carry an
embedded text layer. It is the first code path that turns real indexed page text
into retrievable chunks. Until now ``DocumentChunk`` rows existed only as seeded
demo data.

Scope and boundaries:

* It reads ``DocumentPage.extracted_text`` only. It does not parse files, does
  not OCR, does not call an AI provider, and does not use embeddings, vector
  search, or any external service. Chunking is deterministic and local.
* It only chunks pages whose ``text_extraction_status`` is ``text_extracted``
  and whose ``extracted_text`` is non-empty. Pages marked
  ``no_extractable_text``, ``not_indexed``, or any other state produce no chunks.
* A chunk never spans pages. Each page is chunked independently.
* It does not change the indexing system or the existing page-text evidence
  retrieval service. It does not finalize any review outcome. Derived chunks are
  review-support material for a human reviewer, not a conclusion.

Provenance limitation (intentional for this pass): the ``DocumentChunk`` table
has no provenance or source field, and this pass does not add a database column.
To keep seeded chunks and real-derived chunks from mixing in a misleading way,
real-derived chunks are marked by their ``chunk_id`` prefix
(``rdc_``). Re-running the pipeline for a document deletes and replaces only the
real-derived chunks for that same document (those whose ``chunk_id`` starts with
the real-derived prefix). Seeded chunks are never deleted. A dedicated
provenance column is tracked as a later step (PR 2 in the implementation map).
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services.real_intake_service import (
    DEMO_ACTOR_NAME,
    _now,
    ensure_demo_actor,
    record_audit_event,
)

# A chunk_id prefix that marks a chunk as derived from real indexed page text.
# This is the provenance marker used in place of a database column for this pass.
REAL_DERIVED_CHUNK_PREFIX = "rdc_"

# Only pages with this extraction status and non-empty text are chunked.
INDEXED_TEXT_STATUS = "text_extracted"

# Chunking targets. A chunk accumulates up to this many words within a single
# page before it is flushed. Chunks never cross a page boundary regardless.
_TARGET_CHUNK_WORDS = 120
_MAX_KEYWORDS = 8
_MAX_HEADING_WORDS = 8
_MAX_HEADING_CHARS = 80

# Domain vocabulary used to surface meaningful keywords for civil and stormwater
# review text. Multi-word phrases are listed before single words so a phrase is
# preferred when present. Matching is plain, lowercase substring matching.
_DOMAIN_TERMS: tuple[str, ...] = (
    "detention basin",
    "retention basin",
    "infiltration basin",
    "water quality",
    "peak flow",
    "erosion control",
    "sediment control",
    "drainage area",
    "operation and maintenance",
    "stormwater",
    "bioretention",
    "infiltration",
    "detention",
    "retention",
    "drainage",
    "runoff",
    "erosion",
    "sediment",
    "swppp",
    "culvert",
    "grading",
    "watershed",
    "outfall",
    "outlet",
    "basin",
    "easement",
    "setback",
    "impervious",
    "wetland",
    "floodplain",
    "hydrology",
    "hydraulic",
    "topography",
    "subdivision",
)

# Common words excluded from frequency-based keyword fallback.
_STOPWORDS: frozenset[str] = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "are",
        "was",
        "were",
        "has",
        "have",
        "had",
        "will",
        "shall",
        "into",
        "onto",
        "over",
        "under",
        "near",
        "toward",
        "between",
        "their",
        "there",
        "which",
        "where",
        "when",
        "they",
        "them",
        "than",
        "then",
        "also",
        "such",
        "each",
        "per",
        "via",
        "about",
        "above",
        "below",
        "shown",
        "noted",
        "page",
        "sheet",
    }
)


class ChunkingError(Exception):
    """Raised when a chunking operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_project(db: Session, project_id: str) -> models.Project:
    project = db.get(models.Project, project_id)
    if project is None:
        raise ChunkingError("Project not found.", status_code=404)
    return project


def _require_document(
    db: Session, project_id: str, document_id: str
) -> models.Document:
    document = db.get(models.Document, document_id)
    if document is None or document.project_id != project_id:
        raise ChunkingError("Document not found.", status_code=404)
    return document


def _document_display_name(document: models.Document) -> str:
    return document.original_file_name or document.file_name


def _looks_like_heading(line: str) -> bool:
    """Return True when a line looks like a short section heading.

    The heuristic is deterministic and conservative: a heading is a short line
    of a few words that does not end with sentence punctuation and reads as a
    title (all caps, or mostly capitalized words starting with a capital).
    """

    text = line.strip()
    if not text or len(text) > _MAX_HEADING_CHARS:
        return False
    words = text.split()
    if len(words) > _MAX_HEADING_WORDS:
        return False
    if text[-1] in ".,;:!?":
        return False
    if not any(char.isalpha() for char in text):
        return False
    if text.isupper():
        return True
    if text[:1].isupper():
        capitalized = sum(1 for word in words if word[:1].isupper())
        if capitalized >= max(1, len(words) - 1):
            return True
    return False


def _lines(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return [line.strip() for line in normalized.split("\n")]


def _chunk_page_text(text: str) -> list[tuple[str | None, str]]:
    """Split a single page's text into (section_heading, content) chunks.

    Chunks are built only from this page's text, so a chunk never spans pages.
    A detected heading is carried as the section heading for the content that
    follows it until the next heading. When a page yields no content under the
    heuristic, the whole collapsed page text is returned as one chunk with no
    section heading so a real indexed page with text always produces a chunk.
    """

    chunks: list[tuple[str | None, str]] = []
    current_heading: str | None = None
    buffer_words: list[str] = []

    def flush() -> None:
        nonlocal buffer_words
        if buffer_words:
            content = " ".join(" ".join(buffer_words).split()).strip()
            if content:
                chunks.append((current_heading, content))
            buffer_words = []

    for line in _lines(text):
        if not line:
            continue
        if _looks_like_heading(line):
            flush()
            current_heading = line
            continue
        for word in line.split():
            buffer_words.append(word)
            if len(buffer_words) >= _TARGET_CHUNK_WORDS:
                flush()
    flush()

    if not chunks:
        collapsed = " ".join(text.split()).strip()
        if collapsed:
            chunks.append((None, collapsed))
    return chunks


def _extract_keywords(content: str) -> list[str]:
    """Return a deterministic, bounded keyword list for chunk content.

    Domain vocabulary present in the content is listed first, in vocabulary
    order. Remaining slots are filled with the most frequent non-trivial tokens,
    ordered by frequency then alphabetically for stable output.
    """

    lowered = content.lower()
    keywords: list[str] = []
    for term in _DOMAIN_TERMS:
        if term in lowered and term not in keywords:
            keywords.append(term)
        if len(keywords) >= _MAX_KEYWORDS:
            return keywords[:_MAX_KEYWORDS]

    frequency: dict[str, int] = {}
    for token in re.findall(r"[a-z0-9]+", lowered):
        if len(token) < 4 or token in _STOPWORDS:
            continue
        frequency[token] = frequency.get(token, 0) + 1
    ranked = sorted(frequency.items(), key=lambda item: (-item[1], item[0]))
    for token, _count in ranked:
        if token in keywords:
            continue
        keywords.append(token)
        if len(keywords) >= _MAX_KEYWORDS:
            break
    return keywords[:_MAX_KEYWORDS]


def _indexed_text_pages(
    db: Session, project_id: str, document_id: str
) -> list[models.DocumentPage]:
    stmt = (
        select(models.DocumentPage)
        .where(
            models.DocumentPage.project_id == project_id,
            models.DocumentPage.document_id == document_id,
            models.DocumentPage.text_extraction_status == INDEXED_TEXT_STATUS,
        )
        .order_by(models.DocumentPage.page_number)
    )
    return list(db.scalars(stmt).all())


def _existing_real_derived_chunks(
    db: Session, project_id: str, document_id: str
) -> list[models.DocumentChunk]:
    """Return prior real-derived chunks for a document.

    Only chunks whose chunk_id carries the real-derived prefix are returned, so
    seeded chunks are never selected for deletion even if a future document were
    to share a seeded document_id.
    """

    stmt = select(models.DocumentChunk).where(
        models.DocumentChunk.project_id == project_id,
        models.DocumentChunk.document_id == document_id,
        models.DocumentChunk.chunk_id.like(f"{REAL_DERIVED_CHUNK_PREFIX}%"),
    )
    return list(db.scalars(stmt).all())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def rebuild_document_chunks(
    db: Session,
    *,
    project_id: str,
    document_id: str,
    actor_name: str = DEMO_ACTOR_NAME,
) -> dict:
    """Rebuild real-derived chunks for one document from its indexed page text.

    The operation is idempotent. It first removes the document's prior
    real-derived chunks, then creates fresh chunks from the current indexed page
    text, so re-running never duplicates chunks and never deletes seeded chunks.
    Returns a summary of counts and statuses only.
    """

    _require_project(db, project_id)
    document = _require_document(db, project_id, document_id)
    ensure_demo_actor(db)

    removed = 0
    for stale in _existing_real_derived_chunks(db, project_id, document_id):
        db.delete(stale)
        removed += 1
    # Flush the deletes before inserting so re-running with stable chunk ids does
    # not collide with the rows being replaced.
    if removed:
        db.flush()

    pages = _indexed_text_pages(db, project_id, document_id)
    document_type = document.document_type
    file_name = _document_display_name(document)

    chunk_index = 0
    pages_chunked = 0
    for page in pages:
        page_text = page.extracted_text or ""
        if not page_text.strip():
            continue
        page_chunks = _chunk_page_text(page_text)
        if not page_chunks:
            continue
        pages_chunked += 1
        for page_ordinal, (section_heading, content) in enumerate(page_chunks):
            chunk_id = (
                f"{REAL_DERIVED_CHUNK_PREFIX}{document_id}_p{page.page_number}"
                f"_{page_ordinal}"
            )
            db.add(
                models.DocumentChunk(
                    chunk_id=chunk_id,
                    project_id=project_id,
                    document_id=document_id,
                    document_type=document_type,
                    file_name=file_name,
                    page_number=page.page_number,
                    section_heading=section_heading,
                    chunk_index=chunk_index,
                    content=content,
                    keywords=_extract_keywords(content),
                    related_checklist_items=[],
                    related_findings=[],
                )
            )
            chunk_index += 1

    record_audit_event(
        db,
        project_id=project_id,
        event_type="document_chunks_rebuilt",
        related_entity_type="document",
        related_entity_id=document_id,
        description=(
            f"Reviewer rebuilt page-derived chunks for "
            f"'{file_name}': {chunk_index} chunk(s) from {pages_chunked} "
            f"indexed page(s)."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "document_id": document_id,
            "chunk_count": chunk_index,
            "pages_chunked": pages_chunked,
            "removed_prior_chunk_count": removed,
        },
    )
    db.commit()

    return {
        "document_id": document_id,
        "project_id": project_id,
        "document_type": document_type,
        "file_name": file_name,
        "pages_chunked": pages_chunked,
        "chunk_count": chunk_index,
        "removed_prior_chunk_count": removed,
    }
