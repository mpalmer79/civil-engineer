import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  formatBytes,
  proofManifest,
  proofResult,
  validateProofResult,
  type ProofResult,
} from "@/lib/proof/data";

const ARTIFACT_DIR = path.join(
  process.cwd(),
  "public",
  "proof-of-concept",
  "dxf",
);

describe("proof manifest consistency", () => {
  it("lists exactly four artifacts with unique ids", () => {
    expect(proofManifest.artifacts).toHaveLength(4);
    const ids = proofManifest.artifacts.map((a) => a.artifact_id);
    expect(new Set(ids).size).toBe(4);
  });

  it("marks every artifact synthetic with a snapshot id", () => {
    for (const artifact of proofManifest.artifacts) {
      expect(artifact.synthetic).toBe(true);
      expect(artifact.snapshot_id).toBe(proofManifest.snapshot_id);
    }
  });

  it("matches the bytes on disk for size and sha256", () => {
    for (const artifact of proofManifest.artifacts) {
      const data = readFileSync(path.join(ARTIFACT_DIR, artifact.filename));
      expect(data.byteLength).toBe(artifact.file_size_bytes);
      const digest = createHash("sha256").update(data).digest("hex");
      expect(digest).toBe(artifact.sha256);
    }
  });

  it("declares a download route for each artifact", () => {
    for (const artifact of proofManifest.artifacts) {
      expect(artifact.download_route).toBe(
        `/api/proof-of-concept/download/${artifact.artifact_id}`,
      );
    }
  });

  it("covers the four required artifact formats", () => {
    const types = proofManifest.artifacts.map((a) => a.file_type).sort();
    expect(types).toEqual(["dxf", "json", "markdown", "zip"]);
  });
});

describe("proof result integrity", () => {
  it("passes its own validation", () => {
    const validation = validateProofResult();
    expect(validation.problems).toEqual([]);
    expect(validation.ok).toBe(true);
  });

  it("records every ground-truth check as passing", () => {
    expect(proofResult.checks.length).toBeGreaterThan(30);
    expect(proofResult.checks.every((check) => check.pass)).toBe(true);
  });

  it("is marked synthetic and states its boundary", () => {
    expect(proofResult.synthetic).toBe(true);
    expect(proofResult.boundary_statement).toContain("does not verify CAD");
    expect(proofResult.boundary_statement).toContain("human review");
  });

  it("does not pair detention and infiltration basin 1 as a conflict", () => {
    const conflicts = proofResult.findings.filter(
      (finding) => finding.finding_type === "possible_label_conflict",
    );
    for (const conflict of conflicts) {
      const pairsBoth =
        conflict.description.includes("DETENTION BASIN 1") &&
        conflict.description.includes("INFILTRATION BASIN 1");
      expect(pairsBoth).toBe(false);
    }
  });

  it("classifies the five previously over-flagged layers", () => {
    const categories = Object.fromEntries(
      proofResult.layers.map((layer) => [layer.layer_name, layer.category]),
    );
    expect(categories["C-PROP"]).toBe("property_boundary");
    expect(categories["C-ROAD"]).toBe("road_alignment");
    expect(categories["C-LOTS"]).toBe("lots_parcels");
    expect(categories["C-LABEL"]).toBe("annotation");
    expect(categories["C-LANDSCAPE"]).toBe("landscape");
  });

  it("detects tampered metrics", () => {
    const tampered = {
      ...proofResult,
      counts: { ...proofResult.counts, entities: 9999 },
    } as ProofResult;
    const validation = validateProofResult(tampered);
    expect(validation.ok).toBe(false);
    expect(
      validation.problems.some((problem) =>
        problem.includes("Entity type totals"),
      ),
    ).toBe(true);
  });

  it("detects a failed embedded check", () => {
    const tampered = {
      ...proofResult,
      checks: [
        ...proofResult.checks,
        { check: "example", expected: 1, actual: 2, pass: false },
      ],
    } as ProofResult;
    expect(validateProofResult(tampered).ok).toBe(false);
  });
});

describe("formatBytes", () => {
  it("formats sizes across ranges", () => {
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(2048)).toBe("2.0 KB");
    expect(formatBytes(3 * 1024 * 1024)).toBe("3.00 MB");
  });
});
