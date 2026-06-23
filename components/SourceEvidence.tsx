import type { EvidenceItem } from "@/lib/api";
import EvidenceRoleBadge from "@/components/EvidenceRoleBadge";

// Renders source evidence for a finding or checklist item. Evidence is source
// material for reviewer evaluation, not a final engineering conclusion.
export default function SourceEvidence({
  evidence,
  emptyNote = "Source evidence is served by the backend. Start the API to view linked chunks.",
}: {
  evidence: EvidenceItem[];
  emptyNote?: string;
}) {
  if (evidence.length === 0) {
    return (
      <p className="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-500">
        {emptyNote}
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <ul className="space-y-2">
        {evidence.map((item, i) => (
          <li
            key={`${item.chunkId ?? item.documentId}-${i}`}
            className="rounded-lg border border-slate-200 bg-white p-3"
          >
            <div className="flex flex-wrap items-center gap-2">
              {item.evidenceRole ? (
                <EvidenceRoleBadge role={item.evidenceRole} />
              ) : null}
              <span className="text-xs font-medium text-slate-500">
                retrieval score {Math.round(item.score * 100)}%
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-700">{item.excerpt}</p>
            <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-400">
              <span className="font-mono">{item.fileName}</span>
              {item.pageNumber != null ? (
                <span>page {item.pageNumber}</span>
              ) : null}
              {item.sectionHeading ? (
                <span>section: {item.sectionHeading}</span>
              ) : null}
            </div>
            <p className="mt-1 text-xs text-slate-500">{item.relevanceReason}</p>
          </li>
        ))}
      </ul>
      <p className="text-xs italic text-slate-400">
        {evidence[0].safetyNote} Needs human review.
      </p>
    </div>
  );
}
