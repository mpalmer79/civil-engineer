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
from app.core.logging import log_event
from app.db.database import SessionLocal, init_db
from app.db.seed import PROJECT_ID, seed_database
from app.db.seed_evidence import seed_evidence
from app.db.seed_plansheets import seed_plansheets
from app.services import (
    access_control_service,
    cad_intake_service,
    checklist_review_service,
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
        # Seed the Sprint 4 starter stormwater rule pack so the rule pack and
        # checklist read endpoints and frontend have a reusable review-support
        # template without a manual create call. It is a starter template, not a
        # legal ordinance.
        checklist_review_service.ensure_starter_rule_pack(db)
        # Seed the Sprint 5 demo organization, demo users, memberships, and demo
        # project access, and mark Brookside Meadows as a public demo so it stays
        # readable without a login. Seeded passwords are local demo only.
        access_control_service.ensure_auth_seed(db)
        db.commit()
    finally:
        db.close()
    # Log a safe startup configuration summary. The log helper redacts secrets,
    # paths, and the database URL, so this only records operational status:
    # selected storage provider, auth/demo flags, and database kind. No secret
    # value, URL, credential, or raw path is ever logged.
    _log_startup_configuration()
    yield


def _log_startup_configuration() -> None:
    """Log selected operational configuration without any secrets."""

    database_kind = (
        "sqlite"
        if settings.DATABASE_URL.strip().lower().startswith("sqlite")
        else "external"
    )
    object_storage_configured = (
        bool(settings.OBJECT_STORAGE_BUCKET)
        if (settings.STORAGE_PROVIDER or "local").lower() == "s3"
        else False
    )
    log_event(
        "startup_configuration",
        service=settings.PROJECT_NAME,
        version=settings.APP_VERSION,
        api_prefix=settings.API_V1_PREFIX,
        database_kind=database_kind,
        storage_provider=(settings.STORAGE_PROVIDER or "local").lower(),
        object_storage_configured=object_storage_configured,
        auth_demo_mode=settings.AUTH_DEMO_MODE,
        auth_require_login_for_real_projects=(
            settings.AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS
        ),
        allow_public_demo=settings.AUTH_ALLOW_PUBLIC_DEMO,
        demo_mode=settings.DEMO_MODE,
    )


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
