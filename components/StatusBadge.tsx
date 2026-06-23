import type { ChecklistStatus } from "@/data/checklist";
import type { DocumentStatus } from "@/data/documents";

type Status = ChecklistStatus | DocumentStatus;

const styles: Record<Status, string> = {
  // Checklist / finding statuses
  supported: "bg-land-50 text-land-700 ring-land-600/20",
  missing: "bg-red-50 text-red-700 ring-red-600/20",
  conflicting: "bg-amber-50 text-amber-700 ring-amber-600/20",
  unclear: "bg-yellow-50 text-yellow-700 ring-yellow-600/20",
  unresolved: "bg-orange-50 text-orange-700 ring-orange-600/20",
  not_applicable: "bg-slate-100 text-slate-500 ring-slate-300",
  // Document statuses
  present: "bg-land-50 text-land-700 ring-land-600/20",
  partial: "bg-amber-50 text-amber-700 ring-amber-600/20",
  referenced_not_included: "bg-orange-50 text-orange-700 ring-orange-600/20",
  not_yet_submitted: "bg-slate-100 text-slate-600 ring-slate-300",
};

const labels: Partial<Record<Status, string>> = {
  not_applicable: "not applicable",
  referenced_not_included: "referenced, not included",
  not_yet_submitted: "not yet submitted",
};

export default function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={`badge ${styles[status]}`}>
      {labels[status] ?? status}
    </span>
  );
}
