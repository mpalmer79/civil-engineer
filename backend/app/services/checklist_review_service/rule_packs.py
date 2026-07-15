"""Reusable, versioned rule packs and their reads.

A rule pack is a reusable review-support template, not a legal ordinance, not a
compliance standard, and not a binding requirement set. This module seeds the
starter stormwater rule pack and exposes read helpers for rule packs and their
items.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models
from app.services.checklist_review_service.errors import ChecklistReviewError
from app.services.real_intake_service import _now

STARTER_RULE_PACK_ID = "rulepack_brookside_stormwater_starter"
STARTER_RULE_PACK_NAME = "Brookside Stormwater Review Starter Pack"
STARTER_REFERENCE_LABEL = "Starter template, not ordinance"

# Starter stormwater review rule pack items. These are review-support prompts a
# reviewer can use to organize evidence review. They are not legal requirements,
# not compliance standards, and not jurisdiction-approved ordinance language.
STARTER_RULE_PACK_ITEMS: list[dict] = [
    {
        "item_code": "SC-01",
        "category": "Submission completeness",
        "requirement_text": (
            "A complete stormwater submission package is provided for review."
        ),
        "expected_evidence": (
            "Cover sheet, drainage report, and a plan set index listing all "
            "submitted sheets."
        ),
        "applicability_note": "Applies to all stormwater submissions.",
        "risk_level": "medium",
    },
    {
        "item_code": "EC-01",
        "category": "Existing conditions",
        "requirement_text": (
            "Existing site conditions and drainage patterns are described."
        ),
        "expected_evidence": (
            "Existing conditions plan and a narrative describing predevelopment "
            "drainage areas and flow paths."
        ),
        "applicability_note": "Applies to all submissions.",
        "risk_level": "medium",
    },
    {
        "item_code": "EC-02",
        "category": "Existing conditions",
        "requirement_text": "Existing impervious area is quantified.",
        "expected_evidence": "Existing conditions impervious area tabulation.",
        "applicability_note": "Applies when impervious area changes are proposed.",
        "risk_level": "low",
    },
    {
        "item_code": "HY-01",
        "category": "Hydrology and design storms",
        "requirement_text": (
            "Design storm events and the hydrologic method are stated."
        ),
        "expected_evidence": (
            "Hydrology narrative identifying the design storms (for example 2, "
            "10, 25, and 100 year) and the computation method used."
        ),
        "applicability_note": "Applies to all submissions.",
        "risk_level": "high",
    },
    {
        "item_code": "HY-02",
        "category": "Hydrology and design storms",
        "requirement_text": (
            "Predevelopment and postdevelopment runoff are compared."
        ),
        "expected_evidence": (
            "Runoff summary table comparing predevelopment and postdevelopment "
            "peak flows by design storm."
        ),
        "applicability_note": "Applies to all submissions.",
        "risk_level": "high",
    },
    {
        "item_code": "IG-01",
        "category": "Infiltration and groundwater",
        "requirement_text": (
            "Infiltration capacity and seasonal high groundwater are addressed "
            "where infiltration is proposed."
        ),
        "expected_evidence": (
            "Soil or infiltration testing results and the seasonal high "
            "groundwater elevation."
        ),
        "applicability_note": "Applies when infiltration practices are proposed.",
        "risk_level": "high",
    },
    {
        "item_code": "DO-01",
        "category": "Detention and outlet control",
        "requirement_text": (
            "Detention storage and outlet control are sized for the design "
            "storms."
        ),
        "expected_evidence": (
            "Detention basin stage storage table and outlet control structure "
            "computations."
        ),
        "applicability_note": "Applies when detention is proposed.",
        "risk_level": "high",
    },
    {
        "item_code": "DO-02",
        "category": "Detention and outlet control",
        "requirement_text": "An outlet structure detail is provided.",
        "expected_evidence": (
            "Outlet structure detail sheet with orifice and weir dimensions."
        ),
        "applicability_note": "Applies when detention is proposed.",
        "risk_level": "medium",
    },
    {
        "item_code": "WQ-01",
        "category": "Water quality treatment",
        "requirement_text": (
            "Water quality treatment is provided for the required water quality "
            "volume."
        ),
        "expected_evidence": (
            "Water quality volume computation and treatment practice sizing."
        ),
        "applicability_note": "Applies when water quality treatment is required.",
        "risk_level": "high",
    },
    {
        "item_code": "WQ-02",
        "category": "Water quality treatment",
        "requirement_text": (
            "Proposed water quality practices are located on the plans."
        ),
        "expected_evidence": (
            "Plan sheet showing the location of each water quality practice."
        ),
        "applicability_note": "Applies when water quality practices are proposed.",
        "risk_level": "medium",
    },
    {
        "item_code": "DS-01",
        "category": "Downstream analysis",
        "requirement_text": (
            "Downstream conveyance and potential impacts are evaluated."
        ),
        "expected_evidence": (
            "Downstream analysis narrative and a culvert or channel capacity "
            "check."
        ),
        "applicability_note": "Applies when downstream impacts are possible.",
        "risk_level": "medium",
    },
    {
        "item_code": "ES-01",
        "category": "Erosion and sediment control",
        "requirement_text": "An erosion and sediment control plan is provided.",
        "expected_evidence": (
            "Erosion and sediment control plan sheet and the sequence of "
            "construction."
        ),
        "applicability_note": "Applies when land is disturbed.",
        "risk_level": "medium",
    },
    {
        "item_code": "WB-01",
        "category": "Wetlands and buffers",
        "requirement_text": (
            "Wetlands and buffers are identified and respected where present."
        ),
        "expected_evidence": (
            "Wetland delineation or buffer plan, or a note that none are "
            "present."
        ),
        "applicability_note": "Applies when wetlands or buffers are present.",
        "risk_level": "medium",
    },
    {
        "item_code": "OM-01",
        "category": "Operation and maintenance",
        "requirement_text": (
            "An operation and maintenance plan is provided for stormwater "
            "practices."
        ),
        "expected_evidence": (
            "Operation and maintenance plan describing inspection and "
            "maintenance tasks and the responsible party."
        ),
        "applicability_note": "Applies when stormwater practices are proposed.",
        "risk_level": "medium",
    },
    {
        "item_code": "PS-01",
        "category": "Plan sheet consistency",
        "requirement_text": (
            "Plan sheets are internally consistent with the drainage report."
        ),
        "expected_evidence": (
            "Consistency between plan sheet labels, structure tables, and the "
            "drainage report values."
        ),
        "applicability_note": "Applies to all submissions.",
        "risk_level": "medium",
    },
    {
        "item_code": "RR-01",
        "category": "Resubmittal response",
        "requirement_text": (
            "Resubmittal responses address prior review comments."
        ),
        "expected_evidence": (
            "Response to comments letter mapping each prior comment to a "
            "response and the revised sheet."
        ),
        "applicability_note": "Applies to resubmittals only.",
        "risk_level": "low",
    },
]


def ensure_starter_rule_pack(db: Session) -> models.RulePack:
    """Create the seeded starter stormwater rule pack if it does not exist."""

    pack = db.get(models.RulePack, STARTER_RULE_PACK_ID)
    if pack is not None:
        return pack

    now = _now()
    pack = models.RulePack(
        rule_pack_id=STARTER_RULE_PACK_ID,
        name=STARTER_RULE_PACK_NAME,
        jurisdiction_name="Starter template (no jurisdiction)",
        review_domain="stormwater",
        description=(
            "A reusable starter stormwater review checklist for reviewer use. "
            "It is a review-support template, not a legal ordinance, not a "
            "compliance standard, and not a binding requirement set. A reviewer "
            "decides applicability and evidence status for each item."
        ),
        version_label="v1",
        source_mode="seeded_demo",
        is_active=True,
        created_by_name="Seeded demo",
        created_at=now,
        updated_at=now,
    )
    db.add(pack)
    for index, item in enumerate(STARTER_RULE_PACK_ITEMS):
        db.add(
            models.RulePackItem(
                rule_pack_item_id=f"rpi_{STARTER_RULE_PACK_ID}_{item['item_code'].lower().replace('-', '_')}",
                rule_pack_id=STARTER_RULE_PACK_ID,
                item_code=item["item_code"],
                category=item["category"],
                requirement_text=item["requirement_text"],
                expected_evidence=item["expected_evidence"],
                applicability_note=item["applicability_note"],
                risk_level=item["risk_level"],
                review_domain="stormwater",
                reference_label=STARTER_REFERENCE_LABEL,
                sort_order=index,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )
    return pack


def list_rule_packs(db: Session) -> list[dict]:
    """List all rule packs with item counts, newest first."""

    packs = db.scalars(
        select(models.RulePack).order_by(models.RulePack.created_at)
    ).all()
    return [_rule_pack_dict(db, pack) for pack in packs]


def get_rule_pack(db: Session, rule_pack_id: str) -> dict:
    pack = db.get(models.RulePack, rule_pack_id)
    if pack is None:
        raise ChecklistReviewError("Rule pack not found.", status_code=404)
    detail = _rule_pack_dict(db, pack)
    detail["items"] = [
        _rule_pack_item_dict(item) for item in _rule_pack_items(db, rule_pack_id)
    ]
    return detail


def _rule_pack_items(db: Session, rule_pack_id: str) -> list[models.RulePackItem]:
    return list(
        db.scalars(
            select(models.RulePackItem)
            .where(models.RulePackItem.rule_pack_id == rule_pack_id)
            .order_by(models.RulePackItem.sort_order)
        ).all()
    )


def _rule_pack_dict(db: Session, pack: models.RulePack) -> dict:
    item_count = db.scalar(
        select(func.count())
        .select_from(models.RulePackItem)
        .where(models.RulePackItem.rule_pack_id == pack.rule_pack_id)
    )
    return {
        "rule_pack_id": pack.rule_pack_id,
        "name": pack.name,
        "jurisdiction_name": pack.jurisdiction_name,
        "review_domain": pack.review_domain,
        "description": pack.description,
        "version_label": pack.version_label,
        "source_mode": pack.source_mode,
        "is_active": pack.is_active,
        "created_by_name": pack.created_by_name,
        "created_at": pack.created_at,
        "updated_at": pack.updated_at,
        "item_count": int(item_count or 0),
    }


def _rule_pack_item_dict(item: models.RulePackItem) -> dict:
    return {
        "rule_pack_item_id": item.rule_pack_item_id,
        "rule_pack_id": item.rule_pack_id,
        "item_code": item.item_code,
        "category": item.category,
        "requirement_text": item.requirement_text,
        "expected_evidence": item.expected_evidence,
        "applicability_note": item.applicability_note,
        "risk_level": item.risk_level,
        "review_domain": item.review_domain,
        "reference_label": item.reference_label,
        "sort_order": item.sort_order,
        "is_active": item.is_active,
    }
