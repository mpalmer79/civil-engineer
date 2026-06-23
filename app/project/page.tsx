import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import ProjectSummaryCard from "@/components/ProjectSummaryCard";
import MetricCard from "@/components/MetricCard";
import SectionCard from "@/components/SectionCard";
import SafetyBoundaryBanner from "@/components/SafetyBoundaryBanner";
import {
  getProject,
  getDocuments,
  getChecklist,
  getFindings,
  getAuditEvents,
  getEvaluationData,
} from "@/lib/api";

export default async function ProjectPage() {
  const [brookside, documents, checklist, findings, auditEvents, evaluation] =
    await Promise.all([
      getProject(),
      getDocuments(),
      getChecklist(),
      getFindings(),
      getAuditEvents(),
      getEvaluationData(),
    ]);
  const evaluationCases = evaluation.cases;

  const dashboardCards = [
    {
      value: documents.length,
      label: "Documents",
      hint: `${documents.filter((d) => d.status === "present").length} present`,
      href: "/documents",
      accent: "water" as const,
    },
    {
      value: `${checklist.filter((c) => c.expectedStatus === "supported").length} / ${checklist.length}`,
      label: "Checklist supported",
      hint: "Remaining need follow-up",
      href: "/checklist",
      accent: "land" as const,
    },
    {
      value: findings.filter((f) => f.riskLevel === "high").length,
      label: "High-risk findings",
      hint: "Review-support issues",
      href: "/findings",
      accent: "red" as const,
    },
    {
      value: findings.filter((f) => f.humanReviewState === "pending").length,
      label: "Pending human review",
      hint: "Awaiting reviewer action",
      href: "/findings",
      accent: "amber" as const,
    },
    {
      value: evaluationCases.length,
      label: "Evaluation cases",
      hint: `${evaluationCases.filter((c) => c.passed).length} passed`,
      href: "/evaluation",
      accent: "water" as const,
    },
    {
      value: auditEvents.length,
      label: "Audit events",
      hint: "Traceability records",
      href: "/audit",
      accent: "slate" as const,
    },
  ];

  return (
    <div>
      <PageHeader
        eyebrow="Project dashboard"
        title="Brookside Meadows"
        description="The primary review fixture for Civil Engineer AI: a fictional 47-lot single-family subdivision in the Town of Hartwell, submitted for subdivision and post-construction stormwater review."
      />

      <div className="mx-auto max-w-7xl space-y-10 px-4 py-10 sm:px-6 lg:px-8">
        {/* Dashboard cards */}
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
          {dashboardCards.map((card) => (
            <Link
              key={card.label}
              href={card.href}
              className="transition-transform hover:-translate-y-0.5"
            >
              <MetricCard
                value={card.value}
                label={card.label}
                hint={card.hint}
                accent={card.accent}
              />
            </Link>
          ))}
        </div>

        <ProjectSummaryCard project={brookside} />

        {/* Site conditions + improvements */}
        <div className="grid gap-6 lg:grid-cols-2">
          <SectionCard
            title="Existing site conditions"
            description="Documented existing conditions that drive checklist applicability and ground the findings."
          >
            <ul className="space-y-3">
              {brookside.siteConditions.map((c) => (
                <li key={c.type} className="rounded-lg bg-slate-50 p-3">
                  <p className="text-sm font-semibold text-slate-800">
                    {c.label}
                  </p>
                  <p className="mt-0.5 text-sm text-slate-600">
                    {c.description}
                  </p>
                </li>
              ))}
            </ul>
          </SectionCard>

          <SectionCard
            title="Proposed improvements"
            description="Proposed design elements, including the green-and-gray stormwater treatment train."
          >
            <ul className="space-y-3">
              {brookside.proposedImprovements.map((imp) => (
                <li key={imp.label} className="rounded-lg bg-slate-50 p-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold text-slate-800">
                      {imp.label}
                    </p>
                    {imp.aliases.length > 0 ? (
                      <span className="badge bg-amber-50 text-amber-700 ring-amber-600/20">
                        also labeled {imp.aliases.join(", ")}
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-0.5 text-sm text-slate-600">
                    {imp.description}
                  </p>
                </li>
              ))}
            </ul>
          </SectionCard>
        </div>

        {/* Known constraints */}
        <SectionCard
          title="Known constraints"
          description="Realistic engineering tensions a reviewer would track on this package."
        >
          <ul className="grid gap-3 sm:grid-cols-2">
            {brookside.knownConstraints.map((k) => (
              <li
                key={k}
                className="flex items-start gap-2 rounded-lg bg-amber-50 px-3 py-2 text-sm text-slate-700"
              >
                <span aria-hidden="true" className="mt-0.5 text-amber-600">
                  ▲
                </span>
                {k}
              </li>
            ))}
          </ul>
        </SectionCard>

        {/* Why a strong fixture */}
        <SectionCard title="Why this project is a strong AI review fixture">
          <div className="space-y-3 text-sm text-slate-600">
            <p>
              Brookside Meadows is deliberately authored with realistic planted
              conflicts, missing evidence, and civil engineering tensions so the
              review-support system has concrete, checkable work to do, not a toy
              example.
            </p>
            <ul className="grid gap-2 sm:grid-cols-2">
              <li className="rounded-lg bg-slate-50 px-3 py-2">
                Conflicting design-storm assumptions across the report and the
                town checklist.
              </li>
              <li className="rounded-lg bg-slate-50 px-3 py-2">
                A proposed infiltration basin with missing field testing and
                unaddressed groundwater separation.
              </li>
              <li className="rounded-lg bg-slate-50 px-3 py-2">
                A downstream culvert concern with no downstream capacity
                discussion.
              </li>
              <li className="rounded-lg bg-slate-50 px-3 py-2">
                Maintenance ownership, erosion-control sequencing, an open RFI,
                and a referenced-but-missing sheet.
              </li>
            </ul>
            <p>
              It is also richer than the v1 stormwater review needs, carrying
              grading, roadway, utility, erosion-control, phasing, and inspection
              content, so the same fixture supports every future module.
            </p>
          </div>
        </SectionCard>

        <SafetyBoundaryBanner />
      </div>
    </div>
  );
}
