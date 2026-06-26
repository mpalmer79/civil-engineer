"""Tests for Production Foundations Sprint 4 checklist-driven evidence review.

These tests exercise the seeded starter rule pack, applying a rule pack to a real
project as a checklist, reviewer-controlled checklist item status updates,
checklist evidence search over indexed PDF page text, evidence links, and draft
finding creation from a checklist item. They confirm the review-support
boundary: rule packs are templates not legal determinations, checklist status is
review-support only, excerpts are short, audit metadata carries no full page
text or storage paths, and no final-decision wording appears.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.safety import PROHIBITED_FINAL_DECISION_WORDS
from app.services.checklist_review_service import STARTER_RULE_PACK_ID
from tests.test_pdf_indexing import _make_pdf

BROOKSIDE_ID = "proj_brookside_meadows"

PAGE_TEXT = (
    "Stormwater detention basin outlet structure design for the proposed "
    "subdivision. The detention basin controls peak runoff and the outlet "
    "structure limits discharge to the downstream culvert during the design "
    "storm event for the contributing watershed area and drainage network."
)


def _create_project(client: TestClient, name: str = "Checklist Project") -> str:
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


def _create_checklist(client: TestClient, project_id: str) -> dict:
    response = client.post(
        f"/api/v1/projects/{project_id}/checklists/from-rule-pack",
        json={"rule_pack_id": STARTER_RULE_PACK_ID},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _first_item(client: TestClient, project_id: str, checklist_id: str) -> dict:
    items = client.get(
        f"/api/v1/projects/{project_id}/checklists/{checklist_id}/items"
    )
    assert items.status_code == 200
    return items.json()[0]


def _upload_and_index(client: TestClient, project_id: str) -> str:
    pdf_bytes = _make_pdf([PAGE_TEXT])
    upload = client.post(
        f"/api/v1/projects/{project_id}/documents/upload",
        files={"file": ("plan.pdf", pdf_bytes, "application/pdf")},
        data={"document_type": "stormwater_report"},
    )
    assert upload.status_code in (200, 201), upload.text
    document_id = upload.json()["document_id"]
    index = client.post(
        f"/api/v1/projects/{project_id}/documents/{document_id}/index-pdf"
    )
    assert index.status_code == 200, index.text
    return document_id


# ---------------------------------------------------------------------------
# Rule packs
# ---------------------------------------------------------------------------


def test_starter_rule_pack_seeded_and_listed(client: TestClient):
    response = client.get("/api/v1/rule-packs")
    assert response.status_code == 200
    packs = response.json()
    starter = next(p for p in packs if p["rule_pack_id"] == STARTER_RULE_PACK_ID)
    assert starter["source_mode"] == "seeded_demo"
    assert starter["item_count"] >= 12


def test_get_rule_pack_detail(client: TestClient):
    response = client.get(f"/api/v1/rule-packs/{STARTER_RULE_PACK_ID}")
    assert response.status_code == 200
    detail = response.json()
    assert len(detail["items"]) >= 12
    categories = {i["category"] for i in detail["items"]}
    assert "Detention and outlet control" in categories
    for item in detail["items"]:
        assert item["reference_label"] == "Starter template, not ordinance"


def test_starter_pack_does_not_claim_legal_determination(client: TestClient):
    detail = client.get(f"/api/v1/rule-packs/{STARTER_RULE_PACK_ID}").json()
    blob = (
        (detail.get("description") or "")
        + " ".join(i["requirement_text"] for i in detail["items"])
        + " ".join(i["expected_evidence"] for i in detail["items"])
    ).lower()
    for word in PROHIBITED_FINAL_DECISION_WORDS:
        assert word not in blob
    for word in ("compliant", "ordinance-approved", "legally binding"):
        assert word not in blob


def test_get_rule_pack_404(client: TestClient):
    assert client.get("/api/v1/rule-packs/missing").status_code == 404


# ---------------------------------------------------------------------------
# Project checklists
# ---------------------------------------------------------------------------


def test_create_project_checklist_from_rule_pack(client: TestClient):
    project_id = _create_project(client)
    checklist = _create_checklist(client, project_id)
    assert checklist["status"] == "checklist_started"
    assert checklist["item_count"] >= 12
    assert checklist["rule_pack_id"] == STARTER_RULE_PACK_ID


def test_create_checklist_writes_audit_event(client: TestClient):
    project_id = _create_project(client)
    _create_checklist(client, project_id)
    audit = client.get(f"/api/v1/projects/{project_id}/audit-events")
    types = [e["event_type"] for e in audit.json()]
    assert "project_checklist_created" in types


def test_list_and_get_project_checklist(client: TestClient):
    project_id = _create_project(client)
    checklist = _create_checklist(client, project_id)
    cid = checklist["project_checklist_id"]
    listed = client.get(f"/api/v1/projects/{project_id}/checklists")
    assert any(c["project_checklist_id"] == cid for c in listed.json())
    detail = client.get(f"/api/v1/projects/{project_id}/checklists/{cid}")
    assert detail.status_code == 200
    assert len(detail.json()["items"]) >= 12
    assert "evidence_status_summary" in detail.json()


def test_create_checklist_unknown_rule_pack_404(client: TestClient):
    project_id = _create_project(client)
    response = client.post(
        f"/api/v1/projects/{project_id}/checklists/from-rule-pack",
        json={"rule_pack_id": "missing"},
    )
    assert response.status_code == 404


def test_brookside_seeded_checklist_still_works(client: TestClient):
    # The seeded demo checklist route is preserved alongside the new routes.
    response = client.get(f"/api/v1/projects/{BROOKSIDE_ID}/checklist")
    assert response.status_code == 200
    assert len(response.json()) > 0


# ---------------------------------------------------------------------------
# Checklist item updates
# ---------------------------------------------------------------------------


def test_update_applicability_status(client: TestClient):
    project_id = _create_project(client)
    checklist = _create_checklist(client, project_id)
    item = _first_item(client, project_id, checklist["project_checklist_id"])
    response = client.patch(
        f"/api/v1/projects/{project_id}/checklist-items/{item['project_checklist_item_id']}",
        json={"applicability_status": "not_applicable_by_reviewer"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["applicability_status"] == "not_applicable_by_reviewer"


def test_update_evidence_status_and_note(client: TestClient):
    project_id = _create_project(client)
    checklist = _create_checklist(client, project_id)
    item = _first_item(client, project_id, checklist["project_checklist_id"])
    response = client.patch(
        f"/api/v1/projects/{project_id}/checklist-items/{item['project_checklist_item_id']}",
        json={
            "evidence_status": "missing_evidence",
            "reviewer_note": "Reviewer should request the drainage report",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["evidence_status"] == "missing_evidence"
    assert body["reviewer_note"] == "Reviewer should request the drainage report"


def test_update_rejects_unsupported_status(client: TestClient):
    project_id = _create_project(client)
    checklist = _create_checklist(client, project_id)
    item = _first_item(client, project_id, checklist["project_checklist_id"])
    response = client.patch(
        f"/api/v1/projects/{project_id}/checklist-items/{item['project_checklist_item_id']}",
        json={"evidence_status": "compliant"},
    )
    assert response.status_code == 422


def test_update_rejects_prohibited_language(client: TestClient):
    project_id = _create_project(client)
    checklist = _create_checklist(client, project_id)
    item = _first_item(client, project_id, checklist["project_checklist_id"])
    response = client.patch(
        f"/api/v1/projects/{project_id}/checklist-items/{item['project_checklist_item_id']}",
        json={"reviewer_note": "This item is approved and certified"},
    )
    assert response.status_code == 422


def test_update_writes_audit_events(client: TestClient):
    project_id = _create_project(client)
    checklist = _create_checklist(client, project_id)
    item = _first_item(client, project_id, checklist["project_checklist_id"])
    client.patch(
        f"/api/v1/projects/{project_id}/checklist-items/{item['project_checklist_item_id']}",
        json={"applicability_status": "not_applicable_by_reviewer"},
    )
    audit = client.get(f"/api/v1/projects/{project_id}/audit-events")
    types = [e["event_type"] for e in audit.json()]
    assert "checklist_item_marked_not_applicable_by_reviewer" in types


def test_update_missing_item_404(client: TestClient):
    project_id = _create_project(client)
    response = client.patch(
        f"/api/v1/projects/{project_id}/checklist-items/missing",
        json={"evidence_status": "missing_evidence"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Checklist evidence search
# ---------------------------------------------------------------------------


def test_checklist_evidence_search_returns_excerpts(client: TestClient):
    project_id = _create_project(client)
    _upload_and_index(client, project_id)
    checklist = _create_checklist(client, project_id)
    # The DO-01 detention item should surface the detention basin page.
    items = client.get(
        f"/api/v1/projects/{project_id}/checklists/{checklist['project_checklist_id']}/items"
    ).json()
    detention = next(i for i in items if i["item_code"] == "DO-01")
    response = client.post(
        f"/api/v1/projects/{project_id}/checklist-items/{detention['project_checklist_item_id']}/evidence-search",
        json={"query_text": "detention basin outlet"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["result_count"] >= 1
    excerpt = data["results"][0]["excerpt"]
    assert excerpt and len(excerpt) < len(PAGE_TEXT)


def test_checklist_evidence_search_no_indexed_pages(client: TestClient):
    project_id = _create_project(client)
    checklist = _create_checklist(client, project_id)
    item = _first_item(client, project_id, checklist["project_checklist_id"])
    response = client.post(
        f"/api/v1/projects/{project_id}/checklist-items/{item['project_checklist_item_id']}/evidence-search",
        json={},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["result_count"] == 0
    assert "No indexed page text" in data["message"]


def test_checklist_evidence_search_writes_audit_and_hides_paths(client: TestClient):
    project_id = _create_project(client)
    _upload_and_index(client, project_id)
    checklist = _create_checklist(client, project_id)
    item = _first_item(client, project_id, checklist["project_checklist_id"])
    client.post(
        f"/api/v1/projects/{project_id}/checklist-items/{item['project_checklist_item_id']}/evidence-search",
        json={"query_text": "detention basin"},
    )
    audit = client.get(f"/api/v1/projects/{project_id}/audit-events")
    types = [e["event_type"] for e in audit.json()]
    assert "checklist_evidence_search_performed" in types
    for event in audit.json():
        meta_blob = str(event.get("event_metadata") or {})
        assert PAGE_TEXT not in meta_blob
        assert "storage_path" not in meta_blob


# ---------------------------------------------------------------------------
# Evidence links
# ---------------------------------------------------------------------------


def test_link_evidence_to_checklist_item(client: TestClient):
    project_id = _create_project(client)
    document_id = _upload_and_index(client, project_id)
    checklist = _create_checklist(client, project_id)
    item = _first_item(client, project_id, checklist["project_checklist_id"])
    response = client.post(
        f"/api/v1/projects/{project_id}/checklist-items/{item['project_checklist_item_id']}/evidence-links",
        json={
            "document_id": document_id,
            "page_number": 1,
            "reviewer_note": "Detention basin shown on this page",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["document_id"] == document_id
    assert body["link_status"] == "reviewer_selected"


def test_link_evidence_unknown_document_404(client: TestClient):
    project_id = _create_project(client)
    checklist = _create_checklist(client, project_id)
    item = _first_item(client, project_id, checklist["project_checklist_id"])
    response = client.post(
        f"/api/v1/projects/{project_id}/checklist-items/{item['project_checklist_item_id']}/evidence-links",
        json={"document_id": "doc_missing"},
    )
    assert response.status_code == 404


def test_link_evidence_writes_audit_event(client: TestClient):
    project_id = _create_project(client)
    document_id = _upload_and_index(client, project_id)
    checklist = _create_checklist(client, project_id)
    item = _first_item(client, project_id, checklist["project_checklist_id"])
    client.post(
        f"/api/v1/projects/{project_id}/checklist-items/{item['project_checklist_item_id']}/evidence-links",
        json={"document_id": document_id, "page_number": 1},
    )
    audit = client.get(f"/api/v1/projects/{project_id}/audit-events")
    types = [e["event_type"] for e in audit.json()]
    assert "checklist_evidence_linked" in types


# ---------------------------------------------------------------------------
# Draft finding from checklist item
# ---------------------------------------------------------------------------


def test_create_draft_finding_from_checklist_item(client: TestClient):
    project_id = _create_project(client)
    document_id = _upload_and_index(client, project_id)
    checklist = _create_checklist(client, project_id)
    item = _first_item(client, project_id, checklist["project_checklist_id"])
    response = client.post(
        f"/api/v1/projects/{project_id}/checklist-items/{item['project_checklist_item_id']}/draft-finding",
        json={
            "title": "Detention basin outlet sizing needs reviewer confirmation",
            "risk_level": "high",
            "evidence_status": "missing_evidence",
            "reason_it_matters": "Affects downstream culvert capacity",
            "recommended_human_action": "Reviewer should request the outlet sizing",
            "document_id": document_id,
            "page_number": 1,
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    finding = body["finding"]
    assert finding["finding_origin"] == "checklist_review"
    assert finding["human_review_status"] == "draft"
    assert item["project_checklist_item_id"] in finding["related_checklist_items"]
    assert body["citation"]["document_id"] == document_id
    assert body["citation"]["citation_context"] == "checklist_evidence"
    assert body["checklist_item"]["review_status"] == "draft_finding_created"
    assert body["checklist_item"]["related_finding_id"] == finding["finding_id"]


def test_draft_finding_without_citation(client: TestClient):
    project_id = _create_project(client)
    checklist = _create_checklist(client, project_id)
    item = _first_item(client, project_id, checklist["project_checklist_id"])
    response = client.post(
        f"/api/v1/projects/{project_id}/checklist-items/{item['project_checklist_item_id']}/draft-finding",
        json={"title": "Submission completeness needs reviewer confirmation"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["citation"] is None


def test_draft_finding_writes_audit_event(client: TestClient):
    project_id = _create_project(client)
    checklist = _create_checklist(client, project_id)
    item = _first_item(client, project_id, checklist["project_checklist_id"])
    client.post(
        f"/api/v1/projects/{project_id}/checklist-items/{item['project_checklist_item_id']}/draft-finding",
        json={"title": "Draft finding from checklist"},
    )
    audit = client.get(f"/api/v1/projects/{project_id}/audit-events")
    types = [e["event_type"] for e in audit.json()]
    assert "checklist_draft_finding_created" in types


def test_draft_finding_rejects_prohibited_language(client: TestClient):
    project_id = _create_project(client)
    checklist = _create_checklist(client, project_id)
    item = _first_item(client, project_id, checklist["project_checklist_id"])
    response = client.post(
        f"/api/v1/projects/{project_id}/checklist-items/{item['project_checklist_item_id']}/draft-finding",
        json={"title": "Plan is approved and compliant"},
    )
    assert response.status_code == 422


def test_draft_finding_rejects_invalid_review_status(client: TestClient):
    project_id = _create_project(client)
    checklist = _create_checklist(client, project_id)
    item = _first_item(client, project_id, checklist["project_checklist_id"])
    response = client.post(
        f"/api/v1/projects/{project_id}/checklist-items/{item['project_checklist_item_id']}/draft-finding",
        json={"title": "Draft finding", "human_review_status": "resolved"},
    )
    assert response.status_code == 422


def test_no_final_decision_wording_in_checklist_responses(client: TestClient):
    project_id = _create_project(client)
    checklist = _create_checklist(client, project_id)
    item = _first_item(client, project_id, checklist["project_checklist_id"])
    response = client.post(
        f"/api/v1/projects/{project_id}/checklist-items/{item['project_checklist_item_id']}/draft-finding",
        json={"title": "Draft finding from checklist item"},
    )
    blob = response.text.lower()
    for word in PROHIBITED_FINAL_DECISION_WORDS:
        assert word not in blob
    for word in ("resolved", "closed", "noncompliant", "passes review"):
        assert word not in blob


# ---------------------------------------------------------------------------
# Regression
# ---------------------------------------------------------------------------


def test_list_checklists_unknown_project_404(client: TestClient):
    assert (
        client.get("/api/v1/projects/proj_missing/checklists").status_code == 404
    )


def test_get_checklist_404(client: TestClient):
    project_id = _create_project(client)
    response = client.get(
        f"/api/v1/projects/{project_id}/checklists/pcl_missing"
    )
    assert response.status_code == 404


def test_draft_finding_bad_document_id_422(client: TestClient):
    project_id = _create_project(client)
    checklist = _create_checklist(client, project_id)
    item = _first_item(client, project_id, checklist["project_checklist_id"])
    response = client.post(
        f"/api/v1/projects/{project_id}/checklist-items/{item['project_checklist_item_id']}/draft-finding",
        json={"title": "Draft finding", "document_id": "doc_missing"},
    )
    assert response.status_code == 422


def test_health_endpoint_still_works(client: TestClient):
    assert client.get("/health").status_code == 200


def test_brookside_demo_still_loads(client: TestClient):
    assert client.get(f"/api/v1/projects/{BROOKSIDE_ID}").status_code == 200
    assert client.get(f"/api/v1/projects/{BROOKSIDE_ID}/findings").status_code == 200
