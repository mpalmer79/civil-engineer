import Link from "next/link";
import type { Metadata } from "next";
import RequestFailureCard from "@/components/RequestFailureCard";

import BrooksideProjectVisual from "@/components/BrooksideProjectVisual";
import PageHeader from "@/components/PageHeader";
import GuidedDemoExperience, {
  type DemoProofCard,
} from "@/components/GuidedDemoExperience";
import PilotReleaseNote from "@/components/PilotReleaseNote";
import { aecDemoSteps, BROOKSIDE_PROJECT_ID } from "@/lib/demoJourney";
import {
  getCadReviewFindings,
  getPlanConsistencySummary,
  getProjectTraceability,
} from "@/lib/api";
import { pageMetadata } from "@/lib/pageMetadata";

export const dynamic = "force-dynamic";

export const metadata: Metadata = pageMetadata({
  title: "Brookside Meadows Guided Review | Civil Engineer AI",
  description:
    "Follow a synthetic 47-lot subdivision through document intake, evidence review, findings, applicant responses, and reviewer-controlled handoff. Seeded demo data, no login needed.",
  path: "/guided-demo",
});

// Build a fixture-backed proof card. When a count is available it shows the
// number; when the backend is unavailable it falls back to a qualitative card
// instead of inventing a value.
function proofCard(value: number | null | undefined, label: string): DemoProofCard {
  return { value: typeof value === "number" ? String(value) : null, label };
}

export default async function GuidedDemoPage() {
  // Fixture-backed counts from the seeded Brookside Meadows demo, fetched in
  // parallel. This is a public demo surface: when the backend misses, the demo
  // degrades to qualitative proof cards rather than fake numbers or a
  // full-page failure.
  const [traceabilityResult, planSummaryResult, cadFindingsResult] = await Promise.all([
    getProjectTraceability(BROOKSIDE_PROJECT_ID),
    getPlanConsistencySummary(BROOKSIDE_PROJECT_ID),
    getCadReviewFindings(BROOKSIDE_PROJECT_ID),
  ]);
  const traceability = traceabilityResult.ok ? traceabilityResult.data : null;
  const planSummary = planSummaryResult.ok ? planSummaryResult.data : null;
  const cadFindings = cadFindingsResult.ok ? cadFindingsResult.data : null;

  const summary = traceability?.summary ?? null;
  const proof: DemoProofCard[] = [
    proofCard(cadFindings?.length || null, "CAD review-support findings"),
    proofCard(planSummary?.planConsistencyFindings, "Plan consistency findings"),
    proofCard(summary?.totalTraceabilityRows, "Traceability rows"),
    proofCard(summary?.totalWorkflowItems, "Workflow items"),
    proofCard(summary?.totalPacketItems, "Review packet items"),
  ];

  return (
    <div>
      <PageHeader
        eyebrow="Guided demo · Sample project"
        title="Run the Brookside Meadows pre-submittal QA"
        description="See how a civil and AEC team catches review-support issues before a stormwater package goes to a municipal reviewer. This guided demo runs on the Brookside Meadows sample project using seeded demo data. No login is needed."
        actions={
          <Link href="/start-here" className="btn btn-secondary">
            Start Here overview
          </Link>
        }
      />

      <div className="mx-auto max-w-5xl space-y-8 px-4 py-6 sm:px-6 sm:py-10 lg:px-8">
        {/* Restrained Brookside cover: names the case study and shows the
            conceptual aerial without pushing the first demo action out of
            reach. */}
        <section
          aria-labelledby="brookside-cover-heading"
          className="surface-card p-4 sm:p-6"
        >
          <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr] lg:items-center lg:gap-8">
            <BrooksideProjectVisual variant="demo-cover" priority />
            <div>
              <h2
                id="brookside-cover-heading"
                className="text-lg font-semibold text-slate-900"
              >
                Brookside Meadows Guided Review
              </h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
                Follow a synthetic 47-lot subdivision through document intake,
                evidence review, findings, applicant responses, and
                reviewer-controlled handoff.
              </p>
            </div>
          </div>
        </section>

        {/* Buyer context and what the demo will show, before the tour. */}
        <section className="surface-card p-6">
          <h2 className="text-lg font-semibold text-slate-900">
            Brookside Meadows pre-submittal QA
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            The simulated buyer is a civil and AEC team preparing a stormwater
            and site package. They want to catch the review-support issues a
            municipal reviewer would catch, before they submit, to reduce
            avoidable resubmittal risk.
          </p>
          <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
            What this demo will show
          </p>
          <ol className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {aecDemoSteps.map((s) => (
              <li
                key={s.id}
                className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700"
              >
                <span className="font-semibold text-slate-900">{s.step}.</span>{" "}
                {s.eyebrow}
              </li>
            ))}
          </ol>
        </section>

        <GuidedDemoExperience
          projectId={BROOKSIDE_PROJECT_ID}
          steps={aecDemoSteps}
          proof={proof}
          pilotHref="/pilot"
        />

        <PilotReleaseNote variant="compact" />
      </div>
    </div>
  );
}
