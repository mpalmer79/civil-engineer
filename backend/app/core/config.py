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

    # Deployment mode. "development" and "pilot" allow a local SQLite database so
    # the prototype and tests run with no external service. "production" requires
    # a Postgres DATABASE_URL: production SaaS data must not live on ephemeral
    # SQLite. The strict check is enforced at startup only when APP_ENV is
    # "production", so local development, tests, and preview builds are never
    # blocked. See docs/PRODUCTION_DATABASE.md.
    APP_ENV: str = "development"

    # Database connection string. SQLite is the default for local development and
    # tests. For production SaaS a Postgres URL is required (for example a Railway
    # Postgres plugin URL). Railway and some providers hand out a legacy
    # "postgres://" scheme; it is normalized to a SQLAlchemy driver URL by
    # app.db.database. No secret in this value is ever logged or returned by the
    # diagnostics or readiness APIs.
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

    # Identifier of the seeded reference project that is marked as the public
    # demo at startup. The default matches the seeded Brookside Meadows fixture
    # (app.db.seeds), so behavior is unchanged unless a deployment overrides it.
    PUBLIC_DEMO_PROJECT_ID: str = "proj_brookside_meadows"

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

    # Production Phase 4B/4C auth lifecycle and team invitations. Reset and
    # invitation tokens are stored only as a one-way hash; these set their
    # validity windows. AUTH_EXPOSE_DEV_TOKENS lets non-production environments
    # return the plaintext reset/invite token in the API response so local
    # development and tests can complete the flow without an email provider. It is
    # forced off in production regardless of this value (see expose_dev_tokens).
    AUTH_PASSWORD_RESET_EXPIRE_MINUTES: int = 60
    AUTH_INVITATION_EXPIRE_DAYS: int = 14
    AUTH_EXPOSE_DEV_TOKENS: bool = True

    # Email provider (Production Phase 4D). The default "noop" mailer logs a
    # redacted delivery record and sends nothing, which keeps local development
    # and tests free of any email service. Set EMAIL_PROVIDER=smtp and the
    # EMAIL_SMTP_* settings to deliver real email through an SMTP server. No SMTP
    # credential is read while the provider is "noop", and no credential is ever
    # logged. EMAIL_FROM is the envelope sender. APP_PUBLIC_BASE_URL is the public
    # frontend origin used to build reset and invitation links in emails.
    EMAIL_PROVIDER: str = "noop"
    EMAIL_FROM: str = "no-reply@example.com"
    EMAIL_SMTP_HOST: str = ""
    EMAIL_SMTP_PORT: int = 587
    EMAIL_SMTP_USERNAME: str = ""
    EMAIL_SMTP_PASSWORD: str = ""
    EMAIL_SMTP_USE_TLS: bool = True
    APP_PUBLIC_BASE_URL: str = "http://localhost:3000"

    # Billing and Stripe (Production Phase 4D). Minimal checkout for the
    # professional plan and signature-verified webhooks are wired, but only become
    # active when the Stripe settings are configured. Billing is considered
    # active only when STRIPE_SECRET_KEY is set (see billing_enabled). Checkout is
    # available only when the checkout settings are all set (see
    # stripe_checkout_configured), and webhooks are verified only when
    # STRIPE_WEBHOOK_SECRET is set. These are backend-only and are never exposed
    # to the frontend. No real payment is processed while STRIPE_SECRET_KEY is
    # unset. STRIPE_TEST_MODE is descriptive: keep it true unless live keys are
    # configured.
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_PROFESSIONAL: str = ""
    STRIPE_SUCCESS_URL: str = ""
    STRIPE_CANCEL_URL: str = ""
    STRIPE_TEST_MODE: bool = True

    # Usage enforcement (Production Phase 4D). Usage limits are advisory by
    # default so local development, tests, and existing flows are never blocked.
    # Set USAGE_ENFORCEMENT_ENABLED=true to hard-enforce the selected low-risk
    # categories (project creation, document registration, review packet
    # generation) for real organizations. The public Brookside demo and the demo
    # organization are never enforced. See docs/BILLING_AND_USAGE.md.
    USAGE_ENFORCEMENT_ENABLED: bool = False

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
    def app_env(self) -> str:
        """Return the normalized deployment mode (lowercase, trimmed)."""

        return (self.APP_ENV or "development").strip().lower()

    @property
    def is_production(self) -> bool:
        """Return True when running in strict production mode."""

        return self.app_env == "production"

    @property
    def billing_enabled(self) -> bool:
        """Return True only when a Stripe secret key is configured.

        Billing is deferred in this phase, so this is False by default. The
        billing UI and API report an honest inactive state until a real Stripe
        secret key is set. No real payment is processed while this is False.
        """

        return bool(self.STRIPE_SECRET_KEY.strip())

    @property
    def email_configured(self) -> bool:
        """Return True when a real email provider is configured to send.

        Only the SMTP provider is implemented. It requires a host; credentials
        are optional for unauthenticated relays. The noop provider is never
        considered configured to send.
        """

        provider = (self.EMAIL_PROVIDER or "noop").strip().lower()
        if provider == "smtp":
            return bool(self.EMAIL_SMTP_HOST.strip())
        return False

    @property
    def stripe_checkout_configured(self) -> bool:
        """Return True when Stripe checkout can be created.

        Requires the secret key, the professional price id, and both redirect
        URLs. When any is missing, checkout reports an honest unavailable state.
        """

        return all(
            value.strip()
            for value in (
                self.STRIPE_SECRET_KEY,
                self.STRIPE_PRICE_PROFESSIONAL,
                self.STRIPE_SUCCESS_URL,
                self.STRIPE_CANCEL_URL,
            )
        )

    @property
    def stripe_webhook_configured(self) -> bool:
        """Return True when webhook signatures can be verified."""

        return bool(self.STRIPE_SECRET_KEY.strip() and self.STRIPE_WEBHOOK_SECRET.strip())

    @property
    def billing_mode(self) -> str:
        """Return the billing mode: inactive, test, or live. No secret leaks."""

        if not self.billing_enabled:
            return "inactive"
        return "test" if self.STRIPE_TEST_MODE else "live"

    @property
    def public_base_url(self) -> str:
        """Return the public frontend base URL without a trailing slash."""

        return (self.APP_PUBLIC_BASE_URL or "http://localhost:3000").rstrip("/")

    @property
    def expose_dev_tokens(self) -> bool:
        """Return True when plaintext reset/invite tokens may be returned.

        Allowed only outside strict production mode and only when
        AUTH_EXPOSE_DEV_TOKENS is on, so local development and tests can complete
        the reset/invite flow without an email provider. Production never exposes
        a token in an API response.
        """

        return self.AUTH_EXPOSE_DEV_TOKENS and not self.is_production

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
