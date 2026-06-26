import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
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
          <SectionCard title="Backend required">
            <p className="text-sm text-slate-600">
              Rule packs are served by the backend. Start the API to view them.
            </p>
          </SectionCard>
        ) : rulePacks.length === 0 ? (
          <SectionCard title="No rule packs yet">
            <p className="text-sm text-slate-600">
              No rule packs are available yet.
            </p>
          </SectionCard>
        ) : (
          <ul className="space-y-3">
            {rulePacks.map((pack) => (
              <li key={pack.rulePackId} className="surface-card p-5 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <Link
                    href={`/rule-packs/${pack.rulePackId}`}
                    className="text-base font-semibold text-water-700 hover:underline"
                  >
                    {pack.name}
                  </Link>
                  <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
                    {pack.isActive ? "Active" : "Inactive"}
                  </span>
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
