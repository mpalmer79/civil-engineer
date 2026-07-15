"""Real-derived chunk evidence search.

This path searches DocumentChunk rows built from indexed PDF page text (the real
chunk pipeline). It complements, and does not replace, the page-text search. Only
real-derived chunks (identified by the durable chunk_origin provenance field, or
the legacy real-derived chunk_id prefix for older rows) are searched, so seeded
demo chunks are never returned here and cannot be mislabeled as extracted from an
uploaded PDF. Keyword, semantic, and hybrid modes all rank deterministically and
report a plain ranking reason. Every result is a candidate for reviewer review.

TODO(provenance): DocumentChunk has no source_mode/provenance column yet, so
real-derived chunks are identified by their chunk_id prefix. A future pass should
add a dedicated provenance column (for example source_mode) and switch this
filter to use it. See docs/PHASE_1_REAL_PDF_INDEXING_AUDIT.md, PR 2.
"""

from __future__ import annotations

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.safety import reject_prohibited_language
from app.db import models
from app.services.embedding_service import (
    EmbeddingError,
    cosine_similarity,
    embed_text,
)
from app.services.evidence_retrieval_service._common import (
    _document_display_name,
    _document_map,
    _excerpt_around,
    _record_retrieval_query,
    _require_project,
    _safe_filter_metadata,
    _tokens,
)
from app.services.evidence_retrieval_service.errors import (
    MAX_RETRIEVAL_RESULTS,
    MIN_RETRIEVAL_QUERY_LENGTH,
    RetrievalError,
    _RRF_K,
    _SEMANTIC_MIN_SIMILARITY,
)
from app.services.page_chunking_service import (
    CHUNK_ORIGIN_REAL_DERIVED,
    INDEXED_TEXT_STATUS,
    REAL_DERIVED_CHUNK_PREFIX,
)
from app.services.real_intake_service import (
    DEMO_ACTOR_NAME,
    ensure_demo_actor,
    record_audit_event,
)


def _real_derived_chunks(
    db: Session, project_id: str
) -> list[models.DocumentChunk]:
    """Return a project's real-derived chunks in stable order.

    Prefers the durable chunk_origin provenance field. Older rows created before
    that column have a null chunk_origin and are matched by the legacy
    real-derived chunk_id prefix, so a transition database keeps working.
    """

    stmt = (
        select(models.DocumentChunk)
        .where(
            models.DocumentChunk.project_id == project_id,
            or_(
                models.DocumentChunk.chunk_origin == CHUNK_ORIGIN_REAL_DERIVED,
                and_(
                    models.DocumentChunk.chunk_origin.is_(None),
                    models.DocumentChunk.chunk_id.like(
                        f"{REAL_DERIVED_CHUNK_PREFIX}%"
                    ),
                ),
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


_CHUNK_MODE_QUERY_TYPE = {
    "keyword": "chunk_keyword",
    "semantic": "chunk_semantic",
    "hybrid": "chunk_hybrid",
}


def _collect_searchable_chunks(
    db: Session,
    project_id: str,
    filters: dict,
) -> tuple[
    list[tuple[models.DocumentChunk, models.DocumentPage, models.Document | None]],
    int,
]:
    """Return (chunk, page, document) triples that pass the not-indexed guardrail
    and the metadata filters, plus the count of searchable chunks before filters.

    Only chunks whose source page is indexed with extractable text are
    searchable, so a non-indexed or no-text page is never treated as evidence
    absent. searchable_count reflects how much indexed chunk evidence exists at
    all, independent of the query or the document filters.
    """

    chunks = _real_derived_chunks(db, project_id)
    documents = _document_map(db, project_id)
    pages = _page_lookup(db, project_id)

    document_id = filters.get("document_id")
    document_type = filters.get("document_type")
    extraction_status = filters.get("text_extraction_status")
    page_min = filters.get("page_min")
    page_max = filters.get("page_max")

    searchable_count = 0
    collected: list[
        tuple[models.DocumentChunk, models.DocumentPage, models.Document | None]
    ] = []
    for chunk in chunks:
        page = (
            pages.get((chunk.document_id, chunk.page_number))
            if chunk.page_number is not None
            else None
        )
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
        if (
            extraction_status
            and page.text_extraction_status != extraction_status
        ):
            continue
        if page_min is not None and (chunk.page_number or 0) < int(page_min):
            continue
        if page_max is not None and (chunk.page_number or 0) > int(page_max):
            continue
        collected.append((chunk, page, document))
    return collected, searchable_count


def _keyword_chunk_results(
    candidates: list[tuple],
    query_text: str,
) -> list[dict]:
    query_tokens = _tokens(query_text)
    results: list[dict] = []
    for chunk, page, document in candidates:
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
    return results


def _semantic_chunk_results(
    db: Session,
    project_id: str,
    candidates: list[tuple],
    query_text: str,
) -> list[dict]:
    # Local import avoids a circular import (chunk_embedding_service imports this
    # module for _real_derived_chunks).
    from app.services import chunk_embedding_service

    try:
        query_vector = embed_text(query_text)
    except EmbeddingError:
        return []
    embeddings = chunk_embedding_service.current_embeddings_by_chunk(
        db, project_id
    )

    results: list[dict] = []
    for chunk, page, document in candidates:
        embedding = embeddings.get(chunk.chunk_id)
        if embedding is None:
            continue
        similarity = cosine_similarity(query_vector, embedding.vector)
        if similarity < _SEMANTIC_MIN_SIMILARITY:
            continue
        score = round(min(similarity, 0.95), 2)
        excerpt = _excerpt_around(chunk.content or "", 0)
        results.append(
            _chunk_result_dict(
                chunk=chunk,
                document=document,
                page=page,
                score=score,
                ranking_reason=(
                    "Ranked by semantic similarity using chunk embedding."
                ),
                # A semantic-only match has no exact keyword overlap; do not
                # fabricate match terms.
                match_terms=[],
                excerpt=excerpt,
            )
        )
    return results


def _hybrid_chunk_results(
    db: Session,
    project_id: str,
    candidates: list[tuple],
    query_text: str,
) -> list[dict]:
    """Combine keyword and semantic rankings with Reciprocal Rank Fusion.

    Each chunk's fused score is the sum of 1/(k + rank) across the keyword and
    semantic rank lists it appears in. Results are then deduplicated to one entry
    per page, keeping the strongest chunk for that page. ranking_score is the
    fused score normalized to the top result so it reads as relevance.
    """

    keyword = _keyword_chunk_results(candidates, query_text)
    semantic = _semantic_chunk_results(db, project_id, candidates, query_text)

    by_chunk: dict[str, dict] = {}
    rrf: dict[str, float] = {}
    for rank, result in enumerate(keyword):
        cid = result["chunk_id"]
        by_chunk.setdefault(cid, result)
        rrf[cid] = rrf.get(cid, 0.0) + 1.0 / (_RRF_K + rank)
    for rank, result in enumerate(semantic):
        cid = result["chunk_id"]
        # Prefer the keyword result for display (it carries match terms and a
        # match-centered excerpt); otherwise use the semantic result.
        by_chunk.setdefault(cid, result)
        rrf[cid] = rrf.get(cid, 0.0) + 1.0 / (_RRF_K + rank)

    if not rrf:
        return []

    # Deduplicate to one result per page, keeping the highest fused score.
    best_per_page: dict[tuple[str, int | None], str] = {}
    for cid, result in by_chunk.items():
        key = (result["document_id"], result["page_number"])
        current = best_per_page.get(key)
        if current is None or rrf[cid] > rrf[current]:
            best_per_page[key] = cid

    max_rrf = max(rrf[cid] for cid in best_per_page.values())
    fused: list[dict] = []
    for cid in best_per_page.values():
        result = dict(by_chunk[cid])
        relevance = rrf[cid] / max_rrf if max_rrf > 0 else 0.0
        result["ranking_score"] = round(min(relevance * 0.95, 0.95), 2)
        result["ranking_reason"] = (
            "Ranked by keyword and semantic signals from real-derived page "
            "chunks."
        )
        fused.append(result)
    return fused


def search_project_chunk_evidence(
    db: Session,
    project_id: str,
    payload: dict,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> dict:
    """Search a project's real-derived chunks and return ranked candidates.

    payload accepts query_text, mode ("keyword", "semantic", or "hybrid"),
    filters (document_id, document_type, text_extraction_status, page_min,
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
    mode = (payload.get("mode") or "keyword").strip()
    if mode not in _CHUNK_MODE_QUERY_TYPE:
        raise RetrievalError(
            f"Unsupported chunk search mode '{mode}'. Allowed: "
            f"{', '.join(sorted(_CHUNK_MODE_QUERY_TYPE))}.",
            status_code=422,
        )
    # Scoped callers (checklist, finding) override the recorded query_type so the
    # response still reads as checklist_item / finding_context while the
    # mechanism underneath is chunk retrieval.
    query_type = payload.get("query_type") or _CHUNK_MODE_QUERY_TYPE[mode]

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

    candidates, searchable_count = _collect_searchable_chunks(
        db, project_id, filters
    )

    if mode == "semantic":
        results = _semantic_chunk_results(db, project_id, candidates, query_text)
    elif mode == "hybrid":
        results = _hybrid_chunk_results(db, project_id, candidates, query_text)
    else:
        results = _keyword_chunk_results(candidates, query_text)

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
        query_type=query_type,
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
            "Reviewer searched real-derived chunk evidence "
            f"({mode}); {len(results)} candidate(s)."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "query_type": query_type,
            "mode": mode,
            "result_count": len(results),
            "searchable_chunk_count": searchable_count,
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
