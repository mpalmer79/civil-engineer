import Link from "next/link";

import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import BackendStatusBanner from "@/components/BackendStatusBanner";
import MarketingMedia from "@/components/MarketingMedia";
import { BROOKSIDE_PROJECT_ID } from "@/lib/demoJourney";
import { marketingMedia } from "@/lib/marketingMedia";
import { projectMedia } from "@/lib/projectMedia";
import { projectMetrics } from "@/lib/api";
import { findings } from "@/data/findings";
import { checklist } from "@/data/checklist";
import { hotspots } from "@/data/hotspots";

// AEC pre-submittal QA homepage, rebuilt media-first. The first screen hooks a
// civil/AEC buyer with a large product visual, a concise outcome headline, and a
// primary CTA into the guided demo. Visual story sections carry the four
// capabilities with copy-light taglines. Fixture-backed proof supports the media
// without dominating it. Professional boundary language stays below the fold as a
// single credibility section. Every claim is review-support only and keeps a
// human reviewer responsible.

const base = `/projects/${BROOKSIDE_PROJECT_ID}`;

// Fixture-backed proof metrics, derived from the seeded Brookside Meadows demo
// data. These count real records in the demo fixtures; they are not invented and
// make no claim about a real submission.
const proofMetrics: { value: string | number; label: string }[] = [
  { value: findings.length, label: "Review-support findings" },
  { value: checklist.length, label: "Checklist items tracked" },
  { value: projectMetrics.documents, label: "Indexed documents" },
  { value: hotspots.length, label: "Mapped site features" },
];

// Four visual story sections, each copy-light and linked to a real Brookside
// Meadows demo surface. Images come from the existing media manifests.
const storySections: {
  eyebrow: string;
  title: string;
  tagline: string;
  href: string;
  cta: string;
  media: { src: string; alt: string };
  label: string;
}[] = [
  {
    eyebrow: "Step 1",
    title: "CAD and DXF intake",
    tagline: "Turn plan metadata into review-support findings.",
    href: `${base}/cad`,
    cta: "Open CAD Intake",
    media: projectMedia.documentsPreview,
    label: "Plan set preview",
  },
  {
    eyebrow: "Step 2",
    title: "Plan and report consistency",
    tagline: "Catch conflicts before they become review comments.",
    href: `${base}/plan-consistency`,
    cta: "Open consistency checks",
    media: marketingMedia.workflow,
    label: "Review workflow",
  },
  {
    eyebrow: "Step 3",
    title: "Evidence traceability",
    tagline: "Every issue stays tied to source context.",
    href: `${base}/traceability`,
    cta: "Open traceability",
    media: marketingMedia.technicalFoundation,
    label: "Traceability visual",
  },
  {
    eyebrow: "Step 4",
    title: "Draft reviewer handoff package",
    tagline: "Package findings into a draft reviewer handoff.",
    href: `${base}/review-packets`,
    cta: "View draft handoff",
    media: marketingMedia.guidedDemoJourney,
    label: "Draft handoff",
  },
];

export default function HomePage() {
  return (
    <div>
      {/* Hero: concise outcome message on the left, large product visual on the
          right. Media-forward, copy-light. */}
      <section className="relative overflow-hidden border-b border-slate-200 bg-white">
        <div className="relative mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
          <div className="grid gap-10 lg:grid-cols-[1fr_1.05fr] lg:items-center">
            <div>
              <span className="chip chip-brand">
                Pre-submittal QA for civil and AEC teams
              </span>
              <h1 className="mt-4 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
                Catch stormwater review issues before submittal.
              </h1>
              <p className="mt-4 max-w-xl text-lg leading-relaxed text-slate-600">
                Upload the package. Surface review-support findings. Trace every
                issue back to source evidence before it goes out.
              </p>
              <p className="mt-3 text-base font-medium text-water-700">
                Reduce avoidable resubmittal risk.
              </p>

              <div className="mt-7 flex flex-wrap gap-3">
                <Link href="/guided-demo" className="btn btn-primary">
                  Run the sample review
                </Link>
                <Link href={`${base}/traceability`} className="btn btn-secondary">
                  Explore traceability
                </Link>
                <Link href={`${base}/review-packets`} className="btn btn-secondary">
                  View sample handoff
                </Link>
              </div>

              <p className="mt-4 text-sm text-slate-500">
                Brookside Meadows is a sample project with seeded demo data. No
                login is needed to explore the review-support workflow.
              </p>
            </div>

            <div className="relative">
              <MarketingMedia
                src={marketingMedia.hero.src}
                alt={marketingMedia.hero.alt}
                variant="hero"
                priority
                label="Stormwater review workspace"
              />
              <span className="absolute right-4 top-4 chip chip-neutral bg-white/90">
                Demo data
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Compact proof band: fixture-backed counts supporting the media. */}
      <section className="border-b border-slate-200 bg-slate-50">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <span className="chip chip-neutral">
              Sample project: Brookside Meadows
            </span>
            <p className="text-xs text-slate-500">
              Counts of real records in the seeded demo data, not a real
              submission.
            </p>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {proofMetrics.map((metric) => (
              <div key={metric.label} className="surface-card p-5 text-center">
                <p className="text-3xl font-bold text-slate-900">
                  {metric.value}
                </p>
                <p className="mt-1 text-sm text-slate-600">{metric.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Visual story: the four capabilities, media-forward and copy-light. */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl space-y-12 px-4 py-14 sm:px-6 lg:space-y-16 lg:px-8">
          {storySections.map((section, i) => (
            <div
              key={section.title}
              className="grid items-center gap-8 lg:grid-cols-2"
            >
              <div className={i % 2 === 1 ? "lg:order-2" : ""}>
                <MarketingMedia
                  src={section.media.src}
                  alt={section.media.alt}
                  variant="wide"
                  label={section.label}
                />
              </div>
              <div className={i % 2 === 1 ? "lg:order-1" : ""}>
                <span className="text-xs font-semibold uppercase tracking-wide text-water-700">
                  {section.eyebrow}
                </span>
                <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-900">
                  {section.title}
                </h2>
                <p className="mt-3 text-lg text-slate-600">{section.tagline}</p>
                <Link
                  href={section.href}
                  className="mt-5 inline-flex text-sm font-semibold text-water-700 hover:text-water-800"
                >
                  {section.cta} →
                </Link>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Credibility: human reviewers stay in control. One boundary section
          below the fold, with a supporting visual. */}
      <section className="border-y border-slate-200 bg-slate-50">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid gap-8 lg:grid-cols-[1.1fr_1fr] lg:items-center">
            <div>
              <h2 className="section-title">Human reviewers stay in control</h2>
              <p className="section-description">
                Civil Engineer AI organizes review-support evidence and flags
                potential issues for review. A qualified professional remains
                responsible for every item. It does not approve, certify, verify,
                validate, or make final engineering decisions.
              </p>
              <div className="mt-5">
                <BackendStatusBanner />
              </div>
              <div className="mt-5">
                <SafetyBoundaryBanner />
              </div>
            </div>
            <MarketingMedia
              src={marketingMedia.humanReviewBoundary.src}
              alt={marketingMedia.humanReviewBoundary.alt}
              variant="panel"
              className="mx-auto max-w-md"
              label="Human review"
            />
          </div>
        </div>
      </section>

      {/* Pilot and demo path. The guided demo stays reachable; the pilot CTA is
          an honest disabled control until a contact route exists. */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="surface-card flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
            <div className="max-w-2xl">
              <h2 className="section-title">Bring it to your own pre-submittal QA</h2>
              <p className="mt-2 text-slate-600">
                Run the guided demo on the Brookside Meadows sample project, or
                start a conversation about a design-partner pilot for your firm.
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
