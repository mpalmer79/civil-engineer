"""CAD intake domain: browser DXF uploads, parse runs, and the extracted
layer, entity, block, text, reference-candidate, and review-support finding
records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.shared import _utcnow

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


# Phase 13: multi-round resubmittal, revision comparison, and applicant response
# cycle. These models track multiple review rounds for a project. They organize
# review-support evidence across rounds and never approve plans, certify
# compliance, verify CAD, validate design, or make final engineering decisions.
# Revision comparison compares extracted DXF metadata only.
