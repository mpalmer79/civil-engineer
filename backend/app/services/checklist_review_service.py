"""Checklist-driven evidence review and rule pack foundation service (Sprint 4).

Production Foundations Sprint 4 adds the first reusable, versioned checklist
foundation for real projects. A reviewer can attach a starter rule pack to a
project as a checklist, search indexed evidence against each checklist
requirement, track reviewer-controlled checklist evidence status, link citations,
and create draft findings from checklist items.

Everything here is review-support only. A rule pack is a reusable review-support
template, not a legal ordinance, not a compliance standard, and not a binding
requirement set. Checklist status is review-support only. Nothing here approves
plans, certifies compliance, verifies CAD, validates design, declares a project
safe, resolves or closes an issue, or makes a final engineering decision. Draft
findings require reviewer confirmation. There are no live AI calls.

Audit metadata records ids, statuses, counts, and safe labels only. It never
records full extracted page text, raw server file paths, secrets, or API keys.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.safety import (
    ALLOWED_CHECKLIST_APPLICABILITY_STATUSES,
    ALLOWED_CHECKLIST_EVIDENCE_STATUSES,
    ALLOWED_CHECKLIST_LINK_STATUSES,
    ALLOWED_CHECKLIST_REVIEW_STATUSES,
    ALLOWED_EVIDENCE_STATUSES,
    ALLOWED_PROJECT_CHECKLIST_STATUSES,
    ALLOWED_REVIEWER_FINDING_STATUSES,
    reject_prohibited_language,
)
from app.db import models
from app.services import evidence_retrieval_service
from app.services.auth_service import ActorContext, audit_kwargs
from app.services.pdf_indexing_service import create_evidence_citation
from app.services.real_intake_service import (
    DEMO_ACTOR_ID,
    DEMO_ACTOR_NAME,
    _now,
    _short,
    ensure_demo_actor,
    record_audit_event,
)

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


class ChecklistReviewError(Exception):
    """Raised when a checklist review operation is not allowed."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ---------------------------------------------------------------------------
# Rule packs
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Project checklists
# ---------------------------------------------------------------------------


def _require_project(db: Session, project_id: str) -> models.Project:
    project = db.get(models.Project, project_id)
    if project is None:
        raise ChecklistReviewError("Project not found.", status_code=404)
    return project


def create_project_checklist_from_rule_pack(
    db: Session,
    project_id: str,
    rule_pack_id: str,
    *,
    name: str | None = None,
    actor_name: str = DEMO_ACTOR_NAME,
    actor: "ActorContext | None" = None,
) -> dict:
    """Attach a rule pack to a project as a working checklist with items."""

    _require_project(db, project_id)
    ensure_demo_actor(db)
    if actor is not None:
        actor_name = actor.display_name
    pack = db.get(models.RulePack, rule_pack_id)
    if pack is None:
        raise ChecklistReviewError("Rule pack not found.", status_code=404)

    now = _now()
    checklist_id = f"pcl_{_short()}"
    checklist = models.ProjectChecklist(
        project_checklist_id=checklist_id,
        project_id=project_id,
        rule_pack_id=rule_pack_id,
        name=(name or pack.name).strip(),
        status="checklist_started",
        source_mode="user_created",
        created_by_actor_id=DEMO_ACTOR_ID,
        created_by_name=actor_name,
        created_at=now,
        updated_at=now,
    )
    db.add(checklist)

    items = _rule_pack_items(db, rule_pack_id)
    for item in items:
        db.add(
            models.ProjectChecklistItem(
                project_checklist_item_id=f"pcli_{_short()}",
                project_checklist_id=checklist_id,
                project_id=project_id,
                rule_pack_item_id=item.rule_pack_item_id,
                item_code=item.item_code,
                category=item.category,
                requirement_text=item.requirement_text,
                expected_evidence=item.expected_evidence,
                applicability_status="needs_reviewer_confirmation",
                evidence_status="not_reviewed",
                review_status="not_started",
                risk_level=item.risk_level,
                sort_order=item.sort_order,
                created_at=now,
                updated_at=now,
            )
        )

    record_audit_event(
        db,
        **audit_kwargs(actor),
        project_id=project_id,
        event_type="project_checklist_created",
        related_entity_type="project_checklist",
        related_entity_id=checklist_id,
        description=(
            f"Reviewer created checklist '{checklist.name}' from rule pack "
            f"'{pack.name}' ({len(items)} item(s))."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "project_checklist_id": checklist_id,
            "rule_pack_id": rule_pack_id,
            "item_count": len(items),
        },
    )
    db.commit()
    db.refresh(checklist)
    return get_project_checklist(db, project_id, checklist_id)


def list_project_checklists(db: Session, project_id: str) -> list[dict]:
    _require_project(db, project_id)
    checklists = db.scalars(
        select(models.ProjectChecklist)
        .where(models.ProjectChecklist.project_id == project_id)
        .order_by(models.ProjectChecklist.created_at)
    ).all()
    return [_checklist_dict(db, c) for c in checklists]


def get_project_checklist(
    db: Session, project_id: str, project_checklist_id: str
) -> dict:
    checklist = db.get(models.ProjectChecklist, project_checklist_id)
    if checklist is None or checklist.project_id != project_id:
        raise ChecklistReviewError(
            "Project checklist not found.", status_code=404
        )
    return _checklist_dict(db, checklist)


def _checklist_items(
    db: Session, project_checklist_id: str
) -> list[models.ProjectChecklistItem]:
    return list(
        db.scalars(
            select(models.ProjectChecklistItem)
            .where(
                models.ProjectChecklistItem.project_checklist_id
                == project_checklist_id
            )
            .order_by(models.ProjectChecklistItem.sort_order)
        ).all()
    )


def _checklist_dict(db: Session, checklist: models.ProjectChecklist) -> dict:
    items = _checklist_items(db, checklist.project_checklist_id)
    evidence_summary: dict[str, int] = {}
    review_summary: dict[str, int] = {}
    for item in items:
        evidence_summary[item.evidence_status] = (
            evidence_summary.get(item.evidence_status, 0) + 1
        )
        review_summary[item.review_status] = (
            review_summary.get(item.review_status, 0) + 1
        )
    return {
        "project_checklist_id": checklist.project_checklist_id,
        "project_id": checklist.project_id,
        "rule_pack_id": checklist.rule_pack_id,
        "name": checklist.name,
        "status": checklist.status,
        "source_mode": checklist.source_mode,
        "created_by_name": checklist.created_by_name,
        "created_at": checklist.created_at,
        "updated_at": checklist.updated_at,
        "item_count": len(items),
        "evidence_status_summary": evidence_summary,
        "review_status_summary": review_summary,
    }


def list_project_checklist_items(
    db: Session, project_id: str, project_checklist_id: str
) -> list[models.ProjectChecklistItem]:
    get_project_checklist(db, project_id, project_checklist_id)
    return _checklist_items(db, project_checklist_id)


def get_checklist_item(
    db: Session, project_id: str, project_checklist_item_id: str
) -> models.ProjectChecklistItem:
    item = db.get(models.ProjectChecklistItem, project_checklist_item_id)
    if item is None or item.project_id != project_id:
        raise ChecklistReviewError("Checklist item not found.", status_code=404)
    return item


# ---------------------------------------------------------------------------
# Checklist item review
# ---------------------------------------------------------------------------


def update_project_checklist_item(
    db: Session,
    project_id: str,
    project_checklist_item_id: str,
    payload: dict,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> models.ProjectChecklistItem:
    """Update reviewer-controlled applicability, evidence, review status, note."""

    item = get_checklist_item(db, project_id, project_checklist_item_id)
    ensure_demo_actor(db)
    reject_prohibited_language(payload.get("reviewer_note"), field="reviewer_note")

    applicability = payload.get("applicability_status")
    evidence = payload.get("evidence_status")
    review = payload.get("review_status")
    note = payload.get("reviewer_note")

    if applicability is not None:
        if applicability not in ALLOWED_CHECKLIST_APPLICABILITY_STATUSES:
            raise ChecklistReviewError(
                f"Invalid applicability_status '{applicability}'.",
                status_code=422,
            )
        item.applicability_status = applicability
    if evidence is not None:
        if evidence not in ALLOWED_CHECKLIST_EVIDENCE_STATUSES:
            raise ChecklistReviewError(
                f"Invalid evidence_status '{evidence}'.", status_code=422
            )
        item.evidence_status = evidence
    if review is not None:
        if review not in ALLOWED_CHECKLIST_REVIEW_STATUSES:
            raise ChecklistReviewError(
                f"Invalid review_status '{review}'.", status_code=422
            )
        item.review_status = review
    if note is not None:
        item.reviewer_note = note
        if review is None and item.review_status == "not_started":
            item.review_status = "reviewer_note_added"

    now = _now()
    item.updated_at = now
    item.reviewed_by_actor_id = DEMO_ACTOR_ID
    item.reviewed_by_name = actor_name
    item.reviewed_at = now

    event_type = "checklist_item_status_updated"
    if applicability == "not_applicable_by_reviewer":
        event_type = "checklist_item_marked_not_applicable_by_reviewer"
    elif note is not None and applicability is None and evidence is None and review is None:
        event_type = "checklist_item_note_added"

    record_audit_event(
        db,
        project_id=project_id,
        event_type=event_type,
        related_entity_type="project_checklist_item",
        related_entity_id=project_checklist_item_id,
        description=(
            f"Reviewer updated checklist item {item.item_code}."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "checklist_item_id": project_checklist_item_id,
            "applicability_status": item.applicability_status,
            "evidence_status": item.evidence_status,
            "review_status": item.review_status,
        },
    )
    db.commit()
    db.refresh(item)
    return item


def search_evidence_for_checklist_item(
    db: Session,
    project_id: str,
    project_checklist_item_id: str,
    payload: dict | None = None,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> dict:
    """Search indexed evidence for a checklist item's expected evidence text."""

    item = get_checklist_item(db, project_id, project_checklist_item_id)
    payload = payload or {}
    query_text = (
        payload.get("query_text")
        or item.expected_evidence
        or item.requirement_text
        or ""
    ).strip()

    search_payload = {
        "query_text": query_text,
        "query_type": "checklist_item",
        "filters": {"checklist_item_id": project_checklist_item_id},
        "limit": payload.get("limit", 10),
    }
    result = evidence_retrieval_service.search_project_evidence(
        db, project_id, search_payload, actor_name=actor_name
    )

    record_audit_event(
        db,
        project_id=project_id,
        event_type="checklist_evidence_search_performed",
        related_entity_type="project_checklist_item",
        related_entity_id=project_checklist_item_id,
        description=(
            f"Reviewer searched evidence for checklist item {item.item_code}; "
            f"{result['result_count']} candidate(s)."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "checklist_item_id": project_checklist_item_id,
            "result_count": result["result_count"],
            "retrieval_query_id": result.get("retrieval_query_id"),
        },
    )
    if item.review_status == "not_started":
        item.review_status = "evidence_review_needed"
        item.updated_at = _now()
    db.commit()
    return result


def link_citation_to_checklist_item(
    db: Session,
    project_id: str,
    project_checklist_item_id: str,
    payload: dict,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> models.ChecklistEvidenceLink:
    """Link a document page, citation, or candidate to a checklist item."""

    item = get_checklist_item(db, project_id, project_checklist_item_id)
    ensure_demo_actor(db)
    reject_prohibited_language(payload.get("reviewer_note"), field="reviewer_note")
    reject_prohibited_language(payload.get("quoted_excerpt"), field="quoted_excerpt")

    document_id = (payload.get("document_id") or "").strip()
    if not document_id:
        raise ChecklistReviewError("document_id is required.", status_code=422)
    document = db.get(models.Document, document_id)
    if document is None or document.project_id != project_id:
        raise ChecklistReviewError("Document not found.", status_code=404)

    page_number = payload.get("page_number")
    document_page_id = payload.get("document_page_id")
    if document_page_id:
        page = db.get(models.DocumentPage, document_page_id)
        if page is None or page.document_id != document_id:
            raise ChecklistReviewError(
                "Document page not found for this document.", status_code=422
            )
        page_number = page.page_number

    link_status = payload.get("link_status") or "reviewer_selected"
    if link_status not in ALLOWED_CHECKLIST_LINK_STATUSES:
        raise ChecklistReviewError(
            f"Invalid link_status '{link_status}'.", status_code=422
        )

    # Optionally create an EvidenceCitation in checklist context. This requires a
    # finding, so a citation is only created when create_citation is requested
    # together with a finding_id; otherwise the link stands on its own.
    citation_id = payload.get("evidence_citation_id")

    now = _now()
    link = models.ChecklistEvidenceLink(
        checklist_evidence_link_id=f"clink_{_short()}",
        project_id=project_id,
        project_checklist_item_id=project_checklist_item_id,
        document_id=document_id,
        document_page_id=document_page_id,
        evidence_citation_id=citation_id,
        evidence_candidate_id=payload.get("evidence_candidate_id"),
        page_number=page_number,
        quoted_excerpt=payload.get("quoted_excerpt"),
        reviewer_note=payload.get("reviewer_note"),
        link_status=link_status,
        created_by_actor_id=DEMO_ACTOR_ID,
        created_by_name=actor_name,
        created_at=now,
    )
    db.add(link)

    if item.review_status in ("not_started", "evidence_review_needed"):
        item.review_status = "citation_added"
    item.updated_at = now

    record_audit_event(
        db,
        project_id=project_id,
        event_type="checklist_evidence_linked",
        related_entity_type="project_checklist_item",
        related_entity_id=project_checklist_item_id,
        description=(
            f"Reviewer linked evidence to checklist item {item.item_code}."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "checklist_item_id": project_checklist_item_id,
            "checklist_evidence_link_id": link.checklist_evidence_link_id,
            "document_id": document_id,
            "page_number": page_number,
            "evidence_citation_id": citation_id,
            "evidence_candidate_id": payload.get("evidence_candidate_id"),
            "link_status": link_status,
        },
    )
    db.commit()
    db.refresh(link)
    return link


def list_checklist_item_evidence_links(
    db: Session, project_id: str, project_checklist_item_id: str
) -> list[models.ChecklistEvidenceLink]:
    get_checklist_item(db, project_id, project_checklist_item_id)
    return list(
        db.scalars(
            select(models.ChecklistEvidenceLink)
            .where(
                models.ChecklistEvidenceLink.project_checklist_item_id
                == project_checklist_item_id
            )
            .order_by(models.ChecklistEvidenceLink.created_at)
        ).all()
    )


# ---------------------------------------------------------------------------
# Draft finding from checklist item
# ---------------------------------------------------------------------------


def create_draft_finding_from_checklist_item(
    db: Session,
    project_id: str,
    project_checklist_item_id: str,
    payload: dict,
    *,
    actor_name: str = DEMO_ACTOR_NAME,
) -> dict:
    """Create a reviewer draft finding from a checklist item.

    Creates a Finding with finding_origin checklist_review and a safe draft
    human_review_status, links the related checklist item, optionally creates a
    page-level citation, updates the checklist item review_status to
    draft_finding_created, and writes audit events. The system never decides a
    final outcome; reviewer-entered content is validated against final-decision
    language.
    """

    item = get_checklist_item(db, project_id, project_checklist_item_id)
    ensure_demo_actor(db)

    title = (
        payload.get("title")
        or f"{item.item_code}: {item.requirement_text}"
    ).strip()
    category = (payload.get("category") or item.category or "general").strip()
    risk_level = (payload.get("risk_level") or item.risk_level or "medium").strip()
    evidence_status = payload.get("evidence_status") or "needs_reviewer_confirmation"
    evidence_to_find = (
        payload.get("evidence_to_find") or item.expected_evidence or ""
    ).strip()
    reason_it_matters = (payload.get("reason_it_matters") or "").strip()
    recommended_human_action = (
        payload.get("recommended_human_action") or ""
    ).strip()
    reviewer_note = payload.get("reviewer_note")
    human_review_status = payload.get("human_review_status") or "draft"

    for field, value in (
        ("title", title),
        ("category", category),
        ("risk_level", risk_level),
        ("evidence_to_find", evidence_to_find),
        ("reason_it_matters", reason_it_matters),
        ("recommended_human_action", recommended_human_action),
        ("reviewer_note", reviewer_note),
    ):
        reject_prohibited_language(value, field=field)

    if evidence_status not in ALLOWED_EVIDENCE_STATUSES:
        raise ChecklistReviewError(
            f"Invalid evidence_status '{evidence_status}'.", status_code=422
        )
    if human_review_status not in ALLOWED_REVIEWER_FINDING_STATUSES:
        raise ChecklistReviewError(
            f"Invalid human_review_status '{human_review_status}'.",
            status_code=422,
        )

    now = _now()
    finding_id = f"find_checklist_{_short()}"
    finding = models.Finding(
        finding_id=finding_id,
        project_id=project_id,
        planted_issue="",
        title=title,
        category=category,
        risk_level=risk_level,
        expected_status=evidence_status,
        evidence_status=evidence_status,
        evidence_to_find=evidence_to_find,
        reason_it_matters=reason_it_matters,
        recommended_human_action=recommended_human_action,
        human_review_status=human_review_status,
        related_checklist_items=[project_checklist_item_id],
        related_documents=[],
        source_mode="user_created",
        finding_origin="checklist_review",
        reviewer_notes=reviewer_note,
        created_by_name=actor_name,
        created_by_actor_id=DEMO_ACTOR_ID,
        created_at=now,
        updated_at=now,
    )
    db.add(finding)
    db.flush()

    citation = None
    document_id = payload.get("document_id")
    if document_id:
        document = db.get(models.Document, document_id)
        if document is None or document.project_id != project_id:
            raise ChecklistReviewError(
                "Document not found for citation.", status_code=422
            )
        citation = create_evidence_citation(
            db,
            project_id=project_id,
            finding_id=finding_id,
            document_id=document_id,
            document_page_id=payload.get("document_page_id"),
            page_number=payload.get("page_number"),
            quoted_excerpt=payload.get("citation_excerpt"),
            reviewer_note=(
                f"Linked from checklist item {item.item_code}."
            ),
            citation_type="reviewer_selected",
            created_by_name=actor_name,
        )
        citation.citation_context = "checklist_evidence"
        citation.project_checklist_item_id = project_checklist_item_id
        citation.rule_pack_item_id = item.rule_pack_item_id

    item.related_finding_id = finding_id
    item.review_status = "draft_finding_created"
    item.updated_at = now

    record_audit_event(
        db,
        project_id=project_id,
        event_type="checklist_draft_finding_created",
        related_entity_type="finding",
        related_entity_id=finding_id,
        description=(
            f"Reviewer created draft finding from checklist item "
            f"{item.item_code}."
        ),
        actor_type="reviewer",
        actor_display_name=actor_name,
        metadata={
            "checklist_item_id": project_checklist_item_id,
            "finding_id": finding_id,
            "finding_origin": "checklist_review",
            "evidence_status": evidence_status,
            "human_review_status": human_review_status,
            "evidence_citation_id": (
                citation.evidence_citation_id if citation else None
            ),
        },
    )
    db.commit()
    db.refresh(finding)
    db.refresh(item)
    if citation is not None:
        db.refresh(citation)
    return {"finding": finding, "citation": citation, "checklist_item": item}
