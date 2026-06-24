// Status badge for Phase 6 plan sheet statuses, plan reference consistency
// statuses, and plan consistency finding types. None of these labels uses final
// decision language such as approved, certified, or compliant.

const styles: Record<string, string> = {
  // Plan sheet statuses
  present: "bg-land-50 text-land-700 ring-land-600/20",
  current: "bg-land-50 text-land-700 ring-land-600/20",
  missing: "bg-red-50 text-red-700 ring-red-600/20",
  referenced_not_included: "bg-orange-50 text-orange-700 ring-orange-600/20",
  superseded: "bg-slate-100 text-slate-600 ring-slate-300",
  needs_reviewer_confirmation: "bg-amber-50 text-amber-700 ring-amber-600/20",
  // Plan reference consistency statuses
  consistent: "bg-land-50 text-land-700 ring-land-600/20",
  missing_target: "bg-red-50 text-red-700 ring-red-600/20",
  conflicting_label: "bg-amber-50 text-amber-700 ring-amber-600/20",
  unclear: "bg-yellow-50 text-yellow-700 ring-yellow-600/20",
  needs_human_review: "bg-amber-50 text-amber-700 ring-amber-600/20",
  // Plan consistency finding types
  missing_sheet: "bg-red-50 text-red-700 ring-red-600/20",
  missing_referenced_sheet: "bg-orange-50 text-orange-700 ring-orange-600/20",
  missing_plan_reference: "bg-red-50 text-red-700 ring-red-600/20",
  unclear_revision: "bg-yellow-50 text-yellow-700 ring-yellow-600/20",
  cad_metadata_gap: "bg-amber-50 text-amber-700 ring-amber-600/20",
  requires_human_review: "bg-amber-50 text-amber-700 ring-amber-600/20",
  // Phase 7 plan consistency review action statuses
  needs_follow_up: "bg-amber-50 text-amber-700 ring-amber-600/20",
  reviewer_confirmed: "bg-water-50 text-water-700 ring-water-600/20",
  not_applicable: "bg-slate-100 text-slate-600 ring-slate-300",
  needs_more_information: "bg-yellow-50 text-yellow-700 ring-yellow-600/20",
};

const labels: Record<string, string> = {
  referenced_not_included: "referenced, not included",
  needs_reviewer_confirmation: "needs reviewer confirmation",
  missing_target: "missing target",
  conflicting_label: "conflicting label",
  needs_human_review: "needs human review",
  missing_sheet: "missing sheet",
  missing_referenced_sheet: "missing referenced sheet",
  missing_plan_reference: "missing plan reference",
  unclear_revision: "unclear revision",
  cad_metadata_gap: "CAD metadata gap",
  requires_human_review: "requires human review",
  needs_follow_up: "needs follow up",
  reviewer_confirmed: "reviewer confirmed",
  not_applicable: "not applicable",
  needs_more_information: "needs more information",
};

export default function PlanStatusBadge({ status }: { status: string }) {
  const style = styles[status] ?? "bg-slate-100 text-slate-600 ring-slate-300";
  return <span className={`badge ${style}`}>{labels[status] ?? status}</span>;
}
