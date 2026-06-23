import type { Finding } from "@/data/findings";
import type { EvidenceItem } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import RiskBadge from "@/components/RiskBadge";
import SourceEvidence from "@/components/SourceEvidence";

export default function FindingCard({
  finding,
  evidence = [],
}: {
  finding: Finding;
  evidence?: EvidenceItem[];
}) {
  return (
    <article className="surface-card flex flex-col p-6">
      <div className="flex flex-wrap items-center gap-2">
        <span className="badge bg-slate-100 text-slate-600 ring-slate-300">
          Expected finding
        </span>
        <span className="badge bg-water-50 text-water-700 ring-water-600/20">
          {finding.category}
        </span>
        <RiskBadge level={finding.riskLevel} />
        <StatusBadge status={finding.expectedStatus} />
      </div>

      <h3 className="mt-3 text-base font-semibold text-slate-900">
        {finding.title}
      </h3>

      <dl className="mt-4 space-y-3 text-sm">
        <div>
          <dt className="font-semibold text-slate-700">Evidence to find</dt>
          <dd className="mt-0.5 text-slate-600">{finding.evidenceToFind}</dd>
        </div>
        <div>
          <dt className="font-semibold text-slate-700">Why it matters</dt>
          <dd className="mt-0.5 text-slate-600">{finding.whyItMatters}</dd>
        </div>
        <div>
          <dt className="font-semibold text-slate-700">
            Recommended human action
          </dt>
          <dd className="mt-0.5 text-slate-600">
            {finding.recommendedHumanAction}
          </dd>
        </div>
      </dl>

      <div className="mt-4 border-t border-slate-100 pt-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Source evidence
        </p>
        <div className="mt-2">
          <SourceEvidence evidence={evidence} />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-4 text-xs">
        <span className="flex items-center gap-2 text-slate-500">
          <span className="font-mono">{finding.checklistItemId}</span>
          <span aria-hidden="true">·</span>
          <span className="font-mono">{finding.plantedIssue}</span>
        </span>
        <span className="badge bg-yellow-50 text-yellow-700 ring-yellow-600/20">
          Human review: {finding.humanReviewState}, needs reviewer confirmation
        </span>
      </div>
    </article>
  );
}
