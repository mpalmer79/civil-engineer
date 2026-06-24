import { PROJECT_ID, safeFetch } from "./client";
import { checklist as staticChecklist, type ChecklistItem } from "@/data/checklist";

type ApiChecklistItem = {
  checklist_item_id: string;
  category: string;
  requirement: string;
  expected_evidence: string;
  supporting_documents: string[];
  risk_level: ChecklistItem["riskLevel"];
  applies_when: string;
  expected_status_for_brookside_meadows: ChecklistItem["expectedStatus"];
  planted_issue: string | null;
};

export async function getChecklist(): Promise<ChecklistItem[]> {
  const data = await safeFetch<ApiChecklistItem[]>(
    `/api/v1/projects/${PROJECT_ID}/checklist`,
  );
  if (!data) return staticChecklist;
  return data.map((c) => ({
    checklistItemId: c.checklist_item_id,
    category: c.category,
    requirement: c.requirement,
    expectedEvidence: c.expected_evidence,
    supportingDocuments: c.supporting_documents.join(", "),
    riskLevel: c.risk_level,
    appliesWhen: c.applies_when,
    expectedStatus: c.expected_status_for_brookside_meadows,
    plantedIssue: c.planted_issue,
  }));
}
