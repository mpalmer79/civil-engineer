"""Seed package for the Brookside Meadows review fixture.

This package is the canonical runtime data source for the seeded demo. The
fixture is split by domain:

* reference_project: project identity, metadata, and site constants
* documents: the 19 submission document records
* checklist: the 19 stormwater checklist items
* findings: the 10 planted review-support findings
* workflow: audit events and evaluation cases
* hotspots: site map hotspots
* evidence: document chunks, finding sources, and retrieval queries
* plan_sheets: plan sheet index, CAD-aware metadata, plan references, and
  sheet hotspots

All of it is seeded review-support data, not content extracted from real CAD,
PDF, GIS, or plan files. seed_database, seed_evidence, and seed_plansheets are
the orchestrating entry points called at application startup.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db import models
from app.db.database import SessionLocal, init_db
from app.db.seeds.checklist import CHECKLIST
from app.db.seeds.documents import DOCUMENTS
from app.db.seeds.evidence import (
    CHUNKS,
    FINDING_SOURCES,
    RETRIEVAL_QUERIES,
    evidence_is_loaded,
    seed_evidence,
)
from app.db.seeds.findings import FINDINGS
from app.db.seeds.hotspots import HOTSPOTS
from app.db.seeds.plan_sheets import (
    CAD_METADATA,
    PLAN_REFERENCES,
    PLAN_SHEET_HOTSPOTS,
    PLAN_SHEETS,
    plan_data_is_loaded,
    seed_plansheets,
)
from app.db.seeds.reference_project import PROJECT, PROJECT_ID
from app.db.seeds.workflow import AUDIT_EVENTS, EVALUATION_CASES

__all__ = [
    "AUDIT_EVENTS",
    "CAD_METADATA",
    "CHECKLIST",
    "CHUNKS",
    "DOCUMENTS",
    "EVALUATION_CASES",
    "FINDINGS",
    "FINDING_SOURCES",
    "HOTSPOTS",
    "PLAN_REFERENCES",
    "PLAN_SHEETS",
    "PLAN_SHEET_HOTSPOTS",
    "PROJECT",
    "PROJECT_ID",
    "RETRIEVAL_QUERIES",
    "evidence_is_loaded",
    "main",
    "plan_data_is_loaded",
    "seed_database",
    "seed_evidence",
    "seed_is_loaded",
    "seed_plansheets",
]


def seed_is_loaded(db: Session) -> bool:
    """Return True if the Brookside Meadows project is already present."""

    return db.get(models.Project, PROJECT_ID) is not None


def seed_database(db: Session, *, force: bool = False) -> None:
    """Load the Brookside Meadows fixture into the database.

    If the project already exists and force is False, seeding is skipped so the
    operation is idempotent. With force=True, existing fixture rows are removed
    first and reloaded.
    """

    if seed_is_loaded(db):
        if not force:
            return
        for model in (
            models.Hotspot,
            models.EvaluationCase,
            models.AuditEvent,
            models.Finding,
            models.ChecklistItem,
            models.Document,
            models.Project,
        ):
            db.query(model).delete()
        db.commit()

    db.add(models.Project(**PROJECT))
    db.add_all(
        models.Document(project_id=PROJECT_ID, **doc) for doc in DOCUMENTS
    )
    db.add_all(
        models.ChecklistItem(
            project_id=PROJECT_ID, review_domain="stormwater", **item
        )
        for item in CHECKLIST
    )
    db.add_all(
        models.Finding(project_id=PROJECT_ID, **finding) for finding in FINDINGS
    )
    db.add_all(
        models.AuditEvent(project_id=PROJECT_ID, **event) for event in AUDIT_EVENTS
    )
    db.add_all(
        models.EvaluationCase(project_id=PROJECT_ID, **case)
        for case in EVALUATION_CASES
    )
    db.add_all(
        models.Hotspot(project_id=PROJECT_ID, **spot) for spot in HOTSPOTS
    )
    db.commit()


def main() -> None:
    """Create tables and load the seed data. Used by python -m app.db.seed."""

    init_db()
    db = SessionLocal()
    try:
        seed_database(db, force=True)
        seed_evidence(db, force=True)
        print(
            "Seeded Brookside Meadows: "
            f"{len(DOCUMENTS)} documents, {len(CHECKLIST)} checklist items, "
            f"{len(FINDINGS)} findings, {len(AUDIT_EVENTS)} audit events, "
            f"{len(EVALUATION_CASES)} evaluation cases, {len(HOTSPOTS)} hotspots, "
            f"{len(CHUNKS)} document chunks, {len(FINDING_SOURCES)} finding sources."
        )
    finally:
        db.close()
