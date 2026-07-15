"""Database engine, session factory, and declarative base.

SQLite is the default for local development and tests so the prototype runs with
no external service. Production SaaS uses Postgres, selected by pointing
DATABASE_URL at a Postgres connection string. The provider is chosen from the URL
scheme; nothing else in the application needs to change to switch databases. See
docs/DEPLOYMENT.md for the production migration path.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import Settings, get_settings


def normalize_database_url(url: str) -> str:
    """Return a SQLAlchemy-ready database URL.

    Some providers (Railway among them) hand out the legacy ``postgres://``
    scheme, which SQLAlchemy 2.0 no longer accepts. It is rewritten to the
    psycopg2 driver URL ``postgresql+psycopg2://``. A plain ``postgresql://`` URL
    is also pinned to the psycopg2 driver so the required driver is explicit.
    SQLite and any already-qualified driver URL are returned unchanged. No secret
    in the URL is logged or altered beyond the scheme.
    """

    raw = (url or "").strip()
    if raw.startswith("postgres://"):
        return "postgresql+psycopg2://" + raw[len("postgres://"):]
    if raw.startswith("postgresql://"):
        return "postgresql+psycopg2://" + raw[len("postgresql://"):]
    return raw


def database_provider(url: str) -> str:
    """Return a safe provider class for a URL: 'sqlite', 'postgres', or 'other'.

    Only the scheme is inspected; no host, credential, or path is read, so the
    result is safe to log and to return from the readiness API.
    """

    scheme = (url or "").strip().lower()
    if scheme.startswith("sqlite"):
        return "sqlite"
    if scheme.startswith("postgres"):
        return "postgres"
    return "other"


def _create_engine(settings: Settings):
    """Build the SQLAlchemy engine for the configured database."""

    normalized = normalize_database_url(settings.DATABASE_URL)
    # check_same_thread is a SQLite-specific flag needed because FastAPI may use
    # the connection across threads. It is ignored by other database backends.
    connect_args = (
        {"check_same_thread": False}
        if normalized.startswith("sqlite")
        else {}
    )
    return create_engine(normalized, connect_args=connect_args, future=True)


settings = get_settings()

engine = _create_engine(settings)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and closes it."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_production_database(settings: Settings | None = None) -> None:
    """Refuse to start in strict production mode without a Postgres database.

    Production SaaS data must not live on ephemeral SQLite. When APP_ENV is
    "production" and DATABASE_URL is not a Postgres URL, this raises a clear
    RuntimeError so the misconfiguration is caught at startup instead of silently
    serving customer data from a file that is recreated on each redeploy. In
    development, pilot, and test modes SQLite is allowed and this is a no-op. The
    error message names no secret and includes no connection string.
    """

    settings = settings or get_settings()
    if not settings.is_production:
        return
    if database_provider(settings.DATABASE_URL) != "postgres":
        raise RuntimeError(
            "APP_ENV=production requires a Postgres DATABASE_URL. SQLite is only "
            "supported for local development, tests, and the pilot prototype. Set "
            "DATABASE_URL to a Postgres connection string, or set APP_ENV to "
            "'development' or 'pilot' for prototype use. See "
            "docs/DEPLOYMENT.md."
        )


def init_db() -> None:
    """Create all tables. Models are imported for side effect registration.

    This is a convenience for local development, tests, and the pilot prototype.
    It only creates missing tables and never alters an existing one, so the
    production schema is managed by Alembic migrations (``alembic upgrade head``),
    not by this call. See docs/DEPLOYMENT.md.
    """

    from app.db import models  # noqa: F401  (registers models on Base.metadata)

    Base.metadata.create_all(bind=engine)
