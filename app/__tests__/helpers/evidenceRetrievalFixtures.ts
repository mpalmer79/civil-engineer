// Shared review-support fixtures and seeded data for the evidence retrieval
// test suite. These are plain data objects and word lists reused across the
// evidence search, candidate, and professional-boundary test files. Lifecycle
// hooks and vi.mock calls stay in each test file because vitest hoists them.

export const PROHIBITED_WORDS = [
  "approved",
  "certified",
  "fully compliant",
  "passes review",
  "validated",
  "resolved",
  "closed",
];

export const project = {
  projectId: "proj_user_1",
  projectName: "Retrieval Project",
  projectType: "Subdivision",
  locationContext: "",
  jurisdiction: "Town",
  reviewType: "Review",
  reviewDomain: "stormwater",
  acreage: 1,
  disturbedArea: 1,
  proposedLots: 0,
  status: "intake_started",
  summary: "",
  sourceMode: "user_created",
  createdByName: "Demo Reviewer",
  applicantName: null,
  applicantOrganization: null,
  designEngineerName: null,
  designFirm: null,
  submissionReference: null,
  reviewRoundCurrent: 1,
  parcelIds: [],
  createdAt: null,
  updatedAt: null,
  documentCount: 1,
  findingCount: 0,
  auditEventCount: 1,
};

export const document = {
  documentId: "doc_user_1",
  projectId: "proj_user_1",
  fileName: "doc_abc.pdf",
  originalFileName: "Plan Set.pdf",
  documentType: "stormwater_report",
  status: "uploaded",
  purpose: "",
  expectedKeyInformation: "",
  sourceMode: "user_uploaded",
  uploadStatus: "stored",
  processingStatus: "indexed_with_text",
  contentType: "application/pdf",
  fileSizeBytes: 1,
  checksumSha256: "abc",
  revisionLabel: null,
  revisionDate: null,
  uploadedByName: "Demo Reviewer",
  uploadedAt: null,
  registeredAt: null,
  pageCount: 2,
  indexedAt: null,
  textExtractionStatus: "text_extracted",
  textExtractionSummary: null,
  extractionWarningCount: 0,
};

export const candidate = {
  evidenceCandidateId: "cand_1",
  projectId: "proj_user_1",
  retrievalQueryId: "rq_user_1",
  documentId: "doc_user_1",
  documentPageId: "docpage_1",
  pageNumber: 2,
  findingId: null,
  checklistItemId: null,
  candidateTitle: "Plan Set.pdf page 2",
  candidateExcerpt: "...detention basin outlet...",
  matchTerms: ["detention", "basin"],
  rankingScore: 0.82,
  rankingReason: "Ranked by keyword match.",
  candidateStatus: "saved_for_review",
  candidateOrigin: "keyword_search",
  reviewerNote: null,
  createdByName: "Demo Reviewer",
  createdAt: null,
  updatedAt: null,
  dismissedAt: null,
  promotedFindingId: null,
};

export const searchResponse = {
  ok: true,
  backendReachable: true,
  data: {
    projectId: "proj_user_1",
    queryText: "detention basin",
    queryType: "keyword",
    retrievalQueryId: "rq_user_1",
    resultCount: 1,
    results: [
      {
        documentId: "doc_user_1",
        documentName: "Plan Set.pdf",
        documentType: "stormwater_report",
        documentPageId: "docpage_1",
        pageNumber: 2,
        pageLabel: "Page 2",
        textExtractionStatus: "text_extracted",
        excerpt: "...detention basin outlet...",
        matchTerms: ["detention", "basin"],
        rankingScore: 0.82,
        rankingReason: "Ranked by keyword match: detention, basin.",
        candidateOrigin: "keyword_search",
        retrievalQueryId: "rq_user_1",
      },
    ],
    message: "1 retrieval candidate(s) for reviewer review.",
  },
};

export const chunkSearchResponse = {
  ok: true,
  backendReachable: true,
  data: {
    projectId: "proj_user_1",
    queryText: "detention basin",
    queryType: "chunk_keyword",
    retrievalQueryId: "rq_user_2",
    resultCount: 1,
    results: [
      {
        documentId: "doc_user_1",
        documentName: "Plan Set.pdf",
        documentType: "stormwater_report",
        chunkId: "rdc_doc_user_1_p2_0",
        documentPageId: "docpage_1",
        pageNumber: 2,
        pageLabel: "Page 2",
        textExtractionStatus: "text_extracted",
        excerpt: "...detention basin outlet...",
        matchTerms: ["detention", "basin"],
        rankingScore: 0.78,
        rankingReason:
          "Ranked by keyword match: detention, basin in real-derived page chunk.",
        candidateOrigin: "chunk_search",
        retrievalQueryId: "rq_user_2",
      },
    ],
    message: "1 real-derived chunk candidate(s) for reviewer review.",
  },
};

export const chunkEmptyResponse = {
  ok: true,
  backendReachable: true,
  data: {
    projectId: "proj_user_1",
    queryText: "nomatch",
    queryType: "chunk_keyword",
    retrievalQueryId: "rq_user_3",
    resultCount: 0,
    results: [],
    message:
      "No real-derived chunk text matched these terms. Try different terms or " +
      "filters. This is not a finding about the document content.",
  },
};

export const promoteResponse = {
  ok: true,
  backendReachable: true,
  data: {
    finding: {
      findingId: "find_draft_1",
      projectId: "proj_user_1",
      title: "Outlet sizing draft",
      category: "stormwater",
      riskLevel: "medium",
      evidenceStatus: "needs_reviewer_confirmation",
      humanReviewStatus: "draft",
      findingOrigin: "retrieval_candidate",
      sourceMode: "user_created",
      createdByName: "Demo Reviewer",
    },
    citation: {
      evidenceCitationId: "cite_1",
      projectId: "proj_user_1",
      findingId: "find_draft_1",
      documentId: "doc_user_1",
      documentPageId: "docpage_1",
      pageNumber: 2,
      citationType: "reviewer_selected",
      citationStatus: "needs_reviewer_confirmation",
    },
    candidate: { ...candidate, candidateStatus: "promoted_to_draft" },
  },
};
