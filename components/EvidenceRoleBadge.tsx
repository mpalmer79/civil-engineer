const roleStyles: Record<string, { label: string; className: string }> = {
  supports_finding: {
    label: "supports",
    className: "bg-land-50 text-land-700 ring-land-600/20",
  },
  shows_missing_evidence: {
    label: "missing evidence",
    className: "bg-red-50 text-red-700 ring-red-600/20",
  },
  shows_conflict: {
    label: "conflict",
    className: "bg-amber-50 text-amber-700 ring-amber-600/20",
  },
  context_only: {
    label: "context",
    className: "bg-slate-100 text-slate-600 ring-slate-300",
  },
  requires_reviewer_confirmation: {
    label: "needs reviewer confirmation",
    className: "bg-yellow-50 text-yellow-700 ring-yellow-600/20",
  },
};

export default function EvidenceRoleBadge({ role }: { role: string }) {
  const style = roleStyles[role] ?? {
    label: role,
    className: "bg-slate-100 text-slate-600 ring-slate-300",
  };
  return <span className={`badge ${style.className}`}>{style.label}</span>;
}
