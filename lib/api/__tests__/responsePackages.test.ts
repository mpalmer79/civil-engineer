import { unwrap } from "./testHelpers";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  generateResponsePackage,
  getResponsePackage,
  getResponsePackages,
  updateResponseItemDraftText,
} from "@/lib/api";

function mockFetchOnce(payload: unknown, ok = true, status = 200) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok,
    status,
    json: async () => payload,
  } as Response);
}

function mockFetchUnreachable() {
  globalThis.fetch = vi.fn().mockRejectedValue(new Error("backend down"));
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("response package API mapping", () => {
  it("maps a snake_case package list to the camelCase shape", async () => {
    mockFetchOnce([
      {
        response_package_id: "resp_1",
        project_id: "proj_brookside_meadows",
        source_packet_id: "packet_1",
        title: "Brookside Meadows draft review-support response package",
        audience_type: "design_engineer",
        status: "draft",
        summary: "Draft external response package.",
        draft_intro: "Thank you for the submission.",
        draft_closing: "Please direct questions to the reviewing office.",
        limitations_note: "Draft material.",
        created_by: "system",
        created_at: "2026-06-24T00:00:00Z",
        updated_at: "2026-06-24T00:00:00Z",
      },
    ]);

    const packages = unwrap(await getResponsePackages());
    expect(packages).toHaveLength(1);
    expect(packages[0].responsePackageId).toBe("resp_1");
    expect(packages[0].audienceType).toBe("design_engineer");
    expect(packages[0].sourcePacketId).toBe("packet_1");
  });

  it("maps a package detail with sections, items, and attachments", async () => {
    mockFetchOnce({
      response_package_id: "resp_1",
      project_id: "proj_brookside_meadows",
      source_packet_id: "packet_1",
      title: "Title",
      audience_type: "applicant",
      status: "draft",
      summary: "Summary",
      draft_intro: "Intro",
      draft_closing: "Closing",
      limitations_note: "Limits",
      created_by: "system",
      created_at: "2026-06-24T00:00:00Z",
      updated_at: "2026-06-24T00:00:00Z",
      sections: [
        {
          section_id: "rsec_1",
          response_package_id: "resp_1",
          title: "Requested revisions",
          section_type: "requested_revisions",
          display_order: 1,
          summary: "Items",
          status: "draft",
          requires_human_review: true,
          items: [
            {
              item_id: "ritem_1",
              response_package_id: "resp_1",
              section_id: "rsec_1",
              workflow_item_id: "wfi_1",
              packet_item_id: "item_1",
              title: "Basin outlet detail",
              draft_text: "Please clarify the plan reference.",
              reviewer_note: null,
              severity: "medium",
              status: "draft",
              source_type: "plan_consistency_finding",
              source_id: "pcf_1",
              assigned_role: "plan_reviewer",
              requires_human_review: true,
              display_order: 0,
              evidence_links: [
                {
                  evidence_link_id: "revl_1",
                  response_package_id: "resp_1",
                  response_item_id: "ritem_1",
                  evidence_type: "plan_sheet",
                  evidence_id: "sheet_1",
                  relationship: "plan_sheet",
                  label: "C-3.0",
                  description: null,
                },
              ],
            },
          ],
        },
      ],
      attachments: [
        {
          attachment_id: "ratt_1",
          response_package_id: "resp_1",
          label: "Draft review-support response summary",
          attachment_type: "review_support_summary",
          source_type: "response_package",
          source_id: "resp_1",
          included: true,
          description: "Printable draft.",
        },
      ],
    });

    const detail = unwrap(await getResponsePackage("resp_1"));
    expect(detail).not.toBeNull();
    expect(detail?.sections[0].items[0].workflowItemId).toBe("wfi_1");
    expect(detail?.sections[0].items[0].evidenceLinks[0].label).toBe("C-3.0");
    expect(detail?.attachments[0].attachmentType).toBe("review_support_summary");
  });

  it("surfaces a backend error detail on a rejected draft text edit", async () => {
    mockFetchOnce(
      { detail: "draft_text contains prohibited final-decision wording." },
      false,
      422,
    );
    const result = await updateResponseItemDraftText(
      "resp_1",
      "ritem_1",
      "This plan is approved.",
      undefined,
      "Town Engineer",
    );
    expect(result.ok).toBe(false);
    expect(result.status).toBe(422);
    expect(result.error).toContain("prohibited");
  });

  it("reports the backend unreachable on a network failure", async () => {
    mockFetchUnreachable();
    const packages = await getResponsePackages();
    expect(packages.ok).toBe(false);

    const result = await generateResponsePackage();
    expect(result.ok).toBe(false);
    expect(result.backendReachable).toBe(false);
  });
});
