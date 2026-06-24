import { PROJECT_ID, safeFetch } from "./client";
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

export async function getDocuments(): Promise<ReviewDocument[]> {
  const data = await safeFetch<ApiDocument[]>(
    `/api/v1/projects/${PROJECT_ID}/documents`,
  );
  if (!data) return staticDocuments;
  return data.map((d) => ({
    documentId: d.document_id,
    fileName: d.file_name,
    documentType: d.document_type,
    status: d.status,
    purpose: d.purpose,
    expectedKeyInformation: d.expected_key_information,
    knownIssue: d.intentionally_missing_or_conflicting_information,
  }));
}
