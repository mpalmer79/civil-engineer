import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import StatusChip from "@/components/StatusChip";
import { listRulePacks } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function RulePacksPage() {
  const rulePacks = await listRulePacks();

  return (
    <div>
      <PageHeader
        eyebrow="Checklist foundation"
        title="Rule packs"
        description="Reusable review-support checklist templates for stormwater review. A rule pack is a review template, not a legal determination, not a compliance standard, and not jurisdiction-adopted ordinance language. A reviewer decides applicability and evidence status for each item."
      />

      <div className="mx-auto max-w-6xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        {rulePacks === null ? (
          <div className="alert alert-warning" role="alert">
            <p className="font-semibold">Backend required</p>
            <p className="mt-1">
              Rule packs are served by the backend. Start the API to view them.
            </p>
          </div>
        ) : rulePacks.length === 0 ? (
          <EmptyState
            title="No rule packs yet"
            description="Review-support checklist templates appear here once the backend provides them. A rule pack is a review template, not jurisdiction-adopted ordinance language."
          />
        ) : (
          <ul className="space-y-3">
            {rulePacks.map((pack) => (
              <li
                key={pack.rulePackId}
                className="interactive-card p-5 text-sm"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <Link
                    href={`/rule-packs/${pack.rulePackId}`}
                    className="text-base font-semibold text-water-700 hover:underline"
                  >
                    {pack.name}
                  </Link>
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusChip label="Review-support template" tone="brand" />
                    <StatusChip
                      tone={pack.isActive ? "success" : "neutral"}
                      label={pack.isActive ? "Active" : "Inactive"}
                    />
                  </div>
                </div>
                <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1 sm:grid-cols-4">
                  <div>
                    <dt className="text-xs font-semibold uppercase text-slate-500">
                      Jurisdiction
                    </dt>
                    <dd className="text-slate-800">{pack.jurisdictionName}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-semibold uppercase text-slate-500">
                      Review domain
                    </dt>
                    <dd className="text-slate-800">{pack.reviewDomain}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-semibold uppercase text-slate-500">
                      Version
                    </dt>
                    <dd className="text-slate-800">{pack.versionLabel}</dd>
                  </div>
                  <div>
                    <dt className="text-xs font-semibold uppercase text-slate-500">
                      Items
                    </dt>
                    <dd className="text-slate-800">{pack.itemCount}</dd>
                  </div>
                </dl>
              </li>
            ))}
          </ul>
        )}

        <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          Starter rule packs are review-support templates, not legal
          determinations. Checklist evidence status is for review support and
          requires human confirmation.
        </p>
      </div>
    </div>
  );
}
