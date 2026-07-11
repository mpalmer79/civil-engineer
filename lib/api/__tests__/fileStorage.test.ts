import { unwrap } from "./testHelpers";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  getDocumentStorageStatus,
  getStorageHealth,
} from "@/lib/api";

function mockFetchOnce(payload: unknown, ok = true, status = 200) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok,
    status,
    json: async () => payload,
  } as Response);
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("getDocumentStorageStatus", () => {
  it("maps the snake_case storage status without building a browser auth header", async () => {
    mockFetchOnce({
      document_id: "doc_1",
      project_id: "proj_1",
      file_available: true,
      storage_provider: "local",
      processing_status: "indexed_with_text",
      content_type: "application/pdf",
      file_size_bytes: 1234,
      checksum_sha256: "abc123",
      download_count: 2,
      last_downloaded_at: "2026-06-26T00:00:00Z",
    });
    const status = unwrap(await getDocumentStorageStatus("proj_1", "doc_1"));
    expect(status?.fileAvailable).toBe(true);
    expect(status?.storageProvider).toBe("local");
    expect(status?.downloadCount).toBe(2);
    const headers = (
      (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock
        .calls[0][1] as RequestInit
    ).headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
  });

  it("returns null when the backend is unreachable", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("down"));
    const status = await getDocumentStorageStatus("proj_1", "doc_1");
    expect(status.ok).toBe(false);
    if (!status.ok) expect(status.kind).toBe("network");
  });
});

describe("getStorageHealth", () => {
  it("maps the provider health", async () => {
    mockFetchOnce({
      provider: "local",
      configured: true,
      detail: "Local development storage is configured.",
    });
    const health = unwrap(await getStorageHealth());
    expect(health?.provider).toBe("local");
    expect(health?.configured).toBe(true);
  });
});

describe("downloadDocument", () => {
  it("reports a backend error without building a browser auth header", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: "The stored file is not available." }),
    } as Response);
    const { downloadDocument } = await import("@/lib/api");
    const result = await downloadDocument("proj_1", "doc_1", "plan.pdf");
    expect(result.ok).toBe(false);
    expect(result.error).toContain("not available");
    const headers = (
      (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock
        .calls[0][1] as RequestInit
    ).headers as Record<string, string>;
    expect(headers.Authorization).toBeUndefined();
  });
});
