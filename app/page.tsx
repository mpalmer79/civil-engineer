import Link from "next/link";

import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import BackendStatusBanner from "@/components/BackendStatusBanner";
import { BROOKSIDE_PROJECT_ID } from "@/lib/demoJourney";
import { projectMetrics } from "@/lib/api";
import { findings } from "@/data/findings";
import { checklist } from "@/data/checklist";
import { hotspots } from "@/data/hotspots";

// AEC pre-submittal QA homepage. The first screen sells the outcome: catch
// review issues before a civil/site/stormwater package goes to a municipal
// reviewer. The DXF-to-findings, evidence-traceability, and draft handoff flow
// is the hero proof. Professional boundary language is preserved but moved
// below the fold into a single credibility section. Every claim stays
// review-support only and keeps a human reviewer responsible.

const base = `/projects/${BROOKSIDE_PROJECT_ID}`;

// Hero calls to action. The primary CTA opens the guided demo, a self-running
// pre-submittal QA tour over the Brookside Meadows sample project. Secondary CTAs
// reach the traceability and draft handoff surfaces directly.
const heroCtas = [
  { href: "/guided-demo", label: "Run the sample review", primary: true },
  { href: `${base}/traceability`, label: "Explore traceability", primary: false },
  { href: `${base}/review-packets`, label: "View sample handoff", primary: false },
];

// Fixture-backed proof metrics, derived from the seeded Brookside Meadows demo
// data. These are counts of real records in the demo fixtures, not invented
// numbers and not claims about a real submission.
const findingsCount = findings.length;
const checklistCount = checklist.length;
const siteFeatureCount = hotspots.length;
const documentsCount = projectMetrics.documents;

const proofMetrics: { value: string | number; label: string }[] = [
  { value: findingsCount, label: "Review-support findings" },
  { value: checklistCount, label: "Checklist items tracked" },
  { value: documentsCount, label: "Indexed documents" },
  { value: siteFeatureCount, label: "Mapped site features" },
];

// The four capabilities that matter to an AEC pre-submittal QA buyer. Each card
// links to a real Brookside Meadows demo surface that already exists.
const capabilityCards: { title: string; detail: string; href: string; cta: string }[] = [
  {
    title: "CAD and DXF intake",
    detail:
      "Organize DXF metadata from the plan set and surface review-support findings tied to source context.",
    href: `${base}/cad`,
    cta: "Open CAD Intake",
  },
  {
    title: "Plan and report consistency",
    detail:
      "Flag conflicts between the plan set and the stormwater report so they are caught before submittal, not in a review comment.",
    href: `${base}/plan-consistency`,
    cta: "Open consistency checks",
  },
  {
    title: "Evidence traceability",
    detail:
      "Every finding ties back to a specific page or sheet with source-backed traceability the reviewer can follow.",
    href: `${base}/traceability`,
    cta: "Open traceability",
  },
  {
    title: "Draft reviewer handoff package",
    detail:
      "Assemble a draft handoff package for the municipal reviewer. The human reviewer remains responsible for every item.",
    href: `${base}/review-packets`,
    cta: "View draft handoff",
  },
];

// A small, real preview of review-support findings built from the seeded demo
// fixtures, used in place of a generic hero placeholder image.
const previewFindings = findings.slice(0, 3);

export default function HomePage() {
  return (
    <div>
      {/* Hero: outcome-first message on the left, a live findings preview built
          from real demo data on the right. */}
      <section className="relative overflow-hidden border-b border-slate-200 bg-white">
        <div className="relative mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
          <div className="grid gap-10 lg:grid-cols-[1.05fr_1fr] lg:items-center">
            <div>
              <span className="chip chip-brand">
                Pre-submittal QA for civil and AEC teams
              </span>
              <h1 className="mt-4 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
                Catch stormwater review issues before submittal.
              </h1>
              <p className="mt-4 max-w-xl text-lg leading-relaxed text-slate-600">
                Civil Engineer AI helps civil, site, and stormwater teams run
                internal pre-submittal QA. Upload review files, surface
                review-support findings, link every issue to source evidence,
                and prepare a draft reviewer handoff package.
              </p>
              <p className="mt-3 max-w-xl text-base font-medium text-water-700">
                Reduce avoidable resubmittal risk by reviewing the package
                before it goes out the door.
              </p>

              <div className="mt-7 flex flex-wrap gap-3">
                {heroCtas.map((cta) => (
                  <Link
                    key={cta.href + cta.label}
                    href={cta.href}
                    className={`btn ${cta.primary ? "btn-primary" : "btn-secondary"}`}
                  >
                    {cta.label}
                  </Link>
                ))}
              </div>

              <p className="mt-4 text-sm text-slate-500">
                Brookside Meadows is a sample project with seeded demo data. No
                login is needed to explore the review-support workflow.
              </p>
            </div>

            {/* Live product preview built from seeded demo findings. */}
            <div className="surface-card overflow-hidden p-0 shadow-card">
              <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-5 py-3">
                <span className="text-sm font-semibold text-slate-900">
                  Brookside Meadows: review-support findings
                </span>
                <span className="chip chip-neutral">Demo data</span>
              </div>
              <ul className="divide-y divide-slate-100">
                {previewFindings.map((finding) => (
                  <li key={finding.findingId} className="px-5 py-4">
                    <div className="flex items-center gap-2">
                      <span className="chip chip-neutral">{finding.category}</span>
                      <span className="text-xs font-medium uppercase tracking-wide text-amber-700">
                        Potential issue
                      </span>
                    </div>
                    <p className="mt-2 text-sm font-semibold text-slate-900">
                      {finding.title}
                    </p>
                    <p className="mt-1 text-xs text-slate-600">
                      Evidence: {finding.evidenceToFind}
                    </p>
                  </li>
                ))}
              </ul>
              <div className="border-t border-slate-200 bg-slate-50 px-5 py-3">
                <Link
                  href={`${base}/findings`}
                  className="text-sm font-semibold text-water-700 hover:text-water-800"
                >
                  See all {findingsCount} findings with source evidence →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Proof: fixture-backed metrics from the seeded demo, then the four
          capabilities that matter to an AEC pre-submittal QA buyer. */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div className="max-w-2xl">
              <span className="chip chip-neutral">Sample project: Brookside Meadows</span>
              <h2 className="section-title mt-3">See the review-support workflow working</h2>
              <p className="section-description">
                The numbers below count real records in the seeded Brookside
                Meadows demo fixtures. They show the pre-submittal QA workflow on
                sample data, not a real submission or an engineering outcome.
              </p>
            </div>
            <Link href="/guided-demo" className="btn btn-primary shrink-0">
              Run the sample review
            </Link>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {proofMetrics.map((metric) => (
              <div key={metric.label} className="surface-card p-5">
                <p className="text-3xl font-bold text-slate-900">{metric.value}</p>
                <p className="mt-1 text-sm text-slate-600">{metric.label}</p>
              </div>
            ))}
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            {capabilityCards.map((card) => (
              <div key={card.title} className="surface-card flex h-full flex-col p-6">
                <h3 className="text-base font-semibold text-slate-900">
                  {card.title}
                </h3>
                <p className="mt-2 flex-1 text-sm text-slate-600">{card.detail}</p>
                <Link
                  href={card.href}
                  className="mt-4 text-sm font-semibold text-water-700 hover:text-water-800"
                >
                  {card.cta} →
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Credibility: human reviewers stay in control. One clear boundary
          section below the fold, reassuring after interest is created. */}
      <section className="border-y border-slate-200 bg-slate-50">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid gap-8 lg:grid-cols-[1fr_1.2fr] lg:items-start">
            <div>
              <h2 className="section-title">Human reviewers stay in control</h2>
              <p className="section-description">
                Civil Engineer AI organizes evidence and flags potential issues
                for review. Every item should be reviewed by a qualified
                professional. It does not approve, certify, verify, validate, or
                make final engineering decisions, and it keeps source context
                visible so the reviewer can check the basis for each finding.
              </p>
              <div className="mt-5">
                <BackendStatusBanner />
              </div>
            </div>
            <SafetyBoundaryBanner />
          </div>
        </div>
      </section>

      {/* Pilot and demo path. The guided demo stays reachable, and the pilot
          CTA is an honest placeholder until a contact route exists. */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="surface-card flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
            <div className="max-w-2xl">
              <h2 className="section-title">Bring it to your own pre-submittal QA</h2>
              <p className="mt-2 text-slate-600">
                Walk the full review-support workflow on the Brookside Meadows
                sample project, or start a conversation about a design-partner
                pilot for your firm.
              </p>
            </div>
            <div className="flex flex-wrap gap-3 sm:shrink-0">
              <Link href="/guided-demo" className="btn btn-secondary">
                See the guided demo
              </Link>
              <button
                type="button"
                disabled
                aria-disabled="true"
                title="Pilot access is not open yet."
                className="btn btn-primary cursor-not-allowed opacity-60"
              >
                Pilot access coming soon
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
