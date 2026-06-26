import Link from "next/link";

// A guided, end-to-end review-support thread for one concrete issue: the missing
// infiltration testing / groundwater separation concern on Brookside Meadows. It
// follows that single issue from the checklist requirement through the finding,
// its source evidence, the review packet, the workflow board, and the draft
// response language, ending at the human-review boundary. The content is the
// canonical seeded thread; the live modules serve the same data from the
// backend. This thread proves one complete workflow without requiring the
// reader to understand every module.

type Step = {
  label: string;
  title: string;
  body: string;
  href: string;
  cta: string;
};

const FINDING = {
  id: "find_infiltration_missing",
  title: "Infiltration testing not found for proposed infiltration basin",
  category: "Infiltration",
  risk: "high",
  status: "missing",
};

const steps: Step[] = [
  {
    label: "Checklist requirement",
    title: "If infiltration is proposed, infiltration testing is included",
    body: "The stormwater checklist applies an infiltration-testing requirement because the plans propose an infiltration basin. The expected evidence is field test locations, rates, method, and date. This requirement is what the submitted package is measured against.",
    href: "/checklist",
    cta: "Open the checklist",
  },
  {
    label: "Finding",
    title: FINDING.title,
    body: "An infiltration basin is proposed, but no field infiltration testing logs are in the package. The finding is recorded with status missing and high review attention, and it is routed to human review. Without testing, feasibility and sizing cannot be confirmed by the applicant's submission.",
    href: "/findings",
    cta: "Open findings",
  },
  {
    label: "Source evidence",
    title: "Evidence reference: what the documents do and do not show",
    body: "The expected infiltration-testing-logs.pdf is missing from the package. The soil report notes a seasonal high groundwater condition, and the stormwater report does not reconcile groundwater separation for the infiltration practice. The finding links back to these documents so the gap is traceable to specific sources.",
    href: "/documents",
    cta: "Open documents",
  },
  {
    label: "Review packet item",
    title: "Organized into the review packet",
    body: "The finding becomes a review packet item in the infiltration section, with its evidence links carried along. The evidence traceability matrix shows the connection from the requirement to the finding to the source documents in one place.",
    href: "/review-packet",
    cta: "Open the review packet",
  },
  {
    label: "Workflow board item",
    title: "Tracked on the workflow board",
    body: "The packet item is promoted to the workflow board, where a reviewer triages it, requests follow-up or more information, and records notes. The recommended reviewer action is to request field infiltration testing documentation or a design revision.",
    href: "/workflow-board",
    cta: "Open the workflow board",
  },
  {
    label: "Draft response language",
    title: "Drafted into the response package",
    body: "The response package drafts plain review-support wording for the applicant: please provide field infiltration testing documentation (test locations, rates, method, date, and depth to groundwater) for the proposed infiltration basin, or provide a design revision. Note that the soil report indicates a seasonal high groundwater condition that is not reconciled with the infiltration practice in the stormwater report. The reviewer edits this draft before anything is sent; Civil Engineer AI never issues the response itself.",
    href: "/response-package",
    cta: "Open the response package",
  },
];

export default function GuidedDemoThread() {
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          One issue, end to end
        </p>
        <h3 className="mt-1 text-lg font-semibold text-slate-900">
          Missing infiltration testing and groundwater separation concern
        </h3>
        <p className="mt-2 text-sm text-slate-600">
          Follow a single Brookside Meadows issue through the whole
          review-support workflow. Each step links into the module where the live
          data is served by the backend. This proves one complete thread without
          needing to understand every module first.
        </p>
        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-slate-600">
            category: {FINDING.category}
          </span>
          <span className="rounded-full bg-amber-50 px-2 py-0.5 text-amber-700">
            review attention: {FINDING.risk}
          </span>
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-slate-600">
            status: {FINDING.status}
          </span>
        </div>
      </div>

      <ol className="space-y-4">
        {steps.map((step, index) => (
          <li
            key={step.label}
            className="surface-card flex gap-4 p-5"
          >
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-water-50 text-sm font-bold text-water-700">
              {index + 1}
            </div>
            <div className="flex-1">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {step.label}
              </p>
              <h4 className="mt-0.5 text-base font-semibold text-slate-900">
                {step.title}
              </h4>
              <p className="mt-1 text-sm text-slate-600">{step.body}</p>
              <Link
                href={step.href}
                className="mt-2 inline-block text-sm font-semibold text-water-700 hover:text-water-600"
              >
                {step.cta}
              </Link>
            </div>
          </li>
        ))}
      </ol>

      <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
        <p className="text-sm font-semibold text-amber-800">
          Human-review boundary
        </p>
        <p className="mt-1 text-sm text-amber-700">
          This thread is review-support only. Every step keeps the issue under
          human review, and the issue stays open as a review-support item until a
          person acts on it. Civil Engineer AI does not approve plans, certify
          compliance, verify CAD, validate design, declare the project safe, or
          close the issue. A licensed Professional Engineer remains responsible
          for any final decision.
        </p>
      </div>
    </div>
  );
}
