"""Deterministic mock AI provider.

The mock provider returns fixed, schema-valid draft findings for the checklist
items tied to the Brookside Meadows planted issues. It uses the chunk ids from
the retrieved evidence so source citations are always valid. It does not make
external calls or generate random content, so the demo and tests are stable.
"""

from __future__ import annotations

# Templates keyed by checklist item id. Each aligns with a Phase 3 planted
# issue. Wording avoids prohibited final-decision language.
_TEMPLATES: dict[str, dict] = {
    "chk_infiltration_testing": {
        "finding_type": "missing_evidence",
        "title": "Infiltration testing evidence not found",
        "summary": (
            "Based on the submitted documents, an infiltration basin is "
            "proposed but field infiltration testing was not located in the "
            "retrieved evidence. This is a potential issue that requires "
            "reviewer confirmation."
        ),
        "risk_level": "high",
        "confidence": 0.86,
        "recommended_human_action": (
            "Request field infiltration testing documentation or confirm it was "
            "submitted separately."
        ),
    },
    "chk_downstream_capacity": {
        "finding_type": "missing_evidence",
        "title": "Downstream culvert capacity discussion not found",
        "summary": (
            "Based on the submitted documents, the downstream culvert is "
            "referenced but a downstream capacity discussion was not located in "
            "the retrieved evidence. This needs human review."
        ),
        "risk_level": "high",
        "confidence": 0.82,
        "recommended_human_action": (
            "Request a downstream conveyance or culvert capacity analysis."
        ),
    },
    "chk_oem_owner": {
        "finding_type": "unclear_evidence",
        "title": "Maintenance responsibility may be unclear",
        "summary": (
            "Based on the submitted documents, the operation and maintenance "
            "plan references HOA maintenance, but a recorded responsibility was "
            "not clearly evidenced. This is a potential issue that requires "
            "reviewer confirmation."
        ),
        "risk_level": "high",
        "confidence": 0.78,
        "recommended_human_action": (
            "Request documentation that binds the maintenance party and confirm "
            "the responsible owner."
        ),
    },
    "chk_rfi_closure": {
        "finding_type": "conflicting_evidence",
        "title": "Open RFI on pipe material may be unresolved",
        "summary": (
            "Based on the submitted documents, an RFI on pipe material appears "
            "open with no recorded response in the retrieved evidence. This is "
            "conflicting information that needs human review."
        ),
        "risk_level": "medium",
        "confidence": 0.8,
        "recommended_human_action": (
            "Hold the related item pending an RFI response and confirm the pipe "
            "material."
        ),
    },
    "chk_reference_consistency": {
        "finding_type": "conflicting_evidence",
        "title": "Basin naming may be inconsistent across documents",
        "summary": (
            "Based on the submitted documents, the basin is referred to with "
            "different labels across the plan set and the report. This is "
            "conflicting information that requires reviewer confirmation."
        ),
        "risk_level": "medium",
        "confidence": 0.83,
        "recommended_human_action": (
            "Request consistent basin naming across the plan set and report."
        ),
    },
    "chk_design_storm_consistent": {
        "finding_type": "conflicting_evidence",
        "title": "Design storm assumption may conflict with the town standard",
        "summary": (
            "Based on the submitted documents, the report design storm and the "
            "town standard appear to differ in the retrieved evidence. This is "
            "conflicting information that needs human review."
        ),
        "risk_level": "high",
        "confidence": 0.81,
        "recommended_human_action": (
            "Confirm the applicable town design storm standard and request a "
            "correction if needed."
        ),
    },
    "chk_groundwater_separation": {
        "finding_type": "unclear_evidence",
        "title": "Groundwater separation for infiltration not addressed",
        "summary": (
            "Based on the submitted documents, seasonal high groundwater is "
            "noted but a separation discussion for the infiltration practice was "
            "not located in the retrieved evidence. This requires reviewer "
            "confirmation."
        ),
        "risk_level": "high",
        "confidence": 0.77,
        "recommended_human_action": (
            "Request a separation analysis referencing the documented seasonal "
            "high groundwater depth."
        ),
    },
    "chk_escp_phasing": {
        "finding_type": "conflicting_evidence",
        "title": "Erosion control sequencing may not be tied to phasing",
        "summary": (
            "Based on the submitted documents, the erosion and sediment control "
            "plan does not appear to tie controls to the construction phases in "
            "the retrieved evidence. This needs human review."
        ),
        "risk_level": "medium",
        "confidence": 0.75,
        "recommended_human_action": (
            "Request phased erosion and sediment control sequencing aligned with "
            "the construction phasing plan."
        ),
    },
    "chk_inspection_closeout": {
        "finding_type": "missing_evidence",
        "title": "Inspection corrective action not found",
        "summary": (
            "Based on the submitted documents, an inspection deficiency is noted "
            "but no corrective action closeout was located in the retrieved "
            "evidence. This is a potential issue that needs human review."
        ),
        "risk_level": "high",
        "confidence": 0.8,
        "recommended_human_action": (
            "Request corrective-action evidence or closeout documentation."
        ),
    },
    "chk_referenced_sheets_present": {
        "finding_type": "missing_evidence",
        "title": "Referenced revised grading sheet not found in the package",
        "summary": (
            "Based on the submitted documents, a revised grading sheet is "
            "referenced but was not located in the retrieved evidence. This "
            "requires reviewer confirmation."
        ),
        "risk_level": "medium",
        "confidence": 0.76,
        "recommended_human_action": (
            "Request the missing revised grading sheet."
        ),
    },
}


class MockProvider:
    name = "mock"

    def __init__(self, model_name: str = "mock-review-v1") -> None:
        self.model_name = model_name

    def generate_finding(
        self,
        *,
        project: dict,
        checklist_item: dict,
        evidence: list[dict],
        prompt: str,
    ) -> dict | None:
        item_id = checklist_item.get("checklist_item_id")
        template = _TEMPLATES.get(item_id)
        if template is None:
            # The mock produces draft findings only for the planted-issue items.
            return None

        # Cite up to three chunk ids from the retrieved evidence so the source
        # citations are always valid. If no evidence was retrieved, the service
        # validation will flag the missing citation.
        source_chunk_ids = [
            e["chunk_id"] for e in evidence if e.get("chunk_id")
        ][:3]

        return {
            "checklist_item_id": item_id,
            "finding_type": template["finding_type"],
            "title": template["title"],
            "summary": template["summary"],
            "risk_level": template["risk_level"],
            "confidence": template["confidence"],
            "source_chunk_ids": source_chunk_ids,
            "recommended_human_action": template["recommended_human_action"],
            "requires_human_review": True,
            "safety_boundary_acknowledged": True,
        }
