import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import RequestFailureCard from "@/components/RequestFailureCard";
import SectionCard from "@/components/SectionCard";
import StatusChip from "@/components/StatusChip";
import { getRulePack } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function RulePackDetailPage(
  props: {
    params: Promise<{ rulePackId: string }>;
  }
) {
  const params = await props.params;
  const packResult = await getRulePack(params.rulePackId);
  if (!packResult.ok) {
    if (packResult.kind === "not_found") notFound();
    return (
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <RequestFailureCard failure={packResult} />
      </div>
    );
  }
  const pack = packResult.data;
  const items = pack.items ?? [];
  const categories = Array.from(new Set(items.map((i) => i.category)));

  return (
    <div>
      <PageHeader
        eyebrow="Rule pack"
        title={pack.name}
        description={pack.description ?? "Review-support checklist template."}
      />

      <div className="mx-auto max-w-5xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-3">
          <Link href="/rule-packs" className="nav-link">
            Back to rule packs
          </Link>
          <StatusChip label={pack.jurisdictionName} />
          <StatusChip label={pack.versionLabel} prefix="version" tone="brand" />
          <StatusChip label={`${pack.itemCount} items`} />
        </div>

        <p className="alert alert-warning">
          This is a starter review template, not a legal ordinance and not a
          compliance standard. A reviewer decides applicability and evidence
          status for each item.
        </p>

        {categories.map((category) => (
          <SectionCard key={category} title={category}>
            <ul className="space-y-3">
              {items
                .filter((i) => i.category === category)
                .map((item) => (
                  <li
                    key={item.rulePackItemId}
                    className="subtle-card p-4 text-sm"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <span className="font-semibold text-slate-800">
                        {item.itemCode}: {item.requirementText}
                      </span>
                      <StatusChip label={item.riskLevel} prefix="risk" />
                    </div>
                    <p className="mt-1 text-slate-600">
                      <span className="font-semibold text-slate-500">
                        Expected evidence:
                      </span>{" "}
                      {item.expectedEvidence}
                    </p>
                    {item.applicabilityNote ? (
                      <p className="mt-1 text-xs text-slate-500">
                        Applicability: {item.applicabilityNote}
                      </p>
                    ) : null}
                    {item.referenceLabel ? (
                      <p className="mt-1 text-xs italic text-slate-400">
                        {item.referenceLabel}
                      </p>
                    ) : null}
                  </li>
                ))}
            </ul>
          </SectionCard>
        ))}
      </div>
    </div>
  );
}
