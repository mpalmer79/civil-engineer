import Link from "next/link";

import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import BackendStatusBanner from "@/components/BackendStatusBanner";
import MarketingMedia from "@/components/MarketingMedia";
import { BROOKSIDE_PROJECT_ID } from "@/lib/demoJourney";
import { marketingMedia } from "@/lib/marketingMedia";
import { projectMedia } from "@/lib/projectMedia";
import { dashboardMedia } from "@/lib/dashboardMedia";
import { projectMetrics } from "@/lib/api";
import { findings } from "@/data/findings";
import { checklist } from "@/data/checklist";
import { hotspots } from "@/data/hotspots";

// Media-forward AEC pre-submittal QA homepage. The page leads with a large
// product visual and a short outcome-first headline, then tells the product
// story through four copy-light media sections, a compact fixture-backed proof
// band, and a single professional boundary section below the fold. The AEC
// positioning and the guided demo CTA are preserved. Every claim stays
// review-support only and keeps a human reviewer responsible.

const base = `/projects/${BROOKSIDE_PROJECT_ID}`;

// Hero calls to action. The primary CTA opens the guided demo, a
// self-running pre-submittal QA tour over the Brookside Meadows sample project.
// Secondary CTAs reach the traceability and draft handoff surfaces directly.
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

// The four capabilities that matter to an AEC pre-submittal QA buyer, told as
// copy-light media story blocks. Each links to a real Brookside Meadows demo
// surface that already exists, and reuses an existing civil-engineer asset.
const capabilityStories: {
  title: string;
  copy: string;
  href: string;
  cta: string;
  media: { src: string; alt: string };
  label: string;
}[] = [
  {
    title: "CAD and DXF intake",
    copy: "Turn plan metadata into review-support findings.",
    href: `${base}/cad`,
    cta: "Open CAD Intake",
    media: projectMedia.documentsPreview,
    label: "CAD intake media",
  },
  {
    title: "Plan and report consistency",
    copy: "Catch conflicts before they become review comments.",
    href: `${base}/plan-consistency`,
    cta: "Open consistency checks",
    media: marketingMedia.workflow,
    label: "Plan consistency media",
  },
  {
    title: "Evidence traceability",
    copy: "Every issue stays tied to source context.",
    href: `${base}/traceability`,
    cta: "Open traceability",
    media: marketingMedia.technicalFoundation,
    label: "Traceability media",
  },
  {
    title: "Draft reviewer handoff package",
    copy: "Package findings into a draft reviewer handoff.",
    href: `${base}/review-packets`,
    cta: "View draft handoff",
    media: dashboardMedia.hero,
    label: "Reviewer handoff media",
  },
];

export default function HomePage() {
  return (
    <div>
      {/* Hero: short outcome-first message on the left, a large product visual
          on the right. Boundary language stays out of the hero. */}
      <section className="relative overflow-hidden border-b border-slate-200 bg-gradient-to-br from-water-50 via-white to-slate-50">
        <div className="relative mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8 lg:py-20">
          <div className="grid gap-10 lg:grid-cols-[1.05fr_1.1fr] lg:items-center">
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

            {/* Large product visual. Reuses the committed civil-engineer hero
                asset, with a graceful fallback if the file is missing. */}
            <div className="relative">
              <MarketingMedia
                src={marketingMedia.hero.src}
                alt={marketingMedia.hero.alt}
                variant="hero"
                priority
                label="Hero media"
              />
              <span className="absolute left-4 top-4 chip chip-neutral shadow-card">
                Demo data
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Compact, fixture-backed proof band. It supports the media without
          dominating the page. */}
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm font-medium text-slate-600">
              Counts from the seeded Brookside Meadows sample project, not a real
              submission.
            </p>
            <dl className="grid grid-cols-2 gap-4 sm:flex sm:flex-wrap sm:items-center sm:gap-8">
              {proofMetrics.map((metric) => (
                <div key={metric.label}>
                  <dd className="text-2xl font-bold text-slate-900">
                    {metric.value}
                  </dd>
                  <dt className="text-xs text-slate-500">{metric.label}</dt>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </section>

      {/* Visual story sections: four media-forward capability blocks with
          copy-light text. Image side alternates for visual rhythm. */}
      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
          <div className="max-w-2xl">
            <span className="chip chip-neutral">Sample project: Brookside Meadows</span>
            <h2 className="section-title mt-3">See the workflow, not a wall of text</h2>
            <p className="section-description">
              Four review-support capabilities, each running on seeded demo data
              and linked to a real Brookside Meadows surface.
            </p>
          </div>

          <div className="mt-10 flex flex-col gap-12">
            {capabilityStories.map((story, index) => {
              const imageFirst = index % 2 === 0;
              return (
                <div
                  key={story.title}
                  className="grid items-center gap-6 lg:grid-cols-2 lg:gap-10"
                >
                  <div className={imageFirst ? "lg:order-1" : "lg:order-2"}>
                    <MarketingMedia
                      src={story.media.src}
                      alt={story.media.alt}
                      variant="wide"
                      label={story.label}
                    />
                  </div>
                  <div className={imageFirst ? "lg:order-2" : "lg:order-1"}>
                    <h3 className="text-2xl font-semibold tracking-tight text-slate-900">
                      {story.title}
                    </h3>
                    <p className="mt-3 text-lg text-slate-600">{story.copy}</p>
                    <Link
                      href={story.href}
                      className="mt-5 inline-flex text-sm font-semibold text-water-700 hover:text-water-800"
                    >
                      {story.cta} →
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Credibility: human reviewers stay in control. One concise, visually
          designed boundary section below the fold. */}
      <section className="border-y border-slate-200 bg-slate-50">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="grid gap-8 lg:grid-cols-[1fr_1.1fr] lg:items-center">
            <div>
              <MarketingMedia
                src={marketingMedia.humanReviewBoundary.src}
                alt={marketingMedia.humanReviewBoundary.alt}
                variant="wide"
                label="Human review boundary media"
              />
            </div>
            <div>
              <h2 className="section-title">Human reviewers stay in control</h2>
              <p className="section-description">
                Civil Engineer AI organizes review-support evidence and flags
                potential issues. Human professionals remain responsible for
                every item. It does not approve, certify, verify, validate, or
                make final engineering decisions.
              </p>
              <div className="mt-5">
                <SafetyBoundaryBanner />
              </div>
              <div className="mt-4">
                <BackendStatusBanner />
              </div>
            </div>
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
