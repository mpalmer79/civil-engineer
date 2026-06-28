"""Tests for Phase 4B traceability packet context and reviewer review actions.

These cover inline review packet context on project traceability rows, reviewer
review actions on a single row, handoff readiness signals, and the packet handoff
print view traceability state. Review actions are append-only and never mutate the
source checklist, evidence, finding, workflow, or packet records.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.safety import PROHIBITED_FINAL_DECISION_WORDS
from app.db import models
from app.db.database import SessionLocal
from app.services.checklist_review_service import STARTER_RULE_PACK_ID
from tests.test_pdf_indexing import _make_pdf

PAGE_TEXT = (
    "Stormwater detention basin outlet structure design for the proposed "
    "subdivision. The outlet structure limits discharge to the downstream "
    "culvert during the design storm event for the contributing watershed."
)


def _create_project(client: TestClient, name: str) -> str:
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


def _linked_project(client: TestClient, name: str) -> tuple[str, str]:
    """Create a project with a checklist and one linked evidence row.

    Returns (project_id, linked_checklist_item_id).
    """

    pid = _create_project(client, name)
    checklist = client.post(
        f"/api/v1/projects/{pid}/checklists/from-rule-pack",
        json={"rule_pack_id": STARTER_RULE_PACK_ID},
    )
    assert checklist.status_code == 201, checklist.text
    checklist_id = checklist.json()["project_checklist_id"]
    items = client.get(
        f"/api/v1/projects/{pid}/checklists/{checklist_id}/items"
    ).json()
    assert len(items) >= 2
    item_id = items[0]["project_checklist_item_id"]

    upload = client.post(
        f"/api/v1/projects/{pid}/documents/upload",
        files={"file": ("plan.pdf", _make_pdf([PAGE_TEXT]), "application/pdf")},
        data={"document_type": "stormwater_report"},
    )
    assert upload.status_code == 201, upload.text
    document_id = upload.json()["document_id"]
    index = client.post(
        f"/api/v1/projects/{pid}/documents/{document_id}/index-pdf"
    )
    assert index.status_code == 200, index.text
    link = client.post(
        f"/api/v1/projects/{pid}/checklist-items/{item_id}/evidence-links",
        json={"document_id": document_id, "page_number": 1},
    )
    assert link.status_code in (200, 201), link.text
    return pid, item_id


def _traceability(client: TestClient, pid: str) -> dict:
    response = client.get(f"/api/v1/projects/{pid}/traceability")
    assert response.status_code == 200, response.text
    return response.json()


def _linked_row(data: dict, item_id: str) -> dict:
    rows = [
        r
        for r in data["rows"]
        if r["checklist_item_id"] == item_id
        and r["relationship_type"] == "linked_evidence"
    ]
    assert rows, "expected a linked evidence row"
    return rows[0]


def _action_body(row: dict, action_type: str, note: str | None = None) -> dict:
    body = {
        "action_type": action_type,
        "checklist_item_id": row["checklist_item_id"],
        "evidence_citation_id": row["evidence_citation_id"],
        "finding_id": row["finding_id"],
        "relationship_type": row["relationship_type"],
        "created_by": "Town Engineer",
    }
    if note is not None:
        body["reviewer_note"] = note
    return body


# --- Section 3: reviewer review actions -------------------------------------


def test_reviewer_can_record_and_read_action_history(client: TestClient) -> None:
    pid, item_id = _linked_project(client, "Trace Review Project")
    row = _linked_row(_traceability(client, pid), item_id)
    key = row["traceability_row_key"]

    confirm = client.post(
        f"/api/v1/projects/{pid}/traceability/{key}/review-actions",
        json=_action_body(row, "reviewer_confirmed_link", "Link is useful for review."),
    )
    assert confirm.status_code == 201, confirm.text
    assert confirm.json()["action_type"] == "reviewer_confirmed_link"

    more = client.post(
        f"/api/v1/projects/{pid}/traceability/{key}/review-actions",
        json=_action_body(row, "needs_more_information"),
    )
    assert more.status_code == 201, more.text

    history = client.get(
        f"/api/v1/projects/{pid}/traceability/{key}/review-actions"
    )
    assert history.status_code == 200, history.text
    body = history.json()
    assert body["total_actions"] == 2
    # History is ordered oldest first; the latest reflects the most recent action.
    assert body["actions"][0]["action_type"] == "reviewer_confirmed_link"
    assert body["actions"][-1]["action_type"] == "needs_more_information"

    # The latest action appears inline on the traceability row.
    latest = _linked_row(_traceability(client, pid), item_id)["latest_review_action"]
    assert latest["action_type"] == "needs_more_information"


def test_reviewer_can_request_more_information(client: TestClient) -> None:
    pid, item_id = _linked_project(client, "Trace More Info Project")
    row = _linked_row(_traceability(client, pid), item_id)
    response = client.post(
        f"/api/v1/projects/{pid}/traceability/{row['traceability_row_key']}/review-actions",
        json=_action_body(row, "needs_more_information", "Need the outlet detail sheet."),
    )
    assert response.status_code == 201, response.text
    assert response.json()["reviewer_note"] == "Need the outlet detail sheet."


def test_rejecting_a_link_does_not_delete_source_data(client: TestClient) -> None:
    pid, item_id = _linked_project(client, "Trace Reject Project")
    before = _traceability(client, pid)
    row = _linked_row(before, item_id)
    findings_before = client.get(f"/api/v1/projects/{pid}/findings").json()

    response = client.post(
        f"/api/v1/projects/{pid}/traceability/{row['traceability_row_key']}/review-actions",
        json=_action_body(row, "link_rejected", "Not the right evidence."),
    )
    assert response.status_code == 201, response.text

    after = _traceability(client, pid)
    row_after = _linked_row(after, item_id)
    # The source link, its document, and the page reference all remain.
    assert row_after["document_id"] == row["document_id"]
    assert row_after["page_number"] == row["page_number"]
    assert row_after["evidence_citation_id"] == row["evidence_citation_id"]
    # No findings were created or removed by the review action.
    findings_after = client.get(f"/api/v1/projects/{pid}/findings").json()
    assert len(findings_before) == len(findings_after)
    # The row still carries its source data and now shows the rejection.
    assert row_after["latest_review_action"]["action_type"] == "link_rejected"


def test_prohibited_wording_and_unknown_action_are_rejected(
    client: TestClient,
) -> None:
    pid, item_id = _linked_project(client, "Trace Banned Project")
    row = _linked_row(_traceability(client, pid), item_id)
    key = row["traceability_row_key"]

    banned_note = client.post(
        f"/api/v1/projects/{pid}/traceability/{key}/review-actions",
        json=_action_body(row, "reviewer_confirmed_link", "Requirement is approved."),
    )
    assert banned_note.status_code == 422, banned_note.text

    bad_action = client.post(
        f"/api/v1/projects/{pid}/traceability/{key}/review-actions",
        json=_action_body(row, "approve"),
    )
    assert bad_action.status_code == 422, bad_action.text

    # Neither rejected request was stored.
    history = client.get(
        f"/api/v1/projects/{pid}/traceability/{key}/review-actions"
    ).json()
    assert history["total_actions"] == 0


def test_review_action_404_for_unknown_project(client: TestClient) -> None:
    response = client.post(
        "/api/v1/projects/proj_missing/traceability/trk_x/review-actions",
        json={"action_type": "needs_review"},
    )
    assert response.status_code == 404


# --- Section 5: handoff readiness ------------------------------------------


def test_handoff_readiness_counts_align(client: TestClient) -> None:
    pid, item_id = _linked_project(client, "Trace Readiness Project")
    data = _traceability(client, pid)
    readiness = data["handoff_readiness"]
    assert readiness["total_traceability_rows"] == len(data["rows"])
    assert readiness["rows_with_reviewer_action"] == 0
    assert readiness["ready_for_reviewer_handoff_count"] == 0
    # There is at least one unlinked checklist item in the starter pack.
    assert readiness["rows_without_linked_evidence"] >= 1

    row = _linked_row(data, item_id)
    confirm = client.post(
        f"/api/v1/projects/{pid}/traceability/{row['traceability_row_key']}/review-actions",
        json=_action_body(row, "reviewer_confirmed_link"),
    )
    assert confirm.status_code == 201, confirm.text

    updated = _traceability(client, pid)["handoff_readiness"]
    assert updated["rows_with_reviewer_action"] == 1
    assert updated["ready_for_reviewer_handoff_count"] == 1


def test_traceability_readiness_has_no_banned_language(client: TestClient) -> None:
    pid, _ = _linked_project(client, "Trace Language Project")
    response = client.get(f"/api/v1/projects/{pid}/traceability")
    blob = response.text.lower()
    for word in PROHIBITED_FINAL_DECISION_WORDS:
        assert word.lower() not in blob


# --- Section 2 + 6: inline packet context and packet handoff view ----------


def _insert_packet_for_checklist_item(project_id: str, item_id: str) -> str:
    """Insert a minimal review packet that links to a checklist item.

    Returns the packet id. Uses a direct session so the packet context is
    deterministic regardless of the project's findings.
    """

    session = SessionLocal()
    try:
        suffix = project_id[-8:]
        packet_id = f"pkt_trace_{suffix}"
        section_id = f"sec_trace_{suffix}"
        packet_item_id = f"item_trace_{suffix}"
        session.add(
            models.ReviewPacket(
                packet_id=packet_id,
                project_id=project_id,
                title="Stormwater review packet (draft)",
                packet_type="review_support_draft",
                status="draft",
                summary="Draft packet for traceability test.",
                generated_from_phase="phase_4b_test",
                created_by="system",
                limitations_note="Draft review-support packet.",
            )
        )
        session.add(
            models.ReviewPacketSection(
                section_id=section_id,
                packet_id=packet_id,
                title="Document and checklist findings",
                section_type="document_checklist",
                display_order=0,
                summary="Checklist-linked review-support items.",
                status="draft",
                requires_human_review=True,
            )
        )
        session.add(
            models.ReviewPacketItem(
                item_id=packet_item_id,
                packet_id=packet_id,
                section_id=section_id,
                item_type="finding",
                title="Detention basin outlet detail",
                description="Outlet detail needs reviewer confirmation.",
                severity="medium",
                source_type="finding",
                source_id="find_trace_test",
                reviewer_status="draft",
                reviewer_note=None,
                requires_human_review=True,
                display_order=0,
            )
        )
        session.add(
            models.ReviewPacketEvidenceLink(
                evidence_link_id=f"evl_trace_{suffix}",
                packet_id=packet_id,
                item_id=packet_item_id,
                evidence_type="checklist_item",
                evidence_id=item_id,
                relationship="checklist_item",
                label="Outlet checklist item",
            )
        )
        session.commit()
        return packet_id
    finally:
        session.close()


def test_traceability_row_includes_inline_packet_context(
    client: TestClient,
) -> None:
    pid, item_id = _linked_project(client, "Trace Packet Context Project")
    packet_id = _insert_packet_for_checklist_item(pid, item_id)

    row = _linked_row(_traceability(client, pid), item_id)
    assert row["packet_context_count"] >= 1
    contexts = row["packet_contexts"]
    assert any(c["review_packet_id"] == packet_id for c in contexts)
    ctx = next(c for c in contexts if c["review_packet_id"] == packet_id)
    assert ctx["review_packet_item_id"].startswith("item_trace_")
    assert ctx["packet_item_status"] == "draft"
    assert ctx["packet_source_link"]["type"] == "review_packet"


def test_row_without_packet_is_reported_honestly(client: TestClient) -> None:
    pid, item_id = _linked_project(client, "Trace No Packet Project")
    row = _linked_row(_traceability(client, pid), item_id)
    assert row["packet_context_count"] == 0
    assert row["packet_contexts"] == []


def test_packet_print_view_includes_traceability_review_state(
    client: TestClient,
) -> None:
    pid, item_id = _linked_project(client, "Trace Print View Project")
    packet_id = _insert_packet_for_checklist_item(pid, item_id)

    first = client.get(f"/api/v1/review-packets/{packet_id}/print-view")
    assert first.status_code == 200, first.text
    data = first.json()
    # Draft notice and professional limitations remain visible.
    assert data["draft_notice"]
    assert data["professional_limitations"]
    trace_rows = data["traceability_review_rows"]
    assert trace_rows, "expected packet traceability review rows"
    target = next(
        r for r in trace_rows if r["checklist_title"] == _linked_row(
            _traceability(client, pid), item_id
        )["checklist_title"]
    )
    assert target["requires_reviewer_confirmation"] is True
    assert target["review_action_type"] is None

    # After a reviewer action the print view reflects the review state.
    row = _linked_row(_traceability(client, pid), item_id)
    confirm = client.post(
        f"/api/v1/projects/{pid}/traceability/{row['traceability_row_key']}/review-actions",
        json=_action_body(row, "reviewer_confirmed_link"),
    )
    assert confirm.status_code == 201, confirm.text

    second = client.get(
        f"/api/v1/review-packets/{packet_id}/print-view"
    ).json()
    updated = next(
        r
        for r in second["traceability_review_rows"]
        if r["traceability_row_key"] == row["traceability_row_key"]
    )
    assert updated["requires_reviewer_confirmation"] is False
    assert updated["review_action_type"] == "reviewer_confirmed_link"
