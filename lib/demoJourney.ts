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

// The focused AEC pre-submittal QA demo. This is the buyer-facing product tour
// used by the guided demo: a civil/AEC team runs the Brookside Meadows sample
// package through review-support QA before it goes to a municipal reviewer. Each
// step links to the real Brookside Meadows surface it describes. Nothing here
// approves, certifies, verifies, or validates anything; every step stays
// review-support only and a human reviewer remains responsible.
export type AecDemoStep = {
  id: string;
  step: number;
  eyebrow: string;
  title: string;
  narrative: string;
  highlights: string[];
  href: string;
  ctaLabel: string;
  whatToNotice: string;
};

export const aecDemoSteps: AecDemoStep[] = [
  {
    id: "cad-intake",
    step: 1,
    eyebrow: "CAD / DXF intake",
    title: "Surface review-support findings from the plan set",
    narrative:
      "The Brookside Meadows team starts with the CAD plan set. Civil Engineer AI organizes DXF metadata and surfaces review-support findings tied back to source context, so likely review issues show up before submittal.",
    highlights: [
      "Organized DXF metadata from the plan set",
      "Review-support findings, each a potential issue for human review",
      "Promoted and unpromoted findings stay under reviewer control",
    ],
    href: `${base}/cad`,
    ctaLabel: "Open CAD intake",
    whatToNotice:
      "Findings are potential issues for a human reviewer, not engineering conclusions.",
  },
  {
    id: "plan-consistency",
    step: 2,
    eyebrow: "Plan and report consistency",
    title: "Catch conflicts between the plan set and the report",
    narrative:
      "Next, the team checks the plan set against the stormwater report. Consistency checks flag conflicting references and gaps so they are caught in pre-submittal QA instead of in a municipal review comment.",
    highlights: [
      "Plan and report conflicts flagged for review",
      "Inconsistent or missing references surfaced",
      "Findings that require reviewer confirmation",
    ],
    href: `${base}/plan-consistency`,
    ctaLabel: "Open consistency checks",
    whatToNotice:
      "A flagged conflict is a prompt to review, not a statement of final correctness.",
  },
  {
    id: "traceability",
    step: 3,
    eyebrow: "Evidence traceability",
    title: "Trace every requirement back to source evidence",
    narrative:
      "The team follows source-backed traceability: a requirement-to-evidence matrix that links each checklist requirement to the evidence behind it, and is honest where no evidence is linked yet.",
    highlights: [
      "Requirement-to-evidence matrix with source-backed links",
      "Linked evidence and potential support, never marked satisfied",
      "A clear no-linked-evidence-yet distinction",
    ],
    href: `${base}/traceability`,
    ctaLabel: "Open traceability",
    whatToNotice:
      "Linked evidence is potential support for review; it does not mean a requirement is satisfied.",
  },
  {
    id: "workflow-board",
    step: 4,
    eyebrow: "Workflow board",
    title: "Track the items that need reviewer attention",
    narrative:
      "Findings become workflow items the team can work. The board tracks items needing reviewer attention, follow-up work, and which items are signalled ready for handoff.",
    highlights: [
      "Items needing reviewer attention in one place",
      "Follow-up workflow across the review",
      "Ready-for-handoff signals, not completion claims",
    ],
    href: `${base}/workflow-board`,
    ctaLabel: "Open workflow board",
    whatToNotice:
      "Ready-for-handoff is an organizational signal, not a statement that review is complete.",
  },
  {
    id: "draft-handoff",
    step: 5,
    eyebrow: "Draft reviewer handoff",
    title: "Assemble a draft reviewer handoff package",
    narrative:
      "Finally, the team assembles a draft reviewer handoff package: the findings, evidence links, and traceability references organized for the next reviewer, with the professional boundary kept visible.",
    highlights: [
      "Draft handoff package with evidence links",
      "Traceability references carried into the handoff",
      "Professional limitations stay visible on the draft",
    ],
    href: `${base}/review-packets`,
    ctaLabel: "View draft handoff",
    whatToNotice:
      "This is a draft reviewer handoff package, not a final or certified report.",
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

// A focused five-minute path for a recruiter or hiring manager who wants the
// fastest credible tour. Each entry links to an existing public route.
export const fiveMinutePath: { label: string; href: string; note: string }[] = [
  {
    label: "Start Here",
    href: "/start-here",
    note: "This page: what it is, who it is for, and the demo path.",
  },
  {
    label: "Guided Demo",
    href: "/guided-demo",
    note: "The reviewer journey, plus one concern traced end to end.",
  },
  {
    label: "Brookside Meadows sample project",
    href: base,
    note: "The seeded public demo project and its workflow entry points.",
  },
  {
    label: "Evidence and checklist workflow",
    href: `${base}/evidence-search`,
    note: "Page-level evidence search and checklist evidence status.",
  },
  {
    label: "Response package preview",
    href: `${base}/response-packages`,
    note: "How reviewer communication records are assembled.",
  },
  {
    label: "Deployment status",
    href: "/deployment-status",
    note: "Operational readiness, storage, and backend health.",
  },
];

// A deeper path for a technical evaluator who wants to assess the engineering
// foundation. These are topics to look at, not all distinct routes.
export const technicalPath: string[] = [
  "Architecture and data model: Next.js frontend, FastAPI backend, SQLAlchemy models.",
  "PDF page indexing: digital PDFs indexed into per-page records with extracted text.",
  "Evidence citation flow: findings cite an exact page or section as a source reference.",
  "Deterministic candidate retrieval: ranked page-text search with no live AI calls.",
  "Auth and access control: local accounts, organizations, roles, and per-project access.",
  "Object storage abstraction: pluggable durable storage with credentials kept server-side.",
  "Audit trail: reviewer actions and accesses recorded as audit events.",
  "Deployment diagnostics: readiness, storage, and environment checks without exposing secrets.",
];

// Intentionally out of scope. Stating these plainly keeps the product honest and
// avoids any impression of an approval or certification engine.
export const outOfScope: string[] = [
  "No live AI calls",
  "No OCR",
  "No DWG parsing or CAD geometry validation",
  "No GIS integration",
  "No enterprise single sign-on",
  "No full applicant portal",
  "No final approval, certification, or compliance determination",
];

// A concise, visitor-facing reviewer walkthrough checklist. It mirrors the demo
// journey so an evaluator can tick through the workflow in order.
export const reviewerChecklist: string[] = [
  "Open Brookside Meadows",
  "Review documents",
  "Inspect indexed pages",
  "View evidence citations",
  "Search evidence candidates",
  "Review checklist items",
  "Open findings",
  "Review applicant response matrix",
  "Open response package",
  "Preview comment letter",
  "Check dashboard",
  "Check deployment status",
];

// Notes aimed at a recruiter or technical evaluator skimming the demo.
export const evaluatorNotes: string[] = [
  "The workflow is document-first and evidence-first: findings trace back to a specific page.",
  "The system is reviewer-controlled. It organizes evidence and never decides an engineering outcome.",
  "Search results and findings are candidates that require reviewer confirmation.",
  "Reviewer response packages are communication records, not approvals or issue closures.",
  "Live AI calls, OCR, DWG parsing, and final approval workflows are intentionally out of scope.",
];
