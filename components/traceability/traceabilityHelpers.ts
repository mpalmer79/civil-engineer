import { humanizeStatus } from "@/components/StatusChip";
import type {
  ProjectTraceabilityRow,
  ProjectTraceabilitySourceLink,
} from "@/lib/api";

// Pure helpers for the review-support traceability matrix. Nothing here states
// a requirement is satisfied, approved, certified, verified, or validated.

// Reviewer review action options. Labels stay review-support only: confirming a
// link confirms it is useful for review, not that a requirement is satisfied.
export const REVIEW_ACTIONS: { value: string; label: string }[] = [
  { value: "reviewer_confirmed_link", label: "Confirm link for review" },
  { value: "needs_more_information", label: "Needs more information" },
  { value: "not_applicable", label: "Not applicable" },
  { value: "link_rejected", label: "Reject link" },
  { value: "follow_up_needed", label: "Follow-up needed" },
  { value: "needs_review", label: "Needs review" },
];

const ACTION_LABELS: Record<string, string> = Object.fromEntries(
  REVIEW_ACTIONS.map((a) => [a.value, a.label]),
);

export function actionLabel(actionType: string): string {
  return ACTION_LABELS[actionType] ?? humanizeStatus(actionType);
}

export function resolveRoute(
  projectId: string,
  link: ProjectTraceabilitySourceLink,
): { label: string; href: string } | null {
  const id = link.id ?? "";
  switch (link.type) {
    case "document":
      return id
        ? { label: "Document", href: `/projects/${projectId}/documents/${id}` }
        : null;
    case "finding":
      return id
        ? { label: "Finding", href: `/projects/${projectId}/findings/${id}` }
        : null;
    case "workflow_board":
      return {
        label: "Workflow board",
        href: `/projects/${projectId}/workflow-board`,
      };
    case "review_packet":
      return {
        label: "Review packets",
        href: `/projects/${projectId}/review-packets`,
      };
    case "plan_sheet":
      return id
        ? {
            label: "Plan sheet",
            href: `/projects/${projectId}/plan-sheets/${id}`,
          }
        : null;
    default:
      return null;
  }
}

export type TraceabilityFilters = {
  status: string;
  relationship: string;
  action: string;
  documentId: string;
  source: string;
  packet: string;
};

// Client-side row filtering. This is a filtered view of existing links, not a
// statement that requirements are satisfied or unsupported.
export function filterTraceabilityRows(
  rows: ProjectTraceabilityRow[],
  filters: TraceabilityFilters,
): ProjectTraceabilityRow[] {
  const { status, relationship, action, documentId, source, packet } = filters;
  return rows.filter((r) => {
    if (status !== "all" && r.checklistStatus !== status) return false;
    if (relationship !== "all" && r.relationshipType !== relationship)
      return false;
    if (action === "yes" && !r.reviewerActionNeeded) return false;
    if (action === "no" && r.reviewerActionNeeded) return false;
    if (documentId !== "all" && r.documentId !== documentId) return false;
    if (source !== "all" && r.relationshipSource !== source) return false;
    if (packet === "in" && (r.packetContextCount ?? 0) === 0) return false;
    if (packet === "out" && (r.packetContextCount ?? 0) > 0) return false;
    return true;
  });
}
