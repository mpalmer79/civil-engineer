"""AI Review Assistant service.

This service runs the controlled AI review workflow:

1. Load applicable checklist items for the project.
2. Retrieve source evidence for each checklist item (Phase 3 retrieval).
3. Build a constrained prompt from the retrieved evidence only.
4. Call the configured provider (mock by default).
5. Validate the output against the schema and safety rules.
6. Save the result as a draft review-support finding that requires human review.
7. Write audit events at each step.

The AI does not make final engineering decisions. Every draft finding requires
human review. Validation failures are stored and audited, never hidden.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.prompts import build_checklist_review_prompt
from app.ai.provider import get_provider
from app.ai.validators import validate_ai_output
from app.core.config import get_settings
from app.db import models
from app.services import checklist_service, retrieval_service


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:8]


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
            audit_event_id=f"audit_ai_{uuid.uuid4().hex[:12]}",
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


def _checklist_item_dict(item: models.ChecklistItem) -> dict:
    return {
        "checklist_item_id": item.checklist_item_id,
        "category": item.category,
        "requirement": item.requirement,
        "expected_evidence": item.expected_evidence,
    }


def list_ai_review_runs(db: Session, project_id: str) -> list[models.AIReviewRun]:
    stmt = (
        select(models.AIReviewRun)
        .where(models.AIReviewRun.project_id == project_id)
        .order_by(models.AIReviewRun.started_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_ai_review_run(db: Session, review_run_id: str) -> models.AIReviewRun | None:
    stmt = select(models.AIReviewRun).where(
        models.AIReviewRun.review_run_id == review_run_id
    )
    return db.scalars(stmt).first()


def list_draft_findings_for_run(
    db: Session, review_run_id: str
) -> list[models.AIDraftFinding]:
    stmt = (
        select(models.AIDraftFinding)
        .where(models.AIDraftFinding.review_run_id == review_run_id)
        .order_by(models.AIDraftFinding.draft_finding_id)
    )
    return list(db.scalars(stmt).all())


def list_draft_findings_for_project(
    db: Session, project_id: str
) -> list[models.AIDraftFinding]:
    stmt = (
        select(models.AIDraftFinding)
        .where(models.AIDraftFinding.project_id == project_id)
        .order_by(models.AIDraftFinding.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_draft_finding(
    db: Session, draft_finding_id: str
) -> models.AIDraftFinding | None:
    stmt = select(models.AIDraftFinding).where(
        models.AIDraftFinding.draft_finding_id == draft_finding_id
    )
    return db.scalars(stmt).first()


def start_ai_review_run(
    db: Session, project_id: str, run_type: str = "full_checklist"
) -> models.AIReviewRun:
    """Run the AI review workflow for a project and return the run record."""

    settings = get_settings()
    provider = get_provider(settings)
    prompt_version = settings.PROMPT_VERSION

    review_run_id = f"airun_{_short()}"
    run = models.AIReviewRun(
        review_run_id=review_run_id,
        project_id=project_id,
        run_type=run_type,
        provider=provider.name,
        model_name=provider.model_name,
        status="running",
        prompt_version=prompt_version,
        checklist_item_count=0,
        draft_findings_created=0,
        safety_failures=0,
        started_at=_now(),
    )
    db.add(run)
    _audit(
        db,
        project_id=project_id,
        event_type="ai_review_run_started",
        related_entity_type="ai_review_run",
        related_entity_id=review_run_id,
        description="AI review run started with constrained, evidence-first workflow.",
        metadata={
            "provider": provider.name,
            "model_name": provider.model_name,
            "prompt_version": prompt_version,
        },
    )
    db.commit()

    checklist_items = checklist_service.list_checklist_items(db, project_id)
    created = 0
    failures = 0

    for item in checklist_items:
        item_dict = _checklist_item_dict(item)
        _audit(
            db,
            project_id=project_id,
            event_type="checklist_item_loaded",
            related_entity_type="checklist_item",
            related_entity_id=item.checklist_item_id,
            description=f"Loaded checklist item {item.checklist_item_id}.",
        )

        evidence = retrieval_service.evidence_for_checklist_item(
            db, project_id, item.checklist_item_id
        )
        chunk_ids = [e["chunk_id"] for e in evidence if e.get("chunk_id")]
        _audit(
            db,
            project_id=project_id,
            event_type="evidence_retrieved",
            related_entity_type="checklist_item",
            related_entity_id=item.checklist_item_id,
            description=(
                f"Retrieved {len(evidence)} source chunks for "
                f"{item.checklist_item_id}."
            ),
            metadata={"retrieved_chunk_ids": chunk_ids},
        )

        prompt = build_checklist_review_prompt(item_dict, evidence)
        _audit(
            db,
            project_id=project_id,
            event_type="prompt_built",
            related_entity_type="checklist_item",
            related_entity_id=item.checklist_item_id,
            description="Constrained prompt built from retrieved evidence.",
            metadata={"prompt_version": prompt_version},
        )

        project_dict = {"project_id": project_id}
        raw = provider.generate_finding(
            project=project_dict,
            checklist_item=item_dict,
            evidence=evidence,
            prompt=prompt,
        )
        _audit(
            db,
            project_id=project_id,
            event_type="provider_called",
            related_entity_type="checklist_item",
            related_entity_id=item.checklist_item_id,
            description=f"Provider {provider.name} called for {item.checklist_item_id}.",
            metadata={"provider": provider.name, "produced_output": raw is not None},
        )

        if raw is None:
            # The provider produced no draft finding for this item.
            continue

        outcome = validate_ai_output(raw, set(chunk_ids))
        draft_finding_id = f"draft_{review_run_id[6:]}_{item.checklist_item_id}"

        if outcome.ok and outcome.parsed is not None:
            parsed = outcome.parsed
            db.add(
                models.AIDraftFinding(
                    draft_finding_id=draft_finding_id,
                    review_run_id=review_run_id,
                    project_id=project_id,
                    checklist_item_id=parsed.checklist_item_id,
                    finding_type=parsed.finding_type,
                    title=parsed.title,
                    summary=parsed.summary,
                    risk_level=parsed.risk_level,
                    confidence=parsed.confidence,
                    status="requires_human_review",
                    recommended_human_action=parsed.recommended_human_action,
                    source_chunk_ids=parsed.source_chunk_ids,
                    validation_status="validation_passed",
                    safety_check_status="safety_check_passed",
                    validation_errors=[],
                )
            )
            created += 1
            _audit(
                db,
                project_id=project_id,
                event_type="draft_finding_generated",
                related_entity_type="ai_draft_finding",
                related_entity_id=draft_finding_id,
                description=f"Draft review-support finding generated: {parsed.title}.",
                metadata={
                    "checklist_item_id": item.checklist_item_id,
                    "source_chunk_ids": parsed.source_chunk_ids,
                },
            )
            _audit(
                db,
                project_id=project_id,
                event_type="draft_finding_validation_passed",
                related_entity_type="ai_draft_finding",
                related_entity_id=draft_finding_id,
                description="Draft finding passed schema validation.",
            )
            _audit(
                db,
                project_id=project_id,
                event_type="safety_check_passed",
                related_entity_type="ai_draft_finding",
                related_entity_id=draft_finding_id,
                description="Draft finding passed safety wording and citation checks.",
            )
        else:
            failures += 1
            safety_status = (
                "safety_check_failed"
                if any(e.startswith("safety:") for e in outcome.errors)
                else "safety_check_passed"
            )
            db.add(
                models.AIDraftFinding(
                    draft_finding_id=draft_finding_id,
                    review_run_id=review_run_id,
                    project_id=project_id,
                    checklist_item_id=item.checklist_item_id,
                    finding_type=(
                        outcome.parsed.finding_type
                        if outcome.parsed
                        else "requires_human_review"
                    ),
                    title=(
                        outcome.parsed.title
                        if outcome.parsed
                        else "Draft finding failed validation"
                    ),
                    summary=(
                        "This draft output failed validation and is not a valid "
                        "draft finding. See validation errors."
                    ),
                    risk_level=(
                        outcome.parsed.risk_level if outcome.parsed else "low"
                    ),
                    confidence=(
                        outcome.parsed.confidence if outcome.parsed else 0.0
                    ),
                    status="validation_failed",
                    recommended_human_action=(
                        "Discard or regenerate. This output did not pass "
                        "validation."
                    ),
                    source_chunk_ids=(
                        outcome.parsed.source_chunk_ids if outcome.parsed else []
                    ),
                    validation_status="validation_failed",
                    safety_check_status=safety_status,
                    validation_errors=outcome.errors,
                )
            )
            _audit(
                db,
                project_id=project_id,
                event_type="draft_finding_validation_failed",
                related_entity_type="ai_draft_finding",
                related_entity_id=draft_finding_id,
                description="Draft finding failed validation and was not accepted.",
                metadata={
                    "checklist_item_id": item.checklist_item_id,
                    "validation_errors": outcome.errors,
                },
            )
            if safety_status == "safety_check_failed":
                _audit(
                    db,
                    project_id=project_id,
                    event_type="safety_check_failed",
                    related_entity_type="ai_draft_finding",
                    related_entity_id=draft_finding_id,
                    description="Draft finding failed safety checks.",
                    metadata={"validation_errors": outcome.errors},
                )

    run.checklist_item_count = len(checklist_items)
    run.draft_findings_created = created
    run.safety_failures = failures
    run.status = "completed"
    run.completed_at = _now()
    _audit(
        db,
        project_id=project_id,
        event_type="ai_review_run_completed",
        related_entity_type="ai_review_run",
        related_entity_id=review_run_id,
        description=(
            f"AI review run completed: {created} draft findings created, "
            f"{failures} validation failures. All drafts require human review."
        ),
        metadata={
            "draft_findings_created": created,
            "validation_failures": failures,
        },
    )
    db.commit()
    db.refresh(run)
    return run
