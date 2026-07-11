import { createHash } from "node:crypto";

import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";

import { GET } from "@/app/api/proof-of-concept/download/[artifactId]/route";
import { proofManifest } from "@/lib/proof/data";

function request(artifactId: string) {
  return new NextRequest(
    `http://app.local/api/proof-of-concept/download/${encodeURIComponent(artifactId)}`,
  );
}

function params(artifactId: string) {
  return { params: Promise.resolve({ artifactId }) };
}

describe("proof artifact download route", () => {
  it("serves every artifact in the manifest with correct headers", async () => {
    for (const artifact of proofManifest.artifacts) {
      const res = await GET(
        request(artifact.artifact_id),
        params(artifact.artifact_id),
      );
      expect(res.status).toBe(200);
      expect(res.headers.get("content-type")).toBe(artifact.content_type);
      expect(res.headers.get("content-length")).toBe(
        String(artifact.file_size_bytes),
      );
      expect(res.headers.get("content-disposition")).toBe(
        `attachment; filename="${artifact.filename}"`,
      );
      const body = Buffer.from(await res.arrayBuffer());
      expect(body.byteLength).toBe(artifact.file_size_bytes);
      const digest = createHash("sha256").update(body).digest("hex");
      expect(digest).toBe(artifact.sha256);
    }
  });

  it("rejects an unknown artifact id", async () => {
    const res = await GET(request("does-not-exist"), params("does-not-exist"));
    expect(res.status).toBe(404);
  });

  it("rejects path traversal attempts", async () => {
    for (const attempt of [
      "../../package.json",
      "..%2F..%2Fpackage.json",
      "proof-dxf/../secret",
      "proof-dxf%00",
      ".hidden",
    ]) {
      const res = await GET(request(attempt), params(attempt));
      expect(res.status).toBe(404);
    }
  });

  it("rejects an empty and an oversized id", async () => {
    expect((await GET(request(""), params(""))).status).toBe(404);
    const long = "a".repeat(200);
    expect((await GET(request(long), params(long))).status).toBe(404);
  });
});
