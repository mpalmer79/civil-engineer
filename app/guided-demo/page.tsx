import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import GuidedDemoThread from "@/components/GuidedDemoThread";
import GuidedDemoCard from "@/components/GuidedDemoCard";
import DemoNoteCard from "@/components/DemoNoteCard";
import MarketingMedia from "@/components/MarketingMedia";
import { BROOKSIDE_PROJECT_ID, demoJourneySteps } from "@/lib/demoJourney";
import { marketingMedia } from "@/lib/marketingMedia";

export const dynamic = "force-dynamic";

export default function GuidedDemoPage() {
  const base = `/projects/${BROOKSIDE_PROJECT_ID}`;
  return (
    <div>
      <PageHeader
        eyebrow="Guided demo"
        title="Walk the Brookside Meadows reviewer journey"
        description="Brookside Meadows is a synthetic public demo fixture. Follow the recommended demo path through the review-support workflow, then see one concern traced end to end. New here? Start Here gives the fastest overview."
        actions={
          <Link href="/start-here" className="btn btn-secondary">
            Start Here overview
          </Link>
        }
      />

      <div className="mx-auto max-w-5xl space-y-10 px-4 py-10 sm:px-6 lg:px-8">
        <SafetyBoundaryBanner variant="compact" />

        <DemoNoteCard
          message="You are exploring the public Brookside Meadows sample project. No account is needed to look around; some deeper records may prompt sign in."
          actionHref={base}
          actionLabel="Open Brookside Meadows"
        />

        {/* Recommended demo path: the reviewer journey, step by step. */}
        <section>
          <h2 className="section-title">Recommended demo path</h2>
          <p className="mt-2 max-w-3xl text-slate-600">
            The reviewer journey in the order a reviewer works, from the sample
            project through documents, evidence, checklist review, findings,
            applicant responses, resubmittals, the response package, and the
            dashboard.
          </p>
          <MarketingMedia
            src={marketingMedia.guidedDemoJourney.src}
            alt={marketingMedia.guidedDemoJourney.alt}
            variant="wide"
            className="mt-6"
            label="Guided demo placeholder"
          />
          <ol className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {demoJourneySteps.map((step) => (
              <li key={step.step}>
                <GuidedDemoCard step={step} />
              </li>
            ))}
          </ol>
        </section>

        {/* One concern, end to end: the narrative deep dive. */}
        <section>
          <h2 className="section-title">One concern, end to end</h2>
          <p className="mt-2 max-w-3xl text-slate-600">
            For a deeper look, follow a single review-support concern, missing
            infiltration testing and an unaddressed groundwater separation
            discussion, from checklist requirement through finding, evidence,
            review packet, workflow board, and draft response, ending at the
            human-review boundary.
          </p>
          <div className="mt-6">
            <GuidedDemoThread />
          </div>
        </section>

        <MarketingMedia
          src={marketingMedia.humanReviewBoundary.src}
          alt={marketingMedia.humanReviewBoundary.alt}
          variant="panel"
          className="mx-auto max-w-2xl"
          label="Human review placeholder"
        />

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
