import Link from "next/link";
import { notFound } from "next/navigation";

import PageHeader from "@/components/PageHeader";
import SectionCard from "@/components/SectionCard";
import SourceBadge from "@/components/SourceBadge";
import RegisterResubmittalRound from "@/components/RegisterResubmittalRound";
import { getProjectDetail, listResubmittalRounds } from "@/lib/api";

export const dynamic = "force-dynamic";

// Resubmittal rounds landing page. Lists registered resubmittal rounds and lets a
// reviewer register a new round. Registering a round records an applicant
// submission for reviewer review. It does not decide whether the resubmittal
// satisfies engineering requirements and does not resolve or close anything.
export default async function ResubmittalRoundsPage(
  props: {
    params: Promise<{ projectId: string }>;
  }
) {
  const params = await props.params;
  const [project, rounds] = await Promise.all([
    getProjectDetail(params.projectId),
    listResubmittalRounds(params.projectId),
  ]);
  if (!project) {
    notFound();
  }
  const base = `/projects/${params.projectId}`;

  return (
    <div>
      <PageHeader
        eyebrow="Resubmittal rounds"
        title={`Resubmittal rounds for ${project.projectName}`}
        description="Register applicant resubmittals and track them across review rounds. A resubmittal round records an applicant submission for reviewer review. It does not finalize a review outcome and does not resolve or close anything."
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
          title="Registered rounds"
          description="Each round groups the documents and carried-forward items received from the applicant for that review round."
        >
          {rounds === null ? (
            <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
              Resubmittal rounds are served by the backend. Start the API to
              view them.
            </p>
          ) : rounds.length === 0 ? (
            <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-500">
              No resubmittal rounds registered yet. Register a round below when
              the applicant submits revised material.
            </p>
          ) : (
            <ul className="space-y-3">
              {rounds.map((r) => (
                <li
                  key={r.resubmittalRoundId}
                  className="rounded-lg border border-slate-200 p-4"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <Link
                      href={`${base}/resubmittals/${r.resubmittalRoundId}`}
                      className="text-base font-semibold text-water-700 hover:underline"
                    >
                      Round {r.roundNumber}: {r.roundLabel}
                    </Link>
                    <span className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">
                      {r.status}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">
                    {r.documentCount} document(s), {r.carriedForwardItemCount}{" "}
                    carried-forward item(s).
                    {r.submittedByName
                      ? ` Submitted by ${r.submittedByName}.`
                      : ""}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        <RegisterResubmittalRound projectId={params.projectId} />

        <p className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          Resubmittal rounds are review-support records only. Registering a round
          and linking documents does not decide whether the resubmittal satisfies
          engineering requirements. Every round needs human review.
        </p>
      </div>
    </div>
  );
}
