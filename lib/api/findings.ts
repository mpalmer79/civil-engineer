import { PROJECT_ID, safeFetch } from "./client";
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

export async function getFindings(): Promise<Finding[]> {
  const data = await safeFetch<ApiFinding[]>(
    `/api/v1/projects/${PROJECT_ID}/findings`,
  );
  if (!data) return staticFindings;
  return data.map((f) => ({
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
  }));
}
