// Controlled proof-artifact downloads. The artifact ID is looked up in the
// generated manifest allowlist; nothing about the request selects a
// filesystem path. Unknown IDs, traversal attempts, and anything not in the
// manifest return 404.

import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import path from "node:path";

import { NextRequest, NextResponse } from "next/server";

import { proofManifest } from "@/lib/proof/data";

const ARTIFACT_DIR = path.join(
  process.cwd(),
  "public",
  "proof-of-concept",
  "dxf",
);

const ARTIFACT_ID_PATTERN = /^[a-z][a-z0-9-]{0,63}$/;

export async function GET(
  _request: NextRequest,
  context: { params: Promise<{ artifactId: string }> },
): Promise<NextResponse> {
  const { artifactId } = await context.params;

  if (!ARTIFACT_ID_PATTERN.test(artifactId)) {
    return NextResponse.json(
      { detail: "Unknown proof artifact." },
      { status: 404 },
    );
  }

  const artifact = proofManifest.artifacts.find(
    (entry) => entry.artifact_id === artifactId,
  );
  if (!artifact) {
    return NextResponse.json(
      { detail: "Unknown proof artifact." },
      { status: 404 },
    );
  }

  // The filename comes from the generated manifest, never from the request.
  const filePath = path.join(ARTIFACT_DIR, path.basename(artifact.filename));
  let data: Buffer;
  try {
    data = await readFile(filePath);
  } catch {
    return NextResponse.json(
      { detail: "Proof artifact unavailable." },
      { status: 404 },
    );
  }

  // Integrity: the served bytes must match the manifest hash. A mismatch
  // means the artifacts and manifest are out of sync, which is a build
  // problem the client should see as unavailable rather than silently
  // receiving different content.
  const digest = createHash("sha256").update(data).digest("hex");
  if (digest !== artifact.sha256) {
    return NextResponse.json(
      { detail: "Proof artifact failed its integrity check." },
      { status: 500 },
    );
  }

  return new NextResponse(new Uint8Array(data), {
    status: 200,
    headers: {
      "content-type": artifact.content_type,
      "content-length": String(data.byteLength),
      "content-disposition": `attachment; filename="${artifact.filename}"`,
      "cache-control": "public, max-age=3600",
      "x-proof-sha256": artifact.sha256,
    },
  });
}
