// Typed content for the public homepage. The homepage explains what Civil
// Engineer AI is, who it supports, and how to evaluate it. It intentionally
// shows no operational widgets: every number below is a reference-project fact
// counted from the seeded Brookside Meadows fixture and labeled as such.
// Brookside Meadows is a synthetic reference project used for product
// evaluation. Live operational data lives behind sign-in on /dashboard, and
// deployment health lives on /deployment-status where it is derived from real
// diagnostics.

import { checklist } from "@/data/checklist";
import { documents } from "@/data/documents";
import { findings } from "@/data/findings";
import { BROOKSIDE_PROJECT_ID } from "@/lib/demoJourney";

export const brooksideBase = `/projects/${BROOKSIDE_PROJECT_ID}`;

export type HomeImage = {
  src: string;
  alt: string;
};

export const heroImage: HomeImage = {
  src: "/images/civil-engineer/site-plan-review-hero.webp",
  alt: "Illustrative preliminary site plan for the synthetic Brookside Meadows case study, showing proposed roads, lots, a stormwater basin, and review evidence callouts",
};

export const workspaceImage: HomeImage = {
  src: "/images/civil-engineer/dxf-review-report-workspace.webp",
  alt: "Civil Engineer AI coffee mug beside organized DXF analysis and stormwater review reports on a glass office desk",
};

export const brooksideProjectImage: HomeImage = {
  src: "/images/civil-engineer/brookside-project-thumbnail.webp",
  alt: "Aerial visualization of the synthetic Brookside Meadows subdivision project used in the Civil Engineer AI stormwater review demonstration",
};

// Reference-project facts, counted directly from the seeded fixture so the
// homepage can never drift from the data it describes. The ten planted review
// issues are documented in docs/BROOKSIDE_MEADOWS_PROJECT_STORY.md (I-1
// through I-10).

export type CaseStudyFact = {
  value: string;
  label: string;
};

export const caseStudyFacts: readonly CaseStudyFact[] = [
  { value: "47", label: "Lots in the synthetic subdivision" },
  { value: String(documents.length), label: "Documents in the demo package" },
  { value: "10", label: "Intentionally planted review issues" },
  { value: String(checklist.length), label: "Checklist items tracked" },
  { value: String(findings.length), label: "Review-support findings" },
] as const;

export type WorkflowStage = {
  stage: number;
  title: string;
  detail: string;
  href: string;
};

export const workflowStages: readonly WorkflowStage[] = [
  {
    stage: 1,
    title: "Project intake",
    detail:
      "Register the project and its submission package so every later action has a stable record to attach to.",
    href: brooksideBase,
  },
  {
    stage: 2,
    title: "Document and DXF intake",
    detail:
      "Store submitted documents, index digital PDF pages, and parse DXF metadata deterministically through CAD Intake.",
    href: `${brooksideBase}/documents`,
  },
  {
    stage: 3,
    title: "Evidence indexing and retrieval",
    detail:
      "Search indexed page text so each concern can point at the exact page and excerpt that supports it.",
    href: `${brooksideBase}/evidence-search`,
  },
  {
    stage: 4,
    title: "Checklist and finding review",
    detail:
      "Work a stormwater checklist with evidence status per item; findings stay review-support only.",
    href: `${brooksideBase}/checklists`,
  },
  {
    stage: 5,
    title: "Applicant response tracking",
    detail:
      "Track applicant responses and resubmittal rounds against the findings that prompted them.",
    href: `${brooksideBase}/response-matrix`,
  },
  {
    stage: 6,
    title: "Reviewer-controlled handoff",
    detail:
      "Assemble a response package for reviewer handoff, with revision history and audit attribution.",
    href: `${brooksideBase}/response-packages`,
  },
] as const;

export type RealVsSeededItem = {
  title: string;
  detail: string;
};

export const realVsSeeded: readonly RealVsSeededItem[] = [
  {
    title: "Implemented",
    detail:
      "FastAPI backend with authentication, per-project access control, document storage, PDF page indexing, DXF metadata parsing, evidence retrieval, and audit events.",
  },
  {
    title: "Seeded demo",
    detail:
      "Brookside Meadows is a synthetic reference project used for product evaluation. Its documents, findings, and responses are fixtures, clearly labeled, and never presented as a real municipal submission.",
  },
  {
    title: "Intentionally out of scope",
    detail:
      "No live AI calls by default, no OCR, no DWG parsing, no GIS, and no approval, certification, or compliance determination of any kind.",
  },
] as const;

// Professional evaluation pathways. Each pathway routes a visitor to the
// surface that answers their question: the guided product tour, the technical
// validation, the architecture documentation, or a pilot request.

export type ProductPathway = {
  title: string;
  detail: string;
  href: string;
  linkLabel: string;
  external?: boolean;
};

export const productPathways: readonly ProductPathway[] = [
  {
    title: "Explore the platform",
    detail:
      "Follow the guided tour through the Brookside Meadows reference project, a synthetic fixture built for product evaluation, and see one concern traced from intake to reviewer handoff.",
    href: "/guided-demo",
    linkLabel: "Start the guided tour",
  },
  {
    title: "Review the technical validation",
    detail:
      "A synthetic, structurally valid subdivision DXF is processed through the real upload and parse services, compared against versioned ground truth, and published with downloadable artifacts and SHA-256 hashes. The validation shows deterministic metadata extraction and review support, not engineering approval.",
    href: "/proof-of-concept",
    linkLabel: "Open the DXF validation report",
  },
  {
    title: "Examine the architecture",
    detail:
      "Read the architecture documentation: the Next.js frontend, FastAPI backend, relational data model, storage abstraction, and the real-versus-seeded boundary behind every surface.",
    href: "https://github.com/mpalmer79/civil-engineer/tree/main/docs",
    linkLabel: "Browse the documentation",
    external: true,
  },
  {
    title: "Request a pilot",
    detail:
      "Municipal and civil engineering review teams can request a pilot workspace and evaluate the review-support workflow against their own submission process.",
    href: "/pilot",
    linkLabel: "Request a pilot workspace",
  },
] as const;
