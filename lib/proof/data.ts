// Proof-of-concept data access. The page renders exclusively from the
// generated artifacts (manifest.json and the structured test result), so the
// displayed metrics can never drift from the evidence: validateProofResult
// re-checks the artifact's own ground-truth checks and cross-checks the
// headline counts against the detailed rows, and the page fails visibly when
// anything disagrees.

import manifestJson from "@/public/proof-of-concept/dxf/manifest.json";
import resultJson from "@/public/proof-of-concept/dxf/brookside_meadows_dxf_test_result.json";

export interface ProofArtifact {
  artifact_id: string;
  display_name: string;
  filename: string;
  description: string;
  file_type: string;
  content_type: string;
  file_size_bytes: number;
  sha256: string;
  snapshot_id: string;
  synthetic: boolean;
  download_route: string;
  related_test_scenario: string;
  source_generator: string;
}

export interface ProofManifest {
  snapshot_id: string;
  synthetic_disclosure: string;
  artifacts: ProofArtifact[];
}

export interface ProofPipelineStage {
  stage: string;
  boundary: string;
  module: string;
}

export interface ProofLayer {
  layer_name: string;
  entity_count: number;
  category: string;
  requires_human_review: boolean;
  classification_rule: {
    rule_kind: string;
    confidence: string;
    explanation: string;
  };
}

export interface ProofReference {
  reference_text: string;
  normalized_reference: string;
  reference_type: string;
  match_state: string;
  confidence_label: string;
  match_reason: string;
}

export interface ProofFinding {
  finding_type: string;
  severity: string;
  title: string;
  description: string;
  requires_human_review: boolean;
  deterministic_rule: boolean;
}

export interface ProofCheck {
  check: string;
  expected: unknown;
  actual: unknown;
  pass: boolean;
}

export interface ProofResult {
  snapshot_id: string;
  fixture_version: string;
  synthetic: boolean;
  parser: { name: string; version: string };
  drawing_units: string;
  pipeline: ProofPipelineStage[];
  intake: {
    upload_http_status: number;
    validation_status: string;
    parse_status: string;
  };
  counts: Record<string, number>;
  entity_types: Record<string, number>;
  layers: ProofLayer[];
  blocks: { block_name: string; insert_count: number }[];
  references: ProofReference[];
  findings: ProofFinding[];
  checks: ProofCheck[];
  limitations: string[];
  boundary_statement: string;
}

export const proofManifest = manifestJson as ProofManifest;
export const proofResult = resultJson as ProofResult;

export interface ProofValidation {
  ok: boolean;
  problems: string[];
}

// Cross-checks the structured artifact against itself and the manifest. The
// page must not display metrics that the artifact's evidence does not
// support.
export function validateProofResult(
  result: ProofResult = proofResult,
  manifest: ProofManifest = proofManifest,
): ProofValidation {
  const problems: string[] = [];

  for (const check of result.checks) {
    if (!check.pass) {
      problems.push(
        `Ground-truth check failed in the artifact: ${check.check}`,
      );
    }
  }

  if (result.references.length !== result.counts.reference_candidates) {
    problems.push(
      "Reference rows disagree with the reference candidate count.",
    );
  }
  if (result.findings.length !== result.counts.findings) {
    problems.push("Finding rows disagree with the finding count.");
  }
  if (result.layers.length !== result.counts.layers) {
    problems.push("Layer rows disagree with the layer count.");
  }

  const matched = result.references.filter(
    (reference) => reference.match_state === "matched",
  ).length;
  if (matched !== result.counts.matched_references) {
    problems.push("Matched reference rows disagree with the matched count.");
  }
  const missingOrAmbiguous = result.references.filter(
    (reference) =>
      reference.match_state === "missing" ||
      reference.match_state === "ambiguous",
  ).length;
  if (missingOrAmbiguous !== result.counts.missing_or_ambiguous_references) {
    problems.push(
      "Missing and ambiguous rows disagree with the reported count.",
    );
  }

  const entityTotal = Object.values(result.entity_types).reduce(
    (sum, value) => sum + value,
    0,
  );
  if (entityTotal !== result.counts.entities) {
    problems.push("Entity type totals disagree with the entity count.");
  }

  if (manifest.artifacts.length !== 4) {
    problems.push("The manifest must list exactly four artifacts.");
  }
  if (manifest.snapshot_id !== result.snapshot_id) {
    problems.push("Manifest and result snapshot identifiers disagree.");
  }
  for (const artifact of manifest.artifacts) {
    if (!/^[0-9a-f]{64}$/.test(artifact.sha256)) {
      problems.push(`Artifact ${artifact.artifact_id} has an invalid hash.`);
    }
    if (!artifact.synthetic) {
      problems.push(
        `Artifact ${artifact.artifact_id} is not marked synthetic.`,
      );
    }
  }

  if (!result.synthetic) {
    problems.push("The result is not marked synthetic.");
  }

  return { ok: problems.length === 0, problems };
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}
