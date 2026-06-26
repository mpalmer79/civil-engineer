"""FastAPI application entry point for the Civil Engineer AI backend.

Civil Engineer AI is a review-support and evidence-organization system. It does
not approve plans, certify compliance, stamp drawings, or replace a licensed
Professional Engineer. The backend serves seeded Brookside Meadows review data
through a versioned read API.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import get_settings
from app.db.database import SessionLocal, init_db
from app.db.seed import PROJECT_ID, seed_database
from app.db.seed_evidence import seed_evidence
from app.db.seed_plansheets import seed_plansheets
from app.services import (
    cad_intake_service,
    command_center_service,
    real_intake_service,
    response_package_service,
    review_cycle_service,
    review_packet_service,
    workflow_service,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create tables and load the seed fixture if the database is empty."""

    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
        seed_evidence(db)
        seed_plansheets(db)
        # Generate a review-support packet draft once so the Phase 8 read
        # endpoints and frontend have data without a manual generate call.
        review_packet_service.ensure_packet(db, PROJECT_ID)
        # Generate the reviewer workflow board once so the Phase 9 read
        # endpoints and frontend have data without a manual generate call.
        workflow_service.ensure_workflow_board(db, PROJECT_ID)
        # Generate the draft external response package once so the Phase 10 read
        # endpoints and frontend have data without a manual generate call.
        response_package_service.ensure_response_package(db, PROJECT_ID)
        # Register and parse the sample DXF once so the Phase 11 CAD intake read
        # endpoints and frontend have data without a manual upload or parse call.
        cad_intake_service.ensure_cad_intake(db, PROJECT_ID)
        # Create the initial review cycle once so the Phase 13 read endpoints and
        # frontend have a current cycle without a manual create call.
        review_cycle_service.ensure_review_cycle(db, PROJECT_ID)
        # Generate the initial command center snapshot once so the Phase 14
        # dashboard read endpoints and frontend have data without a manual call.
        command_center_service.ensure_command_center(db, PROJECT_ID)
        # Create the Sprint 1 demo reviewer identity so real intake actions
        # (project creation, document registration, reviewer findings) carry
        # attribution. Real authentication will replace this placeholder.
        real_intake_service.ensure_demo_actor(db)
        db.commit()
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Review-support API for stormwater and land development review. Civil "
        "Engineer AI organizes review-support evidence for a human reviewer: "
        "browser DXF upload and metadata parsing, CAD intake, plan sheet review, "
        "findings and evidence traceability, review packets, a workflow board, "
        "draft response packages, resubmittal and DXF metadata revision "
        "comparison, and a reviewer command center that aggregates the whole "
        "review state. It does not approve plans, certify compliance, verify "
        "CAD, validate design, declare a project safe, or close or resolve "
        "issues, and there is no action called approve. DXF is the only "
        "supported file type; DWG, Autodesk, OCR, and GIS are out of scope. The "
        "mock AI provider is the default and no live AI calls are included."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS allows the configured local dev origins plus the deployed frontend origin
# (FRONTEND_ORIGIN). Set FRONTEND_ORIGIN to the deployed frontend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str | bool]:
    """Liveness and identity check for the backend."""

    return {
        "status": "ok",
        "service": "Civil Engineer AI Backend",
        "version": settings.APP_VERSION,
        "demo_mode": settings.DEMO_MODE,
    }


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
