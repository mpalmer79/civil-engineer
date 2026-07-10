import Link from "next/link";
import Image from "next/image";

import DemoDataBadge from "@/components/DemoDataBadge";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import { checklist } from "@/data/checklist";
import { documents } from "@/data/documents";
import { findings } from "@/data/findings";
import { BROOKSIDE_PROJECT_ID, fiveMinutePath, technicalPath } from "@/lib/demoJourney";

// Recruiter-first product entry. This page explains what Civil Engineer AI is,
// who it supports, and how to evaluate it. It intentionally shows no
// operational widgets: every number below is a case-study fact counted from
// the seeded Brookside Meadows fixture and labeled as such. Live operational
// data lives behind sign-in on /dashboard, and deployment health lives on
// /deployment-status where it is derived from real diagnostics.

const base = `/projects/${BROOKSIDE_PROJECT_ID}`;

const heroImage = {
  src: "/images/civil-engineer/site-plan-review-hero.webp",
  alt: "Illustrative preliminary site plan for the synthetic Brookside Meadows case study, showing proposed roads, lots, a stormwater basin, and review evidence callouts",
} as const;

// Case-study facts, counted directly from the seeded fixture so the homepage
// can never drift from the data it describes. The ten planted review issues
// are documented in docs/BROOKSIDE_MEADOWS_PROJECT_STORY.md (I-1 through I-10).
const caseStudyFacts = [
  { value: "47", label: "Lots in the synthetic subdivision" },
  { value: String(documents.length), label: "Documents in the demo package" },
  { value: "10", label: "Intentionally planted review issues" },
  { value: String(checklist.length), label: "Checklist items tracked" },
  { value: String(findings.length), label: "Review-support findings" },
] as const;

const workflowStages = [
  {
    stage: 1,
    title: "Project intake",
    detail:
      "Register the project and its submission package so every later action has a stable record to attach to.",
    href: base,
  },
  {
    stage: 2,
    title: "Document and DXF intake",
    detail:
      "Store submitted documents, index digital PDF pages, and parse DXF metadata deterministically through CAD Intake.",
    href: `${base}/documents`,
  },
  {
    stage: 3,
    title: "Evidence indexing and retrieval",
    detail:
      "Search indexed page text so each concern can point at the exact page and excerpt that supports it.",
    href: `${base}/evidence-search`,
  },
  {
    stage: 4,
    title: "Checklist and finding review",
    detail:
      "Work a stormwater checklist with evidence status per item; findings stay review-support only.",
    href: `${base}/checklists`,
  },
  {
    stage: 5,
    title: "Applicant response tracking",
    detail:
      "Track applicant responses and resubmittal rounds against the findings that prompted them.",
    href: `${base}/response-matrix`,
  },
  {
    stage: 6,
    title: "Reviewer-controlled handoff",
    detail:
      "Assemble a response package for reviewer handoff, with revision history and audit attribution.",
    href: `${base}/response-packages`,
  },
] as const;

const realVsSeeded = [
  {
    title: "Implemented",
    detail:
      "FastAPI backend with authentication, per-project access control, document storage, PDF page indexing, DXF metadata parsing, evidence retrieval, and audit events.",
  },
  {
    title: "Seeded demo",
    detail:
      "Brookside Meadows is a synthetic case study. Its documents, findings, and responses are fixtures, clearly labeled, and never presented as a real municipal submission.",
  },
  {
    title: "Intentionally out of scope",
    detail:
      "No live AI calls by default, no OCR, no DWG parsing, no GIS, and no approval, certification, or compliance determination of any kind.",
  },
] as const;

export default function HomePage() {
  return (
    <div className="bg-white text-slate-900">
      {/* Hero */}
      <section
        aria-labelledby="home-hero-heading"
        className="border-b border-slate-100 bg-gradient-to-b from-slate-50 to-white"
      >
        <div className="mx-auto max-w-6xl px-4 pb-12 pt-12 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-xs font-semibold uppercase tracking-wider text-water-700">
              Stormwater review support
            </p>
            <h1
              id="home-hero-heading"
              className="mt-3 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl"
            >
              Review stormwater submissions with evidence, context, and human
              control.
            </h1>
            <p className="mt-4 text-base leading-relaxed text-slate-600">
              Civil Engineer AI organizes project documents, plan references,
              review findings, applicant responses, and revision history for
              municipal stormwater reviewers. It supports the review; a
              licensed engineer makes every decision.
            </p>

            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              <Link
                href="/guided-demo"
                className="rounded-lg bg-water-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-water-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-water-600"
              >
                Start the Brookside Meadows Guided Demo
              </Link>
              <Link
                href="/start-here"
                className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-water-600"
              >
                Review the Technical Overview
              </Link>
            </div>
          </div>

          <figure className="mx-auto mt-10 max-w-4xl">
            <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card-lg">
              <div className="relative aspect-[16/9] w-full">
                <Image
                  src={heroImage.src}
                  alt={heroImage.alt}
                  fill
                  priority
                  sizes="(max-width: 768px) 100vw, 896px"
                  className="object-cover object-center"
                />
              </div>
            </div>
            <figcaption className="mt-3 flex flex-wrap items-center justify-center gap-2 text-xs text-slate-500">
              <DemoDataBadge label="Synthetic case study" />
              <span>
                Brookside Meadows is a fictional 47-lot subdivision in the
                fictional Town of Hartwell. It is not a real project or a real
                approval.
              </span>
            </figcaption>
          </figure>
        </div>
      </section>

      {/* Case-study proof points */}
      <section aria-labelledby="case-study-heading" className="border-b border-slate-100">
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="flex flex-col items-start justify-between gap-2 sm:flex-row sm:items-end">
            <div>
              <h2 id="case-study-heading" className="text-xl font-semibold text-slate-950">
                The Brookside Meadows case study
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                Fixed facts from the seeded review fixture, not live operational
                metrics.
              </p>
            </div>
            <DemoDataBadge />
          </div>

          <dl className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {caseStudyFacts.map((fact) => (
              <div
                key={fact.label}
                className="rounded-xl border border-slate-200 bg-white p-4 shadow-card"
              >
                <dd className="text-2xl font-bold text-slate-950">{fact.value}</dd>
                <dt className="mt-1 text-xs text-slate-500">{fact.label}</dt>
              </div>
            ))}
          </dl>

          <p className="mt-4 text-xs text-slate-500">
            The ten planted issues (a design storm discrepancy, missing
            infiltration testing, a basin naming conflict, a missing revised
            sheet, and others) are documented in the project story and traced
            through every module, so the same concern is inspectable end to
            end.
          </p>
        </div>
      </section>

      {/* Six-stage reviewer workflow */}
      <section aria-labelledby="workflow-heading" className="border-b border-slate-100 bg-slate-50">
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
          <h2 id="workflow-heading" className="text-xl font-semibold text-slate-950">
            One reviewer journey, six stages
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Each stage links into the seeded Brookside Meadows workspace so you
            can inspect the full module behind it.
          </p>

          <ol className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {workflowStages.map((s) => (
              <li key={s.stage}>
                <Link
                  href={s.href}
                  className="flex h-full flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-card transition hover:border-water-300 hover:shadow-card-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-water-600"
                >
                  <span className="text-xs font-semibold uppercase tracking-wide text-water-700">
                    Stage {s.stage}
                  </span>
                  <span className="mt-1 text-sm font-semibold text-slate-900">
                    {s.title}
                  </span>
                  <span className="mt-2 text-xs leading-relaxed text-slate-600">
                    {s.detail}
                  </span>
                </Link>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Human review boundary */}
      <section aria-labelledby="boundary-heading" className="border-b border-slate-100">
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
          <h2 id="boundary-heading" className="text-xl font-semibold text-slate-950">
            The human review boundary
          </h2>
          <p className="mt-1 max-w-3xl text-sm text-slate-600">
            AI provides review support. You make the decisions. Every review is
            human. The system organizes evidence and drafts review-support
            findings; it never approves a plan, certifies compliance, or
            replaces a licensed Professional Engineer.
          </p>
          <div className="mt-5">
            <SafetyBoundaryBanner />
          </div>
        </div>
      </section>

      {/* Real versus seeded */}
      <section aria-labelledby="real-vs-seeded-heading" className="border-b border-slate-100 bg-slate-50">
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
          <h2 id="real-vs-seeded-heading" className="text-xl font-semibold text-slate-950">
            What is real and what is seeded
          </h2>
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
            {realVsSeeded.map((item) => (
              <div
                key={item.title}
                className="rounded-xl border border-slate-200 bg-white p-5 shadow-card"
              >
                <h3 className="text-sm font-semibold text-slate-900">{item.title}</h3>
                <p className="mt-2 text-xs leading-relaxed text-slate-600">{item.detail}</p>
              </div>
            ))}
          </div>
          <p className="mt-4 text-xs text-slate-500">
            The full real-versus-seeded matrix lives in the repository at
            docs/real-vs-mocked.md, and the technical overview page summarizes
            the architecture behind it.
          </p>
        </div>
      </section>

      {/* Recruiter review paths */}
      <section aria-labelledby="review-paths-heading" className="border-b border-slate-100">
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
          <h2 id="review-paths-heading" className="text-xl font-semibold text-slate-950">
            Two ways to evaluate this project
          </h2>

          <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-card">
              <h3 className="text-sm font-semibold text-slate-900">
                Five-minute product path
              </h3>
              <ol className="mt-3 space-y-2">
                {fiveMinutePath.map((step) => (
                  <li key={step.href} className="text-xs text-slate-600">
                    <Link
                      href={step.href}
                      className="font-medium text-water-700 hover:underline"
                    >
                      {step.label}
                    </Link>
                    <span className="ml-1">{step.note}</span>
                  </li>
                ))}
              </ol>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-card">
              <h3 className="text-sm font-semibold text-slate-900">
                Fifteen-minute technical path
              </h3>
              <ul className="mt-3 list-disc space-y-2 pl-4">
                {technicalPath.map((topic) => (
                  <li key={topic} className="text-xs text-slate-600">
                    {topic}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section aria-labelledby="final-cta-heading" className="bg-slate-900">
        <div className="mx-auto max-w-6xl px-4 py-12 text-center sm:px-6 lg:px-8">
          <h2 id="final-cta-heading" className="text-xl font-semibold text-white">
            See one concern traced from document to handoff
          </h2>
          <p className="mx-auto mt-2 max-w-2xl text-sm text-slate-300">
            The guided demo walks the Brookside Meadows review in about five
            minutes: intake, evidence, checklist, applicant response, and
            reviewer-controlled handoff.
          </p>
          <div className="mt-6">
            <Link
              href="/guided-demo"
              className="inline-block rounded-lg bg-water-500 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-water-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              Start the Guided Demo
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
