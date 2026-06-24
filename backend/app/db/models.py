"""SQLAlchemy models for the Civil Engineer AI backend.

The schema includes the Phase 2 core review entities, the Phase 3 source
evidence entities, the Phase 4 AI review entities, the Phase 5 human review and
evaluation entities, and the Phase 6 plan sheet and CAD-aware review entities.
JSON columns are used for arrays and nested values during the local prototype
phase, with a clean path to normalization later.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


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
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
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
        DateTime, default=datetime.utcnow
    )
