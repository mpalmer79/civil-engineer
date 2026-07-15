import { apiGetMapped, type ApiResult } from "../client";
import {
  mapDocument,
  mapFinding,
  mapProject,
  type ApiProjectDetail,
} from "./mappers";
import type {
  ProjectAuditEvent,
  ProjectDetail,
  ProjectDocument,
  ProjectSourceMode,
  ReviewerFinding,
} from "./types";

// Read calls return a typed ApiResult that preserves the failure status and
// category so callers can render explicit failure states instead of
// substituting simulated project records.
//
// NEXT_PUBLIC_API_BASE_URL is the backend origin only (for example
// http://localhost:8000). It must not include the /api/v1 path; this client
// appends /api/v1 paths itself.

export async function listProjects(
  sourceMode?: ProjectSourceMode | "all",
): Promise<ApiResult<ProjectDetail[]>> {
  const query =
    sourceMode && sourceMode !== "all" ? `?source_mode=${sourceMode}` : "";
  return apiGetMapped<ApiProjectDetail[], ProjectDetail[]>(
    `/api/v1/projects${query}`,
    (data) => data.map(mapProject),
  );
}

export async function getProjectDetail(
  projectId: string,
): Promise<ApiResult<ProjectDetail>> {
  return apiGetMapped<ApiProjectDetail, ProjectDetail>(
    `/api/v1/projects/${projectId}`,
    mapProject,
  );
}

export async function listProjectDocuments(
  projectId: string,
): Promise<ApiResult<ProjectDocument[]>> {
  return apiGetMapped<Record<string, unknown>[], ProjectDocument[]>(
    `/api/v1/projects/${projectId}/documents`,
    (data) => data.map(mapDocument),
  );
}

export async function getProjectDocument(
  projectId: string,
  documentId: string,
): Promise<ApiResult<ProjectDocument>> {
  const docs = await listProjectDocuments(projectId);
  if (!docs.ok) return docs;
  const doc = docs.data.find((d) => d.documentId === documentId);
  if (!doc) {
    return {
      ok: false,
      kind: "not_found",
      status: 404,
      message: "This document does not exist on this project record.",
      retryable: false,
    };
  }
  return { ...docs, data: doc };
}

export async function listProjectFindings(
  projectId: string,
): Promise<ApiResult<ReviewerFinding[]>> {
  return apiGetMapped<Record<string, unknown>[], ReviewerFinding[]>(
    `/api/v1/projects/${projectId}/findings`,
    (data) => data.map(mapFinding),
  );
}

export async function getProjectFinding(
  projectId: string,
  findingId: string,
): Promise<ApiResult<ReviewerFinding>> {
  const findings = await listProjectFindings(projectId);
  if (!findings.ok) return findings;
  const finding = findings.data.find((f) => f.findingId === findingId);
  if (!finding) {
    return {
      ok: false,
      kind: "not_found",
      status: 404,
      message: "This finding does not exist on this project record.",
      retryable: false,
    };
  }
  return { ...findings, data: finding };
}

export async function listProjectAuditEvents(
  projectId: string,
): Promise<ApiResult<ProjectAuditEvent[]>> {
  return apiGetMapped<Record<string, unknown>[], ProjectAuditEvent[]>(
    `/api/v1/projects/${projectId}/audit-events`,
    (data) =>
      data.map((e) => ({
        auditEventId: e.audit_event_id as string,
        projectId: e.project_id as string,
        eventType: e.event_type as string,
        actorType: e.actor_type as string,
        actorDisplayName: (e.actor_display_name as string) ?? null,
        relatedEntityType: e.related_entity_type as string,
        relatedEntityId: e.related_entity_id as string,
        description: e.description as string,
        timestamp: e.timestamp as string,
        eventMetadata: (e.event_metadata as Record<string, unknown>) ?? {},
      })),
  );
}
