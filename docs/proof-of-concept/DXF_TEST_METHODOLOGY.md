# DXF Test Methodology

## Reproducible harness

Two committed scripts rebuild the entire proof:

```
python scripts/generate_brookside_proof_dxf.py
python scripts/run_dxf_proof.py
```

Requirements: Python 3.12 and `backend/requirements.txt`. No API keys, no
external services, no network access.

### Generator

`scripts/generate_brookside_proof_dxf.py` builds the synthetic DXF with the
repository-pinned ezdxf version. Determinism measures:

* all coordinates come from fixed loops
* volatile header values are pinned (`$TDCREATE`, `$TDUPDATE`, GUIDs)
* the ezdxf written-by timestamp is normalized
* the CLASSES section is sorted (ezdxf emits it in per-process hash order)

Regenerating the file produces identical bytes on the same ezdxf version.

### Integration runner

`scripts/run_dxf_proof.py`:

1. Generates the DXF in memory.
2. Boots the real FastAPI application against a throwaway SQLite database
   seeded with the Brookside Meadows fixture.
3. Uploads the DXF through `POST /api/v1/projects/{id}/cad-files/upload`,
   the same multipart route the browser uses.
4. Requests parsing through `POST /api/v1/cad-files/{id}/parse`.
5. Retrieves layers, entities, blocks, text, reference candidates, and
   findings through the reviewer-facing endpoints.
6. Compares everything against `scripts/dxf_proof_expected.json` (42
   ground-truth checks, including forbidden false positives).
7. Writes the four public artifacts and the manifest with SHA-256 hashes.
8. Exits nonzero when any check fails.

No test-only shortcut bypasses the production parser.

## Exercised pipeline

1. File upload (`backend/app/api/v1/cad_intake.py`)
2. Intake validation (`cad_intake_service.validate_cad_upload_file`)
3. Safe storage registration (`cad_intake_service.save_uploaded_dxf_file`)
4. DXF parse request (`backend/app/api/v1/cad_intake.py`)
5. ezdxf processing (`cad_intake_service.parse_dxf_file`)
6. Layer extraction and classification
   (`backend/app/services/cad/layer_taxonomy.py`)
7. Entity extraction with safe bounds
   (`backend/app/services/cad/geometry.py`)
8. Text extraction (`cad_intake_service`)
9. Block extraction (`cad_intake_service`)
10. Reference parsing (`backend/app/services/cad/reference_parser.py`)
11. Facility identity and review-support findings
    (`backend/app/services/cad/facility_identity.py`)
12. Database persistence (`backend/app/db/models.py`)
13. Reviewer-facing result retrieval (`backend/app/api/v1/cad_intake.py`)

## Continuous integration

The `dxf-proof` CI job reruns the harness on every push and then runs
`git diff --exit-code public/proof-of-concept`, so the committed artifacts
must exactly match a fresh regeneration. The `e2e` job additionally uploads
the same DXF through the browser (Playwright), verifies the parse results in
the UI, and confirms no backend token reaches browser-readable storage.

## Test corpus

Beyond the proof drawing, `backend/tests/test_cad_dxf_corpus.py` runs a
generated fixture corpus through the same upload and parse endpoints: layer
aliases, minimal and malformed files, oversized uploads, entity-count
truncation, nested and transformed blocks, model and paper space, unicode,
reference scenarios, facility-number overlap, existing versus proposed
layers, and unknown-layer-heavy drawings. Unit suites cover the taxonomy
(40-entry labeled corpus), facility identity, reference parsing (including
negative cases), and geometry bounds.
