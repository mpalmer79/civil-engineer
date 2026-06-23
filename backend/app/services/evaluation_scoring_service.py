"""Evaluation scoring service.

This service compares an AI review run's draft findings against the seeded
Brookside Meadows expected findings. The scoring is intentionally transparent
and heuristic: it matches draft findings to expected findings using related
checklist items, category, and title keyword overlap, then reports recall,
precision, citation validity, prohibited wording, and validation and safety
failure counts.

The evaluation does not certify the AI or declare the package compliant. It is a
quality signal for a human reviewer. Failed draft findings are counted
separately from valid drafts and never count as matches.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import HUMAN_REVIEW_STATUSES, find_prohibited_language
from app.db import models
from app.services import ai_review_service, checklist_service, finding_service


class EvaluationError(Exception):
    """Raised when an evaluation run cannot be scored."""


# Match priority, strongest first. A draft is matched to at most one expected
# finding, and an expected finding is matched by at most one draft.
_TITLE_SIMILARITY_THRESHOLD = 0.18

# Stopwords removed before computing title keyword overlap so common words do
# not inflate the similarity score.
_STOPWORDS = {
    "the",
    "and",
    "for",
    "not",
    "may",
    "with",
    "was",
    "are",
    "from",
    "this",
    "that",
    "have",
    "been",
    "into",
    "across",
    "found",
    "draft",
    "finding",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _audit(
    db: Session,
    *,
    project_id: str,
    event_type: str,
    related_entity_type: str,
    related_entity_id: str,
    description: str,
    metadata: dict | None = None,
) -> None:
    db.add(
        models.AuditEvent(
            audit_event_id=f"audit_eval_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            event_type=event_type,
            actor_type="system",
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            description=description,
            timestamp=_now(),
            event_metadata=metadata or {},
        )
    )


def _title_tokens(text: str) -> set[str]:
    tokens = {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) >= 3}
    return tokens - _STOPWORDS


def _title_similarity(a: str, b: str) -> float:
    ta, tb = _title_tokens(a), _title_tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


@dataclass
class _MatchCandidate:
    expected: models.Finding
    match_type: str
    confidence: float
    matched_on: str
    priority: int


@dataclass
class _ScoringComputation:
    expected_count: int
    draft_count: int
    matched_count: int
    unmatched_expected: list[models.Finding] = field(default_factory=list)
    extra_drafts: list[models.AIDraftFinding] = field(default_factory=list)
    matches: list[tuple[models.AIDraftFinding, _MatchCandidate]] = field(
        default_factory=list
    )


def get_evaluation_result(
    db: Session, evaluation_result_id: str
) -> models.AIEvaluationResult | None:
    stmt = select(models.AIEvaluationResult).where(
        models.AIEvaluationResult.evaluation_result_id == evaluation_result_id
    )
    return db.scalars(stmt).first()


def get_matches_for_result(
    db: Session, evaluation_result_id: str
) -> list[models.AIEvaluationMatch]:
    stmt = (
        select(models.AIEvaluationMatch)
        .where(
            models.AIEvaluationMatch.evaluation_result_id == evaluation_result_id
        )
        .order_by(models.AIEvaluationMatch.created_at)
    )
    return list(db.scalars(stmt).all())


def list_results_for_project(
    db: Session, project_id: str
) -> list[models.AIEvaluationResult]:
    stmt = (
        select(models.AIEvaluationResult)
        .where(models.AIEvaluationResult.project_id == project_id)
        .order_by(models.AIEvaluationResult.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def latest_result_for_run(
    db: Session, review_run_id: str
) -> models.AIEvaluationResult | None:
    stmt = (
        select(models.AIEvaluationResult)
        .where(models.AIEvaluationResult.review_run_id == review_run_id)
        .order_by(models.AIEvaluationResult.created_at.desc())
    )
    return db.scalars(stmt).first()


def _candidate_for(
    draft: models.AIDraftFinding,
    expected: models.Finding,
    draft_category: str | None,
) -> _MatchCandidate | None:
    """Return the best match candidate between a draft and an expected finding."""

    if draft.checklist_item_id in (expected.related_checklist_items or []):
        return _MatchCandidate(
            expected=expected,
            match_type="related_checklist_match",
            confidence=0.95,
            matched_on=f"checklist_item:{draft.checklist_item_id}",
            priority=3,
        )
    if draft_category and draft_category.lower() == (expected.category or "").lower():
        return _MatchCandidate(
            expected=expected,
            match_type="exact_category_match",
            confidence=0.7,
            matched_on=f"category:{expected.category}",
            priority=2,
        )
    similarity = _title_similarity(draft.title, expected.title)
    if similarity >= _TITLE_SIMILARITY_THRESHOLD:
        return _MatchCandidate(
            expected=expected,
            match_type="title_similarity_match",
            confidence=round(similarity, 2),
            matched_on="title_keyword_overlap",
            priority=1,
        )
    return None


def _compute(
    valid_drafts: list[models.AIDraftFinding],
    expected_findings: list[models.Finding],
    category_by_item: dict[str, str],
) -> _ScoringComputation:
    used_expected: set[str] = set()
    matches: list[tuple[models.AIDraftFinding, _MatchCandidate]] = []
    extra_drafts: list[models.AIDraftFinding] = []

    for draft in valid_drafts:
        draft_category = category_by_item.get(draft.checklist_item_id)
        best: _MatchCandidate | None = None
        for expected in expected_findings:
            if expected.finding_id in used_expected:
                continue
            candidate = _candidate_for(draft, expected, draft_category)
            if candidate is None:
                continue
            if best is None or (candidate.priority, candidate.confidence) > (
                best.priority,
                best.confidence,
            ):
                best = candidate
        if best is not None:
            used_expected.add(best.expected.finding_id)
            matches.append((draft, best))
        else:
            extra_drafts.append(draft)

    unmatched_expected = [
        f for f in expected_findings if f.finding_id not in used_expected
    ]
    return _ScoringComputation(
        expected_count=len(expected_findings),
        draft_count=len(valid_drafts),
        matched_count=len(matches),
        unmatched_expected=unmatched_expected,
        extra_drafts=extra_drafts,
        matches=matches,
    )


def evaluate_review_run(
    db: Session, review_run_id: str
) -> models.AIEvaluationResult:
    """Score an AI review run against the project's expected findings."""

    run = ai_review_service.get_ai_review_run(db, review_run_id)
    if run is None:
        raise EvaluationError("AI review run not found.")

    project_id = run.project_id
    evaluation_result_id = f"eval_{uuid.uuid4().hex[:10]}"

    _audit(
        db,
        project_id=project_id,
        event_type="evaluation_scoring_started",
        related_entity_type="ai_review_run",
        related_entity_id=review_run_id,
        description="Evaluation scoring started for the AI review run.",
        metadata={
            "review_run_id": review_run_id,
            "evaluation_result_id": evaluation_result_id,
        },
    )

    all_drafts = ai_review_service.list_draft_findings_for_run(db, review_run_id)
    valid_drafts = [
        d for d in all_drafts if d.validation_status == "validation_passed"
    ]
    failed_drafts = [
        d for d in all_drafts if d.validation_status == "validation_failed"
    ]
    expected_findings = [
        f
        for f in finding_service.list_findings(db, project_id)
        if f.planted_issue
    ]

    if not all_drafts:
        _audit(
            db,
            project_id=project_id,
            event_type="evaluation_scoring_failed",
            related_entity_type="ai_review_run",
            related_entity_id=review_run_id,
            description="Evaluation could not run: the review run has no draft findings.",
            metadata={"review_run_id": review_run_id},
        )
        db.commit()
        raise EvaluationError(
            "The review run has no draft findings to evaluate."
        )
    if not expected_findings:
        _audit(
            db,
            project_id=project_id,
            event_type="evaluation_scoring_failed",
            related_entity_type="ai_review_run",
            related_entity_id=review_run_id,
            description="Evaluation could not run: no expected findings are seeded.",
            metadata={"review_run_id": review_run_id},
        )
        db.commit()
        raise EvaluationError("No expected findings are available to score against.")

    category_by_item = {
        item.checklist_item_id: item.category
        for item in checklist_service.list_checklist_items(db, project_id)
    }
    project_chunk_ids = {c.chunk_id for c in _project_chunks(db, project_id)}

    computation = _compute(valid_drafts, expected_findings, category_by_item)

    # Citation validity: a valid draft cites at least one chunk id and every
    # cited chunk id exists in the project's retrieved evidence.
    cited_ok = 0
    for d in valid_drafts:
        ids = d.source_chunk_ids or []
        if ids and all(cid in project_chunk_ids for cid in ids):
            cited_ok += 1
    citation_validity_rate = (
        round(cited_ok / len(valid_drafts), 4) if valid_drafts else 0.0
    )

    # Human review required rate: fraction of valid drafts whose status keeps
    # the finding under human review (it never becomes final on its own).
    under_review = sum(
        1 for d in valid_drafts if d.status in HUMAN_REVIEW_STATUSES
    )
    human_review_required_rate = (
        round(under_review / len(valid_drafts), 4) if valid_drafts else 0.0
    )

    # Prohibited wording across reviewer-facing fields of every draft.
    prohibited_word_count = 0
    for d in all_drafts:
        for text in (d.title, d.summary, d.recommended_human_action):
            prohibited_word_count += len(find_prohibited_language(text))

    validation_failure_count = len(failed_drafts)
    safety_failure_count = sum(
        1 for d in all_drafts if d.safety_check_status == "safety_check_failed"
    )

    recall = (
        round(computation.matched_count / computation.expected_count, 4)
        if computation.expected_count
        else 0.0
    )
    precision = (
        round(computation.matched_count / computation.draft_count, 4)
        if computation.draft_count
        else 0.0
    )

    # Overall score is a transparent weighted blend of the core signals. It is a
    # heuristic summary, not a precise grade.
    no_prohibited = 1.0 if prohibited_word_count == 0 else 0.0
    overall_score = round(
        0.4 * recall
        + 0.3 * precision
        + 0.2 * citation_validity_rate
        + 0.1 * no_prohibited,
        4,
    )

    result = models.AIEvaluationResult(
        evaluation_result_id=evaluation_result_id,
        project_id=project_id,
        review_run_id=review_run_id,
        expected_findings_count=computation.expected_count,
        draft_findings_count=computation.draft_count,
        matched_findings_count=computation.matched_count,
        unmatched_expected_count=len(computation.unmatched_expected),
        extra_draft_findings_count=len(computation.extra_drafts),
        citation_validity_rate=citation_validity_rate,
        human_review_required_rate=human_review_required_rate,
        prohibited_word_count=prohibited_word_count,
        validation_failure_count=validation_failure_count,
        safety_failure_count=safety_failure_count,
        recall=recall,
        precision=precision,
        overall_score=overall_score,
    )
    db.add(result)

    for draft, candidate in computation.matches:
        match_id = f"match_{uuid.uuid4().hex[:10]}"
        db.add(
            models.AIEvaluationMatch(
                evaluation_match_id=match_id,
                evaluation_result_id=evaluation_result_id,
                expected_finding_id=candidate.expected.finding_id,
                draft_finding_id=draft.draft_finding_id,
                match_type=candidate.match_type,
                match_confidence=candidate.confidence,
                matched_on=candidate.matched_on,
                notes=(
                    f"Draft {draft.draft_finding_id} matched expected "
                    f"{candidate.expected.finding_id} ({candidate.expected.planted_issue})."
                ),
            )
        )
        _audit(
            db,
            project_id=project_id,
            event_type="evaluation_match_created",
            related_entity_type="ai_evaluation_match",
            related_entity_id=match_id,
            description=(
                f"Matched draft {draft.draft_finding_id} to expected "
                f"{candidate.expected.finding_id} via {candidate.match_type}."
            ),
            metadata={
                "evaluation_result_id": evaluation_result_id,
                "review_run_id": review_run_id,
                "draft_finding_id": draft.draft_finding_id,
                "expected_finding_id": candidate.expected.finding_id,
                "match_type": candidate.match_type,
                "match_confidence": candidate.confidence,
            },
        )

    for expected in computation.unmatched_expected:
        db.add(
            models.AIEvaluationMatch(
                evaluation_match_id=f"match_{uuid.uuid4().hex[:10]}",
                evaluation_result_id=evaluation_result_id,
                expected_finding_id=expected.finding_id,
                draft_finding_id=None,
                match_type="unmatched_expected",
                match_confidence=0.0,
                matched_on=None,
                notes=(
                    f"Expected finding {expected.finding_id} "
                    f"({expected.planted_issue}) had no matching draft finding."
                ),
            )
        )

    for draft in computation.extra_drafts:
        db.add(
            models.AIEvaluationMatch(
                evaluation_match_id=f"match_{uuid.uuid4().hex[:10]}",
                evaluation_result_id=evaluation_result_id,
                expected_finding_id=None,
                draft_finding_id=draft.draft_finding_id,
                match_type="extra_draft",
                match_confidence=0.0,
                matched_on=None,
                notes=(
                    f"Draft finding {draft.draft_finding_id} had no matching "
                    "expected finding."
                ),
            )
        )

    _audit(
        db,
        project_id=project_id,
        event_type="evaluation_scoring_completed",
        related_entity_type="ai_evaluation_result",
        related_entity_id=evaluation_result_id,
        description=(
            "Evaluation scoring completed. This is a heuristic quality signal "
            "for human reviewers, not a certification of the AI or the package."
        ),
        metadata={
            "review_run_id": review_run_id,
            "evaluation_result_id": evaluation_result_id,
            "expected_findings_count": computation.expected_count,
            "draft_findings_count": computation.draft_count,
            "matched_findings_count": computation.matched_count,
            "unmatched_expected_count": len(computation.unmatched_expected),
            "extra_draft_findings_count": len(computation.extra_drafts),
            "recall": recall,
            "precision": precision,
            "citation_validity_rate": citation_validity_rate,
            "validation_failure_count": validation_failure_count,
            "safety_failure_count": safety_failure_count,
            "prohibited_word_count": prohibited_word_count,
            "overall_score": overall_score,
        },
    )

    db.commit()
    db.refresh(result)
    return result


def _project_chunks(db: Session, project_id: str):
    """Return the project's document chunks (used for citation validity)."""

    from app.services import retrieval_service

    return retrieval_service.list_project_chunks(db, project_id)
