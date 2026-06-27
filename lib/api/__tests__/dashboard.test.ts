import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { setAuthToken, clearAuthToken } from "@/lib/api/client";
import {
  getReviewerDashboard,
  getReviewerQueue,
  getOrganizationDashboard,
  updateProjectPriority,
} from "@/lib/api/dashboard";
import { getProjectWorkloadSummary } from "@/lib/api/operationalMetrics";

function reviewerPayload() {
  return {
    scope: "reviewer",
    generated_at: "2026-06-26T00:00:00Z",
    user_id: "u1",
    display_name: "Reviewer One",
    accessible_project_count: 2,
    projects_with_pending_action_count: 1,
    totals: {
      documents_needing_indexing: 3,
      pending_reviewer_action_count: 5,
      response_packages_ready_for_handoff: 1,
      applicant_responses_needing_review: 2,
    },
    projects: [
      {
        project_id: "proj_1",
        project_name: "Brookside Meadows",
        status: "under_review_support",
        source_mode: "demo_fixture",
        organization_id: "org_1",
        assigned_reviewer_user_id: null,
        assigned_reviewer_name: null,
        review_priority: "standard",
        review_due_date: null,
        last_reviewer_activity_at: null,
        age_bucket: "updated_today",
        due_date_indicators: [],
        pending_reviewer_action_count: 5,
        has_pending_reviewer_action: true,
        metrics: { documents_needing_indexing: 3 },
      },
    ],
    queue: [
      {
        queue_item_id: "proj_1:documents_needing_indexing",
        project_id: "proj_1",
        project_name: "Brookside Meadows",
        item_type: "document_indexing",
        label: "Documents needing indexing",
        count: 3,
        status: "pending_reviewer_action",
        age_bucket: "updated_today",
        target_path: "/projects/proj_1/documents",
      },
    ],
    access_note: "Operational indicators only.",
  };
}

beforeEach(() => {
  clearAuthToken();
});

afterEach(() => {
  vi.restoreAllMocks();
  clearAuthToken();
});

describe("dashboard API client", () => {
  it("sends the Authorization header on protected routes", async () => {
    setAuthToken("tok-123");
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => reviewerPayload(),
    } as Response);
    globalThis.fetch = fetchMock;

    const result = await getReviewerDashboard();
    expect(result.ok).toBe(true);
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = init.headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer tok-123");
    // The client appends the /api/v1 path itself.
    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/dashboard/reviewer");
  });

  it("maps snake_case dashboard payloads to camelCase", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => reviewerPayload(),
    } as Response);

    const result = await getReviewerDashboard();
    expect(result.data?.accessibleProjectCount).toBe(2);
    expect(result.data?.totals.pendingReviewerActionCount).toBe(5);
    expect(result.data?.projects[0].ageBucket).toBe("updated_today");
    expect(result.data?.queue[0].itemType).toBe("document_indexing");
    expect(result.data?.queue[0].targetPath).toBe("/projects/proj_1/documents");
  });

  it("preserves a 403 status so a permission denial is distinguishable", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ detail: "You are not a member of this organization." }),
    } as Response);

    const result = await getOrganizationDashboard("org_x");
    expect(result.ok).toBe(false);
    expect(result.status).toBe(403);
    expect(result.backendReachable).toBe(true);
  });

  it("reports backend unavailability without throwing", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("down"));
    const result = await getReviewerQueue();
    expect(result.ok).toBe(false);
    expect(result.backendReachable).toBe(false);
  });

  it("sends priority updates with snake_case body", async () => {
    setAuthToken("tok-9");
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => reviewerPayload().projects[0],
    } as Response);
    globalThis.fetch = fetchMock;

    await updateProjectPriority("proj_1", { reviewPriority: "elevated" });
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(init.body as string)).toMatchObject({
      review_priority: "elevated",
    });
  });

  it("maps a project workload summary payload", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        scope: "project",
        generated_at: "2026-06-26T00:00:00Z",
        project_id: "proj_1",
        project_name: "Brookside Meadows",
        status: "under_review_support",
        source_mode: "demo_fixture",
        organization_id: "org_1",
        assigned_reviewer_user_id: null,
        assigned_reviewer_name: null,
        review_priority: null,
        review_due_date: null,
        last_reviewer_activity_at: null,
        age_bucket: "waiting_1_to_3_days",
        due_date_indicators: [],
        pending_reviewer_action_count: 4,
        has_pending_reviewer_action: true,
        metrics: { documents_uploaded: 2 },
        queue: [],
        access_note: "Operational indicators only.",
      }),
    } as Response);

    const result = await getProjectWorkloadSummary("proj_1");
    expect(result.ok).toBe(true);
    expect(result.data?.ageBucket).toBe("waiting_1_to_3_days");
    expect(result.data?.metrics.documentsUploaded).toBe(2);
  });
});
