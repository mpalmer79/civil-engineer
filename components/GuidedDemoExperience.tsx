"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

import { trackDemoEvent } from "@/lib/analytics";
import type { AecDemoStep } from "@/lib/demoJourney";

// The buyer-facing guided demo: a focused SaaS product tour of the Brookside
// Meadows pre-submittal QA workflow. It runs on seeded demo data, needs no
// login, and links each step to the real Brookside Meadows surface. Boundary
// language is present as reassurance, not as the lead message. Nothing here
// approves, certifies, verifies, or validates anything.

export type DemoProofCard = {
  // A formatted count string when a fixture-backed count is available, or null
  // to render a qualitative proof statement instead. Counts are never invented.
  value: string | null;
  label: string;
};

export default function GuidedDemoExperience({
  projectId,
  steps,
  proof,
  pilotHref = null,
}: {
  projectId: string;
  steps: AecDemoStep[];
  proof: DemoProofCard[];
  pilotHref?: string | null;
}) {
  const base = `/projects/${projectId}`;
  const [current, setCurrent] = useState(0);
  const completedRef = useRef(false);
  const startedRef = useRef(false);

  const step = steps[current];
  const isLast = current === steps.length - 1;

  // Fire demo_started once on mount.
  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    trackDemoEvent("demo_started", { projectId });
  }, [projectId]);

  // Fire demo_step_viewed on each step, and demo_completed when the final step
  // is reached for the first time.
  useEffect(() => {
    trackDemoEvent("demo_step_viewed", { step: step.step, stepId: step.id });
    if (isLast && !completedRef.current) {
      completedRef.current = true;
      trackDemoEvent("demo_completed", { steps: steps.length });
    }
  }, [step.step, step.id, isLast, steps.length]);

  const goTo = (index: number) => {
    if (index < 0 || index >= steps.length) return;
    setCurrent(index);
  };

  return (
    <div className="space-y-8">
      {/* Wow moment: fixture-backed proof from the seeded demo, near the top. */}
      <section className="surface-card p-6">
        <span className="chip chip-neutral">Sample project: Brookside Meadows</span>
        <h2 className="mt-3 text-2xl font-bold tracking-tight text-slate-900">
          Review-support findings surfaced from the Brookside Meadows demo
          package
        </h2>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          One reviewer workflow connects CAD metadata, plan and report
          consistency, source-backed traceability, workflow items, and a draft
          reviewer handoff package. The figures below count real records in the
          seeded demo data, not a real submission.
        </p>
        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {proof.map((card) => (
            <div key={card.label} className="rounded-lg bg-slate-50 p-4">
              {card.value !== null ? (
                <p className="text-2xl font-bold text-slate-900">{card.value}</p>
              ) : (
                <p className="text-sm font-semibold text-water-700">Included</p>
              )}
              <p className="mt-1 text-xs text-slate-600">{card.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Step navigation with a progress indicator. */}
      <nav
        aria-label="Demo steps"
        className="sticky top-0 z-10 -mx-4 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur sm:mx-0 sm:rounded-lg sm:border sm:px-4"
      >
        <div className="flex items-center justify-between gap-3">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Step {step.step} of {steps.length}
          </span>
          <div
            className="h-1.5 w-32 overflow-hidden rounded-full bg-slate-200"
            role="progressbar"
            aria-valuenow={step.step}
            aria-valuemin={1}
            aria-valuemax={steps.length}
          >
            <div
              className="h-full rounded-full bg-water-600 transition-all"
              style={{ width: `${(step.step / steps.length) * 100}%` }}
            />
          </div>
        </div>
        <ol className="mt-3 flex flex-wrap gap-2">
          {steps.map((s, i) => (
            <li key={s.id}>
              <button
                type="button"
                onClick={() => goTo(i)}
                aria-current={i === current ? "step" : undefined}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                  i === current
                    ? "bg-water-600 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {s.step}. {s.eyebrow}
              </button>
            </li>
          ))}
        </ol>
      </nav>

      {/* Current step content. */}
      <section className="surface-card p-6">
        <span className="text-xs font-semibold uppercase tracking-wide text-water-700">
          {step.eyebrow}
        </span>
        <h3 className="mt-2 text-xl font-bold text-slate-900">{step.title}</h3>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          {step.narrative}
        </p>
        <ul className="mt-4 grid gap-2 sm:grid-cols-3">
          {step.highlights.map((h) => (
            <li
              key={h}
              className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700"
            >
              {h}
            </li>
          ))}
        </ul>
        <p className="mt-4 text-xs text-slate-500">
          What to notice: {step.whatToNotice}
        </p>
        <div className="mt-5">
          <Link
            href={step.href}
            onClick={() =>
              trackDemoEvent("demo_cta_clicked", {
                stepId: step.id,
                href: step.href,
              })
            }
            className="btn btn-primary"
          >
            {step.ctaLabel}
          </Link>
        </div>
      </section>

      {/* Back / Next controls. */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => goTo(current - 1)}
          disabled={current === 0}
          className="btn btn-secondary disabled:cursor-not-allowed disabled:opacity-50"
        >
          Back
        </button>
        <button
          type="button"
          onClick={() => goTo(current + 1)}
          disabled={isLast}
          className="btn btn-primary disabled:cursor-not-allowed disabled:opacity-50"
        >
          Next
        </button>
      </div>

      {/* Next-step CTAs. */}
      <section className="surface-card p-6">
        <h3 className="text-lg font-semibold text-slate-900">
          Take it further
        </h3>
        <p className="mt-1 text-sm text-slate-600">
          Explore the full Brookside Meadows sample project, or open the command
          center to see the whole review-support workflow in one place.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link
            href={base}
            onClick={() =>
              trackDemoEvent("demo_cta_clicked", {
                stepId: "explore-project",
                href: base,
              })
            }
            className="btn btn-secondary"
          >
            Explore the full demo project
          </Link>
          <Link
            href={`${base}/command-center`}
            onClick={() =>
              trackDemoEvent("demo_cta_clicked", {
                stepId: "command-center",
                href: `${base}/command-center`,
              })
            }
            className="btn btn-secondary"
          >
            View command center
          </Link>
          {pilotHref ? (
            <Link
              href={pilotHref}
              onClick={() => trackDemoEvent("pilot_cta_clicked", {})}
              className="btn btn-primary"
            >
              Start a pilot conversation
            </Link>
          ) : (
            <button
              type="button"
              disabled
              aria-disabled="true"
              title="Pilot access is not open yet."
              className="btn btn-primary cursor-not-allowed opacity-60"
            >
              Pilot access coming soon
            </button>
          )}
        </div>
      </section>

      {/* Boundary reassurance: present, but below the demo story. */}
      <section className="rounded-lg border border-slate-200 bg-slate-50 p-6">
        <h3 className="text-base font-semibold text-slate-900">
          Human reviewers stay responsible
        </h3>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          This demo organizes review-support evidence on a sample project. Every
          finding is a potential issue for human review, and a qualified
          professional should review each item. The product does not approve,
          certify, verify, validate, or make final engineering decisions, and
          source context stays visible so the reviewer can check the basis for
          each finding.
        </p>
      </section>
    </div>
  );
}
