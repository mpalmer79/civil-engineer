// Human-friendly labels for Sprint 9 dashboard vocabulary. All labels are
// review-support only. None uses final-decision wording such as approved,
// certified, compliant, verified, resolved, or closed.

export const AGE_BUCKET_LABELS: Record<string, string> = {
  updated_today: "Updated today",
  waiting_1_to_3_days: "Waiting 1 to 3 days",
  waiting_4_to_7_days: "Waiting 4 to 7 days",
  waiting_more_than_7_days: "Waiting more than 7 days",
};

export const DUE_DATE_INDICATOR_LABELS: Record<string, string> = {
  due_date_set: "Due date set",
  due_soon: "Due soon",
  past_due_for_reviewer_attention: "Past due for reviewer attention",
};

export const QUEUE_ITEM_TYPE_LABELS: Record<string, string> = {
  document_indexing: "Documents needing indexing",
  evidence_candidate_triage: "Evidence candidates needing triage",
  checklist_evidence_review: "Checklist evidence review needed",
  applicant_response_review: "Applicant response needs reviewer review",
  carried_forward_matrix_item: "Carried forward for review",
  response_package_handoff: "Package ready for reviewer handoff",
};

export const PRIORITY_LABELS: Record<string, string> = {
  low: "Low",
  standard: "Standard",
  elevated: "Elevated",
  time_sensitive: "Time sensitive",
};

export function ageBucketLabel(bucket: string): string {
  return AGE_BUCKET_LABELS[bucket] ?? bucket;
}

export function queueTypeLabel(itemType: string): string {
  return QUEUE_ITEM_TYPE_LABELS[itemType] ?? itemType;
}

export function priorityLabel(priority: string | null): string {
  if (!priority) return "Not set";
  return PRIORITY_LABELS[priority] ?? priority;
}

export function dueDateIndicatorLabel(indicator: string): string {
  return DUE_DATE_INDICATOR_LABELS[indicator] ?? indicator;
}
