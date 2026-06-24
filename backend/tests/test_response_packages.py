"""Phase 10 external review response package tests."""

from __future__ import annotations

import re
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.safety import (
    ALLOWED_RESPONSE_ACTIONS,
    ALLOWED_RESPONSE_ITEM_STATUSES,
    ALLOWED_RESPONSE_PACKAGE_STATUSES,
)
from app.services.response_package_service import select_source_workflow_items

PROJECT_ID = "proj_brookside_meadows"

FORBIDDEN_WORDS = [
    "approved",
    "certified",
    "verified",
    "passed",
    "failed",
    "compliant",
    "noncompliant",
    "safe",
    "unsafe",
    "design validated",
]
_FORBIDDEN_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in FORBIDDEN_WORDS) + r")\b"
)


def _has_forbidden(text: str | None) -> bool:
    if not text:
        return False
    return bool(_FORBIDDEN_RE.search(text.lower()))


def _mark_some_ready_for_handoff(client: TestClient, count: int = 3) -> list[str]:
    items = client.get(
        f"/api/v1/projects/{PROJECT_ID}/workflow-board"
    ).json()
    marked: list[str] = []
    for item in items:
        if len(marked) >= count:
            break
        wid = item["workflowItemId"] if "workflowItemId" in item else item["workflow_item_id"]
        res = client.patch(
            f"/api/v1/workflow-items/{wid}/status",
            json={"new_status": "ready_for_handoff", "reviewer_name": "Town Engineer"},
        )
        if res.status_code == 200:
            marked.append(wid)
    return marked


@pytest.fixture(scope="module")
def package(client: TestClient) -> dict:
    _mark_some_ready_for_handoff(client, 3)
    response = client.post(
        f"/api/v1/projects/{PROJECT_ID}/response-packages/generate"
    )
    assert response.status_code == 200
    return response.json()


def test_select_source_workflow_items_tiers() -> None:
    # Tier 1: ready_for_handoff items win.
    ready = SimpleNamespace(
        status="ready_for_handoff", requires_human_review=True, section_type="x"
    )
    follow = SimpleNamespace(
        status="needs_follow_up", requires_human_review=True, section_type="x"
    )
    selected, fallback = select_source_workflow_items([ready, follow])
    assert selected == [ready]
    assert fallback is False

    # Tier 2: no ready items, fall back to follow-up or more-information items.
    selected, fallback = select_source_workflow_items([follow])
    assert selected == [follow]
    assert fallback is True

    # Tier 3: only draft items remain, defensive fallback still returns them.
    draft = SimpleNamespace(
        status="draft", requires_human_review=True, section_type="x"
    )
    selected, fallback = select_source_workflow_items([draft])
    assert selected == [draft]
    assert fallback is True

    # Limitations and excluded items are never promoted.
    lim = SimpleNamespace(
        status="ready_for_handoff",
        requires_human_review=True,
        section_type="limitations",
    )
    excluded = SimpleNamespace(
        status="excluded_from_packet", requires_human_review=True, section_type="x"
    )
    selected, _ = select_source_workflow_items([lim, excluded, draft])
    assert lim not in selected
    assert excluded not in selected


def test_generation_creates_sections(package: dict) -> None:
    section_types = [s["section_type"] for s in package["sections"]]
    for expected in [
        "opening_summary",
        "attachments",
        "limitations_and_review_boundary",
    ]:
        assert expected in section_types
    # At least one topical demand section is present.
    demand = {
        "requested_revisions",
        "missing_information",
        "plan_sheet_items",
        "stormwater_items",
        "erosion_control_items",
        "wetland_buffer_items",
    }
    assert demand.intersection(section_types)


def test_items_link_back_to_workflow_and_packet(package: dict) -> None:
    linked = 0
    for section in package["sections"]:
        if section["section_type"] in {
            "opening_summary",
            "attachments",
            "limitations_and_review_boundary",
        }:
            continue
        for item in section["items"]:
            assert item["workflow_item_id"]
            if item["packet_item_id"]:
                linked += 1
    assert linked > 0


def test_evidence_links_point_to_valid_entities(
    client: TestClient, package: dict
) -> None:
    valid: dict[str, set[str]] = {
        "document": {
            d["document_id"]
            for d in client.get(
                f"/api/v1/projects/{PROJECT_ID}/documents"
            ).json()
        },
        "checklist_item": {
            c["checklist_item_id"]
            for c in client.get(
                f"/api/v1/projects/{PROJECT_ID}/checklist"
            ).json()
        },
        "plan_sheet": {
            s["sheet_id"]
            for s in client.get(
                f"/api/v1/projects/{PROJECT_ID}/plan-sheets"
            ).json()
        },
        "plan_consistency_finding": {
            f["plan_finding_id"]
            for f in client.get(
                f"/api/v1/projects/{PROJECT_ID}/plan-consistency-findings"
            ).json()
        },
    }
    checked = 0
    for section in package["sections"]:
        for item in section["items"]:
            for link in item["evidence_links"]:
                etype = link["evidence_type"]
                if etype in valid:
                    assert link["evidence_id"] in valid[etype], (
                        f"{etype} {link['evidence_id']} not a seeded entity"
                    )
                    checked += 1
    assert checked > 0


def test_attachment_checklist(client: TestClient, package: dict) -> None:
    pid = package["response_package_id"]
    attachments = client.get(
        f"/api/v1/response-packages/{pid}/attachments"
    ).json()
    assert len(attachments) >= 1
    types = {a["attachment_type"] for a in attachments}
    assert "review_support_summary" in types


def test_print_view_includes_limitations(
    client: TestClient, package: dict
) -> None:
    pid = package["response_package_id"]
    pv = client.get(f"/api/v1/response-packages/{pid}/print-view").json()
    assert "Professional Engineer" in pv["external_communication_boundary"]
    assert pv["draft_notice"]
    assert pv["limitations_note"]
    assert len(pv["signoff_checklist"]) >= 1
    # The sign-off checklist confirms human review is still required.
    labels = " ".join(c["label"].lower() for c in pv["signoff_checklist"])
    assert "human review" in labels


def test_draft_text_avoids_prohibited_wording(package: dict) -> None:
    for section in package["sections"]:
        for item in section["items"]:
            assert not _has_forbidden(item["draft_text"]), item["draft_text"]


def test_package_status_update(client: TestClient, package: dict) -> None:
    pid = package["response_package_id"]
    response = client.patch(
        f"/api/v1/response-packages/{pid}/status",
        json={"new_status": "reviewer_checked", "reviewer_note": "Looks reasonable."},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "reviewer_checked"


def _first_demand_item(package: dict) -> dict:
    for section in package["sections"]:
        if section["section_type"] not in {
            "opening_summary",
            "attachments",
            "limitations_and_review_boundary",
        } and section["items"]:
            return section["items"][0]
    raise AssertionError("No demand item found")


def test_item_status_update(client: TestClient, package: dict) -> None:
    pid = package["response_package_id"]
    item = _first_demand_item(package)
    response = client.patch(
        f"/api/v1/response-packages/{pid}/items/{item['item_id']}/status",
        json={"new_status": "included", "reviewer_note": "Include this item."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "included"


def test_item_draft_text_update(client: TestClient, package: dict) -> None:
    pid = package["response_package_id"]
    item = _first_demand_item(package)
    response = client.patch(
        f"/api/v1/response-packages/{pid}/items/{item['item_id']}/draft-text",
        json={
            "draft_text": "Please provide the revised drainage report for review.",
            "reviewer_name": "Town Engineer",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["draft_text"].startswith("Please provide")
    assert body["status"] == "needs_revision"


def test_note_creation(client: TestClient, package: dict) -> None:
    pid = package["response_package_id"]
    item = _first_demand_item(package)
    response = client.post(
        f"/api/v1/response-packages/{pid}/items/{item['item_id']}/notes",
        json={
            "reviewer_note": "Discuss this item with the applicant first.",
            "reviewer_name": "Town Engineer",
        },
    )
    assert response.status_code == 200
    assert response.json()["action_type"] == "note_added"


def test_invalid_status_rejected(client: TestClient, package: dict) -> None:
    pid = package["response_package_id"]
    item = _first_demand_item(package)
    # Prohibited final-decision status on the package.
    assert (
        client.patch(
            f"/api/v1/response-packages/{pid}/status",
            json={"new_status": "approved"},
        ).status_code
        == 422
    )
    # draft is the seeded status, not a manual package transition.
    assert (
        client.patch(
            f"/api/v1/response-packages/{pid}/status",
            json={"new_status": "draft"},
        ).status_code
        == 422
    )
    # Prohibited final-decision status on an item.
    assert (
        client.patch(
            f"/api/v1/response-packages/{pid}/items/{item['item_id']}/status",
            json={"new_status": "verified"},
        ).status_code
        == 422
    )


def test_draft_text_prohibited_wording_rejected(
    client: TestClient, package: dict
) -> None:
    pid = package["response_package_id"]
    item = _first_demand_item(package)
    response = client.patch(
        f"/api/v1/response-packages/{pid}/items/{item['item_id']}/draft-text",
        json={
            "draft_text": "This plan is approved and the design is compliant.",
            "reviewer_name": "Town Engineer",
        },
    )
    assert response.status_code == 422


def test_missing_package_rejected(client: TestClient) -> None:
    assert (
        client.get("/api/v1/response-packages/resp_missing").status_code == 404
    )
    assert (
        client.patch(
            "/api/v1/response-packages/resp_missing/status",
            json={"new_status": "reviewer_checked"},
        ).status_code
        == 404
    )


def test_history(client: TestClient, package: dict) -> None:
    pid = package["response_package_id"]
    history = client.get(
        f"/api/v1/response-packages/{pid}/history"
    ).json()
    action_types = {a["action_type"] for a in history["actions"]}
    assert "package_generated" in action_types
    for action in history["actions"]:
        assert action["action_type"] in ALLOWED_RESPONSE_ACTIONS


def test_summary_counts(client: TestClient, package: dict) -> None:
    pid = package["response_package_id"]
    summary = client.get(
        f"/api/v1/response-packages/{pid}/summary"
    ).json()
    assert summary["total_items"] > 0
    assert summary["total_sections"] > 0
    assert summary["total_attachments"] > 0


def test_no_prohibited_vocabulary(client: TestClient, package: dict) -> None:
    for status in ALLOWED_RESPONSE_PACKAGE_STATUSES:
        assert not _has_forbidden(status)
    for status in ALLOWED_RESPONSE_ITEM_STATUSES:
        assert not _has_forbidden(status)
    for action in ALLOWED_RESPONSE_ACTIONS:
        assert not _has_forbidden(action)
    assert not _has_forbidden(package["status"])
    assert not _has_forbidden(package["summary"])
    assert not _has_forbidden(package["audience_type"])
    for section in package["sections"]:
        assert not _has_forbidden(section["section_type"])
        assert not _has_forbidden(section["title"])
        assert not _has_forbidden(section["summary"])
        for item in section["items"]:
            assert not _has_forbidden(item["title"])
            assert not _has_forbidden(item["draft_text"])
            assert not _has_forbidden(item["status"])
            assert not _has_forbidden(item["severity"])
    pid = package["response_package_id"]
    pv = client.get(f"/api/v1/response-packages/{pid}/print-view").json()
    assert not _has_forbidden(pv["external_communication_boundary"])
    assert not _has_forbidden(pv["draft_notice"])
    assert not _has_forbidden(pv["limitations_note"])


def test_audit_events_written(client: TestClient, package: dict) -> None:
    pid = package["response_package_id"]
    client.get(f"/api/v1/response-packages/{pid}")
    client.get(f"/api/v1/response-packages/{pid}/print-view")
    client.get(f"/api/v1/response-packages/{pid}/attachments")
    client.get(f"/api/v1/response-packages/{pid}/history")
    events = client.get(
        f"/api/v1/projects/{PROJECT_ID}/audit-events"
    ).json()
    types = {e["event_type"] for e in events}
    assert "response_package_generated" in types
    assert "response_package_viewed" in types
    assert "response_package_print_view_requested" in types
    assert "response_package_attachments_viewed" in types
    assert "response_package_history_requested" in types
    assert "response_package_status_updated" in types
    assert "response_item_status_updated" in types
    assert "response_item_draft_text_updated" in types
    assert "response_package_note_added" in types


def test_idempotent_generation(client: TestClient) -> None:
    # Defined last: regeneration rebuilds the package and replaces its id, so it
    # must run after the tests that rely on the module fixture's package id.
    first = client.post(
        f"/api/v1/projects/{PROJECT_ID}/response-packages/generate"
    )
    assert first.status_code == 200
    packages = client.get(
        f"/api/v1/projects/{PROJECT_ID}/response-packages"
    ).json()
    # Generation rebuilds: only one package remains for the project.
    assert len(packages) == 1
