import Link from "next/link";

import PageHeader from "@/components/PageHeader";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import GuidedDemoCard from "@/components/GuidedDemoCard";
import MarketingMedia from "@/components/MarketingMedia";
import { marketingMedia } from "@/lib/marketingMedia";
import {
  BROOKSIDE_PROJECT_ID,
  demoJourneySteps,
  technicalFoundation,
  evaluatorNotes,
  fiveMinutePath,
  technicalPath,
  outOfScope,
  reviewerChecklist,
} from "@/lib/demoJourney";

export const dynamic = "force-dynamic";

// Start Here: the recruiter and evaluator entry point. It answers what the
// product is, who it is for, what problem it solves, what Brookside Meadows is,
// and what to click first, then lays out the recommended demo path. Brookside
// Meadows is a synthetic public demo fixture. Nothing here approves a plan,
// certifies compliance, or replaces a licensed Professional Engineer.
const base = `/projects/${BROOKSIDE_PROJECT_ID}`;

const secondaryCtas = [
  { href: base, label: "Open Brookside Meadows" },
  { href: "/dashboard", label: "View Reviewer Dashboard" },
  { href: `${base}/evidence-search`, label: "View Evidence Workflow" },
  { href: `${base}/response-packages`, label: "View Response Package" },
  { href: "/deployment-status", label: "View Deployment Status" },
];

export default function StartHerePage() {
  return (
    <div>
      <PageHeader
        eyebrow="Start here"
        title="Start the Brookside Meadows demo"
        description="Civil Engineer AI is a document-first, evidence-first, reviewer-controlled stormwater review-support platform for municipal and civil engineering plan review. This page is the fastest way to understand it: follow the recommended demo path through the Brookside Meadows sample project."
        actions={
          <Link href="/guided-demo" className="btn btn-primary">
            Start Guided Demo
          </Link>
        }
      />

      <div className="mx-auto max-w-6xl space-y-8 px-4 py-6 sm:space-y-10 sm:px-6 sm:py-10 lg:space-y-12 lg:px-8">
        <SafetyBoundaryBanner variant="compact" />

        {/* What / who / why */}
        <section className="grid gap-3 md:grid-cols-3 md:gap-4">
          <div className="surface-card p-4 sm:p-5">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-water-700">
              What it is
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              A review-support platform that structures the work a reviewer does
              on a stormwater submission: documents, page-level evidence,
              checklist review, findings, applicant responses, resubmittals, and
              reviewer response packages.
            </p>
          </div>
          <div className="surface-card p-4 sm:p-5">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-water-700">
              Who it is for
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              Municipal and civil engineering plan reviewers who need evidence
              traceability and an organized, reviewer-controlled workflow across
              review rounds.
            </p>
          </div>
          <div className="surface-card p-4 sm:p-5">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-water-700">
              What it solves
            </h2>
            <p className="mt-2 text-sm text-slate-600">
              Plan review is scattered across PDFs, checklists, and email. This
              keeps every finding tied to a specific page and tracks the review
              from intake to a reviewer communication record.
            </p>
          </div>
        </section>

        {/* What is Brookside Meadows */}
        <section className="surface-card border-amber-200 bg-amber-50/40 p-4 sm:p-6">
          <h2 className="section-title">What is Brookside Meadows?</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
            Brookside Meadows is a synthetic public demo fixture: a fictional
            residential development used to show the review-support workflow with
            seeded demo records. It is not a real submission and does not
            represent a real permitting, approval, or compliance determination.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <Link href="/guided-demo" className="btn btn-primary btn-sm">
              Start Guided Demo
            </Link>
            <Link href={base} className="btn btn-secondary btn-sm">
              Open Brookside Meadows
            </Link>
          </div>
        </section>

        {/* Recruiter and technical evaluator review path */}
        <section className="surface-card p-4 sm:p-6">
          <span className="page-eyebrow">For recruiters and technical evaluators</span>
          <h2 className="section-title mt-2">Review this project in 5 minutes</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
            A fast path to understand the product, and a deeper path to assess
            the engineering foundation.
          </p>

          <div className="mt-5 grid gap-5 lg:mt-6 lg:grid-cols-2 lg:gap-6">
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wide text-water-700">
                5-minute path
              </h3>
              <ol className="mt-3 space-y-2">
                {fiveMinutePath.map((item, i) => (
                  <li key={item.href + item.label} className="subtle-card p-3">
                    <Link
                      href={item.href}
                      className="flex items-start gap-3 text-sm"
                    >
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-water-50 text-xs font-bold text-water-700">
                        {i + 1}
                      </span>
                      <span>
                        <span className="font-semibold text-water-700">
                          {item.label}
                        </span>
                        <span className="mt-0.5 block text-xs text-slate-600">
                          {item.note}
                        </span>
                      </span>
                    </Link>
                  </li>
                ))}
              </ol>
            </div>

            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wide text-water-700">
                Deeper technical path
              </h3>
              <ol className="mt-3 space-y-2">
                {technicalPath.map((item, i) => (
                  <li
                    key={item}
                    className="flex items-start gap-3 text-sm text-slate-700"
                  >
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-bold text-slate-600">
                      {i + 1}
                    </span>
                    {item}
                  </li>
                ))}
              </ol>
            </div>
          </div>

          <div className="mt-6 grid gap-5 md:grid-cols-2 md:gap-6">
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                What to notice
              </h3>
              <ul className="mt-3 space-y-1.5">
                {evaluatorNotes.map((note) => (
                  <li
                    key={note}
                    className="flex items-start gap-2 text-sm text-slate-700"
                  >
                    <span aria-hidden="true" className="mt-0.5 text-water-600">
                      +
                    </span>
                    {note}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                Intentionally out of scope
              </h3>
              <ul className="mt-3 flex flex-wrap gap-2">
                {outOfScope.map((item) => (
                  <li key={item}>
                    <span className="chip chip-neutral">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* Recommended demo path */}
        <section>
          <h2 className="section-title">Recommended demo path</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
            Follow these steps in order through the Brookside Meadows sample
            project. Each step links to a real workflow route and notes what to
            look for. Some deeper records may prompt sign in.
          </p>
          <MarketingMedia
            src={marketingMedia.guidedDemoJourney.src}
            alt={marketingMedia.guidedDemoJourney.alt}
            variant="wide"
            className="mt-5 sm:mt-6"
            imageClassName="object-contain p-2 sm:p-3 lg:object-cover lg:p-0"
            label="Guided demo placeholder"
          />
          <ol className="mt-5 grid gap-3 sm:mt-6 sm:grid-cols-2 sm:gap-4 lg:grid-cols-3">
            {demoJourneySteps.map((step) => (
              <li key={step.step}>
                <GuidedDemoCard step={step} />
              </li>
            ))}
          </ol>
        </section>

        {/* Reviewer walkthrough checklist */}
        <section className="surface-card p-4 sm:p-6">
          <h2 className="section-title">Reviewer walkthrough checklist</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
            A quick checklist to tick through the Brookside Meadows workflow in
            order.
          </p>
          <ul className="mt-4 grid gap-2 md:grid-cols-2">
            {reviewerChecklist.map((item) => (
              <li
                key={item}
                className="flex items-start gap-2 text-sm text-slate-700"
              >
                <span
                  aria-hidden="true"
                  className="mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded border border-slate-300 text-[10px] text-slate-400"
                >
                  ✓
                </span>
                {item}
              </li>
            ))}
          </ul>
        </section>

        {/* Technical foundation */}
        <section>
          <h2 className="section-title">Technical foundation</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
            Built as a full-stack review-support system. These are delivered
            capabilities, described without exaggeration.
          </p>
          <MarketingMedia
            src={marketingMedia.technicalFoundation.src}
            alt={marketingMedia.technicalFoundation.alt}
            variant="wide"
            className="mt-5 sm:mt-6"
            imageClassName="object-contain p-2 sm:p-3 lg:object-cover lg:p-0"
            label="Technical foundation placeholder"
          />
          <div className="mt-5 grid gap-3 sm:mt-6 sm:grid-cols-2 sm:gap-4 lg:grid-cols-3">
            {technicalFoundation.map((item) => (
              <div key={item.title} className="subtle-card p-4">
                <h3 className="text-sm font-semibold text-slate-900">
                  {item.title}
                </h3>
                <p className="mt-1 text-xs text-slate-600">{item.detail}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Secondary CTAs */}
        <section className="surface-card p-4 sm:p-6">
          <h2 className="section-title">Jump to a part of the workflow</h2>
          <div className="mt-4 flex flex-wrap gap-3">
            {secondaryCtas.map((cta) => (
              <Link key={cta.href + cta.label} href={cta.href} className="btn btn-secondary btn-sm">
                {cta.label}
              </Link>
            ))}
          </div>
        </section>

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
