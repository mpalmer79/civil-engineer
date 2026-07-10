import { PROJECT_ID, apiFetch, type DemoSourced } from "./client";
import { documents as staticDocuments, type ReviewDocument } from "@/data/documents";

type ApiDocument = {
  document_id: string;
  file_name: string;
  document_type: string;
  status: ReviewDocument["status"];
  purpose: string;
  expected_key_information: string;
  intentionally_missing_or_conflicting_information: string | null;
};

export async function getDocuments(): Promise<DemoSourced<ReviewDocument[]>> {
  const result = await apiFetch<ApiDocument[]>(
    `/api/v1/projects/${PROJECT_ID}/documents`,
  );
  // Explicit public-demo policy: when the demo backend is unreachable this
  // surface renders the repository fixture snapshot and says so. Authenticated
  // surfaces never do this; see docs/adr/0002-data-source-boundaries.md.
  if (!result.ok) return { data: staticDocuments, source: "demo_fixture" };
  const data = result.data;
  return { source: "backend_seeded", data: data.map((d) => ({
    documentId: d.document_id,
    fileName: d.file_name,
    documentType: d.document_type,
    status: d.status,
    purpose: d.purpose,
    expectedKeyInformation: d.expected_key_information,
    knownIssue: d.intentionally_missing_or_conflicting_information,
  })) };
}
