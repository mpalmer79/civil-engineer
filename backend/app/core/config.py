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

    # Production Foundations Sprint 6 durable file storage. STORAGE_PROVIDER
    # selects the storage backend: "local" stores uploaded files under
    # LOCAL_STORAGE_DIR for development; "s3" uses S3-compatible object storage
    # for deployment so uploads survive redeploys. Object storage credentials are
    # backend-only and are never exposed to the frontend. They are read only when
    # STORAGE_PROVIDER is "s3". LOCAL_STORAGE_DIR defaults to PROJECT_UPLOAD_DIR so
    # existing local uploads keep working.
    STORAGE_PROVIDER: str = "local"
    LOCAL_STORAGE_DIR: str = "./project_uploads"
    OBJECT_STORAGE_BUCKET: str = ""
    OBJECT_STORAGE_ENDPOINT_URL: str = ""
    OBJECT_STORAGE_REGION: str = "us-east-1"
    OBJECT_STORAGE_ACCESS_KEY_ID: str = ""
    OBJECT_STORAGE_SECRET_ACCESS_KEY: str = ""
    OBJECT_STORAGE_FORCE_PATH_STYLE: bool = True
    OBJECT_STORAGE_PUBLIC_BASE_URL: str = ""
    OBJECT_STORAGE_SIGNED_URL_EXPIRE_SECONDS: int = 300

    @property
    def local_storage_dir(self) -> str:
        """Return the local storage directory, defaulting to the upload dir."""

        return self.LOCAL_STORAGE_DIR or self.PROJECT_UPLOAD_DIR

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

    # Production Foundations Sprint 5 local authentication and access control.
    # AUTH_SECRET_KEY signs local access tokens. The default is a clearly marked
    # development-only value; a deployment MUST override it with a strong secret.
    # AUTH_DEMO_MODE keeps the public Brookside Meadows demo and demo reviewer
    # fallback working without a login. AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS
    # requires a signed-in user for real (non-demo) project actions when true.
    # AUTH_ALLOW_PUBLIC_DEMO lets demo_public projects be read without a login.
    AUTH_SECRET_KEY: str = "dev-only-insecure-change-me"
    AUTH_TOKEN_EXPIRE_MINUTES: int = 120
    AUTH_DEMO_MODE: bool = True
    AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS: bool = True
    AUTH_ALLOW_PUBLIC_DEMO: bool = True
    AUTH_MIN_PASSWORD_LENGTH: int = 8
    # Seeded local demo credentials. These are for local development and the
    # portfolio demo only and must be changed or disabled before any real use.
    AUTH_SEED_DEMO_USERS: bool = True
    AUTH_DEMO_REVIEWER_PASSWORD: str = "demo-reviewer-pass"
    AUTH_DEMO_ADMIN_PASSWORD: str = "demo-admin-pass"

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
