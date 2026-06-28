"""Aggregate API router for version 1 endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    ai_review,
    audit,
    auth,
    cad_intake,
    cad_metadata,
    checklist,
    checklist_review,
    chunks,
    command_center,
    dashboard,
    diagnostics,
    documents,
    evaluation,
    evidence_retrieval,
    file_storage,
    findings,
    hotspots,
    human_review,
    pdf_evidence,
    pilot,
    plan_consistency,
    plan_references,
    plan_sheet_hotspots,
    plan_sheets,
    projects,
    response_matrix,
    response_packages,
    retrieval,
    reviewer_response_packages,
    review_cycle,
    review_packets,
    traceability,
    workflow,
)

api_router = APIRouter()
api_router.include_router(projects.router)
api_router.include_router(documents.router)
api_router.include_router(checklist.router)
api_router.include_router(findings.router)
api_router.include_router(audit.router)
api_router.include_router(evaluation.router)
api_router.include_router(hotspots.router)
api_router.include_router(chunks.router)
api_router.include_router(retrieval.router)
api_router.include_router(ai_review.router)
api_router.include_router(human_review.router)
api_router.include_router(plan_sheets.router)
api_router.include_router(cad_metadata.router)
api_router.include_router(plan_references.router)
api_router.include_router(plan_consistency.router)
api_router.include_router(plan_sheet_hotspots.router)
api_router.include_router(review_packets.router)
api_router.include_router(traceability.router)
api_router.include_router(workflow.router)
api_router.include_router(response_packages.router)
api_router.include_router(cad_intake.router)
api_router.include_router(review_cycle.router)
api_router.include_router(command_center.router)
api_router.include_router(pdf_evidence.router)
api_router.include_router(evidence_retrieval.router)
api_router.include_router(checklist_review.router)
api_router.include_router(auth.router)
api_router.include_router(file_storage.router)
api_router.include_router(response_matrix.router)
api_router.include_router(reviewer_response_packages.router)
api_router.include_router(dashboard.router)
api_router.include_router(diagnostics.router)
api_router.include_router(pilot.router)
