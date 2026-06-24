// Status badge for reviewer workflow board items. None of these statuses is a
// final engineering decision; they describe where an item sits in the review
// workflow.
const styles: Record<string, string> = {
  draft: "bg-slate-100 text-slate-600 ring-slate-300",
  needs_triage: "bg-sky-50 text-sky-700 ring-sky-600/20",
  needs_follow_up: "bg-amber-50 text-amber-700 ring-amber-600/20",
  needs_more_information: "bg-orange-50 text-orange-700 ring-orange-600/20",
  reviewer_checked: "bg-land-50 text-land-700 ring-land-600/20",
  excluded_from_packet: "bg-slate-100 text-slate-500 ring-slate-300",
  ready_for_handoff: "bg-water-50 text-water-700 ring-water-600/20",
};

const labels: Record<string, string> = {
  draft: "draft",
  needs_triage: "needs triage",
  needs_follow_up: "needs follow-up",
  needs_more_information: "needs more information",
  reviewer_checked: "reviewer checked",
  excluded_from_packet: "excluded from packet",
  ready_for_handoff: "ready for handoff",
};

export default function WorkflowStatusBadge({ status }: { status: string }) {
  const style = styles[status] ?? "bg-slate-100 text-slate-600 ring-slate-300";
  return (
    <span className={`badge ${style}`}>{labels[status] ?? status}</span>
  );
}
