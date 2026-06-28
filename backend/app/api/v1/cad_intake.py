"""Real CAD (DXF) intake API routes.

These endpoints register a DXF file (from a bundled sample or a browser upload),
parse it, read the extracted review-support metadata, reference candidates, and
findings, and promote selected CAD findings into the workflow board. Parsing
extracts metadata from a real DXF file. No endpoint verifies CAD, validates
geometry or design, certifies compliance, or makes a final engineering decision,
and there is no action called approve. DXF is the only supported file type; DWG
is out of scope.

Read side effects: GET /cad-parse-runs/{id}/summary, /layers, /text,
GET /cad-files/{id}/review-context, GET /projects/{id}/cad-parse-queue,
GET /projects/{id}/cad-intake/dashboard, and
GET /projects/{id}/cad-review-findings/unpromoted each write an audit event
recording the access. This is intentional so the decision history shows reviewer
access.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.cad_intake import (
    CadBlockExtractRead,
    CadEntityExtractRead,
    CadFileCreate,
    CadFileReviewContext,
    CadFileUploadRead,
    CadFindingPromotionRequest,
    CadFindingPromotionResponse,
    CadIntakeDashboard,
    CadLayerExtractRead,
    CadParseQueueItem,
    CadParseRunRead,
    CadParseSummary,
    CadPlanSheetComparison,
    CadReferenceCandidateRead,
    CadReviewFindingRead,
    CadSelectedPromotionRequest,
    CadSelectedPromotionResponse,
    CadTextExtractRead,
    CadUploadLimits,
    CadUploadResponse,
    CadWorkflowItemsResult,
)
from app.services import cad_intake_service, project_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
    require_project_reviewer,
)
from app.services.cad_intake_service import CadIntakeError

router = APIRouter(tags=["cad-intake"])

User = models.UserAccount | None


def _guard_parse_run_read(db: Session, parse_run_id: str, user: User) -> None:
    """404 if the parse run is missing, otherwise require read access."""

    run = cad_intake_service.get_cad_parse_run(db, parse_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Parse run not found")
    require_project_read(db, run.project_id, user)


def _guard_cad_file_reviewer(db: Session, cad_file_id: str, user: User) -> None:
    """Require reviewer access for an existing CAD file; service 404s if missing."""

    cad_file = cad_intake_service.get_cad_file(db, cad_file_id)
    if cad_file is not None:
        require_project_reviewer(db, cad_file.project_id, user)


@router.get("/cad-upload-limits", response_model=CadUploadLimits)
def get_cad_upload_limits() -> CadUploadLimits:
    # Static upload-policy information; not project-scoped data.
    return CadUploadLimits.model_validate(
        cad_intake_service.get_cad_upload_limits()
    )


@router.post(
    "/projects/{project_id}/cad-files/upload",
    response_model=CadUploadResponse,
)
async def upload_cad_file(
    project_id: str,
    file: UploadFile = File(...),
    uploaded_by: str = Form("reviewer"),
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CadUploadResponse:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_reviewer(db, project_id, user)
    content_bytes = await file.read()
    try:
        cad_file = cad_intake_service.create_cad_file_from_upload(
            db,
            project_id=project_id,
            original_file_name=file.filename,
            content_type=file.content_type,
            content_bytes=content_bytes,
            uploaded_by=uploaded_by,
        )
    except CadIntakeError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return CadUploadResponse(
        cad_file=CadFileUploadRead.model_validate(cad_file),
        validation_status=cad_file.validation_status or "accepted",
        validation_message=cad_file.validation_message or "",
        next_action="request_parse",
        note=(
            "DXF stored for review-support parsing only. Upload does not verify "
            "CAD, validate design, approve plans, or certify compliance. Request "
            "parse to extract review-support metadata."
        ),
    )


@router.post(
    "/projects/{project_id}/cad-files",
    response_model=CadFileUploadRead,
)
def create_cad_file(
    project_id: str,
    body: CadFileCreate,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CadFileUploadRead:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_reviewer(db, project_id, user)
    try:
        cad_file = cad_intake_service.create_cad_file_from_sample(
            db,
            project_id=project_id,
            sample_key=body.sample_key,
            uploaded_by=body.uploaded_by,
        )
    except CadIntakeError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return cad_file


@router.post("/cad-files/{cad_file_id}/parse", response_model=CadParseRunRead)
def parse_cad_file(
    cad_file_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CadParseRunRead:
    _guard_cad_file_reviewer(db, cad_file_id, user)
    try:
        run = cad_intake_service.parse_dxf_file(db, cad_file_id)
    except CadIntakeError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return run


@router.get(
    "/projects/{project_id}/cad-files",
    response_model=list[CadFileUploadRead],
)
def list_cad_files(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[CadFileUploadRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return cad_intake_service.list_cad_files(db, project_id)


@router.get(
    "/projects/{project_id}/cad-parse-runs",
    response_model=list[CadParseRunRead],
)
def list_cad_parse_runs(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[CadParseRunRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return cad_intake_service.list_cad_parse_runs(db, project_id)


@router.get("/cad-parse-runs/{parse_run_id}", response_model=CadParseRunRead)
def get_cad_parse_run(
    parse_run_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CadParseRunRead:
    run = cad_intake_service.get_cad_parse_run(db, parse_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Parse run not found")
    require_project_read(db, run.project_id, user)
    return run


@router.get(
    "/cad-parse-runs/{parse_run_id}/summary",
    response_model=CadParseSummary,
)
def get_cad_parse_summary(
    parse_run_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CadParseSummary:
    _guard_parse_run_read(db, parse_run_id, user)
    result = cad_intake_service.get_cad_parse_summary(db, parse_run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Parse run not found")
    return CadParseSummary.model_validate(result)


@router.get(
    "/cad-parse-runs/{parse_run_id}/layers",
    response_model=list[CadLayerExtractRead],
)
def list_cad_layers(
    parse_run_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[CadLayerExtractRead]:
    _guard_parse_run_read(db, parse_run_id, user)
    return cad_intake_service.list_cad_layers(db, parse_run_id)


@router.get(
    "/cad-parse-runs/{parse_run_id}/entities",
    response_model=list[CadEntityExtractRead],
)
def list_cad_entities(
    parse_run_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[CadEntityExtractRead]:
    _guard_parse_run_read(db, parse_run_id, user)
    return cad_intake_service.list_cad_entities(db, parse_run_id)


@router.get(
    "/cad-parse-runs/{parse_run_id}/blocks",
    response_model=list[CadBlockExtractRead],
)
def list_cad_blocks(
    parse_run_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[CadBlockExtractRead]:
    _guard_parse_run_read(db, parse_run_id, user)
    return cad_intake_service.list_cad_blocks(db, parse_run_id)


@router.get(
    "/cad-parse-runs/{parse_run_id}/text",
    response_model=list[CadTextExtractRead],
)
def list_cad_text(
    parse_run_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[CadTextExtractRead]:
    _guard_parse_run_read(db, parse_run_id, user)
    return cad_intake_service.list_cad_text(db, parse_run_id)


@router.get(
    "/cad-parse-runs/{parse_run_id}/reference-candidates",
    response_model=list[CadReferenceCandidateRead],
)
def list_cad_reference_candidates(
    parse_run_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[CadReferenceCandidateRead]:
    _guard_parse_run_read(db, parse_run_id, user)
    return cad_intake_service.list_cad_reference_candidates(db, parse_run_id)


@router.post(
    "/cad-parse-runs/{parse_run_id}/compare-plan-sheets",
    response_model=CadPlanSheetComparison,
)
def compare_plan_sheets(
    parse_run_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CadPlanSheetComparison:
    run = cad_intake_service.get_cad_parse_run(db, parse_run_id)
    if run is not None:
        require_project_reviewer(db, run.project_id, user)
    result = cad_intake_service.compare_cad_references_to_plan_sheets(
        db, parse_run_id
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Parse run not found")
    return CadPlanSheetComparison.model_validate(result)


@router.get(
    "/projects/{project_id}/cad-review-findings",
    response_model=list[CadReviewFindingRead],
)
def list_cad_review_findings(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[CadReviewFindingRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return cad_intake_service.list_cad_review_findings(db, project_id)


@router.post(
    "/projects/{project_id}/workflow-items/from-cad-findings",
    response_model=CadWorkflowItemsResult,
)
def create_workflow_items_from_cad_findings(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CadWorkflowItemsResult:
    require_project_reviewer(db, project_id, user)
    try:
        result = cad_intake_service.create_workflow_items_from_cad_findings(
            db, project_id
        )
    except CadIntakeError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return CadWorkflowItemsResult.model_validate(result)


@router.get(
    "/cad-files/{cad_file_id}/review-context",
    response_model=CadFileReviewContext,
)
def get_cad_file_review_context(
    cad_file_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CadFileReviewContext:
    cad_file = cad_intake_service.get_cad_file(db, cad_file_id)
    if cad_file is None:
        raise HTTPException(status_code=404, detail="CAD file not found")
    require_project_read(db, cad_file.project_id, user)
    result = cad_intake_service.get_cad_file_review_context(db, cad_file_id)
    if result is None:
        raise HTTPException(status_code=404, detail="CAD file not found")
    return CadFileReviewContext.model_validate(result)


@router.post(
    "/cad-files/{cad_file_id}/request-parse",
    response_model=CadParseRunRead,
)
def request_cad_parse(
    cad_file_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CadParseRunRead:
    _guard_cad_file_reviewer(db, cad_file_id, user)
    try:
        run = cad_intake_service.request_cad_parse(db, cad_file_id)
    except CadIntakeError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return run


@router.get(
    "/projects/{project_id}/cad-parse-queue",
    response_model=list[CadParseQueueItem],
)
def get_cad_parse_queue(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[CadParseQueueItem]:
    require_project_read(db, project_id, user)
    try:
        rows = cad_intake_service.get_cad_parse_queue(db, project_id)
    except CadIntakeError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return [CadParseQueueItem.model_validate(row) for row in rows]


@router.get(
    "/projects/{project_id}/cad-intake/dashboard",
    response_model=CadIntakeDashboard,
)
def get_cad_intake_dashboard(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CadIntakeDashboard:
    require_project_read(db, project_id, user)
    try:
        result = cad_intake_service.get_cad_intake_dashboard(db, project_id)
    except CadIntakeError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return CadIntakeDashboard.model_validate(result)


@router.get(
    "/projects/{project_id}/cad-review-findings/unpromoted",
    response_model=list[CadReviewFindingRead],
)
def list_unpromoted_cad_findings(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[CadReviewFindingRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return cad_intake_service.list_unpromoted_cad_findings(db, project_id)


@router.post(
    "/cad-review-findings/{cad_review_finding_id}/promote-to-workflow",
    response_model=CadFindingPromotionResponse,
)
def promote_cad_finding_to_workflow(
    cad_review_finding_id: str,
    body: CadFindingPromotionRequest | None = None,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CadFindingPromotionResponse:
    finding = db.execute(
        select(models.CadReviewFinding).where(
            models.CadReviewFinding.cad_review_finding_id == cad_review_finding_id
        )
    ).scalar_one_or_none()
    if finding is not None:
        require_project_reviewer(db, finding.project_id, user)
    payload = body or CadFindingPromotionRequest()
    try:
        result = cad_intake_service.promote_cad_finding_to_workflow(
            db,
            cad_review_finding_id,
            reviewer_name=payload.reviewer_name,
            reviewer_note=payload.reviewer_note,
        )
    except CadIntakeError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return CadFindingPromotionResponse.model_validate(result)


@router.post(
    "/projects/{project_id}/cad-review-findings/promote-selected",
    response_model=CadSelectedPromotionResponse,
)
def promote_selected_cad_findings(
    project_id: str,
    body: CadSelectedPromotionRequest,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CadSelectedPromotionResponse:
    require_project_reviewer(db, project_id, user)
    try:
        result = cad_intake_service.promote_selected_cad_findings_to_workflow(
            db,
            project_id,
            body.cad_review_finding_ids,
            reviewer_name=body.reviewer_name,
            reviewer_note=body.reviewer_note,
        )
    except CadIntakeError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.message
        ) from exc
    return CadSelectedPromotionResponse.model_validate(result)
