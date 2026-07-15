import { requireString } from "../client";
import type { ReviewCycle } from "./types";

// Module-internal wire mapping helpers shared by the read and mutation paths.
// These are not part of the public @/lib/api surface.

export type Json = Record<string, unknown>;

export function camel<T>(obj: Json | null | undefined): T {
  const out: Json = {};
  if (!obj) return out as T;
  for (const [key, value] of Object.entries(obj)) {
    const ck = key.replace(/_([a-z])/g, (_m, c: string) => c.toUpperCase());
    out[ck] = value;
  }
  return out as T;
}

export function mapReviewCycle(d: Json): ReviewCycle {
  return camel<ReviewCycle>(d);
}

// Strict read-path mapper. The requireString assertions make a structurally
// invalid backend payload surface as an explicit invalid_response failure
// through apiGetMapped instead of propagating undefined fields into the UI.
export function mapReviewCycleRead(d: Json): ReviewCycle {
  requireString(d.review_cycle_id, "review_cycle_id");
  requireString(d.project_id, "project_id");
  return mapReviewCycle(d);
}
