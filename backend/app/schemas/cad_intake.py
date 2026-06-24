"""Pydantic schemas for Phase 11 real CAD (DXF) intake and parsing.

Intake parses a real DXF file and extracts review-support metadata: layers,
entities, blocks, text, reference candidates, and review-support findings. It
does not verify CAD, validate geometry or design, certify compliance, or make
final engineering decisions. DXF is the only supported file type in this phase.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CadFileCreate(BaseModel):
    """Request body for registering a CAD file for intake.

    For this phase, intake uses a bundled sample DXF fixture resolved by
    sample_key. Browser file upload is documented as a later enhancement, so the
    client does not pass an arbitrary storage path.
    """

    sample_key: str = "brookside_meadows"
    uploaded_by: str = "reviewer"


class CadFileUploadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cad_file_id: str
    project_id: str
    file_name: str
    file_type: str
    file_size_bytes: int
    storage_path: str
    upload_status: str
    uploaded_by: str
    limitations_note: str
    created_at: datetime


class CadParseRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parse_run_id: str
    cad_file_id: str
    project_id: str
    parser_name: str
    parser_version: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    entity_count: int
    layer_count: int
    block_count: int
    text_count: int
    warning_count: int
    error_message: str | None = None
    limitations_note: str


class CadLayerExtractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    layer_extract_id: str
    parse_run_id: str
    cad_file_id: str
    project_id: str
    layer_name: str
    entity_count: int
    has_text: bool
    has_geometry: bool
    review_category: str
    requires_human_review: bool


class CadEntityExtractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entity_extract_id: str
    parse_run_id: str
    cad_file_id: str
    project_id: str
    entity_type: str
    layer_name: str | None = None
    block_name: str | None = None
    handle: str | None = None
    text_value: str | None = None
    x_min: float | None = None
    y_min: float | None = None
    x_max: float | None = None
    y_max: float | None = None
    review_category: str
    requires_human_review: bool


class CadBlockExtractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    block_extract_id: str
    parse_run_id: str
    cad_file_id: str
    project_id: str
    block_name: str
    insert_count: int
    layer_names: list[str] = Field(default_factory=list)
    text_values: list[str] = Field(default_factory=list)
    review_category: str
    requires_human_review: bool


class CadTextExtractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    text_extract_id: str
    parse_run_id: str
    cad_file_id: str
    project_id: str
    text_value: str
    normalized_text: str
    entity_type: str
    layer_name: str | None = None
    block_name: str | None = None
    handle: str | None = None
    x: float | None = None
    y: float | None = None
    review_category: str
    reference_type: str
    requires_human_review: bool


class CadReferenceCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: str
    parse_run_id: str
    cad_file_id: str
    project_id: str
    reference_text: str
    normalized_reference: str
    reference_type: str
    source_entity_id: str | None = None
    source_text_id: str | None = None
    matched_plan_sheet_id: str | None = None
    matched_plan_reference_id: str | None = None
    confidence_label: str
    match_reason: str
    requires_human_review: bool


class CadReviewFindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cad_review_finding_id: str
    parse_run_id: str
    cad_file_id: str
    project_id: str
    finding_type: str
    title: str
    description: str
    severity: str
    source_reference_candidate_id: str | None = None
    source_layer_extract_id: str | None = None
    source_text_extract_id: str | None = None
    linked_plan_sheet_id: str | None = None
    linked_workflow_item_id: str | None = None
    status: str
    requires_human_review: bool
    created_at: datetime


class CadParseSummary(BaseModel):
    parse_run_id: str
    cad_file_id: str
    project_id: str
    status: str
    entity_count: int
    layer_count: int
    block_count: int
    text_count: int
    warning_count: int
    reference_candidate_count: int
    finding_count: int
    layers_by_category: dict[str, int]
    references_by_type: dict[str, int]
    references_by_confidence: dict[str, int]
    findings_by_type: dict[str, int]
    limitations_note: str


class CadPlanSheetComparisonRow(BaseModel):
    candidate_id: str
    reference_text: str
    normalized_reference: str
    reference_type: str
    matched_plan_sheet_id: str | None = None
    matched_sheet_number: str | None = None
    confidence_label: str
    match_reason: str


class CadPlanSheetComparison(BaseModel):
    parse_run_id: str
    project_id: str
    total_candidates: int
    matched_count: int
    unmatched_count: int
    rows: list[CadPlanSheetComparisonRow] = Field(default_factory=list)
    findings: list[CadReviewFindingRead] = Field(default_factory=list)
    note: str


class CadFileReviewContext(BaseModel):
    cad_file: CadFileUploadRead
    parse_run: CadParseRunRead | None = None
    summary: CadParseSummary | None = None
    layers: list[CadLayerExtractRead] = Field(default_factory=list)
    reference_candidates: list[CadReferenceCandidateRead] = Field(
        default_factory=list
    )
    findings: list[CadReviewFindingRead] = Field(default_factory=list)
    note: str


class CadWorkflowItemsResult(BaseModel):
    created_count: int
    workflow_item_ids: list[str] = Field(default_factory=list)
    note: str
