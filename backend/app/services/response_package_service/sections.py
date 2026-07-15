"""Workflow item selection, section classification, and draft wording."""

from __future__ import annotations


def select_source_workflow_items(items: list) -> tuple[list, bool]:
    """Select the workflow items a response package should be built from.

    Selection tiers, in order:

    1. Items with status ready_for_handoff (the primary source).
    2. If none are ready, items with status needs_follow_up or
       needs_more_information (the package is labeled draft).
    3. If none of those exist either, any item that still requires human review
       and is not excluded (a defensive fallback so the package is not empty).

    Informational limitations items are never promoted as response demands.
    Returns the selected items and a flag that is True when a fallback tier was
    used so the caller can label the package as draft.
    """

    def _eligible(item) -> bool:
        if not getattr(item, "requires_human_review", True):
            return False
        if item.section_type == "limitations":
            return False
        if item.status == "excluded_from_packet":
            return False
        return True

    eligible = [i for i in items if _eligible(i)]
    ready = [i for i in eligible if i.status == "ready_for_handoff"]
    if ready:
        return ready, False
    follow = [
        i
        for i in eligible
        if i.status in {"needs_follow_up", "needs_more_information"}
    ]
    if follow:
        return follow, True
    return eligible, True


def _classify_section(item) -> str:
    """Map a workflow item to a topical response section type."""

    text = f"{item.title} {item.description}".lower()
    if item.status == "needs_more_information" or item.source_type == "document":
        if any(k in text for k in ("missing", "incomplete", "not included", "provide")):
            return "missing_information"
    if any(k in text for k in ("wetland", "buffer", "setback")):
        return "wetland_buffer_items"
    if any(k in text for k in ("erosion", "sediment", "stabilization")):
        return "erosion_control_items"
    if any(k in text for k in ("basin", "stormwater", "drainage", "detention", "outlet", "runoff")):
        return "stormwater_items"
    if item.section_type in {"plan_sheet_cad", "sheet_hotspots"} or item.source_type in {
        "plan_sheet",
        "plan_reference",
        "sheet_hotspot",
    }:
        return "plan_sheet_items"
    if item.status == "needs_more_information":
        return "missing_information"
    return "requested_revisions"


def _draft_text(item, section_type: str) -> str:
    """Draft plain, professional external-review wording for an item.

    The wording avoids final-decision language. It frames each item as a
    review-support request or observation for a human reviewer.
    """

    title = item.title.strip().rstrip(".")
    description = (item.description or "").strip()
    if section_type == "missing_information":
        lead = (
            f"Please provide additional information regarding {title}. The "
            "available materials appear incomplete for review-support purposes."
        )
    elif section_type == "plan_sheet_items":
        lead = (
            f"Please clarify the plan reference for {title}. The review packet "
            "identifies a potential inconsistency to confirm."
        )
    elif section_type in {"stormwater_items", "erosion_control_items", "wetland_buffer_items"}:
        lead = (
            f"The review packet identifies a potential issue related to {title}. "
            "The following item should be reviewed by the design professional."
        )
    else:
        lead = (
            f"The following item should be reviewed by the design professional: "
            f"{title}."
        )
    if description:
        return f"{lead} Reviewer context: {description}"
    return lead
