import { PROJECT_ID, apiFetch, type DemoSourced } from "./client";
import { findings as staticFindings, type Finding } from "@/data/findings";

type ApiFinding = {
  finding_id: string;
  planted_issue: string;
  title: string;
  category: string;
  risk_level: Finding["riskLevel"];
  expected_status: Finding["expectedStatus"];
  evidence_to_find: string;
  reason_it_matters: string;
  recommended_human_action: string;
  human_review_status: string;
  related_checklist_items: string[];
  related_documents: string[];
};

export async function getFindings(): Promise<DemoSourced<Finding[]>> {
  const result = await apiFetch<ApiFinding[]>(
    `/api/v1/projects/${PROJECT_ID}/findings`,
  );
  // Explicit public-demo policy: when the demo backend is unreachable this
  // surface renders the repository fixture snapshot and says so. Authenticated
  // surfaces never do this; see docs/adr/0002-data-source-boundaries.md.
  if (!result.ok) return { data: staticFindings, source: "demo_fixture" };
  const data = result.data;
  return { source: "backend_seeded", data: data.map((f) => ({
    findingId: f.finding_id,
    plantedIssue: f.planted_issue,
    title: f.title,
    category: f.category,
    riskLevel: f.risk_level,
    expectedStatus: f.expected_status,
    checklistItemId: f.related_checklist_items[0] ?? "",
    evidenceToFind: f.evidence_to_find,
    whyItMatters: f.reason_it_matters,
    recommendedHumanAction: f.recommended_human_action,
    // Phase 1 uses "pending" for an unactioned finding; the backend expresses
    // the same state as "requires_human_review".
    humanReviewState: "pending",
  })) };
}
