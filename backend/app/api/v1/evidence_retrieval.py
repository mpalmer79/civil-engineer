"""Evidence retrieval and reviewer draft finding queue API routes (Sprint 3).

These endpoints search a project's indexed PDF page text deterministically,
manage a reviewer-controlled queue of evidence candidates, and promote a
candidate into a reviewer draft finding with a page-level citation.

Retrieval is deterministic and local. It does not call external services, does
not call an AI provider, and does not OCR. Search results are candidates for
reviewer evaluation, never conclusions. Promotion creates a reviewer draft
finding under human review; it does not approve plans, certify compliance,
verify CAD, validate design, declare a project safe, resolve or close an issue,
or finalize a review outcome. Responses never include full extracted page text
or raw server file paths.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.services.access_control_service import (
    get_optional_user,
    require_project_reviewer,
)
from app.schemas.evidence_retrieval import (
    CandidateDismissRequest,
    ChunkEmbeddingBackfillResponse,
    ChunkEvidenceSearchRequest,
    EvidenceCandidateCreate,
    EvidenceCandidateResponse,
    EvidenceCandidateUpdate,
    EvidenceSearchRequest,
    EvidenceSearchResponse,
    PromoteCandidateToDraftFindingRequest,
    PromoteCandidateToDraftFindingResponse,
    RetrievalQueryResponse,
)
from app.services import chunk_embedding_service
from app.services import evidence_retrieval_service as retrieval
from app.services.evidence_retrieval_service import RetrievalError

router = APIRouter(tags=["evidence-retrieval"])


def _handle(exc: Exception) -> HTTPException:
    status_code = getattr(exc, "status_code", 422)
    message = getattr(exc, "message", str(exc))
    return HTTPException(status_code=status_code, detail=message)


@router.post(
    "/projects/{project_id}/evidence-retrieval/search",
    response_model=EvidenceSearchResponse,
)
def search_evidence(
    project_id: str,
    body: EvidenceSearchRequest,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> EvidenceSearchResponse:
    require_project_reviewer(db, project_id, user)
    try:
        result = retrieval.search_project_evidence(
            db,
            project_id,
            {
                "query_text": body.query_text,
                "query_type": body.query_type,
                "filters": body.filters.model_dump(exclude_none=True),
                "limit": body.limit,
            },
        )
    except (RetrievalError, ValueError) as exc:
        raise _handle(exc) from exc
    return EvidenceSearchResponse.model_validate(result)


@router.post(
    "/projects/{project_id}/evidence-retrieval/chunk-search",
    response_model=EvidenceSearchResponse,
)
def search_chunk_evidence(
    project_id: str,
    body: ChunkEvidenceSearchRequest,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> EvidenceSearchResponse:
    """Keyword search over real-derived document chunks.

    Searches only chunks built from indexed PDF page text. It does not replace
    the page-text search and never returns seeded demo chunks. Results carry
    page-level citation context for the candidate and citation flow.
    """

    require_project_reviewer(db, project_id, user)
    try:
        result = retrieval.search_project_chunk_evidence(
            db,
            project_id,
            {
                "query_text": body.query_text,
                "mode": body.mode,
                "filters": body.filters.model_dump(exclude_none=True),
                "limit": body.limit,
            },
        )
    except (RetrievalError, ValueError) as exc:
        raise _handle(exc) from exc
    return EvidenceSearchResponse.model_validate(result)


@router.post(
    "/projects/{project_id}/evidence-retrieval/embed-chunks",
    response_model=ChunkEmbeddingBackfillResponse,
)
def embed_chunks(
    project_id: str,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ChunkEmbeddingBackfillResponse:
    """Backfill embeddings for the project's real-derived chunks.

    Deterministic and local. Skips chunks already embedded with the current
    model and unchanged content, refreshes stale-model vectors, and never embeds
    empty content. Returns counts only.
    """

    actor = require_project_reviewer(db, project_id, user)
    result = chunk_embedding_service.backfill_project_chunk_embeddings(
        db, project_id, actor_name=actor.display_name
    )
    return ChunkEmbeddingBackfillResponse.model_validate(result)


@router.post(
    "/projects/{project_id}/evidence-retrieval/checklist/{checklist_item_id}",
    response_model=EvidenceSearchResponse,
)
def search_checklist_evidence(
    project_id: str,
    checklist_item_id: str,
    db: Session = Depends(get_db),
) -> EvidenceSearchResponse:
    try:
        result = retrieval.search_by_checklist_item(
            db, project_id, checklist_item_id
        )
    except (RetrievalError, ValueError) as exc:
        raise _handle(exc) from exc
    return EvidenceSearchResponse.model_validate(result)


@router.post(
    "/projects/{project_id}/evidence-retrieval/findings/{finding_id}",
    response_model=EvidenceSearchResponse,
)
def search_finding_evidence(
    project_id: str,
    finding_id: str,
    db: Session = Depends(get_db),
) -> EvidenceSearchResponse:
    try:
        result = retrieval.search_by_finding_context(db, project_id, finding_id)
    except (RetrievalError, ValueError) as exc:
        raise _handle(exc) from exc
    return EvidenceSearchResponse.model_validate(result)


@router.get(
    "/projects/{project_id}/evidence-candidates",
    response_model=list[EvidenceCandidateResponse],
)
def list_candidates(
    project_id: str,
    candidate_status: str | None = Query(default=None),
    finding_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[EvidenceCandidateResponse]:
    return retrieval.list_project_candidates(
        db,
        project_id,
        candidate_status=candidate_status,
        finding_id=finding_id,
    )


@router.post(
    "/projects/{project_id}/evidence-candidates",
    response_model=EvidenceCandidateResponse,
    status_code=201,
)
def save_candidate(
    project_id: str,
    body: EvidenceCandidateCreate,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> EvidenceCandidateResponse:
    require_project_reviewer(db, project_id, user)
    try:
        return retrieval.save_candidate(
            db, project_id, body.model_dump(exclude_none=True)
        )
    except (RetrievalError, ValueError) as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/evidence-candidates/{candidate_id}",
    response_model=EvidenceCandidateResponse,
)
def get_candidate(
    project_id: str,
    candidate_id: str,
    db: Session = Depends(get_db),
) -> EvidenceCandidateResponse:
    try:
        return retrieval.get_candidate(db, project_id, candidate_id)
    except (RetrievalError, ValueError) as exc:
        raise _handle(exc) from exc


@router.patch(
    "/projects/{project_id}/evidence-candidates/{candidate_id}",
    response_model=EvidenceCandidateResponse,
)
def update_candidate(
    project_id: str,
    candidate_id: str,
    body: EvidenceCandidateUpdate,
    db: Session = Depends(get_db),
) -> EvidenceCandidateResponse:
    try:
        return retrieval.update_candidate_status(
            db, project_id, candidate_id, body.model_dump(exclude_none=True)
        )
    except (RetrievalError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/evidence-candidates/{candidate_id}/dismiss",
    response_model=EvidenceCandidateResponse,
)
def dismiss_candidate(
    project_id: str,
    candidate_id: str,
    body: CandidateDismissRequest,
    db: Session = Depends(get_db),
) -> EvidenceCandidateResponse:
    try:
        return retrieval.dismiss_candidate(
            db, project_id, candidate_id, note=body.reviewer_note
        )
    except (RetrievalError, ValueError) as exc:
        raise _handle(exc) from exc


@router.post(
    "/projects/{project_id}/evidence-candidates/{candidate_id}/promote-to-draft-finding",
    response_model=PromoteCandidateToDraftFindingResponse,
    status_code=201,
)
def promote_candidate(
    project_id: str,
    candidate_id: str,
    body: PromoteCandidateToDraftFindingRequest,
    user: models.UserAccount | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> PromoteCandidateToDraftFindingResponse:
    require_project_reviewer(db, project_id, user)
    try:
        result = retrieval.promote_candidate_to_draft_finding(
            db, project_id, candidate_id, body.model_dump(exclude_none=True)
        )
    except (RetrievalError, ValueError) as exc:
        raise _handle(exc) from exc
    return PromoteCandidateToDraftFindingResponse.model_validate(
        {
            "finding": result["finding"],
            "citation": result["citation"],
            "candidate": result["candidate"],
        }
    )


@router.get(
    "/projects/{project_id}/retrieval-queries",
    response_model=list[RetrievalQueryResponse],
)
def list_retrieval_queries(
    project_id: str,
    db: Session = Depends(get_db),
) -> list[RetrievalQueryResponse]:
    return retrieval.list_retrieval_queries(db, project_id)
