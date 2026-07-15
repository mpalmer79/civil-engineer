import { requireString } from "../client";
import type {
  CadBlockExtract,
  CadEntityExtract,
  CadFileUpload,
  CadLayerExtract,
  CadParseRun,
  CadParseSummary,
  CadReferenceCandidate,
  CadReviewFinding,
  CadTextExtract,
} from "./types";

// Module-internal wire types and mappers shared by the read and mutation
// paths. These are not part of the public @/lib/api surface. CAD intake is a
// high-risk mapping surface, so the mappers assert identifiers and required
// fields; a malformed payload fails loudly instead of propagating undefined
// fields.

export type ApiCadFile = {
  cad_file_id: string;
  project_id: string;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  storage_path: string;
  upload_status: string;
  uploaded_by: string;
  limitations_note: string;
  original_file_name: string | null;
  stored_file_name: string | null;
  content_type: string | null;
  upload_source: string;
  validation_status: string | null;
  validation_message: string | null;
  max_file_size_bytes: number;
  parse_requested_at: string | null;
  parse_completed_at: string | null;
  created_at: string;
};

export type ApiParseRun = {
  parse_run_id: string;
  cad_file_id: string;
  project_id: string;
  parser_name: string;
  parser_version: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  entity_count: number;
  layer_count: number;
  block_count: number;
  text_count: number;
  warning_count: number;
  error_message: string | null;
  limitations_note: string;
};

export type ApiLayer = {
  layer_extract_id: string;
  parse_run_id: string;
  cad_file_id: string;
  project_id: string;
  layer_name: string;
  entity_count: number;
  has_text: boolean;
  has_geometry: boolean;
  review_category: string;
  requires_human_review: boolean;
};

export type ApiEntity = {
  entity_extract_id: string;
  parse_run_id: string;
  cad_file_id: string;
  project_id: string;
  entity_type: string;
  layer_name: string | null;
  block_name: string | null;
  handle: string | null;
  text_value: string | null;
  x_min: number | null;
  y_min: number | null;
  x_max: number | null;
  y_max: number | null;
  review_category: string;
  requires_human_review: boolean;
};

export type ApiBlock = {
  block_extract_id: string;
  parse_run_id: string;
  cad_file_id: string;
  project_id: string;
  block_name: string;
  insert_count: number;
  layer_names: string[];
  text_values: string[];
  review_category: string;
  requires_human_review: boolean;
};

export type ApiText = {
  text_extract_id: string;
  parse_run_id: string;
  cad_file_id: string;
  project_id: string;
  text_value: string;
  normalized_text: string;
  entity_type: string;
  layer_name: string | null;
  block_name: string | null;
  handle: string | null;
  x: number | null;
  y: number | null;
  review_category: string;
  reference_type: string;
  requires_human_review: boolean;
};

export type ApiCandidate = {
  candidate_id: string;
  parse_run_id: string;
  cad_file_id: string;
  project_id: string;
  reference_text: string;
  normalized_reference: string;
  reference_type: string;
  source_entity_id: string | null;
  source_text_id: string | null;
  matched_plan_sheet_id: string | null;
  matched_plan_reference_id: string | null;
  confidence_label: string;
  match_reason: string;
  requires_human_review: boolean;
};

export type ApiFinding = {
  cad_review_finding_id: string;
  parse_run_id: string;
  cad_file_id: string;
  project_id: string;
  finding_type: string;
  title: string;
  description: string;
  severity: string;
  source_reference_candidate_id: string | null;
  source_layer_extract_id: string | null;
  source_text_extract_id: string | null;
  linked_plan_sheet_id: string | null;
  linked_workflow_item_id: string | null;
  promoted_to_workflow: boolean;
  promoted_workflow_item_id: string | null;
  status: string;
  requires_human_review: boolean;
  created_at: string;
};

export type ApiSummary = {
  parse_run_id: string;
  cad_file_id: string;
  project_id: string;
  status: string;
  entity_count: number;
  layer_count: number;
  block_count: number;
  text_count: number;
  warning_count: number;
  reference_candidate_count: number;
  finding_count: number;
  layers_by_category: Record<string, number>;
  references_by_type: Record<string, number>;
  references_by_confidence: Record<string, number>;
  findings_by_type: Record<string, number>;
  limitations_note: string;
};

export function mapCadFile(f: ApiCadFile): CadFileUpload {
  return {
    cadFileId: requireString(f.cad_file_id, "cad_file_id"),
    projectId: requireString(f.project_id, "project_id"),
    fileName: requireString(f.file_name, "file_name"),
    fileType: requireString(f.file_type, "file_type"),
    fileSizeBytes: f.file_size_bytes,
    storagePath: f.storage_path,
    uploadStatus: requireString(f.upload_status, "upload_status"),
    uploadedBy: f.uploaded_by,
    limitationsNote: f.limitations_note,
    originalFileName: f.original_file_name ?? null,
    storedFileName: f.stored_file_name ?? null,
    contentType: f.content_type ?? null,
    uploadSource: f.upload_source ?? "sample",
    validationStatus: f.validation_status ?? null,
    validationMessage: f.validation_message ?? null,
    maxFileSizeBytes: f.max_file_size_bytes ?? 0,
    parseRequestedAt: f.parse_requested_at ?? null,
    parseCompletedAt: f.parse_completed_at ?? null,
    createdAt: f.created_at,
  };
}

export function mapParseRun(r: ApiParseRun): CadParseRun {
  return {
    parseRunId: requireString(r.parse_run_id, "parse_run_id"),
    cadFileId: requireString(r.cad_file_id, "cad_file_id"),
    projectId: requireString(r.project_id, "project_id"),
    parserName: r.parser_name,
    parserVersion: r.parser_version,
    status: requireString(r.status, "status"),
    startedAt: r.started_at,
    completedAt: r.completed_at,
    entityCount: r.entity_count,
    layerCount: r.layer_count,
    blockCount: r.block_count,
    textCount: r.text_count,
    warningCount: r.warning_count,
    errorMessage: r.error_message,
    limitationsNote: r.limitations_note,
  };
}

export function mapLayer(l: ApiLayer): CadLayerExtract {
  return {
    layerExtractId: requireString(l.layer_extract_id, "layer_extract_id"),
    parseRunId: requireString(l.parse_run_id, "parse_run_id"),
    cadFileId: requireString(l.cad_file_id, "cad_file_id"),
    projectId: requireString(l.project_id, "project_id"),
    layerName: requireString(l.layer_name, "layer_name"),
    entityCount: l.entity_count,
    hasText: l.has_text,
    hasGeometry: l.has_geometry,
    reviewCategory: l.review_category,
    requiresHumanReview: l.requires_human_review,
  };
}

export function mapEntity(e: ApiEntity): CadEntityExtract {
  return {
    entityExtractId: requireString(e.entity_extract_id, "entity_extract_id"),
    parseRunId: requireString(e.parse_run_id, "parse_run_id"),
    cadFileId: requireString(e.cad_file_id, "cad_file_id"),
    projectId: requireString(e.project_id, "project_id"),
    entityType: requireString(e.entity_type, "entity_type"),
    layerName: e.layer_name,
    blockName: e.block_name,
    handle: e.handle,
    textValue: e.text_value,
    xMin: e.x_min,
    yMin: e.y_min,
    xMax: e.x_max,
    yMax: e.y_max,
    reviewCategory: e.review_category,
    requiresHumanReview: e.requires_human_review,
  };
}

export function mapBlock(b: ApiBlock): CadBlockExtract {
  return {
    blockExtractId: requireString(b.block_extract_id, "block_extract_id"),
    parseRunId: requireString(b.parse_run_id, "parse_run_id"),
    cadFileId: requireString(b.cad_file_id, "cad_file_id"),
    projectId: requireString(b.project_id, "project_id"),
    blockName: requireString(b.block_name, "block_name"),
    insertCount: b.insert_count,
    layerNames: b.layer_names ?? [],
    textValues: b.text_values ?? [],
    reviewCategory: b.review_category,
    requiresHumanReview: b.requires_human_review,
  };
}

export function mapText(t: ApiText): CadTextExtract {
  return {
    textExtractId: requireString(t.text_extract_id, "text_extract_id"),
    parseRunId: requireString(t.parse_run_id, "parse_run_id"),
    cadFileId: requireString(t.cad_file_id, "cad_file_id"),
    projectId: requireString(t.project_id, "project_id"),
    textValue: requireString(t.text_value, "text_value"),
    normalizedText: t.normalized_text,
    entityType: t.entity_type,
    layerName: t.layer_name,
    blockName: t.block_name,
    handle: t.handle,
    x: t.x,
    y: t.y,
    reviewCategory: t.review_category,
    referenceType: t.reference_type,
    requiresHumanReview: t.requires_human_review,
  };
}

export function mapCandidate(c: ApiCandidate): CadReferenceCandidate {
  return {
    candidateId: requireString(c.candidate_id, "candidate_id"),
    parseRunId: requireString(c.parse_run_id, "parse_run_id"),
    cadFileId: requireString(c.cad_file_id, "cad_file_id"),
    projectId: requireString(c.project_id, "project_id"),
    referenceText: requireString(c.reference_text, "reference_text"),
    normalizedReference: c.normalized_reference,
    referenceType: c.reference_type,
    sourceEntityId: c.source_entity_id,
    sourceTextId: c.source_text_id,
    matchedPlanSheetId: c.matched_plan_sheet_id,
    matchedPlanReferenceId: c.matched_plan_reference_id,
    confidenceLabel: c.confidence_label,
    matchReason: c.match_reason,
    requiresHumanReview: c.requires_human_review,
  };
}

export function mapFinding(f: ApiFinding): CadReviewFinding {
  return {
    cadReviewFindingId: requireString(
      f.cad_review_finding_id,
      "cad_review_finding_id",
    ),
    parseRunId: requireString(f.parse_run_id, "parse_run_id"),
    cadFileId: requireString(f.cad_file_id, "cad_file_id"),
    projectId: requireString(f.project_id, "project_id"),
    findingType: requireString(f.finding_type, "finding_type"),
    title: requireString(f.title, "title"),
    description: f.description,
    severity: requireString(f.severity, "severity"),
    sourceReferenceCandidateId: f.source_reference_candidate_id,
    sourceLayerExtractId: f.source_layer_extract_id,
    sourceTextExtractId: f.source_text_extract_id,
    linkedPlanSheetId: f.linked_plan_sheet_id,
    linkedWorkflowItemId: f.linked_workflow_item_id,
    promotedToWorkflow: f.promoted_to_workflow ?? false,
    promotedWorkflowItemId: f.promoted_workflow_item_id ?? null,
    status: f.status,
    requiresHumanReview: f.requires_human_review,
    createdAt: f.created_at,
  };
}

export function mapSummary(s: ApiSummary): CadParseSummary {
  return {
    parseRunId: requireString(s.parse_run_id, "parse_run_id"),
    cadFileId: requireString(s.cad_file_id, "cad_file_id"),
    projectId: requireString(s.project_id, "project_id"),
    status: requireString(s.status, "status"),
    entityCount: s.entity_count,
    layerCount: s.layer_count,
    blockCount: s.block_count,
    textCount: s.text_count,
    warningCount: s.warning_count,
    referenceCandidateCount: s.reference_candidate_count,
    findingCount: s.finding_count,
    layersByCategory: s.layers_by_category,
    referencesByType: s.references_by_type,
    referencesByConfidence: s.references_by_confidence,
    findingsByType: s.findings_by_type,
    limitationsNote: s.limitations_note,
  };
}
