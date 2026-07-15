"""Tests for the inline PDF page cap safeguard.

A very large or hostile PDF must not be indexed unbounded on the request
thread. The service indexes up to PDF_MAX_PAGES pages and marks the document as
needing reviewer follow-up for the remainder.
"""

from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.services import pdf_indexing_service
from tests.test_pdf_indexing import _create_project, _make_pdf, _upload_pdf


def test_index_pdf_is_capped_and_flagged_for_review(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(
        pdf_indexing_service, "get_settings", lambda: SimpleNamespace(PDF_MAX_PAGES=2)
    )
    pid = _create_project(client, "PDF Page Cap Project")
    did = _upload_pdf(
        client,
        pid,
        _make_pdf(["page one", "page two", "page three", "page four"]),
    )

    response = client.post(f"/api/v1/projects/{pid}/documents/{did}/index-pdf")
    assert response.status_code == 200
    summary = response.json()

    # The full page count is still recorded, but only the capped number were
    # indexed, and the document is flagged for reviewer follow-up.
    assert summary["page_count"] == 4
    assert summary["processing_status"] == "indexed_partial_needs_review"
    assert summary["pages_with_text"] == 2

    pages = client.get(f"/api/v1/projects/{pid}/documents/{did}/pages").json()
    assert len(pages) == 2


def test_index_pdf_within_cap_is_not_flagged(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(
        pdf_indexing_service, "get_settings", lambda: SimpleNamespace(PDF_MAX_PAGES=500)
    )
    pid = _create_project(client, "PDF Under Cap Project")
    did = _upload_pdf(client, pid, _make_pdf(["only page"]))

    summary = client.post(
        f"/api/v1/projects/{pid}/documents/{did}/index-pdf"
    ).json()
    assert summary["page_count"] == 1
    assert summary["processing_status"] == "indexed_with_text"
