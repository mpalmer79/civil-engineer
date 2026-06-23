"""Application configuration for the Civil Engineer AI backend.

Settings are read from environment variables, with sensible local defaults so
the backend runs out of the box for Phase 2 development.
"""

from __future__ import annotations

import os
from functools import lru_cache


class Settings:
    """Runtime settings sourced from the environment.

    A small hand rolled settings object keeps Phase 2 dependency light. It can
    be swapped for pydantic-settings BaseSettings later without changing the
    call sites.
    """

    PROJECT_NAME: str = "Civil Engineer AI Backend"
    PHASE: str = "2"
    API_V1_PREFIX: str = "/api/v1"

    def __init__(self) -> None:
        self.DATABASE_URL: str = os.getenv(
            "DATABASE_URL", "sqlite:///./civil_engineer_ai.db"
        )
        raw_origins = os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
        )
        self.CORS_ORIGINS: list[str] = [
            origin.strip() for origin in raw_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()
