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
