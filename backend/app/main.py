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
from app.db.seed import seed_database
from app.db.seed_evidence import seed_evidence
from app.db.seed_plansheets import seed_plansheets

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
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Review-support API for stormwater and land development review. "
        "Phase 6 adds a plan sheet and CAD-aware review foundation: a seeded "
        "plan sheet index, CAD-aware feature metadata, plan references, missing "
        "sheet detection, and plan consistency findings that require human "
        "review. The CAD-aware metadata is seeded, not extracted from real CAD "
        "files. The mock AI provider remains the default and no live AI calls, "
        "embeddings, vector retrieval, or CAD parsing are included."
    ),
    version="0.6.0",
    lifespan=lifespan,
)

# CORS is configured for the local Next.js dev server only. Tighten this with a
# real allowlist before any non-local deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Liveness and identity check for the backend."""

    return {
        "status": "ok",
        "service": "Civil Engineer AI Backend",
        "phase": settings.PHASE,
    }


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
