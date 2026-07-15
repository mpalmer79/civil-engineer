"""Review packet and reviewer workflow board vocabulary."""

from __future__ import annotations

# Phase 8 review packet statuses. These apply to packets, sections, and items.
# None implies a final engineering decision, approval, or certification.
ALLOWED_REVIEW_PACKET_STATUSES: set[str] = {
    "draft",
    "needs_follow_up",
    "reviewer_checked",
    "excluded_from_packet",
    "needs_more_information",
}

# Phase 8 review packet reviewer actions a reviewer may record on a packet item.
# There is intentionally no action called approve. Each action type is the
# target status it sets, so a stored action_type is always one of the allowed
# packet statuses (there is no synthetic status_update action type).
ALLOWED_REVIEW_PACKET_ACTIONS: set[str] = {
    "draft",
    "needs_follow_up",
    "reviewer_checked",
    "excluded_from_packet",
    "needs_more_information",
}

PACKET_ACTION_TO_STATUS: dict[str, str] = {
    "draft": "draft",
    "needs_follow_up": "needs_follow_up",
    "reviewer_checked": "reviewer_checked",
    "excluded_from_packet": "excluded_from_packet",
    "needs_more_information": "needs_more_information",
}

# Phase 9 reviewer workflow board statuses. These describe where a
# review-support item sits in the operational review workflow. None implies a
# final engineering decision, approval, certification, or compliance state.
ALLOWED_WORKFLOW_STATUSES: set[str] = {
    "draft",
    "needs_triage",
    "needs_follow_up",
    "needs_more_information",
    "reviewer_checked",
    "excluded_from_packet",
    "ready_for_handoff",
}

# Phase 9 workflow action types recorded when a reviewer acts on a workflow
# item. There is intentionally no action called approve.
ALLOWED_WORKFLOW_ACTIONS: set[str] = {
    "triage_started",
    "follow_up_requested",
    "more_information_requested",
    "reviewer_checked",
    "excluded_from_packet",
    "ready_for_handoff",
    "note_added",
    "target_date_updated",
}

# Maps a requested workflow status transition to the action type it records.
# draft is the initial seeded status and is not a manual transition target, so
# it is intentionally absent: requesting it is rejected as an invalid status.
WORKFLOW_STATUS_TO_ACTION: dict[str, str] = {
    "needs_triage": "triage_started",
    "needs_follow_up": "follow_up_requested",
    "needs_more_information": "more_information_requested",
    "reviewer_checked": "reviewer_checked",
    "excluded_from_packet": "excluded_from_packet",
    "ready_for_handoff": "ready_for_handoff",
}

# Phase 9 follow-up request statuses. None uses final-decision language.
ALLOWED_FOLLOW_UP_STATUSES: set[str] = {
    "open",
    "response_needed",
    "reviewer_checked",
    "closed_without_decision",
}
