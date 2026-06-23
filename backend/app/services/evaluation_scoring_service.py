"""Evaluation scoring service for AI review runs.

This service compares the draft findings produced by an AI review run against
the expected Brookside Meadows findings and records heuristic, explainable
metrics: recall, precision, citation validity, human-review-required rate, and
quality signals (prohibited words, validation failures, safety failures).

The matching is deliberately simple so a reviewer can understand exactly why a
draft was or was not matched. It is not presented as a mathematically perfect
measure. Failed drafts are counted separately from valid drafts and are never
treated as valid review findings.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.safety import HUMAN_REVIEW_STATUSES, find_prohibited_language
from app.db import models

# Match types, ordered strongest to weakest for explainability.
MATCH_RELATED_CHECKLIST = "related_checklist_match"
MATCH_EXACT_CATEGORY = "exact_category_match"
MATCH_TITLE_SIMILARITY = "title_similarity_match"
MATCH_UNMATCHED_EXPECTED = "unmatched_expected"
MATCH_EXTRA_DRAFT = "extra_draft"

# Minimum Jaccard token overlap between titles to accept a title-similarity
# match. Kept conservative so weak overlaps do not produce false matches.
_TITLE_SIMILARITY_THRESHOLD = 0.34

_STOPWORDS = {
    "the",
    "and",
    "for",
    "not",
    "with",
    "may",
    "are",
    "was",
    "this",
    "that",
    "from",
    "across",
    "into",
}


class EvaluationError(Exception):
    """Raised when evaluation scoring cannot be performed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


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
            actor_type="evaluator",
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            description=description,
            timestamp=_now(),
            event_metadata=metadata or {},
        )
    )


def _title_tokens(text: str) -> set[str]:
    return {
        t
        for t in re.findall(r"[a-z0-9]+", (text or "").lower())
        if len(t) >= 3 and t not in _STOPWORDS
    }


def _title_similarity(a: str, b: str) -> float:
    ta, tb = _title_tokens(a), _title_tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def get_evaluation_result(
    db: Session, evaluation_result_id: str
) -> models.AIEvaluationResult | None:
    return db.scalars(
        select(models.AIEvaluationResult).where(
            models.AIEvaluationResult.evaluation_result_id == evaluation_result_id
        )
    ).first()


def get_matches_for_result(
    db: Session, evaluation_result_id: str
) -> list[models.AIEvaluationMatch]:
    return list(
        db.scalars(
            select(models.AIEvaluationMatch)
            .where(
                models.AIEvaluationMatch.evaluation_result_id
                == evaluation_result_id
            )
            .order_by(models.AIEvaluationMatch.id)
        ).all()
    )


def get_latest_evaluation_for_run(
    db: Session, review_run_id: str
) -> models.AIEvaluationResult | None:
    return db.scalars(
        select(models.AIEvaluationResult)
        .where(models.AIEvaluationResult.review_run_id == review_run_id)
        .order_by(models.AIEvaluationResult.created_at.desc())
    ).first()


def list_evaluation_results_for_project(
    db: Session, project_id: str
) -> list[models.AIEvaluationResult]:
    return list(
        db.scalars(
            select(models.AIEvaluationResult)
            .where(models.AIEvaluationResult.project_id == project_id)
            .order_by(models.AIEvaluationResult.created_at.desc())
        ).all()
    )


def evaluate_review_run(
    db: Session, review_run_id: str
) -> models.AIEvaluationResult:
    """Score one AI review run against the expected findings and store results."""

    run = db.scalars(
        select(models.AIReviewRun).where(
            models.AIReviewRun.review_run_id == review_run_id
        )
    ).first()
    if run is None:
        raise EvaluationError("AI review run not found.", status_code=404)

    project_id = run.project_id

    all_drafts = list(
        db.scalars(
            select(models.AIDraftFinding).where(
                models.AIDraftFinding.review_run_id == review_run_id
            )
        ).all()
    )
    if not all_drafts:
        _audit(
            db,
            project_id=project_id,
            event_type="evaluation_scoring_failed",
            related_entity_type="ai_review_run",
            related_entity_id=review_run_id,
            description="Evaluation could not run: no draft findings in the run.",
        )
        db.commit()
        raise EvaluationError(
            "No draft findings exist for this review run.", status_code=409
        )

    expected = list(
        db.scalars(
            select(models.Finding).where(models.Finding.project_id == project_id)
        ).all()
    )
    if not expected:
        _audit(
            db,
            project_id=project_id,
            event_type="evaluation_scoring_failed",
            related_entity_type="ai_review_run",
            related_entity_id=review_run_id,
            description="Evaluation could not run: no expected findings exist.",
        )
        db.commit()
        raise EvaluationError(
            "No expected findings exist for this project.", status_code=409
        )

    _audit(
        db,
        project_id=project_id,
        event_type="evaluation_scoring_started",
        related_entity_type="ai_review_run",
        related_entity_id=review_run_id,
        description=(
            "Evaluation scoring started: comparing draft findings against "
            "expected findings."
        ),
        metadata={
            "review_run_id": review_run_id,
            "expected_findings_count": len(expected),
            "draft_findings_count": len(all_drafts),
        },
    )

    valid_drafts = [
        d for d in all_drafts if d.validation_status == "validation_passed"
    ]
    validation_failure_count = sum(
        1 for d in all_drafts if d.validation_status == "validation_failed"
    )
    safety_failure_count = sum(
        1 for d in all_drafts if d.safety_check_status == "safety_check_failed"
    )

    # Checklist category lookup for the explainable category match.
    checklist_category: dict[str, str] = {
        item.checklist_item_id: item.category
        for item in db.scalars(
            select(models.ChecklistItem).where(
                models.ChecklistItem.project_id == project_id
            )
        ).all()
    }

    # Project chunk ids for citation validity.
    chunk_ids = {
        c.chunk_id
        for c in db.scalars(
            select(models.DocumentChunk).where(
                models.DocumentChunk.project_id == project_id
            )
        ).all()
    }

    evaluation_result_id = f"evalres_{uuid.uuid4().hex[:12]}"
    matched_draft_ids: set[str] = set()
    matches: list[dict] = []

    def _draft_category(draft: models.AIDraftFinding) -> str | None:
        return checklist_category.get(draft.checklist_item_id)

    for exp in expected:
        related = set(exp.related_checklist_items or [])
        match: dict | None = None

        # 1. Related checklist item match (the planted-issue mapping).
        for d in valid_drafts:
            if d.draft_finding_id in matched_draft_ids:
                continue
            if d.checklist_item_id in related:
                match = {
                    "expected_finding_id": exp.finding_id,
                    "draft_finding_id": d.draft_finding_id,
                    "match_type": MATCH_RELATED_CHECKLIST,
                    "match_confidence": 0.95,
                    "matched_on": d.checklist_item_id,
                    "notes": (
                        "Draft checklist item matches an expected finding "
                        "related checklist item."
                    ),
                }
                break

        # 2. Exact category match.
        if match is None:
            exp_category = (exp.category or "").strip().lower()
            for d in valid_drafts:
                if d.draft_finding_id in matched_draft_ids:
                    continue
                dc = (_draft_category(d) or "").strip().lower()
                if exp_category and dc and exp_category == dc:
                    match = {
                        "expected_finding_id": exp.finding_id,
                        "draft_finding_id": d.draft_finding_id,
                        "match_type": MATCH_EXACT_CATEGORY,
                        "match_confidence": 0.7,
                        "matched_on": exp.category,
                        "notes": "Draft and expected finding share a category.",
                    }
                    break

        # 3. Title similarity match.
        if match is None:
            best_draft: models.AIDraftFinding | None = None
            best_score = 0.0
            for d in valid_drafts:
                if d.draft_finding_id in matched_draft_ids:
                    continue
                score = _title_similarity(exp.title, d.title)
                if score > best_score:
                    best_score, best_draft = score, d
            if best_draft is not None and best_score >= _TITLE_SIMILARITY_THRESHOLD:
                match = {
                    "expected_finding_id": exp.finding_id,
                    "draft_finding_id": best_draft.draft_finding_id,
                    "match_type": MATCH_TITLE_SIMILARITY,
                    "match_confidence": round(best_score, 3),
                    "matched_on": "title_overlap",
                    "notes": (
                        f"Title token overlap {round(best_score, 3)} above "
                        f"threshold {_TITLE_SIMILARITY_THRESHOLD}."
                    ),
                }

        if match is not None:
            matched_draft_ids.add(match["draft_finding_id"])
            matches.append(match)
        else:
            matches.append(
                {
                    "expected_finding_id": exp.finding_id,
                    "draft_finding_id": None,
                    "match_type": MATCH_UNMATCHED_EXPECTED,
                    "match_confidence": 0.0,
                    "matched_on": None,
                    "notes": "No draft finding matched this expected finding.",
                }
            )

    # Extra draft findings: valid drafts that matched no expected finding.
    for d in valid_drafts:
        if d.draft_finding_id not in matched_draft_ids:
            matches.append(
                {
                    "expected_finding_id": None,
                    "draft_finding_id": d.draft_finding_id,
                    "match_type": MATCH_EXTRA_DRAFT,
                    "match_confidence": 0.0,
                    "matched_on": None,
                    "notes": (
                        "Valid draft finding did not match any expected "
                        "finding."
                    ),
                }
            )

    matched_findings_count = len(matched_draft_ids)
    expected_findings_count = len(expected)
    draft_findings_count = len(valid_drafts)
    unmatched_expected_count = expected_findings_count - matched_findings_count
    extra_draft_findings_count = draft_findings_count - matched_findings_count

    recall = (
        matched_findings_count / expected_findings_count
        if expected_findings_count
        else 0.0
    )
    precision = (
        matched_findings_count / draft_findings_count
        if draft_findings_count
        else 0.0
    )

    if valid_drafts:
        good_citations = sum(
            1
            for d in valid_drafts
            if d.source_chunk_ids
            and all(cid in chunk_ids for cid in d.source_chunk_ids)
        )
        citation_validity_rate = good_citations / len(valid_drafts)
        in_human_review = sum(
            1 for d in valid_drafts if d.status in HUMAN_REVIEW_STATUSES
        )
        human_review_required_rate = in_human_review / len(valid_drafts)
    else:
        citation_validity_rate = 0.0
        human_review_required_rate = 0.0

    prohibited_word_count = sum(
        1
        for d in all_drafts
        if find_prohibited_language(d.title)
        or find_prohibited_language(d.summary)
        or find_prohibited_language(d.recommended_human_action)
    )

    overall_score = round(
        0.4 * recall
        + 0.3 * precision
        + 0.2 * citation_validity_rate
        + 0.1 * human_review_required_rate,
        3,
    )

    result = models.AIEvaluationResult(
        evaluation_result_id=evaluation_result_id,
        project_id=project_id,
        review_run_id=review_run_id,
        expected_findings_count=expected_findings_count,
        draft_findings_count=draft_findings_count,
        matched_findings_count=matched_findings_count,
        unmatched_expected_count=unmatched_expected_count,
        extra_draft_findings_count=extra_draft_findings_count,
        citation_validity_rate=round(citation_validity_rate, 3),
        human_review_required_rate=round(human_review_required_rate, 3),
        prohibited_word_count=prohibited_word_count,
        validation_failure_count=validation_failure_count,
        safety_failure_count=safety_failure_count,
        recall=round(recall, 3),
        precision=round(precision, 3),
        overall_score=overall_score,
    )
    db.add(result)

    for m in matches:
        match_id = f"evalmatch_{uuid.uuid4().hex[:12]}"
        db.add(
            models.AIEvaluationMatch(
                evaluation_match_id=match_id,
                evaluation_result_id=evaluation_result_id,
                expected_finding_id=m["expected_finding_id"],
                draft_finding_id=m["draft_finding_id"],
                match_type=m["match_type"],
                match_confidence=m["match_confidence"],
                matched_on=m["matched_on"],
                notes=m["notes"],
            )
        )
        _audit(
            db,
            project_id=project_id,
            event_type="evaluation_match_created",
            related_entity_type="ai_evaluation_match",
            related_entity_id=match_id,
            description=(
                f"Evaluation match recorded: {m['match_type']}."
            ),
            metadata={
                "evaluation_result_id": evaluation_result_id,
                "expected_finding_id": m["expected_finding_id"],
                "draft_finding_id": m["draft_finding_id"],
                "match_type": m["match_type"],
                "match_confidence": m["match_confidence"],
            },
        )

    _audit(
        db,
        project_id=project_id,
        event_type="evaluation_scoring_completed",
        related_entity_type="ai_evaluation_result",
        related_entity_id=evaluation_result_id,
        description=(
            "Evaluation scoring completed. Results are heuristic review-support "
            "metrics, not a final engineering determination."
        ),
        metadata={
            "evaluation_result_id": evaluation_result_id,
            "review_run_id": review_run_id,
            "recall": round(recall, 3),
            "precision": round(precision, 3),
            "matched_findings_count": matched_findings_count,
            "unmatched_expected_count": unmatched_expected_count,
            "extra_draft_findings_count": extra_draft_findings_count,
            "citation_validity_rate": round(citation_validity_rate, 3),
            "validation_failure_count": validation_failure_count,
            "safety_failure_count": safety_failure_count,
            "prohibited_word_count": prohibited_word_count,
            "overall_score": overall_score,
        },
    )

    db.commit()
    db.refresh(result)
    return result
