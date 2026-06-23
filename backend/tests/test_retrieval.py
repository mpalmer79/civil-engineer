"""Retrieval and source evidence tests for the Brookside Meadows fixture."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.safety import (
    ALLOWED_EVIDENCE_ROLES,
    contains_prohibited_language,
)

PROJECT_ID = "proj_brookside_meadows"


def test_seed_includes_document_chunks(client: TestClient) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}/chunks")
    assert response.status_code == 200
    chunks = response.json()
    assert len(chunks) >= 50


def test_seed_includes_finding_sources(client: TestClient) -> None:
    response = client.get("/api/v1/findings/find_infiltration_missing/sources")
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) >= 1
    for source in sources:
        assert source["evidence_role"] in ALLOWED_EVIDENCE_ROLES


def test_document_chunks_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/documents/doc_stormwater_report/chunks")
    assert response.status_code == 200
    chunks = response.json()
    assert len(chunks) >= 2
    assert all(c["document_id"] == "doc_stormwater_report" for c in chunks)


def test_search_infiltration_testing(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/projects/{PROJECT_ID}/search",
        params={"query": "infiltration testing"},
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    joined = " ".join(r["excerpt"].lower() for r in results)
    assert "infiltration" in joined


def test_search_downstream_culvert(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/projects/{PROJECT_ID}/search",
        params={"query": "downstream culvert"},
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    docs = {r["document_id"] for r in results}
    assert "doc_hydraulic_calcs" in docs


def test_search_operation_and_maintenance(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/projects/{PROJECT_ID}/search",
        params={"query": "operation and maintenance"},
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    docs = {r["document_id"] for r in results}
    assert "doc_oem_plan" in docs


def test_finding_evidence_endpoint(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/projects/{PROJECT_ID}/findings/find_infiltration_missing/evidence"
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    for r in results:
        assert r["evidence_role"] in ALLOWED_EVIDENCE_ROLES
        assert r["safety_note"]


def test_checklist_evidence_endpoint(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/projects/{PROJECT_ID}/checklist/chk_infiltration_testing/evidence"
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1


def test_retrieval_includes_metadata_and_pages(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/projects/{PROJECT_ID}/search",
        params={"query": "seasonal high groundwater"},
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    top = results[0]
    for field in (
        "chunk_id",
        "document_id",
        "file_name",
        "document_type",
        "page_number",
        "section_heading",
        "excerpt",
        "relevance_reason",
        "score",
        "safety_note",
    ):
        assert field in top
    assert 0.0 < top["score"] <= 1.0


def test_retrieval_avoids_prohibited_language(client: TestClient) -> None:
    queries = ["infiltration testing", "downstream culvert", "design storm"]
    for q in queries:
        results = client.get(
            f"/api/v1/projects/{PROJECT_ID}/search", params={"query": q}
        ).json()
        for r in results:
            assert not contains_prohibited_language(r["relevance_reason"])
            assert not contains_prohibited_language(r["safety_note"])

    findings = client.get(f"/api/v1/projects/{PROJECT_ID}/findings").json()
    for f in findings:
        evidence = client.get(
            f"/api/v1/projects/{PROJECT_ID}/findings/{f['finding_id']}/evidence"
        ).json()
        for r in evidence:
            assert not contains_prohibited_language(r["excerpt"])
            assert not contains_prohibited_language(r["relevance_reason"])


def test_unknown_finding_evidence_returns_404(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/projects/{PROJECT_ID}/findings/find_nope/evidence"
    )
    assert response.status_code == 404
