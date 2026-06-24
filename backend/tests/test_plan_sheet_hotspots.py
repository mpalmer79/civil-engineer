"""Phase 7 plan sheet hotspot, sheet viewer, and plan review action tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.safety import (
    ALLOWED_PLAN_REVIEW_ACTIONS,
    contains_prohibited_language,
)

PROJECT_ID = "proj_brookside_meadows"


def test_sheet_hotspots_are_seeded(client: TestClient) -> None:
    response = client.get(f"/api/v1/projects/{PROJECT_ID}/sheet-hotspots")
    assert response.status_code == 200
    hotspots = response.json()
    assert len(hotspots) == 8


def test_hotspot_summary(client: TestClient) -> None:
    summary = client.get(
        f"/api/v1/projects/{PROJECT_ID}/sheet-hotspots/summary"
    ).json()
    assert summary["total_hotspots"] == 8
    assert summary["hotspots_requiring_human_review"] == 8
    assert summary["sheets_with_hotspots"] >= 1


def test_hotspot_coordinates_within_bounds(client: TestClient) -> None:
    hotspots = client.get(
        f"/api/v1/projects/{PROJECT_ID}/sheet-hotspots"
    ).json()
    for h in hotspots:
        assert 0.0 <= h["x_percent"] <= 100.0
        assert 0.0 <= h["y_percent"] <= 100.0
        assert 0.0 < h["width_percent"] <= 100.0
        assert 0.0 < h["height_percent"] <= 100.0
        # The hotspot rectangle stays on the sheet preview.
        assert h["x_percent"] + h["width_percent"] <= 100.0
        assert h["y_percent"] + h["height_percent"] <= 100.0


def test_hotspot_references_point_to_existing_entities(
    client: TestClient,
) -> None:
    hotspots = client.get(
        f"/api/v1/projects/{PROJECT_ID}/sheet-hotspots"
    ).json()
    sheet_ids = {
        s["sheet_id"]
        for s in client.get(
            f"/api/v1/projects/{PROJECT_ID}/plan-sheets"
        ).json()
    }
    reference_ids = {
        r["plan_reference_id"]
        for r in client.get(
            f"/api/v1/projects/{PROJECT_ID}/plan-references"
        ).json()
    }
    cad_ids = {
        c["cad_metadata_id"]
        for c in client.get(
            f"/api/v1/projects/{PROJECT_ID}/cad-metadata"
        ).json()
    }
    finding_ids = {
        f["plan_finding_id"]
        for f in client.get(
            f"/api/v1/projects/{PROJECT_ID}/plan-consistency-findings"
        ).json()
    }
    document_ids = {
        d["documentId"] if "documentId" in d else d["document_id"]
        for d in client.get(
            f"/api/v1/projects/{PROJECT_ID}/documents"
        ).json()
    }
    checklist_ids = {
        c["checklist_item_id"]
        for c in client.get(
            f"/api/v1/projects/{PROJECT_ID}/checklist"
        ).json()
    }

    for h in hotspots:
        assert h["sheet_id"] in sheet_ids
        for rid in h["related_plan_reference_ids"]:
            assert rid in reference_ids
        for cid in h["related_cad_metadata_ids"]:
            assert cid in cad_ids
        for fid in h["related_plan_finding_ids"]:
            assert fid in finding_ids
        for did in h["related_document_ids"]:
            assert did in document_ids
        for chk in h["related_checklist_item_ids"]:
            assert chk in checklist_ids


def test_hotspots_for_sheet(client: TestClient) -> None:
    response = client.get("/api/v1/plan-sheets/sheet_c30/sheet-hotspots")
    assert response.status_code == 200
    hotspots = response.json()
    assert len(hotspots) >= 1
    assert all(h["sheet_id"] == "sheet_c30" for h in hotspots)


def test_get_single_hotspot(client: TestClient) -> None:
    response = client.get("/api/v1/sheet-hotspots/hs_c30_basin_conflict")
    assert response.status_code == 200
    assert response.json()["hotspot_type"] == "basin_label_conflict"


def test_sheet_viewer_context(client: TestClient) -> None:
    response = client.get("/api/v1/plan-sheets/sheet_c30/viewer-context")
    assert response.status_code == 200
    ctx = response.json()
    assert ctx["sheet"]["sheet_id"] == "sheet_c30"
    assert len(ctx["hotspots"]) >= 1
    assert len(ctx["plan_references"]) >= 1
    assert len(ctx["cad_metadata"]) >= 1
    assert len(ctx["plan_consistency_findings"]) >= 1
    assert "seeded" in ctx["preview_note"].lower()


def test_viewer_context_unknown_sheet(client: TestClient) -> None:
    response = client.get("/api/v1/plan-sheets/sheet_missing/viewer-context")
    assert response.status_code == 404


def test_create_plan_consistency_review_action(client: TestClient) -> None:
    fid = "plan_find_pref_oem_wet_basin"
    response = client.post(
        f"/api/v1/plan-consistency-findings/{fid}/review-actions",
        json={
            "action": "needs_follow_up",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "Confirm the maintenance party for the basin.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["action"]["action"] == "needs_follow_up"
    assert body["finding"]["status"] == "needs_follow_up"
    assert body["action"]["previous_status"] == "requires_human_review"


def test_review_action_reviewer_confirmed(client: TestClient) -> None:
    fid = "plan_find_pref_escp_c51"
    response = client.post(
        f"/api/v1/plan-consistency-findings/{fid}/review-actions",
        json={
            "action": "reviewer_confirmed",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "Sequence notes clarified in resubmittal.",
        },
    )
    assert response.status_code == 200
    assert response.json()["finding"]["status"] == "reviewer_confirmed"


def test_review_action_requires_note(client: TestClient) -> None:
    fid = "plan_find_pref_rfi_pipe_p12"
    response = client.post(
        f"/api/v1/plan-consistency-findings/{fid}/review-actions",
        json={
            "action": "needs_more_information",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "   ",
        },
    )
    assert response.status_code == 422


def test_review_action_rejects_unknown_action(client: TestClient) -> None:
    fid = "plan_find_pref_rfi_pipe_p12"
    response = client.post(
        f"/api/v1/plan-consistency-findings/{fid}/review-actions",
        json={
            "action": "approve",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "Attempting a prohibited action.",
        },
    )
    assert response.status_code == 422


def test_review_action_unknown_finding(client: TestClient) -> None:
    response = client.post(
        "/api/v1/plan-consistency-findings/plan_find_missing/review-actions",
        json={
            "action": "needs_follow_up",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "No such finding.",
        },
    )
    assert response.status_code == 404


def test_list_review_actions(client: TestClient) -> None:
    fid = "plan_find_pref_oem_wet_basin"
    client.post(
        f"/api/v1/plan-consistency-findings/{fid}/review-actions",
        json={
            "action": "needs_more_information",
            "reviewer_name": "Town Engineer",
            "reviewer_note": "Request the recorded maintenance agreement.",
        },
    )
    per_finding = client.get(
        f"/api/v1/plan-consistency-findings/{fid}/review-actions"
    ).json()
    assert len(per_finding) >= 1
    project_level = client.get(
        f"/api/v1/projects/{PROJECT_ID}/plan-consistency-review-actions"
    ).json()
    assert len(project_level) >= 1


def test_no_prohibited_vocabulary(client: TestClient) -> None:
    # No action name is a prohibited final-decision word, and there is no
    # approve action.
    assert "approve" not in ALLOWED_PLAN_REVIEW_ACTIONS
    assert "approved" not in ALLOWED_PLAN_REVIEW_ACTIONS
    for action in ALLOWED_PLAN_REVIEW_ACTIONS:
        assert not contains_prohibited_language(action)

    # No hotspot type, severity, label, or description carries prohibited
    # final-decision vocabulary.
    hotspots = client.get(
        f"/api/v1/projects/{PROJECT_ID}/sheet-hotspots"
    ).json()
    for h in hotspots:
        assert not contains_prohibited_language(h["hotspot_type"])
        assert not contains_prohibited_language(h["severity"])
        assert not contains_prohibited_language(h["label"])
        assert not contains_prohibited_language(h["description"])


def test_hotspot_audit_events_written(client: TestClient) -> None:
    # Requesting a viewer context and inspecting a hotspot write audit events.
    client.get("/api/v1/plan-sheets/sheet_c40/viewer-context")
    client.get("/api/v1/sheet-hotspots/hs_c40_pipe_p12")
    events = client.get(
        f"/api/v1/projects/{PROJECT_ID}/audit-events"
    ).json()
    types = {e["event_type"] for e in events}
    assert "sheet_hotspot_review_data_seeded" in types
    assert "sheet_viewer_context_requested" in types
    assert "sheet_hotspot_inspected" in types
    assert "plan_consistency_review_action_recorded" in types
    assert "plan_finding_status_updated" in types
