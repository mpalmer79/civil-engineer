"""Deterministic, local evidence retrieval and reviewer draft finding queue.

Production Foundations Sprint 3 adds a trustworthy retrieval layer over the
Sprint 2 indexed PDF page text, plus a reviewer-controlled queue of evidence
candidates that a human reviewer can promote into draft review-support findings.

Retrieval is deterministic and local. It ranks indexed DocumentPage rows by
keyword overlap, exact phrase match, document metadata match, and keyword
density, and it reports a plain ranking reason for each result. It does not use
embeddings, OCR, or any external service, and it never calls an AI provider.
Every retrieval result is a candidate for reviewer evaluation, not a conclusion.

Nothing here approves plans, certifies compliance, verifies CAD, validates
design, declares a project safe, resolves or closes an issue, or makes a final
engineering decision. A reviewer must act to save, promote, or dismiss a
candidate; the system never auto-promotes. Promotion creates a reviewer draft
finding and a page-level citation; it never finalizes a review outcome.

Search results and audit metadata never include full extracted page text, raw
server file paths, secrets, or API keys. Only short excerpts, counts, and
statuses are surfaced.
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_CANDIDATE_ORIGINS,
    ALLOWED_CANDIDATE_STATUSES,
    ALLOWED_EVIDENCE_STATUSES,
    ALLOWED_RETRIEVAL_QUERY_TYPES,
    ALLOWED_REVIEWER_FINDING_STATUSES,
    MAX_RETRIEVAL_RESULTS,
    MIN_RETRIEVAL_QUERY_LENGTH,
    reject_prohibited_language,
)
from app.db import models
from app.services.pdf_indexing_service import create_evidence_citation
from app.services.page_chunking_service import (
    INDEXED_TEXT_STATUS,
    REAL_DERIVED_CHUNK_PREFIX,
)
from app.services.real_intake_service import (
    DEMO_ACTOR_ID,
    DEMO_ACTOR_NAME,
    _now,
    _short,
    ensure_demo_actor,
    record_audit_event,
)

# How a query type maps to the candidate origin recorded when a result from that
# search is saved into the queue.
_ORIGIN_BY_QUERY_TYPE: dict[str, str] = {
    "keyword": "keyword_search",
    "phrase": "phrase_search",
    "checklist_item": "checklist_search",
    "finding_context": "finding_context_search",
    "document_filter": "keyword_search",
    "combined": "keyword_search",
    "chunk_keyword": "chunk_search",
}

_EXCERPT_LIMIT = 240
_EXCERPT_WINDOW = 160


class RetrievalError(Exception):
    """Raised when a retrieval or candidate queue operation is not allowed."""

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
        raise RetrievalError("Project not found.", status_code=404)
    return project


def _tokens(text: str) -> list[str]:
    """Return lowercased alphanumeric tokens of length >= the query minimum."""

    return [
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) >= MIN_RETRIEVAL_QUERY_LENGTH
    ]


def _indexed_pages(db: Session, project_id: str) -> list[models.DocumentPage]:
    """Return project pages that carry extractable text, in stable order."""

    stmt = (
        select(models.DocumentPage)
        .where(
            models.DocumentPage.project_id == project_id,
            models.DocumentPage.text_extraction_status == "text_extracted",
        )
        .order_by(
            models.DocumentPage.document_id,
            models.DocumentPage.page_number,
        )
    )
    return list(db.scalars(stmt).all())


def _document_map(db: Session, project_id: str) -> dict[str, models.Document]:
    stmt = select(models.Document).where(
        models.Document.project_id == project_id
    )
    return {doc.document_id: doc for doc in db.scalars(stmt).all()}


def _document_display_name(document: models.Document | None) -> str:
    if document is None:
        return "Unknown document"
    return document.original_file_name or document.file_name


def _excerpt_around(text: str, match_start: int) -> str:
    """Return a short excerpt centered on the first matched term.

    The excerpt is bounded well below the full page text so a search result
    never returns an entire page. Leading and trailing context is marked with
    an ellipsis when the page text extends beyond the window.
    """

    collapsed = " ".join(text.split())
    if len(collapsed) <= _EXCERPT_LIMIT:
        return collapsed
    # Recompute the match position in the whitespace-collapsed text. Falling
    # back to position 0 keeps the excerpt safe if the term is not found after
    # collapsing (for example when the match spanned a line break).
    start = max(match_start - _EXCERPT_WINDOW // 2, 0)
    snippet = collapsed[start : start + _EXCERPT_LIMIT].strip()
    prefix = "..." if start > 0 else ""
    suffix = "..." if start + _EXCERPT_LIMIT < len(collapsed) else ""
    return f"{prefix}{snippet}{suffix}"


def _score_page(
    *,
    query: str,
    query_tokens: list[str],
    page: models.DocumentPage,
    document: models.Document | None,
    phrase_mode: bool,
) -> tuple[float, str, list[str], str] | None:
    """Score a single page against a query.

    Returns (score, ranking_reason, match_terms, excerpt) or None when the page
    does not match. The score is bounded below 1.0 so the system never implies a
    perfect or certain match.
    """

    text = page.extracted_text or ""
    if not text.strip():
        return None
    lower_text = text.lower()
    query_lower = query.strip().lower()

    matched_terms = [token for token in query_tokens if token in lower_text]
    phrase_hit = bool(query_lower) and query_lower in lower_text
    document_type = (document.document_type if document else "") or ""
    file_name = _document_display_name(document)
    metadata_text = f"{document_type} {file_name}".lower()
    metadata_hit = any(token in metadata_text for token in query_tokens)

    if phrase_mode and not phrase_hit:
        # A phrase search only returns pages where the full phrase appears.
        return None
    if not phrase_hit and not matched_terms and not metadata_hit:
        return None

    # Count total keyword occurrences and compute a simple density signal.
    total_hits = sum(lower_text.count(token) for token in matched_terms)
    word_count = page.word_count or len(lower_text.split()) or 1
    density = total_hits / word_count

    score = 0.45
    if phrase_hit:
        score += 0.25
    score += 0.05 * len(matched_terms)
    score += min(0.10, 0.02 * total_hits)
    score += min(0.10, density * 4)
    if metadata_hit:
        score += 0.05
    score = round(min(score, 0.95), 2)

    # Locate the first matched position for the excerpt window.
    match_start = 0
    if phrase_hit:
        match_start = lower_text.find(query_lower)
    elif matched_terms:
        positions = [lower_text.find(term) for term in matched_terms]
        match_start = min(pos for pos in positions if pos >= 0)
    excerpt = _excerpt_around(text, match_start)

    reasons: list[str] = []
    if phrase_hit:
        reasons.append("exact phrase appears on this page")
    if matched_terms:
        reasons.append("keyword match: " + ", ".join(matched_terms[:4]))
    if total_hits > len(matched_terms):
        reasons.append(f"{total_hits} keyword hit(s) on the page")
    if metadata_hit:
        reasons.append(f"document metadata match ({document_type or file_name})")
    if not reasons:
        reasons.append("text overlap with the query")
    ranking_reason = "Ranked by " + "; ".join(reasons) + "."

    terms = list(matched_terms)
    if phrase_hit and query_lower not in terms:
        terms = [query.strip(), *terms]
    return score, ranking_reason, terms, excerpt


def _result_dict(
    *,
    page: models.DocumentPage,
    document: models.Document | None,
    score: float,
    ranking_reason: str,
    match_terms: list[str],
    excerpt: str,
) -> dict:
    return {
        "document_id": page.document_id,
        "document_name": _document_display_name(document),
        "document_type": (document.document_type if document else None),
        "document_page_id": page.document_page_id,
        "page_number": page.page_number,
        "page_label": page.page_label,
        "text_extraction_status": page.text_extraction_status,
        "excerpt": excerpt,
        "match_terms": match_terms,
        "ranking_score": score,
        "ranking_reason": ranking_reason,
    }


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def search_project_evidence(
    db: Session,
    project_id: str,
    payload: dict,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> dict:
    """Search a project's indexed page text and return ranked candidates.

    payload accepts query_text, query_type, filters (document_id, document_type,
    text_extraction_status, page_min, page_max, checklist_item_id, finding_id),
    and limit. The full result includes short excerpts only, never full page
    text. A RetrievalQuery audit record and an evidence_search_performed audit
    event are written. Raises RetrievalError on validation problems.
    """

    _require_project(db, project_id)
    ensure_demo_actor(db)

    query_text = (payload.get("query_text") or "").strip()
    query_type = (payload.get("query_type") or "keyword").strip()
    filters = dict(payload.get("filters") or {})
    limit = payload.get("limit") or 10

    if query_type not in ALLOWED_RETRIEVAL_QUERY_TYPES:
        raise RetrievalError(
            f"Unsupported query_type '{query_type}'. Allowed: "
            f"{', '.join(sorted(ALLOWED_RETRIEVAL_QUERY_TYPES))}.",
            status_code=422,
        )
    if len(query_text) < MIN_RETRIEVAL_QUERY_LENGTH:
        raise RetrievalError(
            "query_text is required and must be at least "
            f"{MIN_RETRIEVAL_QUERY_LENGTH} characters.",
            status_code=422,
        )
    reject_prohibited_language(query_text, field="query_text")
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 10
    limit = max(1, min(limit, MAX_RETRIEVAL_RESULTS))

    results = _run_search(
        db,
        project_id,
        query_text=query_text,
        phrase_mode=(query_type == "phrase"),
        filters=filters,
        limit=limit,
    )

    origin = _ORIGIN_BY_QUERY_TYPE.get(query_type, "keyword_search")
    message = _result_message(db, project_id, results)
    retrieval_query = _record_retrieval_query(
        db,
        project_id=project_id,
        query_text=query_text,
        query_type=query_type,
        filters=filters,
        result_count=len(results),
        related_checklist_item_id=filters.get("checklist_item_id"),
        related_finding_id=filters.get("finding_id"),
        actor_name=actor_name,
    )
    for result in results:
        result["candidate_origin"] = origin
        result["retrieval_query_id"] = retrieval_query.retrieval_query_id

    record_audit_event(
        db,
        project_id=project_id,
        event_type="evidence_search_performed",
        related_entity_type="retrieval_query",
        related_entity_id=retrieval_query.retrieval_query_id,
        description=(
            f"Reviewer searched indexed evidence ({query_type}); "
            f"{len(results)} candidate(s)."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "query_type": query_type,
            "result_count": len(results),
            "filters": _safe_filter_metadata(filters),
        },
    )
    db.commit()

    return {
        "project_id": project_id,
        "query_text": query_text,
        "query_type": query_type,
        "retrieval_query_id": retrieval_query.retrieval_query_id,
        "result_count": len(results),
        "results": results,
        "message": message,
    }


def _run_search(
    db: Session,
    project_id: str,
    *,
    query_text: str,
    phrase_mode: bool,
    filters: dict,
    limit: int,
) -> list[dict]:
    """Score and rank indexed pages for a query, applying optional filters."""

    pages = _indexed_pages(db, project_id)
    documents = _document_map(db, project_id)
    query_tokens = _tokens(query_text)

    document_id = filters.get("document_id")
    document_type = filters.get("document_type")
    extraction_status = filters.get("text_extraction_status")
    page_min = filters.get("page_min")
    page_max = filters.get("page_max")

    results: list[dict] = []
    for page in pages:
        document = documents.get(page.document_id)
        if document_id and page.document_id != document_id:
            continue
        if document_type and (
            document is None or document.document_type != document_type
        ):
            continue
        if (
            extraction_status
            and page.text_extraction_status != extraction_status
        ):
            continue
        if page_min is not None and page.page_number < int(page_min):
            continue
        if page_max is not None and page.page_number > int(page_max):
            continue

        scored = _score_page(
            query=query_text,
            query_tokens=query_tokens,
            page=page,
            document=document,
            phrase_mode=phrase_mode,
        )
        if scored is None:
            continue
        score, reason, terms, excerpt = scored
        results.append(
            _result_dict(
                page=page,
                document=document,
                score=score,
                ranking_reason=reason,
                match_terms=terms,
                excerpt=excerpt,
            )
        )

    # Stable, deterministic ordering: score first, then document and page so
    # ties resolve the same way on every run.
    results.sort(
        key=lambda r: (
            -r["ranking_score"],
            r["document_id"],
            r["page_number"] or 0,
        )
    )
    return results[:limit]


def _result_message(
    db: Session, project_id: str, results: list[dict]
) -> str:
    if results:
        return f"{len(results)} retrieval candidate(s) for reviewer review."
    if not _indexed_pages(db, project_id):
        return (
            "No indexed page text is available yet. Upload and index a digital "
            "PDF before searching evidence."
        )
    return "No matching indexed page text. Try different terms or filters."


def _safe_filter_metadata(filters: dict) -> dict:
    """Return a filter dict safe for audit metadata (no page text, no paths)."""

    allowed_keys = {
        "document_id",
        "document_type",
        "text_extraction_status",
        "page_min",
        "page_max",
        "checklist_item_id",
        "finding_id",
    }
    return {key: filters[key] for key in allowed_keys if filters.get(key) is not None}


def _record_retrieval_query(
    db: Session,
    *,
    project_id: str,
    query_text: str,
    query_type: str,
    filters: dict,
    result_count: int,
    related_checklist_item_id: str | None,
    related_finding_id: str | None,
    actor_name: str,
) -> models.RetrievalQuery:
    query = models.RetrievalQuery(
        retrieval_query_id=f"rq_user_{_short()}",
        project_id=project_id,
        query_text=query_text,
        query_type=query_type,
        filters=_safe_filter_metadata(filters),
        result_count=result_count,
        related_checklist_item_id=related_checklist_item_id,
        related_finding_id=related_finding_id,
        created_by_actor_id=DEMO_ACTOR_ID,
        created_by_name=actor_name,
        event_metadata={"query_type": query_type, "result_count": result_count},
        created_at=_now(),
    )
    db.add(query)
    db.flush()
    return query


def search_by_checklist_item(
    db: Session,
    project_id: str,
    checklist_item_id: str,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> dict:
    """Search indexed evidence for a checklist item by its requirement text."""

    item = db.get(models.ChecklistItem, checklist_item_id)
    if item is None or item.project_id != project_id:
        raise RetrievalError("Checklist item not found.", status_code=404)
    query_text = (item.requirement or item.expected_evidence or "").strip()
    if len(query_text) < MIN_RETRIEVAL_QUERY_LENGTH:
        raise RetrievalError(
            "The checklist item has no searchable requirement text.",
            status_code=422,
        )
    payload = {
        "query_text": query_text,
        "query_type": "checklist_item",
        "filters": {"checklist_item_id": checklist_item_id},
    }
    return search_project_evidence(db, project_id, payload, actor_name=actor_name)


def search_by_finding_context(
    db: Session,
    project_id: str,
    finding_id: str,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> dict:
    """Search indexed evidence for a finding by its title and evidence text."""

    finding = db.get(models.Finding, finding_id)
    if finding is None or finding.project_id != project_id:
        raise RetrievalError("Finding not found.", status_code=404)
    query_text = (
        finding.title or finding.evidence_to_find or ""
    ).strip()
    if len(query_text) < MIN_RETRIEVAL_QUERY_LENGTH:
        raise RetrievalError(
            "The finding has no searchable title or evidence text.",
            status_code=422,
        )
    payload = {
        "query_text": query_text,
        "query_type": "finding_context",
        "filters": {"finding_id": finding_id},
    }
    return search_project_evidence(db, project_id, payload, actor_name=actor_name)


# ---------------------------------------------------------------------------
# Real-derived chunk search
#
# This path searches DocumentChunk rows built from indexed PDF page text (the
# real chunk pipeline). It complements, and does not replace, the page-text
# search above. Only real-derived chunks (chunk_id prefixed with the
# real-derived marker) are searched, so seeded demo chunks are never returned
# here and cannot be mislabeled as extracted from an uploaded PDF.
#
# TODO(provenance): DocumentChunk has no source_mode/provenance column yet, so
# real-derived chunks are identified by their chunk_id prefix. A future pass
# should add a dedicated provenance column (for example source_mode) and switch
# this filter to use it. See docs/PHASE_1_REAL_PDF_INDEXING_AUDIT.md, PR 2.
# ---------------------------------------------------------------------------


def _real_derived_chunks(
    db: Session, project_id: str
) -> list[models.DocumentChunk]:
    """Return a project's real-derived chunks in stable order."""

    stmt = (
        select(models.DocumentChunk)
        .where(
            models.DocumentChunk.project_id == project_id,
            models.DocumentChunk.chunk_id.like(
                f"{REAL_DERIVED_CHUNK_PREFIX}%"
            ),
        )
        .order_by(
            models.DocumentChunk.document_id,
            models.DocumentChunk.chunk_index,
        )
    )
    return list(db.scalars(stmt).all())


def _page_lookup(
    db: Session, project_id: str
) -> dict[tuple[str, int], models.DocumentPage]:
    """Map (document_id, page_number) to its DocumentPage for a project."""

    stmt = select(models.DocumentPage).where(
        models.DocumentPage.project_id == project_id
    )
    lookup: dict[tuple[str, int], models.DocumentPage] = {}
    for page in db.scalars(stmt).all():
        lookup[(page.document_id, page.page_number)] = page
    return lookup


def _score_chunk_evidence(
    *,
    query: str,
    query_tokens: list[str],
    chunk: models.DocumentChunk,
    document: models.Document | None,
) -> tuple[float, str, list[str], str] | None:
    """Score a real-derived chunk against a query.

    Returns (score, ranking_reason, match_terms, excerpt) or None when the chunk
    does not match. The score is bounded below 1.0 so the system never implies a
    perfect or certain match. Ranking is deterministic and local: exact phrase
    match, keyword overlap, term frequency, and document metadata match.
    """

    content = chunk.content or ""
    if not content.strip():
        return None
    lower_content = content.lower()
    query_lower = query.strip().lower()

    matched_terms = [token for token in query_tokens if token in lower_content]
    keyword_text = " ".join(chunk.keywords or []).lower()
    matched_keywords = [
        keyword
        for keyword in (chunk.keywords or [])
        if any(token in keyword.lower() for token in query_tokens)
    ]
    phrase_hit = bool(query_lower) and query_lower in lower_content

    document_type = (document.document_type if document else "") or ""
    file_name = _document_display_name(document) if document else chunk.file_name
    metadata_text = f"{document_type} {file_name}".lower()
    metadata_hit = any(token in metadata_text for token in query_tokens)
    keyword_hit = bool(matched_keywords) or bool(query_lower and query_lower in keyword_text)

    if not phrase_hit and not matched_terms and not metadata_hit and not keyword_hit:
        return None

    total_hits = sum(lower_content.count(token) for token in matched_terms)

    score = 0.45
    if phrase_hit:
        score += 0.25
    score += 0.05 * len(matched_terms)
    if keyword_hit:
        score += 0.05
    score += min(0.10, 0.02 * total_hits)
    if metadata_hit:
        score += 0.05
    score = round(min(score, 0.95), 2)

    match_start = 0
    if phrase_hit:
        match_start = lower_content.find(query_lower)
    elif matched_terms:
        positions = [lower_content.find(term) for term in matched_terms]
        match_start = min(pos for pos in positions if pos >= 0)
    excerpt = _excerpt_around(content, match_start)

    reasons: list[str] = []
    if phrase_hit:
        reasons.append("exact phrase match")
    if matched_terms:
        reasons.append("keyword match: " + ", ".join(matched_terms[:4]))
    elif matched_keywords:
        reasons.append("keyword match: " + ", ".join(matched_keywords[:4]))
    if total_hits > len(matched_terms):
        reasons.append(f"{total_hits} keyword hit(s) in the chunk")
    if metadata_hit:
        reasons.append(f"document metadata match ({document_type or file_name})")
    if not reasons:
        reasons.append("text overlap with the query")
    ranking_reason = (
        "Ranked by " + " and ".join(reasons[:2])
        + (("; " + "; ".join(reasons[2:])) if reasons[2:] else "")
        + " in real-derived page chunk."
    )

    terms = list(matched_terms)
    if not terms and matched_keywords:
        terms = list(matched_keywords)
    if phrase_hit and query.strip() not in terms:
        terms = [query.strip(), *terms]
    return score, ranking_reason, terms, excerpt


def _chunk_result_dict(
    *,
    chunk: models.DocumentChunk,
    document: models.Document | None,
    page: models.DocumentPage | None,
    score: float,
    ranking_reason: str,
    match_terms: list[str],
    excerpt: str,
) -> dict:
    return {
        "document_id": chunk.document_id,
        "document_name": (
            _document_display_name(document) if document else chunk.file_name
        ),
        "document_type": (
            document.document_type if document else chunk.document_type
        ),
        "chunk_id": chunk.chunk_id,
        "document_page_id": page.document_page_id if page else None,
        "page_number": chunk.page_number,
        "page_label": page.page_label if page else None,
        "text_extraction_status": (
            page.text_extraction_status if page else None
        ),
        "excerpt": excerpt,
        "match_terms": match_terms,
        "ranking_score": score,
        "ranking_reason": ranking_reason,
    }


def _chunk_result_message(
    db: Session, project_id: str, results: list[dict], searchable_count: int
) -> str:
    """Honest message that never implies a negative evidence conclusion."""

    if results:
        return (
            f"{len(results)} real-derived chunk candidate(s) for reviewer "
            "review."
        )
    if searchable_count == 0:
        return (
            "Indexed chunk evidence is not available yet. Index a digital PDF "
            "and build page chunks before searching chunk evidence. This is not "
            "a finding about the document content."
        )
    return (
        "No real-derived chunk text matched these terms. Try different terms or "
        "filters. This is not a finding about the document content."
    )


def search_project_chunk_evidence(
    db: Session,
    project_id: str,
    payload: dict,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> dict:
    """Search a project's real-derived chunks and return ranked candidates.

    payload accepts query_text, filters (document_id, document_type, page_min,
    page_max), and limit. Only real-derived chunks whose source page is indexed
    with extractable text are searched, so a non-indexed or no-text page is never
    treated as evidence absent. Results carry page-level citation context. A
    RetrievalQuery record and an audit event are written.
    """

    _require_project(db, project_id)
    ensure_demo_actor(db)

    query_text = (payload.get("query_text") or "").strip()
    filters = dict(payload.get("filters") or {})
    limit = payload.get("limit") or 10

    if len(query_text) < MIN_RETRIEVAL_QUERY_LENGTH:
        raise RetrievalError(
            "query_text is required and must be at least "
            f"{MIN_RETRIEVAL_QUERY_LENGTH} characters.",
            status_code=422,
        )
    reject_prohibited_language(query_text, field="query_text")
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 10
    limit = max(1, min(limit, MAX_RETRIEVAL_RESULTS))

    chunks = _real_derived_chunks(db, project_id)
    documents = _document_map(db, project_id)
    pages = _page_lookup(db, project_id)
    query_tokens = _tokens(query_text)

    document_id = filters.get("document_id")
    document_type = filters.get("document_type")
    page_min = filters.get("page_min")
    page_max = filters.get("page_max")

    searchable_count = 0
    results: list[dict] = []
    for chunk in chunks:
        page = (
            pages.get((chunk.document_id, chunk.page_number))
            if chunk.page_number is not None
            else None
        )
        # Not-indexed guardrail: only chunks whose source page is indexed with
        # extractable text are searchable evidence. A chunk whose page is not
        # indexed or carries no extractable text is skipped, never reported as
        # evidence absent.
        if page is None or page.text_extraction_status != INDEXED_TEXT_STATUS:
            continue
        searchable_count += 1

        document = documents.get(chunk.document_id)
        if document_id and chunk.document_id != document_id:
            continue
        if document_type and (
            document is None or document.document_type != document_type
        ):
            continue
        if page_min is not None and (chunk.page_number or 0) < int(page_min):
            continue
        if page_max is not None and (chunk.page_number or 0) > int(page_max):
            continue

        scored = _score_chunk_evidence(
            query=query_text,
            query_tokens=query_tokens,
            chunk=chunk,
            document=document,
        )
        if scored is None:
            continue
        score, reason, terms, excerpt = scored
        results.append(
            _chunk_result_dict(
                chunk=chunk,
                document=document,
                page=page,
                score=score,
                ranking_reason=reason,
                match_terms=terms,
                excerpt=excerpt,
            )
        )

    results.sort(
        key=lambda r: (
            -r["ranking_score"],
            r["document_id"],
            r["page_number"] or 0,
        )
    )
    results = results[:limit]

    message = _chunk_result_message(db, project_id, results, searchable_count)
    retrieval_query = _record_retrieval_query(
        db,
        project_id=project_id,
        query_text=query_text,
        query_type="chunk_keyword",
        filters=filters,
        result_count=len(results),
        related_checklist_item_id=filters.get("checklist_item_id"),
        related_finding_id=filters.get("finding_id"),
        actor_name=actor_name,
    )
    for result in results:
        result["candidate_origin"] = "chunk_search"
        result["retrieval_query_id"] = retrieval_query.retrieval_query_id

    record_audit_event(
        db,
        project_id=project_id,
        event_type="chunk_evidence_search_performed",
        related_entity_type="retrieval_query",
        related_entity_id=retrieval_query.retrieval_query_id,
        description=(
            "Reviewer searched real-derived chunk evidence; "
            f"{len(results)} candidate(s)."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "query_type": "chunk_keyword",
            "result_count": len(results),
            "searchable_chunk_count": searchable_count,
            "filters": _safe_filter_metadata(filters),
        },
    )
    db.commit()

    return {
        "project_id": project_id,
        "query_text": query_text,
        "query_type": "chunk_keyword",
        "retrieval_query_id": retrieval_query.retrieval_query_id,
        "result_count": len(results),
        "results": results,
        "message": message,
    }


# ---------------------------------------------------------------------------
# Candidate queue
# ---------------------------------------------------------------------------


def save_candidate(
    db: Session,
    project_id: str,
    payload: dict,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> models.EvidenceCandidate:
    """Save a retrieval result into the reviewer draft queue as a candidate."""

    _require_project(db, project_id)
    ensure_demo_actor(db)

    document_id = (payload.get("document_id") or "").strip()
    if not document_id:
        raise RetrievalError("document_id is required.", status_code=422)
    document = db.get(models.Document, document_id)
    if document is None or document.project_id != project_id:
        raise RetrievalError("Document not found.", status_code=404)

    candidate_title = (payload.get("candidate_title") or "").strip()
    if not candidate_title:
        raise RetrievalError("candidate_title is required.", status_code=422)
    for field in ("candidate_title", "candidate_excerpt", "reviewer_note"):
        reject_prohibited_language(payload.get(field), field=field)

    candidate_status = payload.get("candidate_status") or "saved_for_review"
    if candidate_status not in ALLOWED_CANDIDATE_STATUSES:
        raise RetrievalError(
            f"Invalid candidate_status '{candidate_status}'. Allowed: "
            f"{', '.join(sorted(ALLOWED_CANDIDATE_STATUSES))}.",
            status_code=422,
        )
    candidate_origin = payload.get("candidate_origin") or "manual_save"
    if candidate_origin not in ALLOWED_CANDIDATE_ORIGINS:
        raise RetrievalError(
            f"Invalid candidate_origin '{candidate_origin}'. Allowed: "
            f"{', '.join(sorted(ALLOWED_CANDIDATE_ORIGINS))}.",
            status_code=422,
        )

    page = None
    document_page_id = payload.get("document_page_id")
    page_number = payload.get("page_number")
    if document_page_id:
        page = db.get(models.DocumentPage, document_page_id)
        if page is None or page.document_id != document_id:
            raise RetrievalError(
                "Document page not found for this document.", status_code=422
            )
    elif page_number is not None:
        # Citation integrity: when a candidate (for example a chunk-derived
        # result) supplies only a page number, resolve the matching DocumentPage
        # so the saved candidate carries a real document_page_id. If no page
        # matches, the candidate is still saved with the page number alone.
        page = db.scalars(
            select(models.DocumentPage).where(
                models.DocumentPage.document_id == document_id,
                models.DocumentPage.page_number == int(page_number),
            )
        ).first()
    if page is not None:
        page_number = page.page_number

    finding_id = payload.get("finding_id")
    if finding_id:
        finding = db.get(models.Finding, finding_id)
        if finding is None or finding.project_id != project_id:
            raise RetrievalError(
                "Finding not found for this project.", status_code=422
            )

    now = _now()
    excerpt = payload.get("candidate_excerpt")
    if excerpt:
        excerpt = excerpt[:_EXCERPT_LIMIT]
    candidate = models.EvidenceCandidate(
        evidence_candidate_id=f"cand_{_short()}",
        project_id=project_id,
        retrieval_query_id=payload.get("retrieval_query_id"),
        document_id=document_id,
        document_page_id=page.document_page_id if page else document_page_id,
        page_number=page_number,
        finding_id=finding_id,
        checklist_item_id=payload.get("checklist_item_id"),
        candidate_title=candidate_title,
        candidate_excerpt=excerpt,
        match_terms=list(payload.get("match_terms") or []),
        ranking_score=float(payload.get("ranking_score") or 0.0),
        ranking_reason=payload.get("ranking_reason"),
        candidate_status=candidate_status,
        candidate_origin=candidate_origin,
        reviewer_note=payload.get("reviewer_note"),
        created_by_actor_id=DEMO_ACTOR_ID,
        created_by_name=actor_name,
        created_at=now,
        updated_at=now,
    )
    db.add(candidate)
    record_audit_event(
        db,
        project_id=project_id,
        event_type="evidence_candidate_saved",
        related_entity_type="evidence_candidate",
        related_entity_id=candidate.evidence_candidate_id,
        description=(
            f"Reviewer saved evidence candidate '{candidate_title}' "
            f"({candidate_origin})."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "candidate_id": candidate.evidence_candidate_id,
            "document_id": document_id,
            "page_number": page_number,
            "candidate_status": candidate_status,
            "candidate_origin": candidate_origin,
        },
    )
    db.commit()
    db.refresh(candidate)
    return candidate


def list_project_candidates(
    db: Session,
    project_id: str,
    *,
    candidate_status: str | None = None,
    finding_id: str | None = None,
) -> list[models.EvidenceCandidate]:
    """List saved candidates for a project, newest first, with optional filters."""

    stmt = select(models.EvidenceCandidate).where(
        models.EvidenceCandidate.project_id == project_id
    )
    if candidate_status:
        stmt = stmt.where(
            models.EvidenceCandidate.candidate_status == candidate_status
        )
    if finding_id:
        stmt = stmt.where(models.EvidenceCandidate.finding_id == finding_id)
    stmt = stmt.order_by(models.EvidenceCandidate.created_at.desc())
    return list(db.scalars(stmt).all())


def list_retrieval_queries(
    db: Session, project_id: str
) -> list[models.RetrievalQuery]:
    """List retrieval query history for a project, newest first."""

    stmt = (
        select(models.RetrievalQuery)
        .where(models.RetrievalQuery.project_id == project_id)
        .order_by(models.RetrievalQuery.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_candidate(
    db: Session, project_id: str, candidate_id: str
) -> models.EvidenceCandidate:
    candidate = db.get(models.EvidenceCandidate, candidate_id)
    if candidate is None or candidate.project_id != project_id:
        raise RetrievalError("Evidence candidate not found.", status_code=404)
    return candidate


def update_candidate_status(
    db: Session,
    project_id: str,
    candidate_id: str,
    payload: dict,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> models.EvidenceCandidate:
    """Update a candidate's reviewer note and/or status under reviewer control."""

    candidate = get_candidate(db, project_id, candidate_id)
    reject_prohibited_language(payload.get("reviewer_note"), field="reviewer_note")

    new_status = payload.get("candidate_status")
    if new_status is not None:
        if new_status not in ALLOWED_CANDIDATE_STATUSES:
            raise RetrievalError(
                f"Invalid candidate_status '{new_status}'. Allowed: "
                f"{', '.join(sorted(ALLOWED_CANDIDATE_STATUSES))}.",
                status_code=422,
            )
        candidate.candidate_status = new_status
    if payload.get("reviewer_note") is not None:
        candidate.reviewer_note = payload.get("reviewer_note")
    candidate.updated_at = _now()

    record_audit_event(
        db,
        project_id=project_id,
        event_type="evidence_candidate_updated",
        related_entity_type="evidence_candidate",
        related_entity_id=candidate_id,
        description=f"Reviewer updated evidence candidate {candidate_id}.",
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "candidate_id": candidate_id,
            "candidate_status": candidate.candidate_status,
        },
    )
    db.commit()
    db.refresh(candidate)
    return candidate


def dismiss_candidate(
    db: Session,
    project_id: str,
    candidate_id: str,
    *,
    note: str | None = None,
    actor_name: str = DEMO_ACTOR_NAME,
) -> models.EvidenceCandidate:
    """Mark a candidate as dismissed_by_reviewer. The record is retained."""

    candidate = get_candidate(db, project_id, candidate_id)
    reject_prohibited_language(note, field="reviewer_note")

    candidate.candidate_status = "dismissed_by_reviewer"
    if note is not None:
        candidate.reviewer_note = note
    candidate.dismissed_at = _now()
    candidate.updated_at = candidate.dismissed_at

    record_audit_event(
        db,
        project_id=project_id,
        event_type="evidence_candidate_dismissed",
        related_entity_type="evidence_candidate",
        related_entity_id=candidate_id,
        description=f"Reviewer dismissed evidence candidate {candidate_id}.",
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "candidate_id": candidate_id,
            "candidate_status": "dismissed_by_reviewer",
        },
    )
    db.commit()
    db.refresh(candidate)
    return candidate


# ---------------------------------------------------------------------------
# Promotion to draft finding
# ---------------------------------------------------------------------------


def promote_candidate_to_draft_finding(
    db: Session,
    project_id: str,
    candidate_id: str,
    payload: dict,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> dict:
    """Promote a candidate into a reviewer draft finding plus a citation.

    Creates a Finding with finding_origin retrieval_candidate and a safe draft
    human_review_status, links the source document/page through an
    EvidenceCitation, updates the candidate status to promoted_to_draft, and
    writes audit events. The system never decides severity or a final outcome;
    reviewer-entered content is validated against final-decision language.
    """

    candidate = get_candidate(db, project_id, candidate_id)
    ensure_demo_actor(db)

    if candidate.candidate_status == "promoted_to_draft":
        raise RetrievalError(
            "This candidate was already promoted to a draft finding.",
            status_code=422,
        )
    if candidate.candidate_status == "dismissed_by_reviewer":
        raise RetrievalError(
            "A dismissed candidate cannot be promoted. Re-save it first.",
            status_code=422,
        )

    title = (payload.get("title") or candidate.candidate_title or "").strip()
    if not title:
        raise RetrievalError("title is required.", status_code=422)
    category = (payload.get("category") or "general").strip() or "general"
    risk_level = (payload.get("risk_level") or "medium").strip() or "medium"
    evidence_status = payload.get("evidence_status") or "needs_reviewer_confirmation"
    evidence_to_find = (payload.get("evidence_to_find") or "").strip()
    reason_it_matters = (payload.get("reason_it_matters") or "").strip()
    recommended_human_action = (
        payload.get("recommended_human_action") or ""
    ).strip()
    reviewer_note = payload.get("reviewer_note")
    human_review_status = payload.get("human_review_status") or "draft"

    for field, value in (
        ("title", title),
        ("category", category),
        ("risk_level", risk_level),
        ("evidence_to_find", evidence_to_find),
        ("reason_it_matters", reason_it_matters),
        ("recommended_human_action", recommended_human_action),
        ("reviewer_note", reviewer_note),
    ):
        reject_prohibited_language(value, field=field)

    if evidence_status not in ALLOWED_EVIDENCE_STATUSES:
        raise RetrievalError(
            f"Invalid evidence_status '{evidence_status}'. Allowed: "
            f"{', '.join(sorted(ALLOWED_EVIDENCE_STATUSES))}.",
            status_code=422,
        )
    if human_review_status not in ALLOWED_REVIEWER_FINDING_STATUSES:
        raise RetrievalError(
            f"Invalid human_review_status '{human_review_status}'. Allowed: "
            f"{', '.join(sorted(ALLOWED_REVIEWER_FINDING_STATUSES))}.",
            status_code=422,
        )

    now = _now()
    finding_id = f"find_draft_{_short()}"
    finding = models.Finding(
        finding_id=finding_id,
        project_id=project_id,
        planted_issue="",
        title=title,
        category=category,
        risk_level=risk_level,
        expected_status=evidence_status,
        evidence_status=evidence_status,
        evidence_to_find=evidence_to_find,
        reason_it_matters=reason_it_matters,
        recommended_human_action=recommended_human_action,
        human_review_status=human_review_status,
        related_checklist_items=(
            [candidate.checklist_item_id] if candidate.checklist_item_id else []
        ),
        related_documents=[candidate.document_id],
        source_mode="user_created",
        finding_origin="retrieval_candidate",
        reviewer_notes=reviewer_note,
        created_by_name=actor_name,
        created_by_actor_id=DEMO_ACTOR_ID,
        created_at=now,
        updated_at=now,
    )
    db.add(finding)
    db.flush()

    record_audit_event(
        db,
        project_id=project_id,
        event_type="draft_finding_created_from_candidate",
        related_entity_type="finding",
        related_entity_id=finding_id,
        description=(
            f"Reviewer promoted candidate {candidate_id} into draft finding "
            f"'{title}'."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "candidate_id": candidate_id,
            "finding_id": finding_id,
            "finding_origin": "retrieval_candidate",
            "evidence_status": evidence_status,
            "human_review_status": human_review_status,
            "risk_level": risk_level,
        },
    )

    # Link the source document/page as a page-level evidence citation. The
    # excerpt the reviewer reviewed becomes the citation quote when provided.
    citation_excerpt = (
        payload.get("citation_excerpt") or candidate.candidate_excerpt
    )
    citation = create_evidence_citation(
        db,
        project_id=project_id,
        finding_id=finding_id,
        document_id=candidate.document_id,
        document_page_id=candidate.document_page_id,
        page_number=candidate.page_number,
        quoted_excerpt=citation_excerpt,
        reviewer_note=(
            "Promoted from evidence retrieval candidate "
            f"{candidate_id}."
        ),
        citation_type="reviewer_selected",
        created_by_name=actor_name,
    )
    record_audit_event(
        db,
        project_id=project_id,
        event_type="citation_created_from_candidate",
        related_entity_type="evidence_citation",
        related_entity_id=citation.evidence_citation_id,
        description=(
            f"Citation {citation.evidence_citation_id} created from candidate "
            f"{candidate_id}."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "candidate_id": candidate_id,
            "finding_id": finding_id,
            "evidence_citation_id": citation.evidence_citation_id,
            "document_id": candidate.document_id,
            "page_number": candidate.page_number,
        },
    )

    candidate.candidate_status = "promoted_to_draft"
    candidate.promoted_finding_id = finding_id
    candidate.updated_at = now
    record_audit_event(
        db,
        project_id=project_id,
        event_type="evidence_candidate_promoted_to_draft",
        related_entity_type="evidence_candidate",
        related_entity_id=candidate_id,
        description=(
            f"Candidate {candidate_id} promoted to draft finding {finding_id}."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "candidate_id": candidate_id,
            "finding_id": finding_id,
            "candidate_status": "promoted_to_draft",
        },
    )

    db.commit()
    db.refresh(finding)
    db.refresh(citation)
    db.refresh(candidate)
    return {
        "finding": finding,
        "citation": citation,
        "candidate": candidate,
    }
