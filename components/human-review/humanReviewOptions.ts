// Shared option lists and status labels for the human review queue. There is
// intentionally no "approve" action anywhere in this module.

export const riskFor = (level: string) =>
  level === "high" || level === "medium" || level === "low"
    ? (level as "high" | "medium" | "low")
    : "low";

// Actions allowed for a valid draft finding. There is intentionally no
// "approve" action.
export const VALID_ACTIONS: { value: string; label: string }[] = [
  { value: "accepted", label: "Accept finding" },
  { value: "edited", label: "Edit finding" },
  { value: "rejected", label: "Reject finding" },
  { value: "escalated", label: "Escalate" },
  { value: "marked_unclear", label: "Mark unclear" },
  { value: "requested_more_information", label: "Request more information" },
];

// Failed drafts cannot be accepted or edited. They may only be rejected,
// escalated, or marked unclear pending regeneration.
export const FAILED_ACTIONS: { value: string; label: string }[] = [
  { value: "rejected", label: "Reject finding" },
  { value: "escalated", label: "Escalate" },
  { value: "marked_unclear", label: "Mark unclear" },
];

export const STATUS_LABELS: Record<string, string> = {
  requires_human_review: "Human review required",
  validation_failed: "Validation failure",
  accepted_by_reviewer: "Accepted by reviewer",
  edited_by_reviewer: "Edited by reviewer",
  rejected_by_reviewer: "Rejected by reviewer",
  escalated: "Escalated",
  marked_unclear: "Marked unclear",
  requested_more_information: "More information requested",
};

export const STATUS_ORDER = [
  "requires_human_review",
  "validation_failed",
  "escalated",
  "requested_more_information",
  "marked_unclear",
  "edited_by_reviewer",
  "accepted_by_reviewer",
  "rejected_by_reviewer",
];
