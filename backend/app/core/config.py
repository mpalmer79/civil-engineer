"""Application configuration for the Civil Engineer AI backend.

Settings are read from environment variables (and an optional .env file), with
sensible local defaults so the backend runs out of the box. The same defaults
work for local development; a Railway deployment overrides them through service
environment variables (see docs/RAILWAY_DEPLOYMENT_GUIDE.md).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings sourced from the environment or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    PROJECT_NAME: str = "Civil Engineer AI Backend"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./civil_engineer_ai.db"

    # Browser origins allowed to call the API. CORS_ORIGINS is a comma separated
    # list for local development. FRONTEND_ORIGIN holds the single deployed
    # frontend origin (for example the Railway frontend URL) and is appended to
    # the allowed list when set, so a deployment only needs to set one variable.
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    FRONTEND_ORIGIN: str = ""

    # Browser DXF upload. Uploaded files are stored under this directory using a
    # safe generated file name (never the raw user file name), one subdirectory
    # per project. On Railway this is demo-local storage on the service file
    # system and is not persistent across redeploys; point CAD_UPLOAD_DIR at a
    # mounted volume for persistence. The size limit is enforced during intake
    # validation. DXF is the only supported file type. MAX_CAD_UPLOAD_BYTES is
    # accepted as an alias for the same limit.
    CAD_UPLOAD_DIR: str = "./cad_uploads"
    CAD_MAX_UPLOAD_BYTES: int = Field(
        default=5_000_000,
        validation_alias=AliasChoices(
            "CAD_MAX_UPLOAD_BYTES", "MAX_CAD_UPLOAD_BYTES"
        ),
    )

    # Production Foundations Sprint 1 real project document upload. Uploaded
    # files are stored under PROJECT_UPLOAD_DIR using a safe generated file name
    # (never the raw user file name), one subdirectory per project. On Railway
    # this is demo-local storage and is not persistent across redeploys; point
    # PROJECT_UPLOAD_DIR at a mounted volume for persistence. The size limit is
    # enforced during upload validation. Only the listed extensions are accepted.
    PROJECT_UPLOAD_DIR: str = "./project_uploads"
    MAX_PROJECT_UPLOAD_BYTES: int = 25_000_000
    ALLOWED_PROJECT_UPLOAD_EXTENSIONS: str = (
        ".pdf,.dxf,.csv,.xlsx,.docx,.png,.jpg,.jpeg"
    )

    @property
    def allowed_project_upload_extensions_set(self) -> set[str]:
        """Return the allowed upload extensions as a normalized lowercase set."""

        return {
            ext.strip().lower()
            for ext in self.ALLOWED_PROJECT_UPLOAD_EXTENSIONS.split(",")
            if ext.strip()
        }

    # Demo mode keeps the deployment self-contained: seeded Brookside Meadows
    # demo data is loaded, no authentication is required, and no external service
    # is called. It is on by default for the portfolio demo.
    DEMO_MODE: bool = True

    # AI provider configuration. The default is the deterministic mock provider
    # so the project runs and tests pass without any paid API key. Live calls
    # are disabled by default and require both a provider key and an explicit
    # opt in. Only the OpenAI live provider is implemented today.
    AI_PROVIDER: str = "mock"
    AI_MODEL: str = "mock-review-v1"
    AI_ENABLE_LIVE_CALLS: bool = False
    OPENAI_API_KEY: str = ""
    PROMPT_VERSION: str = "checklist_review_v1"

    @property
    def cors_origins_list(self) -> list[str]:
        """Return the configured CORS origins as a list.

        Combines the CORS_ORIGINS list with FRONTEND_ORIGIN (when set) and
        removes duplicates while preserving order.
        """

        origins = [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]
        if self.FRONTEND_ORIGIN.strip():
            origins.append(self.FRONTEND_ORIGIN.strip())
        seen: set[str] = set()
        unique: list[str] = []
        for origin in origins:
            if origin not in seen:
                seen.add(origin)
                unique.append(origin)
        return unique


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()
