"""Deterministic page-text evidence search.

This path ranks indexed DocumentPage rows by keyword overlap, exact phrase
match, document metadata match, and keyword density, reporting a plain ranking
reason for each result. It is local and deterministic and never calls an AI
provider. The checklist and finding scoped searches delegate to the real-derived
chunk search. Every result is a candidate for reviewer review, not a conclusion.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_RETRIEVAL_QUERY_TYPES,
    reject_prohibited_language,
)
from app.db import models
from app.services.evidence_retrieval_service._common import (
    _checklist_query_text,
    _document_display_name,
    _excerpt_around,
    _finding_query_text,
    _indexed_pages,
    _document_map,
    _record_retrieval_query,
    _require_project,
    _safe_filter_metadata,
    _tokens,
)
from app.services.evidence_retrieval_service.errors import (
    MAX_RETRIEVAL_RESULTS,
    MIN_RETRIEVAL_QUERY_LENGTH,
    RetrievalError,
)
from app.services.real_intake_service import (
    DEMO_ACTOR_NAME,
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


def search_by_checklist_item(
    db: Session,
    project_id: str,
    checklist_item_id: str,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> dict:
    """Search real-derived chunk evidence for a checklist item.

    Uses hybrid chunk retrieval (the strongest path over real chunks). When no
    searchable chunks exist, the response honestly reports that indexed chunk
    evidence is not available yet, never a finding about document content.
    """

    # Local import avoids a circular import: chunk_search depends on this module
    # only through the package re-exports, not the other way around at load time.
    from app.services.evidence_retrieval_service.chunk_search import (
        search_project_chunk_evidence,
    )

    item = db.get(models.ChecklistItem, checklist_item_id)
    if item is None or item.project_id != project_id:
        raise RetrievalError("Checklist item not found.", status_code=404)
    query_text = _checklist_query_text(item)
    if len(query_text) < MIN_RETRIEVAL_QUERY_LENGTH:
        raise RetrievalError(
            "The checklist item has no searchable requirement text.",
            status_code=422,
        )
    payload = {
        "query_text": query_text,
        "mode": "hybrid",
        "query_type": "checklist_item",
        "filters": {"checklist_item_id": checklist_item_id},
    }
    return search_project_chunk_evidence(
        db, project_id, payload, actor_name=actor_name
    )


def search_by_finding_context(
    db: Session,
    project_id: str,
    finding_id: str,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> dict:
    """Search real-derived chunk evidence for a finding's context.

    Uses hybrid chunk retrieval. When no searchable chunks exist, the response
    honestly reports that indexed chunk evidence is not available yet.
    """

    # Local import avoids a circular import (see search_by_checklist_item).
    from app.services.evidence_retrieval_service.chunk_search import (
        search_project_chunk_evidence,
    )

    finding = db.get(models.Finding, finding_id)
    if finding is None or finding.project_id != project_id:
        raise RetrievalError("Finding not found.", status_code=404)
    query_text = _finding_query_text(finding)
    if len(query_text) < MIN_RETRIEVAL_QUERY_LENGTH:
        raise RetrievalError(
            "The finding has no searchable title or evidence text.",
            status_code=422,
        )
    payload = {
        "query_text": query_text,
        "mode": "hybrid",
        "query_type": "finding_context",
        "filters": {"finding_id": finding_id},
    }
    return search_project_chunk_evidence(
        db, project_id, payload, actor_name=actor_name
    )
