// Shared data for the Start Here demo experience and the guided demo. The
// reviewer journey walks a visitor through the Brookside Meadows sample project
// in the order a reviewer would actually work: project, documents, page-level
// evidence, checklist review, findings, applicant responses, resubmittals,
// reviewer response package, comment letter draft, and the operational
// dashboard. Brookside Meadows is a synthetic public demo fixture. None of these
// steps approves a plan, certifies compliance, validates design, or replaces a
// licensed Professional Engineer. Every step stays review-support only.

// The public Brookside Meadows sample project id. Sub-routes are the real
// project workflow routes, scoped to this seeded demo record.
export const BROOKSIDE_PROJECT_ID = "proj_brookside_meadows";

const base = `/projects/${BROOKSIDE_PROJECT_ID}`;

export type DemoJourneyStep = {
  step: number;
  title: string;
  description: string;
  href: string;
  label: string;
  whatToNotice: string;
  category: string;
};

// The recommended demo path. Each step links to the relevant Brookside Meadows
// route and notes what an evaluator should look for. Routes that open a specific
// record (a PDF's pages, a single package's comment letter) link to the parent
// list, with a "what to notice" pointer to the next click.
export const demoJourneySteps: DemoJourneyStep[] = [
  {
    step: 1,
    title: "Review the sample project",
    description:
      "Open the Brookside Meadows project record to see its metadata, review context, and workflow entry points.",
    href: base,
    label: "Open Brookside Meadows",
    whatToNotice:
      "The project overview links to every part of the review-support workflow.",
    category: "Project",
  },
  {
    step: 2,
    title: "Inspect uploaded documents",
    description:
      "See the submitted and referenced documents with storage, processing, and indexing status.",
    href: `${base}/documents`,
    label: "View documents",
    whatToNotice:
      "Status chips track intake handling only; they never imply approval.",
    category: "Documents",
  },
  {
    step: 3,
    title: "Open indexed PDF pages",
    description:
      "Open a digital PDF to view its page-level records and text extraction status.",
    href: `${base}/documents`,
    label: "Open a document",
    whatToNotice:
      "Open a PDF, then View pages to see per-page extraction records.",
    category: "Documents",
  },
  {
    step: 4,
    title: "View page-level evidence",
    description:
      "Search indexed page text to see exactly which page and excerpt supports a concern.",
    href: `${base}/evidence-search`,
    label: "Search evidence",
    whatToNotice:
      "Each result cites a specific page; results are candidates, not conclusions.",
    category: "Evidence",
  },
  {
    step: 5,
    title: "Triage evidence candidates",
    description:
      "Work the evidence candidate queue, where search results wait for reviewer confirmation.",
    href: `${base}/evidence-candidates`,
    label: "Open candidate queue",
    whatToNotice:
      "Candidates require reviewer confirmation before they support a finding.",
    category: "Evidence",
  },
  {
    step: 6,
    title: "Apply checklist review",
    description:
      "Apply a stormwater rule pack and track checklist evidence status item by item.",
    href: `${base}/checklists`,
    label: "Open checklists",
    whatToNotice:
      "Checklist evidence status is review-support only; the reviewer decides applicability.",
    category: "Checklist",
  },
  {
    step: 7,
    title: "Review findings",
    description:
      "See review-support findings with their category, evidence status, and citations.",
    href: `${base}/findings`,
    label: "View findings",
    whatToNotice:
      "No finding is final without a recorded human review action.",
    category: "Findings",
  },
  {
    step: 8,
    title: "Record applicant responses",
    description:
      "Track applicant responses to reviewer comments in the response matrix.",
    href: `${base}/response-matrix`,
    label: "Open response matrix",
    whatToNotice:
      "Applicant responses are recorded for reviewer review, never as proof.",
    category: "Responses",
  },
  {
    step: 9,
    title: "Track resubmittals",
    description:
      "Register resubmittal rounds and see which items are carried forward for review.",
    href: `${base}/resubmittals`,
    label: "View resubmittals",
    whatToNotice:
      "Items are carried forward for review across rounds, not closed.",
    category: "Resubmittals",
  },
  {
    step: 10,
    title: "Build a reviewer response package",
    description:
      "Assemble reviewer-selected records into a controlled response package.",
    href: `${base}/response-packages`,
    label: "Open response packages",
    whatToNotice:
      "A package is a reviewer communication record; it does not approve a project.",
    category: "Response package",
  },
  {
    step: 11,
    title: "Preview a comment letter draft",
    description:
      "Generate and preview a deterministic comment letter draft from a package.",
    href: `${base}/response-packages`,
    label: "Preview comment letter",
    whatToNotice:
      "Open a package, then its comment letter draft and preview. The boundary statement stays visible.",
    category: "Response package",
  },
  {
    step: 12,
    title: "View dashboard and workload",
    description:
      "See the operational reviewer dashboard with workload and pending reviewer action indicators.",
    href: "/dashboard",
    label: "Open dashboard",
    whatToNotice:
      "Counts are operational indicators only, not engineering outcomes.",
    category: "Operations",
  },
];

// Technical foundation summary for evaluators. Each item is a delivered part of
// the full-stack review-support build. These describe capabilities only and make
// no claim beyond what the system actually does.
export const technicalFoundation: { title: string; detail: string }[] = [
  {
    title: "Next.js frontend",
    detail: "Typed React app with a shared visual system and API client.",
  },
  {
    title: "FastAPI backend",
    detail: "Versioned review-support API serving real project records.",
  },
  {
    title: "SQLAlchemy data model",
    detail: "Durable relational model for projects, documents, and review records.",
  },
  {
    title: "PDF page indexing",
    detail: "Indexes digital PDF pages and extracts embedded text per page.",
  },
  {
    title: "Page-level evidence citations",
    detail: "Findings cite an exact page or section as a source reference.",
  },
  {
    title: "Deterministic evidence retrieval",
    detail: "Search ranks indexed page text without live AI calls.",
  },
  {
    title: "Auth and project access control",
    detail: "Local accounts, organizations, roles, and per-project access.",
  },
  {
    title: "Object storage abstraction",
    detail: "Pluggable storage layer for durable document files.",
  },
  {
    title: "Audit trail",
    detail: "Reviewer actions and accesses are recorded as audit events.",
  },
  {
    title: "Reviewer dashboard",
    detail: "Operational workload and pending reviewer action indicators.",
  },
  {
    title: "Deployment diagnostics",
    detail: "Readiness, storage, and environment status without exposing secrets.",
  },
];

// Notes aimed at a recruiter or technical evaluator skimming the demo.
export const evaluatorNotes: string[] = [
  "The workflow is document-first and evidence-first: findings trace back to a specific page.",
  "The system is reviewer-controlled. It organizes evidence and never decides an engineering outcome.",
  "Search results and findings are candidates that require reviewer confirmation.",
  "Reviewer response packages are communication records, not approvals or issue closures.",
  "Live AI calls, OCR, DWG parsing, and final approval workflows are intentionally out of scope.",
];
