"""Phase 8 review packet builder tests."""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.core.safety import ALLOWED_REVIEW_PACKET_ACTIONS

PROJECT_ID = "proj_brookside_meadows"

# Forbidden final-decision vocabulary that must not appear in statuses, action
# names, packet types, labels, or generated output.
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


@pytest.fixture(scope="module")
def packet(client: TestClient) -> dict:
    response = client.post(
        f"/api/v1/projects/{PROJECT_ID}/review-packets/generate"
    )
    assert response.status_code == 200
    return response.json()


def test_packet_generation_creates_sections(packet: dict) -> None:
    section_types = [s["section_type"] for s in packet["sections"]]
    for expected in [
        "executive_summary",
        "document_checklist",
        "plan_sheet_cad",
        "sheet_hotspots",
        "plan_consistency",
        "human_review_actions",
        "traceability",
        "limitations",
    ]:
        assert expected in section_types


def test_packet_generation_creates_items_from_sources(packet: dict) -> None:
    source_types: set[str] = set()
    for section in packet["sections"]:
        for item in section["items"]:
            source_types.add(item["source_type"])
    assert "finding" in source_types
    assert "plan_consistency_finding" in source_types
    assert "sheet_hotspot" in source_types
    assert "plan_sheet" in source_types
    assert "document" in source_types


def test_evidence_links_point_to_valid_entities(
    client: TestClient, packet: dict
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
        "cad_metadata": {
            m["cad_metadata_id"]
            for m in client.get(
                f"/api/v1/projects/{PROJECT_ID}/cad-metadata"
            ).json()
        },
        "plan_reference": {
            r["plan_reference_id"]
            for r in client.get(
                f"/api/v1/projects/{PROJECT_ID}/plan-references"
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
    for section in packet["sections"]:
        for item in section["items"]:
            for link in item["evidence_links"]:
                etype = link["evidence_type"]
                if etype in valid:
                    assert link["evidence_id"] in valid[etype], (
                        f"{etype} {link['evidence_id']} not a seeded entity"
                    )
                    checked += 1
    assert checked > 0


def test_traceability_matrix_fields(client: TestClient, packet: dict) -> None:
    pid = packet["packet_id"]
    result = client.get(f"/api/v1/review-packets/{pid}/traceability").json()
    assert result["total_rows"] > 0
    for row in result["rows"]:
        assert "source_type" in row and row["source_type"]
        assert "source_id" in row
        assert "evidence_type" in row and row["evidence_type"]
        assert "relationship" in row and row["relationship"]
        assert "item_id" in row and row["item_id"]


def test_print_view_includes_limitations(
    client: TestClient, packet: dict
) -> None:
    pid = packet["packet_id"]
    pv = client.get(f"/api/v1/review-packets/{pid}/print-view").json()
    assert "Professional Engineer" in pv["professional_limitations"]
    assert pv["draft_notice"]
    assert len(pv["sections"]) == 8


def test_summary_counts(client: TestClient, packet: dict) -> None:
    pid = packet["packet_id"]
    summary = client.get(f"/api/v1/review-packets/{pid}/summary").json()
    assert summary["total_sections"] == 8
    assert summary["total_items"] > 0
    assert summary["total_evidence_links"] > 0


def test_list_review_packets(client: TestClient, packet: dict) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}/review-packets")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def _first_finding_item(packet: dict) -> dict:
    for section in packet["sections"]:
        if section["section_type"] == "plan_consistency" and section["items"]:
            return section["items"][0]
    raise AssertionError("No plan consistency item found")


def test_reviewer_action_creation(client: TestClient, packet: dict) -> None:
    pid = packet["packet_id"]
    item = _first_finding_item(packet)
    response = client.post(
        f"/api/v1/review-packets/{pid}/items/{item['item_id']}/review-actions",
        json={
            "action_type": "needs_follow_up",
            "reviewer_note": "Confirm this with the applicant.",
            "reviewer_name": "Town Engineer",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["action"]["action_type"] == "needs_follow_up"
    assert body["item"]["reviewer_status"] == "needs_follow_up"


def test_item_status_update(client: TestClient, packet: dict) -> None:
    pid = packet["packet_id"]
    item = _first_finding_item(packet)
    response = client.patch(
        f"/api/v1/review-packets/{pid}/items/{item['item_id']}/status",
        json={"new_status": "reviewer_checked", "reviewer_note": "Looks fine."},
    )
    assert response.status_code == 200
    assert response.json()["reviewer_status"] == "reviewer_checked"


def test_stored_action_types_are_in_allowed_set(
    client: TestClient, packet: dict
) -> None:
    # Cleanup fix: a PATCH status update must record the target status as the
    # action_type, never a synthetic "status_update". Every stored reviewer
    # action_type must be in the allowed packet action set.
    from app.core.safety import ALLOWED_REVIEW_PACKET_ACTIONS
    from app.db import models
    from app.db.database import SessionLocal

    pid = packet["packet_id"]
    item = _first_finding_item(packet)
    client.patch(
        f"/api/v1/review-packets/{pid}/items/{item['item_id']}/status",
        json={"new_status": "needs_more_information", "reviewer_note": "More info."},
    )

    db = SessionLocal()
    try:
        actions = db.query(models.ReviewPacketReviewerAction).all()
        assert actions
        for action in actions:
            assert action.action_type in ALLOWED_REVIEW_PACKET_ACTIONS
            assert action.action_type != "status_update"
    finally:
        db.close()


def test_invalid_action_rejected(client: TestClient, packet: dict) -> None:
    pid = packet["packet_id"]
    item = _first_finding_item(packet)
    response = client.post(
        f"/api/v1/review-packets/{pid}/items/{item['item_id']}/review-actions",
        json={
            "action_type": "approve",
            "reviewer_note": "Attempting a prohibited action.",
            "reviewer_name": "Town Engineer",
        },
    )
    assert response.status_code == 422


def test_invalid_item_rejected(client: TestClient, packet: dict) -> None:
    pid = packet["packet_id"]
    response = client.post(
        f"/api/v1/review-packets/{pid}/items/item_missing/review-actions",
        json={
            "action_type": "needs_follow_up",
            "reviewer_note": "No such item.",
            "reviewer_name": "Town Engineer",
        },
    )
    assert response.status_code == 404


def test_invalid_status_rejected(client: TestClient, packet: dict) -> None:
    pid = packet["packet_id"]
    item = _first_finding_item(packet)
    response = client.patch(
        f"/api/v1/review-packets/{pid}/items/{item['item_id']}/status",
        json={"new_status": "approved"},
    )
    assert response.status_code == 422


def test_no_prohibited_vocabulary(client: TestClient, packet: dict) -> None:
    # Action names.
    for action in ALLOWED_REVIEW_PACKET_ACTIONS:
        assert not _has_forbidden(action)
    # Packet type and status.
    assert not _has_forbidden(packet["packet_type"])
    assert not _has_forbidden(packet["status"])
    # Sections, items, and evidence links.
    for section in packet["sections"]:
        assert not _has_forbidden(section["section_type"])
        assert not _has_forbidden(section["status"])
        assert not _has_forbidden(section["title"])
        for item in section["items"]:
            assert not _has_forbidden(item["item_type"])
            assert not _has_forbidden(item["reviewer_status"])
            assert not _has_forbidden(item["severity"])
            assert not _has_forbidden(item["title"])
            assert not _has_forbidden(item["description"])
            for link in item["evidence_links"]:
                assert not _has_forbidden(link["relationship"])
                assert not _has_forbidden(link["label"])
    # Print view generated text.
    pv = client.get(
        f"/api/v1/review-packets/{packet['packet_id']}/print-view"
    ).json()
    assert not _has_forbidden(pv["professional_limitations"])
    assert not _has_forbidden(pv["draft_notice"])
    assert not _has_forbidden(pv["limitations_note"])


def test_audit_events_written(client: TestClient, packet: dict) -> None:
    pid = packet["packet_id"]
    # Trigger the read side effects and an action.
    client.get(f"/api/v1/review-packets/{pid}")
    client.get(f"/api/v1/review-packets/{pid}/traceability")
    client.get(f"/api/v1/review-packets/{pid}/print-view")
    events = client.get(
        f"/api/v1/projects/{PROJECT_ID}/audit-events"
    ).json()
    types = {e["event_type"] for e in events}
    assert "review_packet_generated" in types
    assert "review_packet_viewed" in types
    assert "review_packet_traceability_requested" in types
    assert "review_packet_print_view_requested" in types
    assert "review_packet_item_action_recorded" in types
    assert "review_packet_item_status_updated" in types
