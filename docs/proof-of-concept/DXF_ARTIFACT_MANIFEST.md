# DXF Artifact Manifest

The proof artifacts live under `public/proof-of-concept/dxf/` and are
described by `manifest.json` in the same directory. The manifest is generated
by `scripts/run_dxf_proof.py`; it is never edited by hand.

## Artifacts

| Artifact ID | File | Type |
| --- | --- | --- |
| proof-dxf | brookside_meadows_realistic_submission.dxf | application/dxf |
| proof-result | brookside_meadows_dxf_test_result.json | application/json |
| proof-report | DXF_INTEGRATION_TEST_REPORT.md | text/markdown |
| proof-bundle | civil_engineer_dxf_test_bundle.zip | application/zip |

Each manifest entry records: artifact ID, display name, filename,
description, file type, content type, size in bytes, SHA-256 hash, snapshot
identifier, synthetic status, download route, related test scenario, and the
source generator. A snapshot identifier is used instead of a build date so
nothing reads as live activity.

## Download controls

Downloads go through `/api/proof-of-concept/download/{artifactId}`
(`app/api/proof-of-concept/download/[artifactId]/route.ts`):

* the artifact ID is validated against a strict pattern and then looked up
  in the manifest allowlist; the request never selects a filesystem path
* unknown IDs, traversal attempts, and encoded traversal return 404
* served bytes are re-hashed and must match the manifest SHA-256; a
  mismatch returns an error instead of silently serving different content
* responses carry the manifest content type, content length, an attachment
  content disposition with the exact filename, and cache headers

## Freshness

The `dxf-proof` CI job regenerates all artifacts and fails on any byte
difference from the committed files, so the manifest, the artifacts, and the
page that renders them cannot drift apart. Unit tests
(`lib/proof/__tests__/proofData.test.ts`) additionally verify the manifest
against the bytes on disk, and Playwright downloads every artifact and
re-verifies its hash end to end.

All artifacts are synthetic review-support data generated from the fictional
Brookside Meadows scenario.
