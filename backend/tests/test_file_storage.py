"""Tests for Production Foundations Sprint 6 durable file storage.

These tests exercise the storage provider abstraction (local and a mocked
S3-compatible provider), document upload through the storage service, the
access-controlled download and storage-status routes, the storage health route,
and PDF indexing from storage. They confirm the security boundary: no raw
filesystem path, storage credential, or signed URL is exposed, and access control
from Sprint 5 is preserved.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.safety import PROHIBITED_FINAL_DECISION_WORDS
from tests.test_pdf_indexing import _make_pdf

BROOKSIDE_ID = "proj_brookside_meadows"


# ---------------------------------------------------------------------------
# Storage provider unit tests
# ---------------------------------------------------------------------------


def test_local_provider_save_read_exists(tmp_path):
    from app.services.storage.local_storage import LocalStorageProvider

    provider = LocalStorageProvider(str(tmp_path))
    key = provider.generate_storage_key("proj_1", "doc_1", "Plan Final.PDF")
    # The generated key never contains the raw original filename.
    assert "Plan" not in key
    assert key.endswith(".pdf")
    stored = provider.save_file(key, b"pdf bytes", "application/pdf")
    assert stored.size_bytes == 9
    assert provider.file_exists(key)
    assert provider.read_file(key) == b"pdf bytes"
    assert provider.get_file_size(key) == 9


def test_local_provider_blocks_traversal(tmp_path):
    from app.services.storage.base import StorageError
    from app.services.storage.local_storage import LocalStorageProvider

    provider = LocalStorageProvider(str(tmp_path))
    with pytest.raises(StorageError):
        provider.read_file("../../etc/passwd")


def test_storage_service_selects_local_by_default():
    from app.services.storage import storage_service

    settings = get_settings()
    old = settings.STORAGE_PROVIDER
    settings.STORAGE_PROVIDER = "local"
    try:
        provider = storage_service.get_storage_provider()
        assert provider.get_provider_name() == "local"
    finally:
        settings.STORAGE_PROVIDER = old


def test_storage_service_rejects_unsupported_provider():
    from app.services.storage import storage_service
    from app.services.storage.base import StorageError

    settings = get_settings()
    old = settings.STORAGE_PROVIDER
    settings.STORAGE_PROVIDER = "ftp"
    try:
        with pytest.raises(StorageError):
            storage_service.get_storage_provider()
    finally:
        settings.STORAGE_PROVIDER = old


class _FakeBody:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data


class _FakeS3Client:
    def __init__(self) -> None:
        self.store: dict[str, bytes] = {}

    def put_object(self, **kwargs):
        self.store[kwargs["Key"]] = kwargs["Body"]
        return {"ETag": '"etag123"', "VersionId": "v1"}

    def get_object(self, Bucket, Key):
        if Key not in self.store:
            raise KeyError(Key)
        return {"Body": _FakeBody(self.store[Key])}

    def head_object(self, Bucket, Key):
        if Key not in self.store:
            raise KeyError(Key)
        return {"ContentLength": len(self.store[Key])}

    def generate_presigned_url(self, *args, **kwargs):
        return "https://signed.example/" + kwargs["Params"]["Key"]


def test_s3_provider_missing_bucket_and_failures():
    from app.services.storage.base import StorageError
    from app.services.storage.s3_storage import S3CompatibleStorageProvider

    settings = get_settings()
    old_bucket = settings.OBJECT_STORAGE_BUCKET
    settings.OBJECT_STORAGE_BUCKET = ""
    try:
        provider = S3CompatibleStorageProvider(settings, client=_FakeS3Client())
        # No bucket configured raises a safe storage error.
        with pytest.raises(StorageError):
            provider.save_file("k", b"x", "application/pdf")
    finally:
        settings.OBJECT_STORAGE_BUCKET = old_bucket


def test_storage_service_helpers_and_fallback(tmp_path):
    from types import SimpleNamespace

    from app.services.storage import storage_service
    from app.services.storage.base import StorageError

    # A document with a legacy local storage_path (no storage_key) is read via
    # the backward-compatibility path.
    legacy_file = tmp_path / "legacy.pdf"
    legacy_file.write_bytes(b"legacy bytes")
    legacy_doc = SimpleNamespace(
        storage_key=None, storage_path=str(legacy_file), storage_provider=None
    )
    assert storage_service.read_document_bytes(legacy_doc) == b"legacy bytes"
    assert storage_service.document_file_exists(legacy_doc) is True
    assert storage_service.document_file_size(legacy_doc) == 12

    # A document with neither a storage key nor an existing path is unavailable.
    missing_doc = SimpleNamespace(
        storage_key=None, storage_path=None, storage_provider=None
    )
    assert storage_service.document_file_exists(missing_doc) is False
    assert storage_service.document_file_size(missing_doc) is None
    with pytest.raises(StorageError):
        storage_service.read_document_bytes(missing_doc)


def test_storage_service_health_for_local():
    from app.services.storage import storage_service

    settings = get_settings()
    old = settings.STORAGE_PROVIDER
    settings.STORAGE_PROVIDER = "local"
    try:
        info = storage_service.storage_health()
        assert info["provider"] == "local"
        assert info["configured"] is True
    finally:
        settings.STORAGE_PROVIDER = old


def test_s3_provider_with_mock_client():
    from app.services.storage.s3_storage import S3CompatibleStorageProvider

    settings = get_settings()
    old_bucket = settings.OBJECT_STORAGE_BUCKET
    settings.OBJECT_STORAGE_BUCKET = "test-bucket"
    try:
        provider = S3CompatibleStorageProvider(settings, client=_FakeS3Client())
        key = "projects/p/d/abc.pdf"
        stored = provider.save_file(key, b"object bytes", "application/pdf")
        assert stored.etag == '"etag123"'
        assert stored.bucket == "test-bucket"
        assert provider.read_file(key) == b"object bytes"
        assert provider.file_exists(key)
        assert provider.get_file_size(key) == 12
        assert not provider.file_exists("missing-key")
        assert provider.create_download_url(key).startswith("https://")
        # Health never includes secrets.
        health = provider.health()
        assert "secret" not in str(health).lower()
        assert "access_key" not in str(health).lower()
    finally:
        settings.OBJECT_STORAGE_BUCKET = old_bucket


# ---------------------------------------------------------------------------
# Upload through storage
# ---------------------------------------------------------------------------


def _create_project(client: TestClient, name: str = "Storage Project") -> str:
    response = client.post(
        "/api/v1/projects",
        json={
            "project_name": name,
            "project_type": "Subdivision",
            "jurisdiction": "Town",
            "review_type": "Review",
            "review_domain": "stormwater",
            "location_context": "Parcel",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["project_id"]


def _upload(client: TestClient, project_id: str, content: bytes | None = None) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/documents/upload",
        files={"file": ("plan.pdf", content or _make_pdf(["Detention basin"]), "application/pdf")},
        data={"document_type": "stormwater_report"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_upload_records_storage_metadata(client: TestClient):
    project_id = _create_project(client)
    doc = _upload(client, project_id)
    assert doc["storage_provider"] == "local"
    assert doc["file_available"] is True
    assert doc["upload_status"] == "stored"
    assert doc["checksum_sha256"] and len(doc["checksum_sha256"]) == 64
    # No raw storage path or storage key is exposed in the response.
    assert "storage_path" not in doc
    assert "storage_key" not in doc


def test_upload_writes_document_stored_audit(client: TestClient):
    project_id = _create_project(client)
    _upload(client, project_id)
    audit = client.get(f"/api/v1/projects/{project_id}/audit-events").json()
    types = [e["event_type"] for e in audit]
    assert "document_stored" in types
    blob = str(audit).lower()
    assert "storage_path" not in blob
    assert "secret" not in blob


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------


def test_download_returns_file_and_increments_count(client: TestClient):
    project_id = _create_project(client)
    pdf = _make_pdf(["Detention basin outlet"])
    doc = _upload(client, project_id, pdf)
    download = client.get(
        f"/api/v1/projects/{project_id}/documents/{doc['document_id']}/download"
    )
    assert download.status_code == 200
    assert download.content == pdf
    assert "attachment" in download.headers.get("content-disposition", "")
    # download_count increments and an audit event is written.
    status = client.get(
        f"/api/v1/projects/{project_id}/documents/{doc['document_id']}/storage-status"
    ).json()
    assert status["download_count"] >= 1
    assert status["last_downloaded_at"] is not None
    audit = client.get(f"/api/v1/projects/{project_id}/audit-events").json()
    assert "document_downloaded" in [e["event_type"] for e in audit]


def test_download_missing_file_returns_safe_error(client: TestClient):
    from app.db import models
    from app.db.database import SessionLocal
    from app.services.storage.storage_service import get_storage_provider

    project_id = _create_project(client)
    doc = _upload(client, project_id)
    db = SessionLocal()
    try:
        document = db.get(models.Document, doc["document_id"])
        get_storage_provider().delete_file(document.storage_key)
    finally:
        db.close()
    download = client.get(
        f"/api/v1/projects/{project_id}/documents/{doc['document_id']}/download"
    )
    assert download.status_code == 404
    assert "not available" in download.json()["detail"].lower()


def test_download_does_not_expose_storage_path(client: TestClient):
    project_id = _create_project(client)
    doc = _upload(client, project_id)
    status = client.get(
        f"/api/v1/projects/{project_id}/documents/{doc['document_id']}/storage-status"
    )
    body = status.text.lower()
    assert "storage_path" not in body
    assert "/project_uploads/" not in body
    assert "storage_key" not in body


# ---------------------------------------------------------------------------
# Storage status and health
# ---------------------------------------------------------------------------


def test_storage_status_returns_safe_metadata(client: TestClient):
    project_id = _create_project(client)
    doc = _upload(client, project_id)
    status = client.get(
        f"/api/v1/projects/{project_id}/documents/{doc['document_id']}/storage-status"
    )
    assert status.status_code == 200
    body = status.json()
    assert body["file_available"] is True
    assert body["storage_provider"] == "local"
    assert body["checksum_sha256"]


def test_storage_health_requires_auth(client: TestClient):
    anon = client.get("/api/v1/storage/health")
    assert anon.status_code == 401
    # Register a user and check health.
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"storage_{uuid.uuid4().hex[:8]}@example.com",
            "display_name": "Storage User",
            "password": "password123",
        },
    )
    token = reg.json()["access_token"]
    health = client.get(
        "/api/v1/storage/health", headers={"Authorization": f"Bearer {token}"}
    )
    assert health.status_code == 200
    body = health.json()
    assert body["provider"] == "local"
    assert "secret" not in str(body).lower()


# ---------------------------------------------------------------------------
# Access control on storage routes
# ---------------------------------------------------------------------------


def _register(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"u_{uuid.uuid4().hex[:8]}@example.com",
            "display_name": "Reviewer",
            "password": "password123",
        },
    )
    return response.json()


def test_download_requires_read_access(client: TestClient):
    owner = _register(client)
    headers = {"Authorization": f"Bearer {owner['access_token']}"}
    project_id = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "project_name": "Private Storage Project",
            "project_type": "Subdivision",
            "jurisdiction": "Town",
            "review_type": "Review",
            "review_domain": "stormwater",
            "location_context": "Parcel",
        },
    ).json()["project_id"]
    upload = client.post(
        f"/api/v1/projects/{project_id}/documents/upload",
        headers=headers,
        files={"file": ("plan.pdf", _make_pdf(["x"]), "application/pdf")},
        data={"document_type": "stormwater_report"},
    )
    assert upload.status_code == 201, upload.text
    document_id = upload.json()["document_id"]
    # Another user without access is denied download and storage status.
    other = _register(client)
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    dl = client.get(
        f"/api/v1/projects/{project_id}/documents/{document_id}/download",
        headers=other_headers,
    )
    assert dl.status_code == 403
    status = client.get(
        f"/api/v1/projects/{project_id}/documents/{document_id}/storage-status",
        headers=other_headers,
    )
    assert status.status_code == 403


# ---------------------------------------------------------------------------
# PDF indexing from storage
# ---------------------------------------------------------------------------


def test_indexing_reads_from_storage(client: TestClient):
    project_id = _create_project(client)
    doc = _upload(client, project_id, _make_pdf(["Detention basin outlet structure"]))
    index = client.post(
        f"/api/v1/projects/{project_id}/documents/{doc['document_id']}/index-pdf"
    )
    assert index.status_code == 200, index.text
    audit = client.get(f"/api/v1/projects/{project_id}/audit-events").json()
    assert "pdf_indexing_file_loaded_from_storage" in [
        e["event_type"] for e in audit
    ]
    # No raw path is exposed in the indexing summary.
    assert "storage_path" not in index.text


# ---------------------------------------------------------------------------
# Security and regression
# ---------------------------------------------------------------------------


def test_no_prohibited_wording_in_storage_messages(client: TestClient):
    project_id = _create_project(client)
    doc = _upload(client, project_id)
    status = client.get(
        f"/api/v1/projects/{project_id}/documents/{doc['document_id']}/storage-status"
    )
    blob = status.text.lower()
    for word in PROHIBITED_FINAL_DECISION_WORDS:
        assert word not in blob


def test_health_and_demo_still_work(client: TestClient):
    assert client.get("/health").status_code == 200
    assert client.get(f"/api/v1/projects/{BROOKSIDE_ID}").status_code == 200
    assert client.get(f"/api/v1/projects/{BROOKSIDE_ID}/documents").status_code == 200
