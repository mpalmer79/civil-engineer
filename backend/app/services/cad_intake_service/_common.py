"""Shared private helpers for the CAD intake service package.

Timestamp and id generation, audit-event recording, layer categorization, text
normalization, review-support finding creation, and seeded plan-sheet lookup.
These helpers are used across the intake submodules and hold no public surface
of their own.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db import models
from app.services import plan_sheet_service
from app.services.cad import layer_taxonomy


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _short() -> str:
    return uuid.uuid4().hex[:12]


def _audit(
    db: Session,
    *,
    project_id: str,
    event_type: str,
    related_entity_type: str,
    related_entity_id: str,
    description: str,
    actor_type: str = "system",
    metadata: dict | None = None,
) -> None:
    db.add(
        models.AuditEvent(
            audit_event_id=f"audit_cad_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            event_type=event_type,
            actor_type=actor_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            description=description,
            timestamp=_now(),
            event_metadata=metadata or {},
        )
    )


def _layer_category(layer_name: str) -> str:
    return layer_taxonomy.layer_category(layer_name)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().upper())


def _seeded_sheet_map(db: Session, project_id: str) -> dict[str, str]:
    return {
        _normalize(s.sheet_number): s.sheet_id
        for s in plan_sheet_service.list_plan_sheets(db, project_id)
    }


def _create_finding(
    db: Session,
    *,
    run: models.CadParseRun,
    finding_type: str,
    title: str,
    description: str,
    severity: str,
    source_reference_candidate_id: str | None = None,
    source_layer_extract_id: str | None = None,
    source_text_extract_id: str | None = None,
    linked_plan_sheet_id: str | None = None,
) -> models.CadReviewFinding:
    finding = models.CadReviewFinding(
        cad_review_finding_id=f"cadfind_{_short()}",
        parse_run_id=run.parse_run_id,
        cad_file_id=run.cad_file_id,
        project_id=run.project_id,
        finding_type=finding_type,
        title=title,
        description=description,
        severity=severity,
        source_reference_candidate_id=source_reference_candidate_id,
        source_layer_extract_id=source_layer_extract_id,
        source_text_extract_id=source_text_extract_id,
        linked_plan_sheet_id=linked_plan_sheet_id,
        status="draft",
        requires_human_review=True,
    )
    db.add(finding)
    _audit(
        db,
        project_id=run.project_id,
        event_type="cad_review_finding_created",
        related_entity_type="cad_review_finding",
        related_entity_id=finding.cad_review_finding_id,
        description=f"CAD review finding created: {finding_type}.",
        metadata={
            "cad_review_finding_id": finding.cad_review_finding_id,
            "finding_type": finding_type,
        },
    )
    return finding
