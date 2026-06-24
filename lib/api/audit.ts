import { PROJECT_ID, safeFetch } from "./client";
import { auditEvents as staticAuditEvents, type AuditEvent } from "@/data/auditEvents";

type ApiAuditEvent = {
  audit_event_id: string;
  event_type: string;
  actor_type: AuditEvent["actorType"];
  related_entity_type: string;
  related_entity_id: string;
  description: string;
  timestamp: string;
};

export async function getAuditEvents(): Promise<AuditEvent[]> {
  const data = await safeFetch<ApiAuditEvent[]>(
    `/api/v1/projects/${PROJECT_ID}/audit-events`,
  );
  if (!data) return staticAuditEvents;
  return data.map((e) => ({
    auditEventId: e.audit_event_id,
    eventType: e.event_type,
    actorType: e.actor_type,
    relatedEntity: e.related_entity_id,
    timestamp: e.timestamp,
    description: e.description,
  }));
}
