"""Deployment configuration tests.

These tests confirm the backend settings behave correctly for a Railway-style
deployment: CORS origin parsing including the deployed frontend origin, the
upload directory and max upload size environment fallbacks, demo mode, and that
the health payload reports a product version rather than a phase number.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import Settings


def _settings(**kwargs) -> Settings:
    # _env_file=None so the test does not read a local .env file.
    return Settings(_env_file=None, **kwargs)


def test_cors_origins_parse_into_a_list() -> None:
    settings = _settings(
        CORS_ORIGINS="http://localhost:3000, http://127.0.0.1:3000"
    )
    assert settings.cors_origins_list == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_frontend_origin_is_added_to_cors_origins() -> None:
    settings = _settings(
        CORS_ORIGINS="http://localhost:3000",
        FRONTEND_ORIGIN="https://demo-frontend.up.railway.app",
    )
    assert "https://demo-frontend.up.railway.app" in settings.cors_origins_list
    # No duplicates when the frontend origin is already in the list.
    settings_dup = _settings(
        CORS_ORIGINS="https://demo-frontend.up.railway.app",
        FRONTEND_ORIGIN="https://demo-frontend.up.railway.app",
    )
    assert settings_dup.cors_origins_list.count(
        "https://demo-frontend.up.railway.app"
    ) == 1


def test_empty_frontend_origin_is_ignored() -> None:
    settings = _settings(CORS_ORIGINS="http://localhost:3000", FRONTEND_ORIGIN="")
    assert settings.cors_origins_list == ["http://localhost:3000"]


def test_upload_dir_default_and_override() -> None:
    # The field default is the local directory (the test process sets a temp
    # CAD_UPLOAD_DIR env var for isolation, so check the model default directly).
    assert Settings.model_fields["CAD_UPLOAD_DIR"].default == "./cad_uploads"
    assert _settings(CAD_UPLOAD_DIR="/data/uploads").CAD_UPLOAD_DIR == "/data/uploads"


def test_max_upload_size_default_and_env_aliases() -> None:
    assert _settings().CAD_MAX_UPLOAD_BYTES == 5_000_000
    # Primary name and the MAX_CAD_UPLOAD_BYTES alias both set the limit.
    assert _settings(CAD_MAX_UPLOAD_BYTES=8_000_000).CAD_MAX_UPLOAD_BYTES == 8_000_000
    assert _settings(MAX_CAD_UPLOAD_BYTES=9_000_000).CAD_MAX_UPLOAD_BYTES == 9_000_000


def test_demo_mode_default_on() -> None:
    assert _settings().DEMO_MODE is True


def test_health_reports_version_not_phase(client: TestClient) -> None:
    body = client.get("/health").json()
    assert "phase" not in body
    assert body["version"]
    assert body["demo_mode"] is True
