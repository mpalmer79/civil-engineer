"""Aggregate API router for version 1 endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    ai_review,
    audit,
    cad_intake,
    cad_metadata,
    checklist,
    chunks,
    documents,
    evaluation,
    findings,
    hotspots,
    human_review,
    plan_consistency,
    plan_references,
    plan_sheet_hotspots,
    plan_sheets,
    projects,
    response_packages,
    retrieval,
    review_packets,
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
api_router.include_router(workflow.router)
api_router.include_router(response_packages.router)
api_router.include_router(cad_intake.router)
