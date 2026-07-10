import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SourceBadge from "@/components/SourceBadge";
import CreateResponseMatrixButton from "@/components/CreateResponseMatrixButton";
import { getProjectDetail, listResponseMatrices } from "@/lib/api";

export const dynamic = "force-dynamic";

// Response matrix landing page. Lists the project response matrices and links to
// each one. A response matrix organizes review-support items and tracks applicant
// responses for reviewer review. It does not approve, certify, verify, resolve, or
// close anything.
export default async function ResponseMatrixLandingPage(
  props: {
    params: Promise<{ projectId: string }>;
  }
) {
  const params = await props.params;
  const [project, matrices] = await Promise.all([
    getProjectDetail(params.projectId),
    listResponseMatrices(params.projectId),
  ]);
  if (!project) {
    notFound();
  }
  const base = `/projects/${params.projectId}`;

  return (
    <div>
      <PageHeader
        eyebrow="Applicant response matrix"
        title={`Response matrix for ${project.projectName}`}
        description="Organize reviewer findings and checklist review items into a response matrix, then record applicant responses for reviewer review across resubmittal rounds. The matrix does not finalize a review outcome and does not resolve or close anything."
      />

      <div className="mx-auto max-w-6xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-3">
          <Link href={base} className="nav-link">
            Back to project
          </Link>
          <Link href={`${base}/findings`} className="nav-link">
            Reviewer findings
          </Link>
          <Link href={`${base}/resubmittals`} className="nav-link">
            Resubmittal rounds
          </Link>
          <SourceBadge sourceMode={project.sourceMode} />
        </div>

        <SectionCard
          title="Response matrices"
          description="Each matrix tracks applicant responses and reviewer follow-up status for a set of review-support items."
        >
          {matrices === null ? (
            <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
              Response matrices are served by the backend. Start the API to view
              them.
            </p>
          ) : matrices.length === 0 ? (
            <div className="space-y-4">
              <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
                No response matrix yet. Create reviewer findings or checklist
                review items before building a response matrix, then create a
                matrix to start tracking applicant responses for reviewer review.
              </p>
              <CreateResponseMatrixButton projectId={params.projectId} />
            </div>
          ) : (
            <div className="space-y-4">
              <ul className="space-y-3">
                {matrices.map((m) => (
                  <li
                    key={m.responseMatrixId}
                    className="rounded-lg border border-slate-200 p-4"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <Link
                        href={`${base}/response-matrix/${m.responseMatrixId}`}
                        className="text-base font-semibold text-water-700 hover:underline"
                      >
                        {m.name}
                      </Link>
                      <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
                        {m.status}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">
                      {m.itemCount} item(s). Current review round{" "}
                      {m.currentRoundNumber}. Created by{" "}
                      {m.createdByName ?? "Seeded demo"}.
                    </p>
                  </li>
                ))}
              </ul>
              <CreateResponseMatrixButton projectId={params.projectId} />
            </div>
          )}
        </SectionCard>

        <p className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          The response matrix is review-support only. Applicant responses are
          recorded for reviewer review, never as proof and never as a final
          outcome. Carry-forward keeps an item under review across rounds. Every
          item needs human review.
        </p>
      </div>
    </div>
  );
}
