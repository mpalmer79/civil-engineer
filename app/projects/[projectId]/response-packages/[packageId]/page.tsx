import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import StatusChip from "@/components/StatusChip";
import EmptyState from "@/components/EmptyState";
import PackageItemActions from "@/components/PackageItemActions";
import AddSourcesToPackagePanel from "@/components/AddSourcesToPackagePanel";
import ResponsePackageWorkflow from "@/components/ResponsePackageWorkflow";
import { getResponsePackageDetail, listProjectFindings } from "@/lib/api";

export const dynamic = "force-dynamic";

// Response package detail page. Shows the package metadata, the reviewer-selected
// items, controls to add records and run the package workflow. Package issuance
// records a reviewer communication only. Nothing here approves, resolves, or
// closes anything.
export default async function ResponsePackageDetailPage(
  props: {
    params: Promise<{ projectId: string; packageId: string }>;
  }
) {
  const params = await props.params;
  const [pkg, findings] = await Promise.all([
    getResponsePackageDetail(params.projectId, params.packageId),
    listProjectFindings(params.projectId),
  ]);
  if (!pkg) {
    notFound();
  }
  const base = `/projects/${params.projectId}`;
  const items = pkg.items ?? [];

  const metadata: [string, string | null][] = [
    ["Package type", pkg.packageType.replace(/_/g, " ")],
    ["Status", pkg.status],
    ["Package number", String(pkg.packageNumber)],
    ["Revision number", String(pkg.revisionNumber)],
    ["Prepared by", pkg.preparedByName ?? "Seeded demo"],
    ["Issued by", pkg.issuedByName],
    ["Issued at", pkg.issuedAt],
  ];

  return (
    <div>
      <PageHeader
        eyebrow="Response package"
        title={pkg.packageTitle}
        description="A reviewer-controlled communication artifact. Package issuance records a reviewer communication. It does not finalize a review outcome, resolve issues, or close issues."
      />
      <div className="mx-auto max-w-5xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-3">
          <Link href={`${base}/response-packages`} className="nav-link">
            Back to response packages
          </Link>
          <Link
            href={`${base}/response-packages/${pkg.responsePackageId}/preview`}
            className="nav-link"
          >
            Preview package
          </Link>
          <StatusChip label={pkg.status} prefix="status" />
        </div>

        <SectionCard title="Package metadata">
          <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
            {metadata.map(([label, value]) => (
              <div
                key={label}
                className="flex justify-between gap-4 border-b border-slate-100 pb-2"
              >
                <dt className="text-sm font-semibold text-slate-500">{label}</dt>
                <dd className="text-sm text-slate-800">{value ?? "n/a"}</dd>
              </div>
            ))}
          </dl>
        </SectionCard>

        <SectionCard
          title="Selected package items"
          description="Reviewer-selected records included in this package. Toggle whether each item is included in the comment letter and update its review-support status."
        >
          {items.length === 0 ? (
            <EmptyState
              title="No items yet"
              description="Add reviewer-selected records before previewing the package."
            />
          ) : (
            <ul className="space-y-3">
              {items.map((item) => (
                <li
                  key={item.responsePackageItemId}
                  className="subtle-card p-4 text-sm"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-semibold text-slate-800">
                      {item.itemNumber ? `Item ${item.itemNumber}` : "Item"}
                      {item.category ? ` - ${item.category}` : ""}
                    </span>
                    <StatusChip label={item.itemStatus} prefix="status" />
                  </div>
                  <p className="mt-1 text-slate-700">{item.reviewerCommentText}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    Source: {item.sourceType.replace(/_/g, " ")}.{" "}
                    {item.includeInLetter
                      ? "Included in letter."
                      : "Excluded from letter."}
                  </p>
                  <PackageItemActions projectId={params.projectId} item={item} />
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        <AddSourcesToPackagePanel
          projectId={params.projectId}
          packageId={pkg.responsePackageId}
          findings={findings ?? []}
        />

        <ResponsePackageWorkflow
          projectId={params.projectId}
          packageId={pkg.responsePackageId}
        />

        <p className="alert alert-info">
          This package is review-support communication only. Issuance records a
          reviewer communication and does not approve, certify, validate, resolve,
          or close anything.
        </p>
      </div>
    </div>
  );
}
