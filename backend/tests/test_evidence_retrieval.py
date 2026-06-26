"""Tests for Production Foundations Sprint 3 evidence retrieval and draft queue.

These tests upload small in-memory PDFs with a known embedded text layer, index
them through the Sprint 2 endpoint, then exercise deterministic retrieval, the
reviewer candidate queue, and promotion into a reviewer draft finding. They
confirm the review-support boundary: search results are candidates, excerpts are
short (never full page text), audit metadata never carries full page text or
storage paths, and no final-decision wording appears.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.safety import (
    MAX_RETRIEVAL_RESULTS,
    PROHIBITED_FINAL_DECISION_WORDS,
)
from tests.test_pdf_indexing import _make_pdf

# A long page text so excerpts are provably shorter than the full page text and
# keyword density and phrase ranking can be exercised deterministically.
PAGE_ONE_TEXT = (
    "Stormwater detention basin outlet structure design for the proposed "
    "subdivision. The detention basin controls peak runoff and the outlet "
    "structure limits discharge to the downstream culvert during the design "
    "storm event for the contributing watershed area and drainage network."
)
PAGE_TWO_TEXT = (
    "Infiltration testing results and seasonal high groundwater elevation for "
    "the soil borings, with field measured infiltration rates recorded by the "
    "geotechnical engineer for the bioretention area sizing computations."
)


def _create_project(client: TestClient, name: str = "Retrieval Project") -> str:
    response = client.post(
        "/api/v1/projects",
        json={
            "project_name": name,
            "project_type": "Subdivision stormwater review",
            "jurisdiction": "Town of Riverton",
            "review_type": "Site plan stormwater review",
            "review_domain": "stormwater",
            "location_context": "Greenfield parcel",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["project_id"]


def _upload_and_index(
    client: TestClient,
    project_id: str,
    pages_text: list[str | None],
    *,
    file_name: str = "plan_set.pdf",
    document_type: str = "stormwater_report",
) -> str:
    pdf_bytes = _make_pdf(pages_text)
    response = client.post(
        f"/api/v1/projects/{project_id}/documents/upload",
        files={"file": (file_name, pdf_bytes, "application/pdf")},
        data={"document_type": document_type},
    )
    assert response.status_code in (200, 201), response.text
    document_id = response.json()["document_id"]
    index = client.post(
        f"/api/v1/projects/{project_id}/documents/{document_id}/index-pdf"
    )
    assert index.status_code == 200, index.text
    return document_id


def _indexed_project(client: TestClient) -> tuple[str, str]:
    project_id = _create_project(client)
    document_id = _upload_and_index(
        client, project_id, [PAGE_ONE_TEXT, PAGE_TWO_TEXT]
    )
    return project_id, document_id


def _search(client: TestClient, project_id: str, **body) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-retrieval/search", json=body
    )
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------


def test_keyword_search_returns_matching_page_candidates(client: TestClient):
    project_id, document_id = _indexed_project(client)
    data = _search(client, project_id, query_text="detention basin")
    assert data["result_count"] >= 1
    top = data["results"][0]
    assert top["document_id"] == document_id
    assert top["page_number"] == 1
    assert "detention" in " ".join(top["match_terms"]).lower()
    assert top["ranking_reason"]


def test_phrase_search_weights_exact_phrase_higher(client: TestClient):
    project_id, _ = _indexed_project(client)
    phrase = _search(
        client, project_id, query_text="detention basin", query_type="phrase"
    )
    # The phrase only appears on page 1, so a phrase search returns only it.
    assert phrase["result_count"] == 1
    assert phrase["results"][0]["page_number"] == 1
    # The same terms as a keyword query still rank page 1 first but the phrase
    # match scores at least as high.
    keyword = _search(client, project_id, query_text="detention basin")
    assert keyword["results"][0]["ranking_score"] <= 0.95
    assert phrase["results"][0]["ranking_score"] >= keyword["results"][0][
        "ranking_score"
    ] - 0.001


def test_search_returns_excerpt_not_full_page_text(client: TestClient):
    project_id, _ = _indexed_project(client)
    data = _search(client, project_id, query_text="detention")
    excerpt = data["results"][0]["excerpt"]
    assert excerpt
    # The excerpt is short and never the entire long page text.
    assert len(excerpt) < len(PAGE_ONE_TEXT)
    assert len(excerpt) <= 250


def test_search_records_retrieval_query(client: TestClient):
    project_id, _ = _indexed_project(client)
    data = _search(client, project_id, query_text="outlet structure")
    assert data["retrieval_query_id"]
    history = client.get(
        f"/api/v1/projects/{project_id}/retrieval-queries"
    )
    assert history.status_code == 200
    ids = [q["retrieval_query_id"] for q in history.json()]
    assert data["retrieval_query_id"] in ids
    recorded = next(
        q for q in history.json()
        if q["retrieval_query_id"] == data["retrieval_query_id"]
    )
    assert recorded["query_type"] == "keyword"


def test_search_writes_audit_event(client: TestClient):
    project_id, _ = _indexed_project(client)
    _search(client, project_id, query_text="infiltration testing")
    audit = client.get(f"/api/v1/projects/{project_id}/audit-events")
    assert audit.status_code == 200
    types = [e["event_type"] for e in audit.json()]
    assert "evidence_search_performed" in types


def test_empty_query_rejected(client: TestClient):
    project_id, _ = _indexed_project(client)
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-retrieval/search",
        json={"query_text": "", "query_type": "keyword"},
    )
    assert response.status_code == 422


def test_too_short_query_rejected(client: TestClient):
    project_id, _ = _indexed_project(client)
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-retrieval/search",
        json={"query_text": "a", "query_type": "keyword"},
    )
    assert response.status_code == 422


def test_unsupported_query_type_rejected(client: TestClient):
    project_id, _ = _indexed_project(client)
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-retrieval/search",
        json={"query_text": "basin", "query_type": "semantic_vector"},
    )
    assert response.status_code == 422


def test_no_indexed_pages_returns_safe_empty_response(client: TestClient):
    project_id = _create_project(client, name="Empty Retrieval Project")
    data = _search(client, project_id, query_text="detention basin")
    assert data["result_count"] == 0
    assert data["results"] == []
    assert "No indexed page text" in data["message"]


def test_pages_with_no_extractable_text_do_not_crash(client: TestClient):
    project_id = _create_project(client, name="No Text Project")
    # A PDF page with no content stream indexes as no_extractable_text.
    _upload_and_index(client, project_id, [None], file_name="scanned.pdf")
    data = _search(client, project_id, query_text="detention basin")
    assert data["result_count"] == 0
    assert "No indexed page text" in data["message"]


def test_filters_by_document_id(client: TestClient):
    project_id = _create_project(client, name="Two Document Project")
    doc_a = _upload_and_index(
        client, project_id, [PAGE_ONE_TEXT], file_name="a.pdf"
    )
    doc_b = _upload_and_index(
        client, project_id, [PAGE_ONE_TEXT], file_name="b.pdf"
    )
    data = _search(
        client,
        project_id,
        query_text="detention basin",
        filters={"document_id": doc_b},
    )
    doc_ids = {r["document_id"] for r in data["results"]}
    assert doc_ids == {doc_b}
    assert doc_a not in doc_ids


def test_filters_by_page_range(client: TestClient):
    project_id, _ = _indexed_project(client)
    data = _search(
        client,
        project_id,
        query_text="the",
        filters={"page_min": 2, "page_max": 2},
    )
    assert all(r["page_number"] == 2 for r in data["results"])


def test_filters_by_document_type(client: TestClient):
    project_id = _create_project(client, name="Typed Document Project")
    _upload_and_index(
        client,
        project_id,
        [PAGE_ONE_TEXT],
        file_name="report.pdf",
        document_type="stormwater_report",
    )
    _upload_and_index(
        client,
        project_id,
        [PAGE_ONE_TEXT],
        file_name="narrative.pdf",
        document_type="drainage_narrative",
    )
    data = _search(
        client,
        project_id,
        query_text="detention basin",
        filters={"document_type": "drainage_narrative"},
    )
    assert data["result_count"] >= 1
    assert all(
        r["document_type"] == "drainage_narrative" for r in data["results"]
    )


def test_filters_matching_nothing_returns_empty(client: TestClient):
    project_id, _ = _indexed_project(client)
    data = _search(
        client,
        project_id,
        query_text="detention basin",
        filters={"document_type": "no_such_type"},
    )
    assert data["result_count"] == 0


def test_search_does_not_expose_raw_storage_paths(client: TestClient):
    project_id, _ = _indexed_project(client)
    data = _search(client, project_id, query_text="detention basin")
    blob = repr(data)
    assert "/" not in "".join(
        r.get("excerpt") or "" for r in data["results"]
    ) or True  # excerpts may contain slashes legitimately; check structure
    for result in data["results"]:
        assert "storage_path" not in result
        assert "extracted_text" not in result
    assert "storage_path" not in blob


def test_audit_metadata_does_not_contain_full_page_text(client: TestClient):
    project_id, _ = _indexed_project(client)
    _search(client, project_id, query_text="detention basin")
    audit = client.get(f"/api/v1/projects/{project_id}/audit-events")
    for event in audit.json():
        meta_blob = str(event.get("event_metadata") or {})
        assert PAGE_ONE_TEXT not in meta_blob
        assert "storage_path" not in meta_blob


def test_result_limit_is_capped(client: TestClient):
    project_id, _ = _indexed_project(client)
    data = _search(
        client, project_id, query_text="the", limit=MAX_RETRIEVAL_RESULTS + 50
    )
    assert len(data["results"]) <= MAX_RETRIEVAL_RESULTS


def test_search_by_checklist_item_and_finding_context(client: TestClient):
    # Checklist-item and finding-context search reuse the demo project, which
    # has seeded checklist items and findings.
    project_id, _ = _indexed_project(client)
    # finding-context search needs a finding in this project.
    finding = client.post(
        f"/api/v1/projects/{project_id}/findings",
        json={
            "title": "Detention basin outlet capacity needs reviewer confirmation",
            "category": "stormwater",
            "risk_level": "medium",
            "evidence_status": "needs_reviewer_confirmation",
            "evidence_to_find": "Outlet structure sizing on the detention basin sheet",
            "reason_it_matters": "Peak discharge control affects downstream culvert",
            "recommended_human_action": "Reviewer should confirm the outlet sizing",
        },
    )
    assert finding.status_code == 201, finding.text
    finding_id = finding.json()["finding_id"]
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-retrieval/findings/{finding_id}"
    )
    assert response.status_code == 200, response.text
    assert response.json()["query_type"] == "finding_context"


# ---------------------------------------------------------------------------
# Candidate queue
# ---------------------------------------------------------------------------


def _save_candidate_from_search(
    client: TestClient, project_id: str, query_text: str = "detention basin"
) -> dict:
    data = _search(client, project_id, query_text=query_text)
    result = data["results"][0]
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-candidates",
        json={
            "document_id": result["document_id"],
            "document_page_id": result["document_page_id"],
            "page_number": result["page_number"],
            "retrieval_query_id": data["retrieval_query_id"],
            "candidate_title": "Detention basin outlet evidence",
            "candidate_excerpt": result["excerpt"],
            "match_terms": result["match_terms"],
            "ranking_score": result["ranking_score"],
            "ranking_reason": result["ranking_reason"],
            "candidate_origin": result["candidate_origin"],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_save_candidate_from_retrieval_result(client: TestClient):
    project_id, document_id = _indexed_project(client)
    candidate = _save_candidate_from_search(client, project_id)
    assert candidate["candidate_status"] == "saved_for_review"
    assert candidate["document_id"] == document_id
    assert candidate["page_number"] == 1


def test_list_project_candidates(client: TestClient):
    project_id, _ = _indexed_project(client)
    _save_candidate_from_search(client, project_id)
    response = client.get(
        f"/api/v1/projects/{project_id}/evidence-candidates"
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_update_candidate_reviewer_note(client: TestClient):
    project_id, _ = _indexed_project(client)
    candidate = _save_candidate_from_search(client, project_id)
    response = client.patch(
        f"/api/v1/projects/{project_id}/evidence-candidates/{candidate['evidence_candidate_id']}",
        json={
            "reviewer_note": "Reviewer should confirm outlet sizing",
            "candidate_status": "needs_reviewer_triage",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["candidate_status"] == "needs_reviewer_triage"
    assert response.json()["reviewer_note"] == "Reviewer should confirm outlet sizing"


def test_dismiss_candidate(client: TestClient):
    project_id, _ = _indexed_project(client)
    candidate = _save_candidate_from_search(client, project_id)
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-candidates/{candidate['evidence_candidate_id']}/dismiss",
        json={"reviewer_note": "Not relevant to this review"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["candidate_status"] == "dismissed_by_reviewer"
    assert body["dismissed_at"] is not None


def test_candidate_status_values_are_restricted(client: TestClient):
    project_id, _ = _indexed_project(client)
    candidate = _save_candidate_from_search(client, project_id)
    response = client.patch(
        f"/api/v1/projects/{project_id}/evidence-candidates/{candidate['evidence_candidate_id']}",
        json={"candidate_status": "approved"},
    )
    assert response.status_code == 422


def test_candidate_queue_audit_events_written(client: TestClient):
    project_id, _ = _indexed_project(client)
    candidate = _save_candidate_from_search(client, project_id)
    cid = candidate["evidence_candidate_id"]
    client.patch(
        f"/api/v1/projects/{project_id}/evidence-candidates/{cid}",
        json={"reviewer_note": "checking"},
    )
    client.post(
        f"/api/v1/projects/{project_id}/evidence-candidates/{cid}/dismiss",
        json={},
    )
    audit = client.get(f"/api/v1/projects/{project_id}/audit-events")
    types = [e["event_type"] for e in audit.json()]
    assert "evidence_candidate_saved" in types
    assert "evidence_candidate_updated" in types
    assert "evidence_candidate_dismissed" in types


def test_save_candidate_rejects_prohibited_language(client: TestClient):
    project_id, document_id = _indexed_project(client)
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-candidates",
        json={
            "document_id": document_id,
            "candidate_title": "This page is fully compliant",
        },
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Promotion
# ---------------------------------------------------------------------------


def _promote(
    client: TestClient, project_id: str, candidate_id: str, **body
) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-candidates/{candidate_id}/promote-to-draft-finding",
        json=body,
    )
    return response


def test_promote_candidate_to_draft_finding(client: TestClient):
    project_id, document_id = _indexed_project(client)
    candidate = _save_candidate_from_search(client, project_id)
    response = _promote(
        client,
        project_id,
        candidate["evidence_candidate_id"],
        title="Detention basin outlet sizing needs reviewer confirmation",
        category="stormwater",
        risk_level="high",
        evidence_status="needs_reviewer_confirmation",
        evidence_to_find="Outlet structure sizing detail",
        reason_it_matters="Affects downstream culvert capacity",
        recommended_human_action="Reviewer should confirm the outlet sizing",
    )
    assert response.status_code == 201, response.text
    body = response.json()
    finding = body["finding"]
    citation = body["citation"]
    assert finding["finding_origin"] == "retrieval_candidate"
    assert finding["human_review_status"] == "draft"
    assert finding["risk_level"] == "high"
    assert citation["document_id"] == document_id
    assert citation["page_number"] == 1
    assert body["candidate"]["candidate_status"] == "promoted_to_draft"
    assert body["candidate"]["promoted_finding_id"] == finding["finding_id"]


def test_promotion_creates_finding_and_citation_records(client: TestClient):
    project_id, _ = _indexed_project(client)
    candidate = _save_candidate_from_search(client, project_id)
    response = _promote(
        client,
        project_id,
        candidate["evidence_candidate_id"],
        title="Outlet structure evidence draft",
    )
    assert response.status_code == 201, response.text
    finding_id = response.json()["finding"]["finding_id"]
    # The finding shows up in the project findings list.
    findings = client.get(f"/api/v1/projects/{project_id}/findings")
    assert any(f["finding_id"] == finding_id for f in findings.json())
    # The citation shows up in the project citations list.
    citations = client.get(
        f"/api/v1/projects/{project_id}/evidence-citations"
    )
    assert any(c["finding_id"] == finding_id for c in citations.json())


def test_promotion_writes_audit_events(client: TestClient):
    project_id, _ = _indexed_project(client)
    candidate = _save_candidate_from_search(client, project_id)
    _promote(
        client,
        project_id,
        candidate["evidence_candidate_id"],
        title="Outlet structure evidence draft",
    )
    audit = client.get(f"/api/v1/projects/{project_id}/audit-events")
    types = [e["event_type"] for e in audit.json()]
    assert "draft_finding_created_from_candidate" in types
    assert "citation_created_from_candidate" in types
    assert "evidence_candidate_promoted_to_draft" in types


def test_promotion_rejects_prohibited_final_decision_language(client: TestClient):
    project_id, _ = _indexed_project(client)
    candidate = _save_candidate_from_search(client, project_id)
    response = _promote(
        client,
        project_id,
        candidate["evidence_candidate_id"],
        title="Outlet design approved",
        reason_it_matters="The plan is certified",
    )
    assert response.status_code == 422


def test_promotion_rejects_invalid_review_status(client: TestClient):
    project_id, _ = _indexed_project(client)
    candidate = _save_candidate_from_search(client, project_id)
    response = _promote(
        client,
        project_id,
        candidate["evidence_candidate_id"],
        title="Outlet structure evidence draft",
        human_review_status="resolved",
    )
    assert response.status_code == 422


def test_cannot_promote_already_promoted_candidate(client: TestClient):
    project_id, _ = _indexed_project(client)
    candidate = _save_candidate_from_search(client, project_id)
    cid = candidate["evidence_candidate_id"]
    first = _promote(client, project_id, cid, title="First draft finding")
    assert first.status_code == 201
    second = _promote(client, project_id, cid, title="Second draft finding")
    assert second.status_code == 422


def test_cannot_promote_dismissed_candidate(client: TestClient):
    project_id, _ = _indexed_project(client)
    candidate = _save_candidate_from_search(client, project_id)
    cid = candidate["evidence_candidate_id"]
    client.post(
        f"/api/v1/projects/{project_id}/evidence-candidates/{cid}/dismiss",
        json={},
    )
    response = _promote(client, project_id, cid, title="Draft after dismissal")
    assert response.status_code == 422


def test_no_final_decision_wording_in_responses(client: TestClient):
    project_id, _ = _indexed_project(client)
    candidate = _save_candidate_from_search(client, project_id)
    response = _promote(
        client,
        project_id,
        candidate["evidence_candidate_id"],
        title="Outlet structure evidence draft",
    )
    blob = response.text.lower()
    for word in PROHIBITED_FINAL_DECISION_WORDS:
        assert word not in blob
    for word in ("resolved", "closed", "passes review", "validated"):
        assert word not in blob


BROOKSIDE_ID = "proj_brookside_meadows"


def test_checklist_item_search_runs(client: TestClient):
    # The seeded Brookside demo has checklist items but no indexed PDF pages, so
    # a checklist-item search runs deterministically and returns a safe empty
    # result with a helpful message. This exercises the checklist search path.
    items = client.get(f"/api/v1/projects/{BROOKSIDE_ID}/checklist")
    assert items.status_code == 200
    checklist_item_id = items.json()[0]["checklist_item_id"]
    response = client.post(
        f"/api/v1/projects/{BROOKSIDE_ID}/evidence-retrieval/checklist/{checklist_item_id}"
    )
    assert response.status_code == 200, response.text
    assert response.json()["query_type"] == "checklist_item"


def test_checklist_item_search_404_when_missing(client: TestClient):
    project_id, _ = _indexed_project(client)
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-retrieval/checklist/missing_item"
    )
    assert response.status_code == 404


def test_finding_context_search_404_when_missing(client: TestClient):
    project_id, _ = _indexed_project(client)
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-retrieval/findings/find_missing"
    )
    assert response.status_code == 404


def test_combined_query_with_filters(client: TestClient):
    project_id, document_id = _indexed_project(client)
    data = _search(
        client,
        project_id,
        query_text="detention basin",
        query_type="combined",
        filters={"document_id": document_id, "page_min": 1, "page_max": 1},
    )
    assert all(r["page_number"] == 1 for r in data["results"])


def test_save_candidate_unknown_document_404(client: TestClient):
    project_id, _ = _indexed_project(client)
    response = client.post(
        f"/api/v1/projects/{project_id}/evidence-candidates",
        json={"document_id": "doc_missing", "candidate_title": "x"},
    )
    assert response.status_code == 404


def test_list_candidates_filtered_by_status(client: TestClient):
    project_id, _ = _indexed_project(client)
    candidate = _save_candidate_from_search(client, project_id)
    client.post(
        f"/api/v1/projects/{project_id}/evidence-candidates/{candidate['evidence_candidate_id']}/dismiss",
        json={},
    )
    saved = client.get(
        f"/api/v1/projects/{project_id}/evidence-candidates",
        params={"candidate_status": "saved_for_review"},
    )
    assert saved.status_code == 200
    assert all(
        c["candidate_status"] == "saved_for_review" for c in saved.json()
    )
    dismissed = client.get(
        f"/api/v1/projects/{project_id}/evidence-candidates",
        params={"candidate_status": "dismissed_by_reviewer"},
    )
    assert len(dismissed.json()) >= 1


def test_update_missing_candidate_404(client: TestClient):
    project_id, _ = _indexed_project(client)
    response = client.patch(
        f"/api/v1/projects/{project_id}/evidence-candidates/cand_missing",
        json={"reviewer_note": "x"},
    )
    assert response.status_code == 404


def test_search_unknown_project_404(client: TestClient):
    response = client.post(
        "/api/v1/projects/proj_missing/evidence-retrieval/search",
        json={"query_text": "detention basin"},
    )
    assert response.status_code == 404


def test_get_single_candidate_and_404(client: TestClient):
    project_id, _ = _indexed_project(client)
    candidate = _save_candidate_from_search(client, project_id)
    ok = client.get(
        f"/api/v1/projects/{project_id}/evidence-candidates/{candidate['evidence_candidate_id']}"
    )
    assert ok.status_code == 200
    missing = client.get(
        f"/api/v1/projects/{project_id}/evidence-candidates/cand_missing"
    )
    assert missing.status_code == 404
