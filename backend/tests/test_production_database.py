"""Production database foundation tests (Production Phase 4A).

Covers database URL normalization and provider detection for SQLite and Postgres
URL forms, the strict production-mode guard, the Alembic migration metadata and
revision wiring, and the readiness migration/provider posture. No test requires a
live Postgres server; Postgres handling is exercised at the URL/configuration
level. Manual Postgres verification is documented in docs/DEPLOYMENT.md.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

from app.core.config import Settings
from app.db import models  # noqa: F401  (registers tables on Base.metadata)
from app.db.database import (
    Base,
    check_production_database,
    database_provider,
    normalize_database_url,
)

_BACKEND_DIR = Path(__file__).resolve().parents[1]


def _settings(**kwargs) -> Settings:
    # _env_file=None so the test does not read a local .env file.
    return Settings(_env_file=None, **kwargs)


# ---------------------------------------------------------------------------
# URL normalization
# ---------------------------------------------------------------------------


def test_sqlite_url_is_unchanged():
    url = "sqlite:///./civil_engineer_ai.db"
    assert normalize_database_url(url) == url


def test_legacy_postgres_scheme_is_normalized_to_psycopg2():
    # Railway and some providers hand out the legacy postgres:// scheme.
    url = "postgres://user:pw@host:5432/dbname"
    assert (
        normalize_database_url(url)
        == "postgresql+psycopg2://user:pw@host:5432/dbname"
    )


def test_plain_postgresql_scheme_is_pinned_to_psycopg2():
    url = "postgresql://user:pw@host:5432/dbname"
    assert (
        normalize_database_url(url)
        == "postgresql+psycopg2://user:pw@host:5432/dbname"
    )


def test_already_qualified_driver_url_is_unchanged():
    url = "postgresql+psycopg2://user:pw@host/db"
    assert normalize_database_url(url) == url


def test_normalize_handles_whitespace():
    assert normalize_database_url("  sqlite:///./x.db  ") == "sqlite:///./x.db"


# ---------------------------------------------------------------------------
# Provider detection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("sqlite:///./x.db", "sqlite"),
        ("sqlite://", "sqlite"),
        ("postgres://u:p@h/d", "postgres"),
        ("postgresql://u:p@h/d", "postgres"),
        ("postgresql+psycopg2://u:p@h/d", "postgres"),
        ("mysql://u:p@h/d", "other"),
        ("", "other"),
    ],
)
def test_database_provider_classifies_scheme(url, expected):
    assert database_provider(url) == expected


# ---------------------------------------------------------------------------
# Strict production-mode guard
# ---------------------------------------------------------------------------


def test_production_with_postgres_is_allowed():
    settings = _settings(
        APP_ENV="production",
        DATABASE_URL="postgresql://user:pw@host:5432/db",
    )
    # Does not raise.
    check_production_database(settings)


def test_production_with_sqlite_is_refused():
    settings = _settings(
        APP_ENV="production",
        DATABASE_URL="sqlite:///./civil_engineer_ai.db",
    )
    with pytest.raises(RuntimeError) as excinfo:
        check_production_database(settings)
    message = str(excinfo.value)
    assert "Postgres" in message
    # The error names no connection string or secret.
    assert "sqlite:///" not in message


def test_development_with_sqlite_is_allowed():
    settings = _settings(APP_ENV="development", DATABASE_URL="sqlite:///./x.db")
    check_production_database(settings)


def test_pilot_with_sqlite_is_allowed():
    settings = _settings(APP_ENV="pilot", DATABASE_URL="sqlite:///./x.db")
    check_production_database(settings)


def test_app_env_is_normalized():
    assert _settings(APP_ENV="  Production ").is_production is True
    assert _settings(APP_ENV="DEVELOPMENT").is_production is False
    assert _settings().app_env == "development"


# ---------------------------------------------------------------------------
# Migration metadata and revisions
# ---------------------------------------------------------------------------


def test_metadata_includes_all_core_and_pilot_tables():
    tables = set(Base.metadata.tables)
    # A representative span across phases plus the production-foundation and
    # pilot tables that the initial migration must include.
    expected = {
        "projects",
        "documents",
        "findings",
        "organizations",
        "organization_memberships",
        "project_access",
        "user_accounts",
        "cad_file_uploads",
        "cad_review_findings",
        "review_packets",
        "workflow_items",
        "response_packages",
        "pilot_requests",
    }
    missing = expected - tables
    assert not missing, f"missing tables in metadata: {missing}"


def test_pilot_request_operator_fields_present_in_metadata():
    columns = set(Base.metadata.tables["pilot_requests"].columns.keys())
    assert {"status", "internal_notes", "last_contacted_at"} <= columns


def test_initial_migration_is_the_base_revision():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config(str(_BACKEND_DIR / "alembic.ini"))
    config.set_main_option(
        "script_location", str(_BACKEND_DIR / "app" / "migrations")
    )
    script = ScriptDirectory.from_config(config)
    # The initial migration is the base of the chain.
    base = script.get_revision("0001_initial_schema")
    assert base.down_revision is None
    # The head has advanced past the initial migration; the chain is linear back
    # to the initial revision.
    head = script.get_current_head()
    assert head == "0004_processing_jobs"
    head_revision = script.get_revision(head)
    assert head_revision.down_revision == "0003_billing_events"
    billing_revision = script.get_revision("0003_billing_events")
    assert billing_revision.down_revision == "0002_auth_billing_usage"
    mid_revision = script.get_revision("0002_auth_billing_usage")
    assert mid_revision.down_revision == "0001_initial_schema"


def test_create_all_from_metadata_builds_pilot_table():
    # Mirrors what the initial migration's upgrade() does: create every table
    # from the live metadata. Validates the metadata is internally consistent and
    # buildable on a fresh SQLite database.
    engine = create_engine("sqlite://", future=True)
    Base.metadata.create_all(bind=engine)
    try:
        inspector = inspect(engine)
        names = set(inspector.get_table_names())
        assert "pilot_requests" in names
        assert "projects" in names
        pilot_cols = {c["name"] for c in inspector.get_columns("pilot_requests")}
        assert {"status", "internal_notes", "last_contacted_at"} <= pilot_cols
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_alembic_upgrade_and_downgrade_on_fresh_sqlite():
    # Apply migrations end to end against a throwaway SQLite file in a subprocess
    # so the test process database (shared by the client fixture) is untouched.
    fd, db_path = tempfile.mkstemp(prefix="civil_engineer_migration_", suffix=".db")
    os.close(fd)
    os.remove(db_path)
    env = dict(os.environ)
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    try:
        up = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=str(_BACKEND_DIR),
            env=env,
            capture_output=True,
            text=True,
        )
        assert up.returncode == 0, up.stderr
        engine = create_engine(f"sqlite:///{db_path}", future=True)
        try:
            names = set(inspect(engine).get_table_names())
            assert "alembic_version" in names
            assert "pilot_requests" in names
            assert "projects" in names
        finally:
            engine.dispose()

        down = subprocess.run(
            [sys.executable, "-m", "alembic", "downgrade", "base"],
            cwd=str(_BACKEND_DIR),
            env=env,
            capture_output=True,
            text=True,
        )
        assert down.returncode == 0, down.stderr
    finally:
        try:
            os.remove(db_path)
        except OSError:
            pass
