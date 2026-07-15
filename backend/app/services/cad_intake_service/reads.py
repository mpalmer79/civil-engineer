"""Read helpers for CAD files, parse runs, and extracted metadata.

These functions return registered CAD files, parse runs, and the per-run layer,
entity, block, text, and reference-candidate extracts, plus the CAD review
findings for a project. Viewing layers and text values writes an audit event so
the decision history shows reviewer access.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services.cad_intake_service._common import _audit


def get_cad_file(db: Session, cad_file_id: str) -> models.CadFileUpload | None:
    return db.scalars(
        select(models.CadFileUpload).where(
            models.CadFileUpload.cad_file_id == cad_file_id
        )
    ).first()


def list_cad_files(db: Session, project_id: str) -> list[models.CadFileUpload]:
    return list(
        db.scalars(
            select(models.CadFileUpload)
            .where(models.CadFileUpload.project_id == project_id)
            .order_by(models.CadFileUpload.created_at.desc())
        ).all()
    )


def get_cad_parse_run(db: Session, parse_run_id: str) -> models.CadParseRun | None:
    return db.scalars(
        select(models.CadParseRun).where(
            models.CadParseRun.parse_run_id == parse_run_id
        )
    ).first()


def list_cad_parse_runs(db: Session, project_id: str) -> list[models.CadParseRun]:
    return list(
        db.scalars(
            select(models.CadParseRun)
            .where(models.CadParseRun.project_id == project_id)
            .order_by(models.CadParseRun.started_at.desc())
        ).all()
    )


def list_cad_layers(
    db: Session, parse_run_id: str, *, audit: bool = True
) -> list[models.CadLayerExtract]:
    layers = list(
        db.scalars(
            select(models.CadLayerExtract)
            .where(models.CadLayerExtract.parse_run_id == parse_run_id)
            .order_by(models.CadLayerExtract.layer_name)
        ).all()
    )
    if audit and layers:
        run = get_cad_parse_run(db, parse_run_id)
        if run is not None:
            _audit(
                db,
                project_id=run.project_id,
                event_type="cad_layers_viewed",
                related_entity_type="cad_parse_run",
                related_entity_id=parse_run_id,
                description="CAD parse run layers viewed.",
                actor_type="reviewer",
                metadata={"parse_run_id": parse_run_id, "layer_count": len(layers)},
            )
            db.commit()
    return layers


def list_cad_entities(
    db: Session, parse_run_id: str
) -> list[models.CadEntityExtract]:
    return list(
        db.scalars(
            select(models.CadEntityExtract)
            .where(models.CadEntityExtract.parse_run_id == parse_run_id)
            .order_by(models.CadEntityExtract.id)
        ).all()
    )


def list_cad_blocks(db: Session, parse_run_id: str) -> list[models.CadBlockExtract]:
    return list(
        db.scalars(
            select(models.CadBlockExtract)
            .where(models.CadBlockExtract.parse_run_id == parse_run_id)
            .order_by(models.CadBlockExtract.block_name)
        ).all()
    )


def list_cad_text(
    db: Session, parse_run_id: str, *, audit: bool = True
) -> list[models.CadTextExtract]:
    texts = list(
        db.scalars(
            select(models.CadTextExtract)
            .where(models.CadTextExtract.parse_run_id == parse_run_id)
            .order_by(models.CadTextExtract.id)
        ).all()
    )
    if audit and texts:
        run = get_cad_parse_run(db, parse_run_id)
        if run is not None:
            _audit(
                db,
                project_id=run.project_id,
                event_type="cad_text_viewed",
                related_entity_type="cad_parse_run",
                related_entity_id=parse_run_id,
                description="CAD parse run text extracts viewed.",
                actor_type="reviewer",
                metadata={"parse_run_id": parse_run_id, "text_count": len(texts)},
            )
            db.commit()
    return texts


def list_cad_reference_candidates(
    db: Session, parse_run_id: str
) -> list[models.CadReferenceCandidate]:
    return list(
        db.scalars(
            select(models.CadReferenceCandidate)
            .where(models.CadReferenceCandidate.parse_run_id == parse_run_id)
            .order_by(models.CadReferenceCandidate.id)
        ).all()
    )


def list_cad_review_findings(
    db: Session, project_id: str
) -> list[models.CadReviewFinding]:
    return list(
        db.scalars(
            select(models.CadReviewFinding)
            .where(models.CadReviewFinding.project_id == project_id)
            .order_by(models.CadReviewFinding.created_at)
        ).all()
    )


def list_unpromoted_cad_findings(
    db: Session, project_id: str, *, audit: bool = True
) -> list[models.CadReviewFinding]:
    """Return CAD review findings not yet promoted to a workflow item.

    A finding is unpromoted when it has no linked workflow item and has not been
    flagged promoted. Excluded findings are skipped. Read side effect (when audit
    is True): writes a cad_unpromoted_findings_viewed audit event.
    """

    findings = [
        f
        for f in list_cad_review_findings(db, project_id)
        if f.linked_workflow_item_id is None
        and not f.promoted_to_workflow
        and f.status != "excluded_from_packet"
    ]
    if audit:
        _audit(
            db,
            project_id=project_id,
            event_type="cad_unpromoted_findings_viewed",
            related_entity_type="project",
            related_entity_id=project_id,
            description="Unpromoted CAD review findings viewed.",
            actor_type="reviewer",
            metadata={"unpromoted_count": len(findings)},
        )
        db.commit()
    return findings
