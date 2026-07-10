import { PROJECT_ID, apiFetch, type DemoSourced } from "./client";
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

export async function getAuditEvents(): Promise<DemoSourced<AuditEvent[]>> {
  const result = await apiFetch<ApiAuditEvent[]>(
    `/api/v1/projects/${PROJECT_ID}/audit-events`,
  );
  // Explicit public-demo policy: when the demo backend is unreachable this
  // surface renders the repository fixture snapshot and says so. Authenticated
  // surfaces never do this; see docs/adr/0002-data-source-boundaries.md.
  if (!result.ok) return { data: staticAuditEvents, source: "demo_fixture" };
  const data = result.data;
  return { source: "backend_seeded", data: data.map((e) => ({
    auditEventId: e.audit_event_id,
    eventType: e.event_type,
    actorType: e.actor_type,
    relatedEntity: e.related_entity_id,
    timestamp: e.timestamp,
    description: e.description,
  })) };
}
