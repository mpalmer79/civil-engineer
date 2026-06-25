// Guided end-to-end demo thread for one concrete review-support concern:
// missing infiltration testing and an unaddressed groundwater separation
// discussion for the proposed Brookside Meadows infiltration basin.
//
// The thread walks one finding through every module so a visitor can follow a
// complete workflow without learning each page first. The content below is
// seeded review-support demo data drawn from the Brookside Meadows fixture
// (the checklist, findings, and documents seed data). Nothing here approves a
// plan, certifies compliance, verifies CAD, or replaces a licensed Professional
// Engineer. Every step stays a review-support step that needs human review.

export type GuidedDemoStep = {
  key: string;
  module: string;
  href: string;
  heading: string;
  body: string;
  detail?: string[];
};

export const guidedDemoFinding = {
  findingId: "find_infiltration_missing",
  title: "Infiltration testing not found for proposed infiltration basin",
  category: "Infiltration",
  relatedFindingId: "find_gw_separation",
  relatedTitle: "Groundwater separation for infiltration not addressed",
};

export const guidedDemoSteps: GuidedDemoStep[] = [
  {
    key: "checklist",
    module: "Checklist requirement",
    href: "/checklist",
    heading: "If infiltration is proposed, infiltration testing is included",
    body: "The stormwater checklist item chk_infiltration_testing applies when the project proposes an infiltration practice. A companion item, chk_groundwater_separation, asks that separation to seasonal high groundwater is addressed.",
    detail: [
      "Expected evidence: test locations, rates, method, and date.",
      "Supporting documents: soils report and infiltration testing documentation.",
      "Risk level: high. Applies when the project has an infiltration practice.",
    ],
  },
  {
    key: "finding",
    module: "Finding",
    href: "/findings",
    heading: guidedDemoFinding.title,
    body: "An infiltration basin is proposed, but no field infiltration testing logs are in the package. A related finding notes that groundwater separation for the infiltration practice is not addressed. Both are review-support findings that need reviewer confirmation, not final engineering conclusions.",
    detail: [
      "Why it matters: infiltration BMPs depend on site-specific testing; without it, feasibility and sizing cannot be confirmed.",
      "Related finding: groundwater separation for infiltration not addressed.",
      "Human review state: pending. No finding is final without a recorded human review action.",
    ],
  },
  {
    key: "evidence",
    module: "Source document and evidence reference",
    href: "/documents",
    heading: "Soils report present, infiltration testing logs missing",
    body: "The soils and geotechnical report (soils-geotechnical-report.pdf) is present and notes seasonal high groundwater, but the separation is never reconciled in the stormwater report. The infiltration testing logs (infiltration-testing-logs.pdf) are missing for a proposed infiltration practice.",
    detail: [
      "Evidence link: doc_soils_report notes seasonal high groundwater.",
      "Evidence gap: doc_infiltration_logs is missing or incomplete.",
      "Each finding traces back to its source document for the reviewer to confirm.",
    ],
  },
  {
    key: "packet",
    module: "Review packet item",
    href: "/review-packet",
    heading: "Infiltration concern assembled into the review packet draft",
    body: "The finding and its evidence are organized into a review packet item under the infiltration section. The packet item collects the checklist requirement, the finding, and the document references so a reviewer can see the whole concern in one place.",
    detail: [
      "Section: infiltration and groundwater separation.",
      "Severity: high. Status: draft, requires human review.",
      "The packet is draft review-support material, not an approval.",
    ],
  },
  {
    key: "workflow",
    module: "Workflow board item",
    href: "/workflow-board",
    heading: "Tracked as a more-information item on the workflow board",
    body: "The promoted finding becomes a workflow item that a reviewer moves through triage, follow-up, more information, reviewer checked, and ready for handoff. The infiltration concern sits in more information while the applicant is asked for the missing testing and separation analysis.",
    detail: [
      "Column: more information requested.",
      "Recommended reviewer action: request field infiltration testing and a separation analysis.",
      "Ready for handoff describes review-support readiness, not approval.",
    ],
  },
  {
    key: "response",
    module: "Draft response package language",
    href: "/response-package",
    heading: "Draft comment back to the applicant",
    body: "The response package drafts external wording grouped by topic. Draft language for this concern: \"The submission proposes an infiltration basin. Field infiltration testing (locations, rates, method, and date) was not found in the package, and separation to seasonal high groundwater is not addressed in the stormwater report. Please provide field infiltration testing documentation and a separation analysis that references the documented seasonal high groundwater depth, or a design revision.\"",
    detail: [
      "Wording is editable and stays review-support language.",
      "Attachment checklist: soils report reference and the missing testing logs.",
      "A human review sign-off is required before the response is sent.",
    ],
  },
  {
    key: "boundary",
    module: "Human-review boundary",
    href: "/human-review",
    heading: "A reviewer and a licensed engineer stay responsible",
    body: "Every step above is a review-support step. Civil Engineer AI organizes the requirement, the finding, the evidence, the packet item, the workflow item, and the draft response, but it does not approve plans, certify compliance, verify CAD, validate the design, or declare the project safe. A human reviewer confirms each finding and a licensed Professional Engineer remains responsible for any final decision.",
    detail: [
      "No finding is final without a recorded human review action.",
      "Sanctioned wording: potential issue, needs human review, recommended follow-up.",
      "There is no action named approve.",
    ],
  },
];

export default function GuidedDemoThread() {
  return (
    <div className="space-y-6">
      <div className="surface-card p-6">
        <p className="text-sm font-semibold uppercase tracking-wide text-water-700">
          Tracked concern
        </p>
        <h2 className="mt-1 text-xl font-bold tracking-tight text-slate-900">
          {guidedDemoFinding.title}
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          This guided thread follows one concern, missing infiltration testing
          and an unaddressed groundwater separation discussion, from checklist
          requirement to draft response and the human-review boundary. It proves
          one complete review-support workflow without requiring you to learn
          every module first.
        </p>
      </div>

      <ol className="space-y-4">
        {guidedDemoSteps.map((step, index) => (
          <li key={step.key} className="surface-card p-6">
            <div className="flex items-start gap-4">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-water-50 text-sm font-bold text-water-700">
                {index + 1}
              </span>
              <div className="min-w-0">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  {step.module}
                </p>
                <h3 className="mt-1 text-base font-semibold text-slate-900">
                  {step.heading}
                </h3>
                <p className="mt-2 text-sm text-slate-600">{step.body}</p>
                {step.detail ? (
                  <ul className="mt-3 space-y-1">
                    {step.detail.map((item) => (
                      <li
                        key={item}
                        className="flex items-start gap-2 text-sm text-slate-600"
                      >
                        <span aria-hidden="true" className="mt-0.5 text-water-600">
                          •
                        </span>
                        {item}
                      </li>
                    ))}
                  </ul>
                ) : null}
                <a
                  href={step.href}
                  className="mt-3 inline-block text-sm font-semibold text-water-700 hover:text-water-800"
                >
                  Open the {step.module.toLowerCase()} module
                </a>
              </div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
