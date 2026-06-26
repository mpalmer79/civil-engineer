"""Test configuration and fixtures.

A throwaway SQLite database file is configured before the application is
imported so tests never touch the development database. The application startup
hook creates the tables and loads the Brookside Meadows seed fixture.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator

import pytest

# Point the backend at an isolated temp database before importing app modules.
_db_fd, _db_path = tempfile.mkstemp(prefix="civil_engineer_test_", suffix=".db")
os.close(_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"

# Isolate Phase 12 browser DXF upload storage in a temp directory so tests never
# write uploaded files into the working tree.
_upload_dir = tempfile.mkdtemp(prefix="civil_engineer_cad_uploads_")
os.environ["CAD_UPLOAD_DIR"] = _upload_dir

# Sprint 5 authentication. The legacy Sprint 1 through 4 suites act on real
# projects without signing in, relying on the demo reviewer fallback. Keep that
# fallback on by default in tests by not requiring a login for real projects.
# The dedicated auth tests opt into strict enforcement with a settings override.
os.environ.setdefault("AUTH_REQUIRE_LOGIN_FOR_REAL_PROJECTS", "false")
os.environ.setdefault("AUTH_DEMO_MODE", "true")
os.environ.setdefault("AUTH_ALLOW_PUBLIC_DEMO", "true")
os.environ.setdefault("AUTH_SECRET_KEY", "test-secret-key")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
    try:
        os.remove(_db_path)
    except OSError:
        pass
