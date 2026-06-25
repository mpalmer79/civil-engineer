"""SQLAlchemy models for the Civil Engineer AI backend.

The schema includes the Phase 2 core review entities, the Phase 3 source
evidence entities, the Phase 4 AI review entities, the Phase 5 human review and
evaluation entities, the Phase 6 plan sheet and CAD-aware review entities, the
Phase 8 review packet entities, the Phase 9 reviewer workflow board entities,
and the Phase 10 external review response package entities. JSON columns are
used for arrays and nested values during the local prototype phase, with a clean
path to normalization later.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp for column defaults.

    Used instead of datetime.utcnow, which is deprecated on Python 3.12 and
    returns a naive datetime. The stored value and column type are unchanged.
    """

    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    project_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_name: Mapped[str] = mapped_column(String, nullable=False)
    project_type: Mapped[str] = mapped_column(String, nullable=False)
    location_context: Mapped[str] = mapped_column(String, nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String, nullable=False)
    review_type: Mapped[str] = mapped_column(String, nullable=False)
    review_domain: Mapped[str] = mapped_column(String, nullable=False)
    acreage: Mapped[float] = mapped_column(Float, nullable=False)
    disturbed_area: Mapped[float] = mapped_column(Float, nullable=False)
    proposed_lots: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    site_conditions: Mapped[list] = mapped_column(JSON, default=list)
    proposed_improvements: Mapped[list] = mapped_column(JSON, default=list)
    known_constraints: Mapped[list] = mapped_column(JSON, default=list)

    documents: Mapped[list["Document"]] = relationship(back_populates="project")
    checklist_items: Mapped[list["ChecklistItem"]] = relationship(
        back_populates="project"
    )
    findings: Mapped[list["Finding"]] = relationship(back_populates="project")
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="project")
    evaluation_cases: Mapped[list["EvaluationCase"]] = relationship(
        back_populates="project"
    )
    hotspots: Mapped[list["Hotspot"]] = relationship(back_populates="project")
    plan_sheets: Mapped[list["PlanSheet"]] = relationship(back_populates="project")


class Document(Base):
    __tablename__ = "documents"

    document_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    expected_key_information: Mapped[str] = mapped_column(Text, nullable=False)
    intentionally_missing_or_conflicting_information: Mapped[str | None] = (
        mapped_column(Text, nullable=True)
    )

    project: Mapped["Project"] = relationship(back_populates="documents")


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    checklist_item_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    review_domain: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    requirement: Mapped[str] = mapped_column(Text, nullable=False)
    expected_evidence: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_documents: Mapped[list] = mapped_column(JSON, default=list)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    applies_when: Mapped[str] = mapped_column(String, nullable=False)
    expected_status_for_brookside_meadows: Mapped[str] = mapped_column(
        String, nullable=False
    )
    planted_issue: Mapped[str | None] = mapped_column(String, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="checklist_items")


class Finding(Base):
    __tablename__ = "findings"

    finding_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    planted_issue: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    expected_status: Mapped[str] = mapped_column(String, nullable=False)
    evidence_to_find: Mapped[str] = mapped_column(Text, nullable=False)
    reason_it_matters: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_human_action: Mapped[str] = mapped_column(Text, nullable=False)
    human_review_status: Mapped[str] = mapped_column(String, nullable=False)
    related_checklist_items: Mapped[list] = mapped_column(JSON, default=list)
    related_documents: Mapped[list] = mapped_column(JSON, default=list)

    project: Mapped["Project"] = relationship(back_populates="findings")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    audit_event_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    actor_type: Mapped[str] = mapped_column(String, nullable=False)
    related_entity_type: Mapped[str] = mapped_column(String, nullable=False)
    related_entity_id: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # Non-sensitive structured context (provider, prompt version, chunk ids,
    # validation and safety status). Never stores secrets or API keys.
    event_metadata: Mapped[dict] = mapped_column("event_metadata", JSON, default=dict)

    project: Mapped["Project"] = relationship(back_populates="audit_events")


class EvaluationCase(Base):
    __tablename__ = "evaluation_cases"

    eval_case_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    input_documents: Mapped[list] = mapped_column(JSON, default=list)
    expected_findings: Mapped[list] = mapped_column(JSON, default=list)
    expected_risk_level: Mapped[str] = mapped_column(String, nullable=False)
    evaluation_metric: Mapped[str] = mapped_column(String, nullable=False)
    seeded_result: Mapped[dict] = mapped_column(JSON, default=dict)

    project: Mapped["Project"] = relationship(back_populates="evaluation_cases")


class Hotspot(Base):
    __tablename__ = "hotspots"

    hotspot_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    civil_purpose: Mapped[str] = mapped_column(Text, nullable=False)
    related_checklist_items: Mapped[list] = mapped_column(JSON, default=list)
    related_planted_issues: Mapped[list] = mapped_column(JSON, default=list)
    future_drilldown: Mapped[str] = mapped_column(Text, nullable=False)
    position_x_percent: Mapped[float] = mapped_column(Float, nullable=False)
    position_y_percent: Mapped[float] = mapped_column(Float, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="hotspots")


class DocumentChunk(Base):
    """A short, retrievable excerpt of source evidence from a document.

    Phase 3 seeds synthetic chunks rather than parsing real documents. Each
    chunk carries enough metadata (page, section, keywords, related checklist
    items and findings) to support keyword and metadata based retrieval.
    """

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chunk_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.document_id"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_heading: Mapped[str | None] = mapped_column(String, nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    related_checklist_items: Mapped[list] = mapped_column(JSON, default=list)
    related_findings: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class FindingSource(Base):
    """Source evidence linking a review-support finding to a document chunk.

    A finding source is not a conclusion. It records where in the submitted
    documents a reviewer can inspect evidence relevant to a finding, and what
    role that evidence plays (supports, shows missing evidence, shows a
    conflict, context only, or requires reviewer confirmation).
    """

    __tablename__ = "finding_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    finding_source_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    finding_id: Mapped[str] = mapped_column(
        ForeignKey("findings.finding_id"), nullable=False
    )
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.document_id"), nullable=False
    )
    chunk_id: Mapped[str | None] = mapped_column(String, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_role: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class RetrievalQuery(Base):
    """An audit record of a retrieval query run against the seeded chunks.

    This supports future auditing of retrieval behavior. Phase 3 seeds a few
    representative queries; later phases can record live queries here.
    """

    __tablename__ = "retrieval_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    retrieval_query_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    query_text: Mapped[str] = mapped_column(String, nullable=False)
    related_checklist_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class AIReviewRun(Base):
    """An execution of the AI Review Assistant over a project's checklist.

    A run records the provider, model, prompt version, and outcome counts so the
    workflow is auditable. The AI does not make final engineering decisions; it
    produces draft review-support findings that require human review.
    """

    __tablename__ = "ai_review_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_run_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    run_type: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String, nullable=False)
    checklist_item_count: Mapped[int] = mapped_column(Integer, default=0)
    draft_findings_created: Mapped[int] = mapped_column(Integer, default=0)
    safety_failures: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class AIDraftFinding(Base):
    """An AI-generated draft review-support finding.

    A draft finding is not a final engineering conclusion. It is generated from
    retrieved source evidence, validated against a strict schema and safety
    checks, and always requires human review before any action.
    """

    __tablename__ = "ai_draft_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draft_finding_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    review_run_id: Mapped[str] = mapped_column(
        ForeignKey("ai_review_runs.review_run_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    checklist_item_id: Mapped[str] = mapped_column(String, nullable=False)
    finding_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    recommended_human_action: Mapped[str] = mapped_column(Text, nullable=False)
    source_chunk_ids: Mapped[list] = mapped_column(JSON, default=list)
    validation_status: Mapped[str] = mapped_column(String, nullable=False)
    safety_check_status: Mapped[str] = mapped_column(String, nullable=False)
    validation_errors: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class HumanReviewAction(Base):
    """A persisted human review decision on an AI draft finding.

    A review action records what a human reviewer did with a draft finding
    (accepted, edited, rejected, escalated, marked unclear, or requested more
    information), the status transition it produced, and any edited text. No
    action approves, certifies, or finalizes an engineering decision. Every
    action keeps the finding under human control.
    """

    __tablename__ = "human_review_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_action_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    draft_finding_id: Mapped[str] = mapped_column(
        ForeignKey("ai_draft_findings.draft_finding_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    review_run_id: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=False)
    edited_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    edited_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    edited_recommended_action: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    previous_status: Mapped[str] = mapped_column(String, nullable=False)
    new_status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class AIEvaluationResult(Base):
    """A scored evaluation of one AI review run against expected findings.

    Evaluation is heuristic and explainable, not a mathematically perfect
    measure. It compares the draft findings from a review run against the
    expected Brookside Meadows findings and records recall, precision, citation
    validity, and quality signals so the workflow stays auditable.
    """

    __tablename__ = "ai_evaluation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_result_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    review_run_id: Mapped[str] = mapped_column(
        ForeignKey("ai_review_runs.review_run_id"), nullable=False
    )
    expected_findings_count: Mapped[int] = mapped_column(Integer, default=0)
    draft_findings_count: Mapped[int] = mapped_column(Integer, default=0)
    matched_findings_count: Mapped[int] = mapped_column(Integer, default=0)
    unmatched_expected_count: Mapped[int] = mapped_column(Integer, default=0)
    extra_draft_findings_count: Mapped[int] = mapped_column(Integer, default=0)
    citation_validity_rate: Mapped[float] = mapped_column(Float, default=0.0)
    human_review_required_rate: Mapped[float] = mapped_column(Float, default=0.0)
    prohibited_word_count: Mapped[int] = mapped_column(Integer, default=0)
    validation_failure_count: Mapped[int] = mapped_column(Integer, default=0)
    safety_failure_count: Mapped[int] = mapped_column(Integer, default=0)
    recall: Mapped[float] = mapped_column(Float, default=0.0)
    precision: Mapped[float] = mapped_column(Float, default=0.0)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class AIEvaluationMatch(Base):
    """A single explainable match record produced during evaluation scoring.

    Each record links an expected finding and/or a draft finding and records how
    the match was made (related checklist item, category, or title similarity)
    or that an item was unmatched or extra.
    """

    __tablename__ = "ai_evaluation_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evaluation_match_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    evaluation_result_id: Mapped[str] = mapped_column(
        ForeignKey("ai_evaluation_results.evaluation_result_id"), nullable=False
    )
    expected_finding_id: Mapped[str | None] = mapped_column(String, nullable=True)
    draft_finding_id: Mapped[str | None] = mapped_column(String, nullable=True)
    match_type: Mapped[str] = mapped_column(String, nullable=False)
    match_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    matched_on: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class PlanSheet(Base):
    """A civil plan sheet record in the Brookside Meadows plan set.

    Phase 6 models the plan sheet index rather than parsing real CAD or PDF
    files. Each record carries sheet metadata (number, title, discipline,
    revision, status) and connects to related documents, checklist items, and
    findings. A sheet status is never a final engineering decision; values such
    as referenced_not_included and needs_reviewer_confirmation keep the work
    under human review.
    """

    __tablename__ = "plan_sheets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sheet_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    sheet_number: Mapped[str] = mapped_column(String, nullable=False)
    sheet_title: Mapped[str] = mapped_column(String, nullable=False)
    discipline: Mapped[str] = mapped_column(String, nullable=False)
    revision: Mapped[str] = mapped_column(String, nullable=False)
    revision_date: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str | None] = mapped_column(String, nullable=True)
    sheet_purpose: Mapped[str] = mapped_column(Text, nullable=False)
    related_documents: Mapped[list] = mapped_column(JSON, default=list)
    related_checklist_items: Mapped[list] = mapped_column(JSON, default=list)
    related_findings: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )

    project: Mapped["Project"] = relationship(back_populates="plan_sheets")


class CadMetadata(Base):
    """CAD-aware metadata for a civil feature referenced in the plan set.

    Phase 6 seeds synthetic CAD-aware metadata rather than extracting it from
    real DWG or DXF files. Each record describes a civil feature (basin, pipe,
    road, lot, utility, and so on), the sheet and layer it relates to, and the
    documents, checklist items, or findings it connects to. This is a future
    ready abstraction for CAD-derived metadata, not verified CAD geometry.
    """

    __tablename__ = "cad_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cad_metadata_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    sheet_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_label: Mapped[str] = mapped_column(String, nullable=False)
    layer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    discipline: Mapped[str] = mapped_column(String, nullable=False)
    related_document_id: Mapped[str | None] = mapped_column(String, nullable=True)
    related_checklist_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    related_finding_id: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class PlanReference(Base):
    """A reference linking a document, sheet, or civil feature to another.

    Plan references record where the submitted package points from one place to
    another (for example, a report citing a sheet, or an RFI citing a pipe). The
    consistency_status records whether the reference target was located and
    whether labels agree. It is review-support evidence, never a final decision.
    """

    __tablename__ = "plan_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_reference_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str] = mapped_column(String, nullable=False)
    target_type: Mapped[str] = mapped_column(String, nullable=False)
    target_id: Mapped[str] = mapped_column(String, nullable=False)
    reference_label: Mapped[str] = mapped_column(String, nullable=False)
    reference_context: Mapped[str] = mapped_column(Text, nullable=False)
    consistency_status: Mapped[str] = mapped_column(String, nullable=False)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class PlanConsistencyFinding(Base):
    """A plan-sheet-specific review-support finding.

    These findings are produced by evaluating the seeded plan sheets and plan
    references for missing sheets, missing reference targets, conflicting
    labels, and unclear revisions. Like every finding in the system, each one
    requires human review and never carries final approval or certification
    language.
    """

    __tablename__ = "plan_consistency_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_finding_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    finding_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    related_sheet_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_document_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_checklist_items: Mapped[list] = mapped_column(JSON, default=list)
    related_cad_metadata_ids: Mapped[list] = mapped_column(JSON, default=list)
    recommended_human_action: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class PlanSheetHotspot(Base):
    """A seeded review-support annotation placed over a plan sheet preview.

    Phase 7 adds a reviewer-facing plan sheet viewer. A hotspot is a seeded
    rectangular annotation (percentage coordinates) over a synthetic plan sheet
    preview that points a reviewer at a civil feature, plan reference, or plan
    consistency finding. Hotspots are seeded review-support metadata, not
    extracted CAD geometry or verified plan locations. They never carry final
    approval, certification, or CAD verification language.
    """

    __tablename__ = "plan_sheet_hotspots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hotspot_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    sheet_id: Mapped[str] = mapped_column(
        ForeignKey("plan_sheets.sheet_id"), nullable=False
    )
    hotspot_type: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    x_percent: Mapped[float] = mapped_column(Float, nullable=False)
    y_percent: Mapped[float] = mapped_column(Float, nullable=False)
    width_percent: Mapped[float] = mapped_column(Float, nullable=False)
    height_percent: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    related_plan_reference_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_cad_metadata_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_plan_finding_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_document_ids: Mapped[list] = mapped_column(JSON, default=list)
    related_checklist_item_ids: Mapped[list] = mapped_column(JSON, default=list)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class PlanConsistencyReviewAction(Base):
    """A persisted human review action on a plan consistency finding.

    Phase 7 lets a reviewer record an action on a plan consistency finding:
    needs_follow_up, reviewer_confirmed, not_applicable, or
    needs_more_information. There is intentionally no action called approve, and
    no action approves a plan, certifies compliance, verifies CAD, or validates
    a design. Every action keeps the finding a review-support finding under
    human control.
    """

    __tablename__ = "plan_consistency_review_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_action_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    plan_finding_id: Mapped[str] = mapped_column(
        ForeignKey("plan_consistency_findings.plan_finding_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=False)
    previous_status: Mapped[str] = mapped_column(String, nullable=False)
    new_status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ReviewPacket(Base):
    """A reviewer-facing review-support packet draft for a project.

    Phase 8 assembles documents, checklist items, findings, plan sheets,
    CAD-aware metadata, hotspots, plan consistency findings, human review
    actions, and audit evidence into a structured review-support packet. The
    packet organizes evidence for a human reviewer. It does not approve plans,
    certify compliance, stamp drawings, verify CAD, validate a design, or make
    final engineering decisions.
    """

    __tablename__ = "review_packets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    packet_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    packet_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    generated_from_phase: Mapped[str] = mapped_column(String, nullable=False)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    limitations_note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ReviewPacketSection(Base):
    """A section of a review packet (for example, plan consistency findings)."""

    __tablename__ = "review_packet_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    section_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    packet_id: Mapped[str] = mapped_column(
        ForeignKey("review_packets.packet_id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    section_type: Mapped[str] = mapped_column(String, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ReviewPacketItem(Base):
    """A single item in a review packet section, linked to a source entity."""

    __tablename__ = "review_packet_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    packet_id: Mapped[str] = mapped_column(
        ForeignKey("review_packets.packet_id"), nullable=False
    )
    section_id: Mapped[str] = mapped_column(
        ForeignKey("review_packet_sections.section_id"), nullable=False
    )
    item_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewer_status: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ReviewPacketEvidenceLink(Base):
    """A link from a packet item to a source evidence entity."""

    __tablename__ = "review_packet_evidence_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evidence_link_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    packet_id: Mapped[str] = mapped_column(
        ForeignKey("review_packets.packet_id"), nullable=False
    )
    item_id: Mapped[str] = mapped_column(
        ForeignKey("review_packet_items.item_id"), nullable=False
    )
    evidence_type: Mapped[str] = mapped_column(String, nullable=False)
    evidence_id: Mapped[str] = mapped_column(String, nullable=False)
    relationship: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ReviewPacketReviewerAction(Base):
    """A persisted reviewer action on a review packet item.

    A reviewer may mark an item needs_follow_up, reviewer_checked,
    excluded_from_packet, or needs_more_information. There is no action called
    approve, and no action approves, certifies, verifies, or validates anything.
    """

    __tablename__ = "review_packet_reviewer_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    packet_id: Mapped[str] = mapped_column(
        ForeignKey("review_packets.packet_id"), nullable=False
    )
    item_id: Mapped[str] = mapped_column(
        ForeignKey("review_packet_items.item_id"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=False)
    previous_status: Mapped[str] = mapped_column(String, nullable=False)
    new_status: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class WorkflowItem(Base):
    """An operational workflow board item tracking a review-support item.

    Phase 9 promotes review packet items into a reviewer workflow board so a
    human reviewer can move each item from triage through follow-up to handoff.
    A workflow item tracks where a review-support item sits in the operational
    review workflow. It does not approve plans, certify compliance, stamp
    drawings, verify CAD, validate a design, or make final engineering
    decisions. Every item stays under human control.
    """

    __tablename__ = "workflow_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_item_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    packet_id: Mapped[str | None] = mapped_column(String, nullable=True)
    packet_item_id: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    assigned_role: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_date: Mapped[str | None] = mapped_column(String, nullable=True)
    section_type: Mapped[str] = mapped_column(String, nullable=False)
    evidence_types: Mapped[list] = mapped_column(JSON, default=list)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class WorkflowAction(Base):
    """A persisted reviewer action on a workflow item.

    Each action records a status transition or note a reviewer made while
    working the board. There is no action called approve, and no action
    approves, certifies, verifies, or validates anything.
    """

    __tablename__ = "workflow_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    workflow_item_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_items.workflow_item_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    previous_status: Mapped[str] = mapped_column(String, nullable=False)
    new_status: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class WorkflowFollowUpRequest(Base):
    """A follow-up request tracked against a workflow item.

    A reviewer may request more information or a follow-up from an applicant or
    another reviewer. The request records what was asked and its status. It
    never records a final engineering decision; closing a request without a
    decision is an explicit allowed state.
    """

    __tablename__ = "workflow_follow_up_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    follow_up_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    workflow_item_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_items.workflow_item_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    requested_from: Mapped[str] = mapped_column(String, nullable=False)
    request_reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_information: Mapped[str] = mapped_column(Text, nullable=False)
    target_date: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ResponsePackage(Base):
    """A draft external review response package for a project.

    Phase 10 turns ready-for-handoff workflow items into a structured draft
    response package a human reviewer can prepare for an applicant, design
    engineer, municipal reviewer, or internal review team. The package supports
    drafting external communication. It does not send email, approve plans,
    certify compliance, stamp drawings, verify CAD, validate the design, or make
    final engineering decisions. Every item stays under human review.
    """

    __tablename__ = "response_packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    response_package_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    source_packet_id: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    audience_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    draft_intro: Mapped[str] = mapped_column(Text, nullable=False)
    draft_closing: Mapped[str] = mapped_column(Text, nullable=False)
    limitations_note: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ResponsePackageSection(Base):
    """A section of a response package, grouping items by topic."""

    __tablename__ = "response_package_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    section_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    response_package_id: Mapped[str] = mapped_column(
        ForeignKey("response_packages.response_package_id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    section_type: Mapped[str] = mapped_column(String, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ResponsePackageItem(Base):
    """A single draft response item, traceable to its workflow and packet item."""

    __tablename__ = "response_package_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    response_package_id: Mapped[str] = mapped_column(
        ForeignKey("response_packages.response_package_id"), nullable=False
    )
    section_id: Mapped[str] = mapped_column(
        ForeignKey("response_package_sections.section_id"), nullable=False
    )
    workflow_item_id: Mapped[str | None] = mapped_column(String, nullable=True)
    packet_item_id: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    draft_text: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    assigned_role: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ResponsePackageEvidenceLink(Base):
    """A link from a response item to a source evidence entity."""

    __tablename__ = "response_package_evidence_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evidence_link_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    response_package_id: Mapped[str] = mapped_column(
        ForeignKey("response_packages.response_package_id"), nullable=False
    )
    response_item_id: Mapped[str] = mapped_column(
        ForeignKey("response_package_items.item_id"), nullable=False
    )
    evidence_type: Mapped[str] = mapped_column(String, nullable=False)
    evidence_id: Mapped[str] = mapped_column(String, nullable=False)
    relationship: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ResponsePackageAttachment(Base):
    """A suggested attachment in the response package attachment checklist."""

    __tablename__ = "response_package_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attachment_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    response_package_id: Mapped[str] = mapped_column(
        ForeignKey("response_packages.response_package_id"), nullable=False
    )
    label: Mapped[str] = mapped_column(String, nullable=False)
    attachment_type: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    included: Mapped[bool] = mapped_column(default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class ResponsePackageAction(Base):
    """A persisted reviewer action on a response package or response item.

    There is no action called approve, and no action approves, certifies,
    verifies, or validates anything.
    """

    __tablename__ = "response_package_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    response_package_id: Mapped[str] = mapped_column(
        ForeignKey("response_packages.response_package_id"), nullable=False
    )
    response_item_id: Mapped[str | None] = mapped_column(String, nullable=True)
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    previous_status: Mapped[str] = mapped_column(String, nullable=False)
    new_status: Mapped[str] = mapped_column(String, nullable=False)
    reviewer_note: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class CadFileUpload(Base):
    """A real CAD file (DXF only) registered for review-support intake.

    Intake parses a real DXF file and extracts review-support metadata. It does
    not verify CAD, validate geometry or design, certify compliance, or make
    final engineering decisions. DWG parsing is out of scope for this phase.

    Phase 12 adds browser upload support. A browser-uploaded file is stored under
    a safe generated stored_file_name (never the raw user file name), and the
    original user file name is kept as original_file_name metadata only.
    validation_status records whether the upload passed intake validation. It
    never records an engineering decision.
    """

    __tablename__ = "cad_file_uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cad_file_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    upload_status: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_by: Mapped[str] = mapped_column(String, nullable=False)
    limitations_note: Mapped[str] = mapped_column(Text, nullable=False)
    # Phase 12 browser upload metadata. Nullable so Phase 11 sample-based intake
    # and existing rows keep working without a migration.
    original_file_name: Mapped[str | None] = mapped_column(String, nullable=True)
    stored_file_name: Mapped[str | None] = mapped_column(String, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String, nullable=True)
    upload_source: Mapped[str] = mapped_column(String, default="sample")
    validation_status: Mapped[str | None] = mapped_column(String, nullable=True)
    validation_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    parse_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    parse_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )


class CadParseRun(Base):
    """A single DXF parse run over a CAD file."""

    __tablename__ = "cad_parse_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parse_run_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    cad_file_id: Mapped[str] = mapped_column(
        ForeignKey("cad_file_uploads.cad_file_id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    parser_name: Mapped[str] = mapped_column(String, nullable=False)
    parser_version: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    entity_count: Mapped[int] = mapped_column(Integer, default=0)
    layer_count: Mapped[int] = mapped_column(Integer, default=0)
    block_count: Mapped[int] = mapped_column(Integer, default=0)
    text_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations_note: Mapped[str] = mapped_column(Text, nullable=False)


class CadLayerExtract(Base):
    """A layer extracted from a DXF parse run."""

    __tablename__ = "cad_layer_extracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    layer_extract_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    parse_run_id: Mapped[str] = mapped_column(
        ForeignKey("cad_parse_runs.parse_run_id"), nullable=False
    )
    cad_file_id: Mapped[str] = mapped_column(String, nullable=False)
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    layer_name: Mapped[str] = mapped_column(String, nullable=False)
    entity_count: Mapped[int] = mapped_column(Integer, default=0)
    has_text: Mapped[bool] = mapped_column(default=False)
    has_geometry: Mapped[bool] = mapped_column(default=False)
    review_category: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class CadEntityExtract(Base):
    """An entity extracted from a DXF parse run.

    Bounding values are stored only when available from the source file. They
    are local drawing coordinates and are not treated as georeferenced.
    """

    __tablename__ = "cad_entity_extracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_extract_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    parse_run_id: Mapped[str] = mapped_column(
        ForeignKey("cad_parse_runs.parse_run_id"), nullable=False
    )
    cad_file_id: Mapped[str] = mapped_column(String, nullable=False)
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    layer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    block_name: Mapped[str | None] = mapped_column(String, nullable=True)
    handle: Mapped[str | None] = mapped_column(String, nullable=True)
    text_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    x_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    y_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    x_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    y_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_category: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class CadBlockExtract(Base):
    """A block definition extracted from a DXF parse run."""

    __tablename__ = "cad_block_extracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    block_extract_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    parse_run_id: Mapped[str] = mapped_column(
        ForeignKey("cad_parse_runs.parse_run_id"), nullable=False
    )
    cad_file_id: Mapped[str] = mapped_column(String, nullable=False)
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    block_name: Mapped[str] = mapped_column(String, nullable=False)
    insert_count: Mapped[int] = mapped_column(Integer, default=0)
    layer_names: Mapped[list] = mapped_column(JSON, default=list)
    text_values: Mapped[list] = mapped_column(JSON, default=list)
    review_category: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class CadTextExtract(Base):
    """A text or mtext value extracted from a DXF parse run."""

    __tablename__ = "cad_text_extracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text_extract_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    parse_run_id: Mapped[str] = mapped_column(
        ForeignKey("cad_parse_runs.parse_run_id"), nullable=False
    )
    cad_file_id: Mapped[str] = mapped_column(String, nullable=False)
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    text_value: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    layer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    block_name: Mapped[str | None] = mapped_column(String, nullable=True)
    handle: Mapped[str | None] = mapped_column(String, nullable=True)
    x: Mapped[float | None] = mapped_column(Float, nullable=True)
    y: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_category: Mapped[str] = mapped_column(String, nullable=False)
    reference_type: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class CadReferenceCandidate(Base):
    """A reference candidate detected in extracted text.

    A candidate may be matched against a seeded Phase 6 plan sheet or plan
    reference. confidence_label records review-support confidence, never
    verification.
    """

    __tablename__ = "cad_reference_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    parse_run_id: Mapped[str] = mapped_column(
        ForeignKey("cad_parse_runs.parse_run_id"), nullable=False
    )
    cad_file_id: Mapped[str] = mapped_column(String, nullable=False)
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    reference_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_reference: Mapped[str] = mapped_column(String, nullable=False)
    reference_type: Mapped[str] = mapped_column(String, nullable=False)
    source_entity_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_text_id: Mapped[str | None] = mapped_column(String, nullable=True)
    matched_plan_sheet_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    matched_plan_reference_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    confidence_label: Mapped[str] = mapped_column(String, nullable=False)
    match_reason: Mapped[str] = mapped_column(Text, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)


class CadReviewFinding(Base):
    """A review-support finding raised from DXF metadata.

    Every finding is a draft that needs human review. There is no action called
    approve, and no finding approves, certifies, verifies, or validates anything.
    """

    __tablename__ = "cad_review_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cad_review_finding_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )
    parse_run_id: Mapped[str] = mapped_column(
        ForeignKey("cad_parse_runs.parse_run_id"), nullable=False
    )
    cad_file_id: Mapped[str] = mapped_column(String, nullable=False)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.project_id"), nullable=False
    )
    finding_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    source_reference_candidate_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    source_layer_extract_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    source_text_extract_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    linked_plan_sheet_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    linked_workflow_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    # Phase 12 workflow promotion tracking. promoted_to_workflow guards against
    # duplicate workflow items from the same CAD finding. promoted_workflow_item_id
    # mirrors linked_workflow_item_id for the promotion path.
    promoted_to_workflow: Mapped[bool] = mapped_column(default=False)
    promoted_workflow_item_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow
    )
