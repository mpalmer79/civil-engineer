// Route awareness for the guide. Maps the current pathname to a page
// explanation so questions like "what am I looking at" and "what should I do
// on this page" get grounded, route-specific answers. Public demo routes are
// distinguished from authenticated routes, and no entry exposes information
// that requires a session.

import type { QuickLink } from "./types";

export type RouteInfo = {
  title: string;
  description: string;
  stage?: string;
  dataSource: "public_demo" | "authenticated" | "public";
  nextSteps?: string;
  links?: QuickLink[];
  sources?: string[];
};

// Ordered: first matching prefix wins, so specific routes come first.
const ROUTE_INFO: { prefix: string; info: RouteInfo }[] = [
  {
    prefix: "/guided-demo",
    info: {
      title: "Guided Demo",
      description:
        "A curated walkthrough of the Brookside Meadows review: intake, evidence, checklist, applicant response, and reviewer-controlled handoff.",
      stage: "All six workflow stages, in order",
      dataSource: "public_demo",
      nextSteps: "Follow the steps in order; each links into the full module behind it.",
      links: [{ href: "/start-here", label: "Technical Overview" }],
      sources: ["app/guided-demo/page.tsx", "lib/demoJourney.ts"],
    },
  },
  {
    prefix: "/start-here",
    info: {
      title: "Technical Overview",
      description:
        "The evaluator entry point: what the product is, the five-minute and technical review paths, the technical foundation, and the demo module index.",
      dataSource: "public",
      links: [{ href: "/guided-demo", label: "Guided Demo" }],
      sources: ["app/start-here/page.tsx"],
    },
  },
  {
    prefix: "/dashboard/queue",
    info: {
      title: "Reviewer Queue",
      description:
        "The authenticated reviewer queue: pending reviewer actions across accessible projects, ordered by review priority.",
      stage: "Checklist and finding review",
      dataSource: "authenticated",
      sources: ["app/dashboard/queue/page.tsx"],
    },
  },
  {
    prefix: "/dashboard",
    info: {
      title: "Reviewer Dashboard",
      description:
        "Authenticated operational overview: accessible projects, workload indicators, and pending reviewer actions. Data comes from the backend; failures render explicit states, never demo substitutions.",
      dataSource: "authenticated",
      sources: ["app/dashboard/page.tsx"],
    },
  },
  {
    prefix: "/documents",
    info: {
      title: "Documents (demo)",
      description:
        "The seeded Brookside Meadows submission package with intake status per document. A data-source notice states whether records come from the connected backend seed or the repository fixture snapshot.",
      stage: "Document and DXF intake",
      dataSource: "public_demo",
      nextSteps: "Open a document to inspect page-level indexing, or continue to evidence search.",
      sources: ["app/documents/page.tsx", "data/documents.ts"],
    },
  },
  {
    prefix: "/checklist",
    info: {
      title: "Checklist (demo)",
      description:
        "The seeded stormwater checklist for Brookside Meadows with expected evidence status per item.",
      stage: "Checklist and finding review",
      dataSource: "public_demo",
      sources: ["app/checklist/page.tsx", "data/checklist.ts"],
    },
  },
  {
    prefix: "/findings",
    info: {
      title: "Findings (demo)",
      description:
        "The review-support findings expected in the Brookside package. Each cites its evidence and requires reviewer confirmation; none is a final determination.",
      stage: "Checklist and finding review",
      dataSource: "public_demo",
      sources: ["app/findings/page.tsx", "data/findings.ts"],
    },
  },
  {
    prefix: "/cad-intake",
    info: {
      title: "CAD Intake (demo)",
      description:
        "DXF metadata parsing: layers, blocks, and text extracted deterministically with ezdxf from the seeded sample file.",
      stage: "Document and DXF intake",
      dataSource: "public_demo",
      sources: ["backend/app/services/cad_intake_service/__init__.py"],
    },
  },
  {
    prefix: "/response-package",
    info: {
      title: "Response Package (demo)",
      description:
        "The reviewer-controlled communication record assembled from findings and applicant responses, with a draft, reviewer check, and issue lifecycle.",
      stage: "Reviewer-controlled handoff",
      dataSource: "public_demo",
      sources: ["backend/app/services/response_package_service/__init__.py"],
    },
  },
  {
    prefix: "/review-packet",
    info: {
      title: "Review Packet (demo)",
      description:
        "The assembled review packet: sections, items, and evidence links prepared for reviewer handoff.",
      stage: "Reviewer-controlled handoff",
      dataSource: "public_demo",
      sources: ["backend/app/services/review_packet_service"],
    },
  },
  {
    prefix: "/audit",
    info: {
      title: "Audit Trail (demo)",
      description:
        "Seeded audit events showing how reviewer actions and system steps are recorded with attribution.",
      dataSource: "public_demo",
      sources: ["data/auditEvents.ts"],
    },
  },
  {
    prefix: "/projects/proj_brookside_meadows",
    info: {
      title: "Brookside Meadows project workspace",
      description:
        "The project-scoped workspace for the public Brookside Meadows demo: documents, evidence, checklists, findings, responses, resubmittals, packages, and audit history.",
      dataSource: "public_demo",
      sources: ["docs/ROUTE_ARCHITECTURE.md"],
    },
  },
  {
    prefix: "/projects",
    info: {
      title: "Projects",
      description:
        "The authenticated project workspace. Signed-in reviewers see their accessible projects; the Brookside demo project remains publicly readable.",
      dataSource: "authenticated",
      sources: ["app/projects/page.tsx"],
    },
  },
  {
    prefix: "/login",
    info: {
      title: "Sign in",
      description:
        "Local account sign-in. The session is an HttpOnly cookie set by the same-origin session endpoint; no token is ever readable by browser code.",
      dataSource: "public",
      sources: ["app/api/session/login/route.ts"],
    },
  },
  {
    prefix: "/pilot",
    info: {
      title: "Pilot",
      description: "Design-partner pilot interest page with an honest scope statement.",
      dataSource: "public",
      sources: ["app/pilot/page.tsx"],
    },
  },
  {
    prefix: "/deployment-status",
    info: {
      title: "Deployment Status",
      description:
        "Operational readiness derived from real diagnostics: backend health, storage configuration, and environment checks. Never a static badge.",
      dataSource: "public",
      sources: ["app/deployment-status/page.tsx"],
    },
  },
  {
    prefix: "/",
    info: {
      title: "Product home",
      description:
        "The recruiter-facing product entry: the case study facts, six-stage workflow, human review boundary, real-versus-seeded summary, and both evaluation paths.",
      dataSource: "public",
      links: [{ href: "/guided-demo", label: "Guided Demo" }],
      sources: ["app/page.tsx"],
    },
  },
];

export function routeInfoFor(route: string): RouteInfo | null {
  if (!route) return null;
  for (const { prefix, info } of ROUTE_INFO) {
    if (prefix === "/" ? route === "/" : route.startsWith(prefix)) return info;
  }
  return null;
}

// True when the question is about the current page rather than a topic.
const PAGE_CONTEXT_PATTERNS: RegExp[] = [
  /\bwhat (am i|are we) looking at\b/,
  /\bwhat is (this|the current) (page|screen|view)\b/,
  /\bwhat should i do (here|on this page)\b/,
  /\bwhere (does this|do i) fit\b/,
  /\bwhat data is (shown|displayed) here\b/,
  /\bis this (page )?(demo|seeded|real) data\b/,
  /\bwhat happens next\b/,
  /\bwhere is this (page )?implemented\b/,
  /\bexplain this page\b/,
];

export function isPageContextQuestion(question: string): boolean {
  const text = question.toLowerCase().replace(/[^a-z0-9 ]+/g, " ").replace(/\s+/g, " ");
  return PAGE_CONTEXT_PATTERNS.some((p) => p.test(text));
}
