import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SourceBadge from "@/components/SourceBadge";
import StatusChip from "@/components/StatusChip";
import EmptyState from "@/components/EmptyState";
import CreateResponsePackageButton from "@/components/CreateResponsePackageButton";
import { getProjectDetail, listResponsePackages } from "@/lib/api";

export const dynamic = "force-dynamic";

// Response packages landing page. Lists reviewer response packages and links to
// each one. A response package assembles reviewer-selected records into a
// controlled communication artifact. It does not approve a project, certify
// compliance, resolve an issue, or close an issue.
export default async function ResponsePackagesLandingPage(
  props: {
    params: Promise<{ projectId: string }>;
  }
) {
  const params = await props.params;
  const [project, packages] = await Promise.all([
    getProjectDetail(params.projectId),
    listResponsePackages(params.projectId),
  ]);
  if (!project) {
    notFound();
  }
  const base = `/projects/${params.projectId}`;

  return (
    <div>
      <PageHeader
        eyebrow="Reviewer response packages"
        title={`Response packages for ${project.projectName}`}
        description="Assemble reviewer-selected findings, checklist items, response matrix items, and citations into a controlled response package, then generate a deterministic comment letter draft. Package issuance records a reviewer communication. It does not finalize a review outcome, resolve issues, or close issues."
      />
      <div className="mx-auto max-w-6xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-3">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link href={`${base}/response-matrix`} className="nav-link">
            Response matrix
          </Link>
          <SourceBadge sourceMode={project.sourceMode} />
        </div>

        <SectionCard
          title="Response packages"
          description="Each package collects reviewer-selected records and tracks status from draft through reviewer handoff and issuance."
        >
          {packages === null ? (
            <p className="alert alert-warning">
              Response packages are served by the backend. Start the API to view
              them.
            </p>
          ) : packages.length === 0 ? (
            <EmptyState
              title="No response package yet"
              description="Create reviewer findings, checklist review items, or response matrix items first, then create a package to assemble a reviewer communication."
            />
          ) : (
            <ul className="grid gap-4 sm:grid-cols-2">
              {packages.map((p) => (
                <li key={p.responsePackageId} className="surface-card p-4">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <Link
                      href={`${base}/response-packages/${p.responsePackageId}`}
                      className="text-base font-semibold text-water-700 hover:underline"
                    >
                      {p.packageTitle}
                    </Link>
                    <StatusChip label={p.status} prefix="status" />
                  </div>
                  <p className="mt-2 text-sm text-slate-600">
                    {p.packageType.replace(/_/g, " ")}. Package {p.packageNumber},
                    revision {p.revisionNumber}. {p.itemCount} item(s).
                    {p.issuedByName ? ` Issued by ${p.issuedByName}.` : ""}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        <CreateResponsePackageButton projectId={params.projectId} />

        <p className="alert alert-info">
          Response packages are review-support communication only. Issuing a
          package records that a reviewer issued a communication. It does not
          approve plans, certify compliance, validate design, resolve issues, or
          close issues. Every package needs human review.
        </p>
      </div>
    </div>
  );
}
