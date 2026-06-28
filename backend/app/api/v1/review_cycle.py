"""Phase 13 multi-round resubmittal, revision comparison, and response cycle API.

These endpoints manage review cycles, resubmittal packages, applicant responses
and mappings, DXF metadata revision comparison, issue carry-forward, response
resolution, and next-cycle preparation. Revision comparison compares extracted
DXF metadata only. No endpoint verifies CAD, validates design, certifies
compliance, or makes a final engineering decision, and there is no action called
approve.

Read side effects: GET /review-cycles/{id}, /review-cycle-dashboard,
/revision-comparisons/{id}, /revision-comparisons/{id}/changes,
/response-mapping-summary, /carry-forward-summary, /resolution-summary, and
/next-cycle-preparation each write an audit event recording reviewer access. This
is intentional so the decision history shows reviewer access.

Access control: project-scoped routes guard on the path project_id. Routes keyed
by a raw entity id (review cycle, resubmittal, comparison run, applicant response,
resolution record) resolve the owning project first so a raw id cannot bypass
tenant access. The public Brookside Meadows demo project stays readable.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.schemas.review_cycle import (
    ApplicantResponseCreate,
    ApplicantResponseMappingCreate,
    ApplicantResponseMappingRead,
    ApplicantResponseRead,
    CarryForwardResult,
    CarryForwardSummary,
    IssueCarryForwardCreate,
    IssueCarryForwardRead,
    NextCyclePreparationRead,
    ResolutionSummary,
    ResponseMappingSummary,
    ResponseResolutionCreate,
    ResponseResolutionRecordRead,
    ResponseResolutionStatusUpdate,
    ResubmittalPackageCreate,
    ResubmittalPackageDetail,
    ResubmittalPackageRead,
    ResubmittalPackageStatusUpdate,
    RevisionChangeRecordRead,
    RevisionComparisonCreate,
    RevisionComparisonRunRead,
    RevisionComparisonSummary,
    ReviewCycleCreate,
    ReviewCycleDashboard,
    ReviewCycleRead,
    ReviewCycleSummary,
)
from app.services import project_service, review_cycle_service
from app.services.access_control_service import (
    get_optional_user,
    require_project_read,
    require_project_reviewer,
)
from app.services.review_cycle_service import ReviewCycleError

router = APIRouter(tags=["review-cycle"])

User = models.UserAccount | None


def _handle(exc: ReviewCycleError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)


# Raw-id project resolvers. Each returns the owning project_id or None if the
# entity is missing (the service then raises its own 404 for mutations).


def _cycle_pid(db: Session, review_cycle_id: str) -> str | None:
    record = review_cycle_service.get_review_cycle_record(db, review_cycle_id)
    return record.project_id if record is not None else None


def _resub_pid(db: Session, resubmittal_package_id: str) -> str | None:
    record = review_cycle_service.get_resubmittal_package_record(
        db, resubmittal_package_id
    )
    return record.project_id if record is not None else None


def _comparison_pid(db: Session, comparison_run_id: str) -> str | None:
    record = review_cycle_service.get_revision_comparison_run_record(
        db, comparison_run_id
    )
    return record.project_id if record is not None else None


def _applicant_pid(db: Session, applicant_response_id: str) -> str | None:
    record = db.execute(
        select(models.ApplicantResponse).where(
            models.ApplicantResponse.applicant_response_id == applicant_response_id
        )
    ).scalar_one_or_none()
    return record.project_id if record is not None else None


def _resolution_pid(db: Session, resolution_record_id: str) -> str | None:
    record = db.execute(
        select(models.ResponseResolutionRecord).where(
            models.ResponseResolutionRecord.resolution_record_id
            == resolution_record_id
        )
    ).scalar_one_or_none()
    return record.project_id if record is not None else None


def _guard_read(db: Session, project_id: str | None, user: User, missing: str) -> None:
    if project_id is None:
        raise HTTPException(status_code=404, detail=missing)
    require_project_read(db, project_id, user)


def _guard_reviewer_if_found(db: Session, project_id: str | None, user: User) -> None:
    # The downstream service raises its own 404 when the entity is missing, so
    # only enforce access when the owning project resolved.
    if project_id is not None:
        require_project_reviewer(db, project_id, user)


# Review cycle.


@router.post(
    "/projects/{project_id}/review-cycles", response_model=ReviewCycleRead
)
def create_review_cycle(
    project_id: str,
    body: ReviewCycleCreate | None = None,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ReviewCycleRead:
    require_project_reviewer(db, project_id, user)
    payload = body or ReviewCycleCreate()
    try:
        return review_cycle_service.create_review_cycle(
            db,
            project_id=project_id,
            cycle_number=payload.cycle_number,
            cycle_name=payload.cycle_name,
            source_response_package_id=payload.source_response_package_id,
            source_workflow_board_id=payload.source_workflow_board_id,
            summary=payload.summary,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/review-cycles",
    response_model=list[ReviewCycleRead],
)
def list_review_cycles(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ReviewCycleRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return review_cycle_service.list_review_cycles(db, project_id)


@router.get("/review-cycles/{review_cycle_id}", response_model=ReviewCycleRead)
def get_review_cycle(
    review_cycle_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ReviewCycleRead:
    cycle = review_cycle_service.get_review_cycle(db, review_cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Review cycle not found")
    require_project_read(db, cycle.project_id, user)
    return cycle


@router.get(
    "/projects/{project_id}/review-cycle-summary",
    response_model=ReviewCycleSummary,
)
def get_review_cycle_summary(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ReviewCycleSummary:
    require_project_read(db, project_id, user)
    try:
        return ReviewCycleSummary.model_validate(
            review_cycle_service.get_review_cycle_summary(db, project_id)
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/review-cycle-dashboard",
    response_model=ReviewCycleDashboard,
)
def get_review_cycle_dashboard(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ReviewCycleDashboard:
    require_project_read(db, project_id, user)
    try:
        return ReviewCycleDashboard.model_validate(
            review_cycle_service.get_review_cycle_dashboard(db, project_id)
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


# Resubmittal.


@router.post(
    "/projects/{project_id}/resubmittals", response_model=ResubmittalPackageRead
)
def create_resubmittal(
    project_id: str,
    body: ResubmittalPackageCreate,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResubmittalPackageRead:
    require_project_reviewer(db, project_id, user)
    try:
        return review_cycle_service.create_resubmittal_package(
            db,
            project_id=project_id,
            review_cycle_id=body.review_cycle_id,
            package_name=body.package_name,
            submitted_by=body.submitted_by,
            summary=body.summary,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/resubmittals",
    response_model=list[ResubmittalPackageRead],
)
def list_resubmittals(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ResubmittalPackageRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return review_cycle_service.list_resubmittal_packages(db, project_id)


@router.get(
    "/resubmittals/{resubmittal_package_id}",
    response_model=ResubmittalPackageDetail,
)
def get_resubmittal(
    resubmittal_package_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResubmittalPackageDetail:
    _guard_read(
        db,
        _resub_pid(db, resubmittal_package_id),
        user,
        "Resubmittal package not found",
    )
    result = review_cycle_service.get_resubmittal_package(
        db, resubmittal_package_id
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Resubmittal package not found")
    return ResubmittalPackageDetail.model_validate(result)


@router.patch(
    "/resubmittals/{resubmittal_package_id}/status",
    response_model=ResubmittalPackageRead,
)
def update_resubmittal_status(
    resubmittal_package_id: str,
    body: ResubmittalPackageStatusUpdate,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResubmittalPackageRead:
    _guard_reviewer_if_found(db, _resub_pid(db, resubmittal_package_id), user)
    try:
        return review_cycle_service.update_resubmittal_package_status(
            db,
            resubmittal_package_id,
            status=body.status,
            reviewer_note=body.reviewer_note,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.post(
    "/resubmittals/{resubmittal_package_id}/cad-files/{cad_file_id}",
    response_model=ResubmittalPackageDetail,
)
def link_cad_file(
    resubmittal_package_id: str,
    cad_file_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResubmittalPackageDetail:
    _guard_reviewer_if_found(db, _resub_pid(db, resubmittal_package_id), user)
    try:
        review_cycle_service.link_cad_file_to_resubmittal(
            db, resubmittal_package_id, cad_file_id
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc
    result = review_cycle_service.get_resubmittal_package(
        db, resubmittal_package_id
    )
    return ResubmittalPackageDetail.model_validate(result)


@router.post(
    "/resubmittals/{resubmittal_package_id}/applicant-responses",
    response_model=ApplicantResponseRead,
)
def create_applicant_response(
    resubmittal_package_id: str,
    body: ApplicantResponseCreate,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ApplicantResponseRead:
    _guard_reviewer_if_found(db, _resub_pid(db, resubmittal_package_id), user)
    try:
        return review_cycle_service.link_applicant_response_to_resubmittal(
            db,
            resubmittal_package_id,
            response_text=body.response_text,
            response_topic=body.response_topic,
            submitted_by=body.submitted_by,
            target_response_item_id=body.target_response_item_id,
            target_workflow_item_id=body.target_workflow_item_id,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


# Applicant responses and mappings.


@router.get(
    "/projects/{project_id}/applicant-responses",
    response_model=list[ApplicantResponseRead],
)
def list_applicant_responses(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ApplicantResponseRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return review_cycle_service.list_applicant_responses(db, project_id)


@router.post(
    "/applicant-responses/{applicant_response_id}/mappings",
    response_model=ApplicantResponseMappingRead,
)
def create_applicant_response_mapping(
    applicant_response_id: str,
    body: ApplicantResponseMappingCreate,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ApplicantResponseMappingRead:
    _guard_reviewer_if_found(db, _applicant_pid(db, applicant_response_id), user)
    try:
        return review_cycle_service.create_applicant_response_mapping(
            db,
            applicant_response_id,
            response_package_item_id=body.response_package_item_id,
            workflow_item_id=body.workflow_item_id,
            mapping_confidence=body.mapping_confidence,
            mapping_reason=body.mapping_reason,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.post(
    "/review-cycles/{review_cycle_id}/suggest-response-mappings",
    response_model=list[ApplicantResponseMappingRead],
)
def suggest_response_mappings(
    review_cycle_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ApplicantResponseMappingRead]:
    _guard_reviewer_if_found(db, _cycle_pid(db, review_cycle_id), user)
    try:
        return review_cycle_service.auto_suggest_response_mappings(
            db, review_cycle_id
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.get(
    "/review-cycles/{review_cycle_id}/response-mapping-summary",
    response_model=ResponseMappingSummary,
)
def get_response_mapping_summary(
    review_cycle_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponseMappingSummary:
    _guard_read(db, _cycle_pid(db, review_cycle_id), user, "Review cycle not found")
    try:
        return ResponseMappingSummary.model_validate(
            review_cycle_service.get_response_mapping_summary(db, review_cycle_id)
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


# Revision comparison.


@router.post(
    "/review-cycles/{review_cycle_id}/revision-comparisons",
    response_model=RevisionComparisonRunRead,
)
def run_revision_comparison(
    review_cycle_id: str,
    body: RevisionComparisonCreate,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> RevisionComparisonRunRead:
    cycle = review_cycle_service.get_review_cycle_record(db, review_cycle_id)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Review cycle not found")
    require_project_reviewer(db, cycle.project_id, user)
    try:
        return review_cycle_service.run_revision_comparison(
            db,
            project_id=cycle.project_id,
            review_cycle_id=review_cycle_id,
            previous_parse_run_id=body.previous_parse_run_id,
            current_parse_run_id=body.current_parse_run_id,
            resubmittal_package_id=body.resubmittal_package_id,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/revision-comparisons",
    response_model=list[RevisionComparisonRunRead],
)
def list_revision_comparisons(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[RevisionComparisonRunRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return review_cycle_service.list_revision_comparison_runs(db, project_id)


@router.get(
    "/revision-comparisons/{comparison_run_id}",
    response_model=RevisionComparisonRunRead,
)
def get_revision_comparison(
    comparison_run_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> RevisionComparisonRunRead:
    _guard_read(
        db, _comparison_pid(db, comparison_run_id), user, "Comparison run not found"
    )
    run = review_cycle_service.get_revision_comparison_run(db, comparison_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Comparison run not found")
    return run


@router.get(
    "/revision-comparisons/{comparison_run_id}/changes",
    response_model=list[RevisionChangeRecordRead],
)
def list_revision_changes(
    comparison_run_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[RevisionChangeRecordRead]:
    _guard_read(
        db, _comparison_pid(db, comparison_run_id), user, "Comparison run not found"
    )
    return review_cycle_service.list_revision_change_records(db, comparison_run_id)


@router.get(
    "/revision-comparisons/{comparison_run_id}/summary",
    response_model=RevisionComparisonSummary,
)
def get_revision_comparison_summary(
    comparison_run_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> RevisionComparisonSummary:
    _guard_read(
        db, _comparison_pid(db, comparison_run_id), user, "Comparison run not found"
    )
    result = review_cycle_service.summarize_revision_changes(db, comparison_run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Comparison run not found")
    return RevisionComparisonSummary.model_validate(result)


# Carry-forward.


@router.post(
    "/review-cycles/{review_cycle_id}/carry-forward",
    response_model=CarryForwardResult,
)
def carry_forward(
    review_cycle_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CarryForwardResult:
    _guard_reviewer_if_found(db, _cycle_pid(db, review_cycle_id), user)
    try:
        return CarryForwardResult.model_validate(
            review_cycle_service.carry_forward_unresolved_items(db, review_cycle_id)
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.post(
    "/review-cycles/{review_cycle_id}/carry-forward-items",
    response_model=IssueCarryForwardRead,
)
def create_carry_forward_item(
    review_cycle_id: str,
    body: IssueCarryForwardCreate,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> IssueCarryForwardRead:
    _guard_reviewer_if_found(db, _cycle_pid(db, review_cycle_id), user)
    try:
        return review_cycle_service.create_issue_carry_forward(
            db,
            review_cycle_id,
            source_workflow_item_id=body.source_workflow_item_id,
            source_response_item_id=body.source_response_item_id,
            source_cad_finding_id=body.source_cad_finding_id,
            source_revision_change_id=body.source_revision_change_id,
            title=body.title,
            reason=body.reason,
            reviewer_name=body.reviewer_name,
            reviewer_note=body.reviewer_note,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/carry-forwards",
    response_model=list[IssueCarryForwardRead],
)
def list_carry_forwards(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[IssueCarryForwardRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return review_cycle_service.list_issue_carry_forwards(db, project_id)


@router.get(
    "/review-cycles/{review_cycle_id}/carry-forward-summary",
    response_model=CarryForwardSummary,
)
def get_carry_forward_summary(
    review_cycle_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> CarryForwardSummary:
    _guard_read(db, _cycle_pid(db, review_cycle_id), user, "Review cycle not found")
    try:
        return CarryForwardSummary.model_validate(
            review_cycle_service.get_carry_forward_summary(db, review_cycle_id)
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


# Resolution.


@router.post(
    "/review-cycles/{review_cycle_id}/resolution-records",
    response_model=ResponseResolutionRecordRead,
)
def create_resolution_record(
    review_cycle_id: str,
    body: ResponseResolutionCreate,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponseResolutionRecordRead:
    _guard_reviewer_if_found(db, _cycle_pid(db, review_cycle_id), user)
    try:
        return review_cycle_service.create_response_resolution_record(
            db,
            review_cycle_id,
            response_package_item_id=body.response_package_item_id,
            workflow_item_id=body.workflow_item_id,
            applicant_response_id=body.applicant_response_id,
            revision_change_record_id=body.revision_change_record_id,
            status=body.status,
            reviewer_note=body.reviewer_note,
            reviewer_name=body.reviewer_name,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.patch(
    "/resolution-records/{resolution_record_id}/status",
    response_model=ResponseResolutionRecordRead,
)
def update_resolution_status(
    resolution_record_id: str,
    body: ResponseResolutionStatusUpdate,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResponseResolutionRecordRead:
    _guard_reviewer_if_found(db, _resolution_pid(db, resolution_record_id), user)
    try:
        return review_cycle_service.update_response_resolution_status(
            db,
            resolution_record_id,
            status=body.status,
            reviewer_note=body.reviewer_note,
            reviewer_name=body.reviewer_name,
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.get(
    "/projects/{project_id}/resolution-records",
    response_model=list[ResponseResolutionRecordRead],
)
def list_resolution_records(
    project_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[ResponseResolutionRecordRead]:
    if project_service.get_project(db, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    require_project_read(db, project_id, user)
    return review_cycle_service.list_response_resolution_records(db, project_id)


@router.get(
    "/review-cycles/{review_cycle_id}/resolution-summary",
    response_model=ResolutionSummary,
)
def get_resolution_summary(
    review_cycle_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ResolutionSummary:
    _guard_read(db, _cycle_pid(db, review_cycle_id), user, "Review cycle not found")
    try:
        return ResolutionSummary.model_validate(
            review_cycle_service.get_resolution_summary(db, review_cycle_id)
        )
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


# Next cycle.


@router.post(
    "/review-cycles/{review_cycle_id}/prepare-next-cycle",
    response_model=NextCyclePreparationRead,
)
def prepare_next_cycle(
    review_cycle_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> NextCyclePreparationRead:
    _guard_reviewer_if_found(db, _cycle_pid(db, review_cycle_id), user)
    try:
        return review_cycle_service.prepare_next_cycle(db, review_cycle_id)
    except ReviewCycleError as exc:
        raise _handle(exc) from exc


@router.get(
    "/review-cycles/{review_cycle_id}/next-cycle-preparation",
    response_model=NextCyclePreparationRead,
)
def get_next_cycle_preparation(
    review_cycle_id: str,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> NextCyclePreparationRead:
    _guard_read(db, _cycle_pid(db, review_cycle_id), user, "Review cycle not found")
    try:
        prep = review_cycle_service.get_next_cycle_preparation(db, review_cycle_id)
    except ReviewCycleError as exc:
        raise _handle(exc) from exc
    if prep is None:
        raise HTTPException(
            status_code=404, detail="Next cycle preparation not found"
        )
    return prep
