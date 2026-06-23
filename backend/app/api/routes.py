"""Aggregate API router for version 1 endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    audit,
    checklist,
    documents,
    evaluation,
    findings,
    hotspots,
    projects,
)

api_router = APIRouter()
api_router.include_router(projects.router)
api_router.include_router(documents.router)
api_router.include_router(checklist.router)
api_router.include_router(findings.router)
api_router.include_router(audit.router)
api_router.include_router(evaluation.router)
api_router.include_router(hotspots.router)
